#!/usr/bin/env python3
"""
qa-env-override — generate a per-task docker-compose override for isolated QA.

Part of the /dev-loop pipeline's environment-isolation binding (see
.claude/dev-loop-adapter.md §6). Wave-parallel tasks each run their own copy of
the dev stack; COMPOSE_PROJECT_NAME isolates containers/networks/volumes, but the
base compose pins host ports, so parallel stacks would still collide on
3306/8080/3000/9090/3001. This tool emits an override that shifts every published
host port by the task's wave slot, leaving container ports (and thus the internal
service-to-service URLs on the isolated network) untouched.

Host port for a service = <base published port> + (slot + 1) * offset-step.

The `+ 1` reserves the base ports: a QA stack never sits on them, so a developer's
own `docker compose up` (or another tool on the default ports) is never displaced,
and slot 0 — the first/only task in a run — is already isolated. Slots 0,1,2,…
land in successive bands above the base.

Usage:
    scripts/qa-env-override.py --task T-201 --slot 2
    scripts/qa-env-override.py --task T-201 --slot 2 --json
    scripts/qa-env-override.py --task T-101 --slot 0 \
        --smoke domain-service:/api/v1/people/1/experiences

The override auto-discovers every service that publishes a host port, so it stays
correct if the base compose gains or loses a service — nothing here is hardcoded
to the current five. A smoke command is emitted only when you name the endpoint to
probe (`--smoke SERVICE:PATH`); the tool never guesses one, since the right check
depends on the task, not the stack.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    sys.exit("qa-env-override: PyYAML is required (pip install pyyaml).")

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_PREFIX = "cvdl_"
# Docker Compose project names: lowercase, must start alnum, then [a-z0-9_-].
_SANITIZE = re.compile(r"[^a-z0-9_-]+")


class OverrideList(list):
    """A list rendered with Compose's `!override` tag so it *replaces* the base
    sequence instead of being appended to it. Without this, a per-task override
    would publish both the base host port and the shifted one — and the base
    ports would still collide across parallel stacks. Requires Docker Compose
    >= 2.24 (the tag is a no-op error on older versions)."""


def _represent_override(dumper, data):
    return dumper.represent_sequence("!override", list(data), flow_style=False)


yaml.add_representer(OverrideList, _represent_override, Dumper=yaml.SafeDumper)


def project_name(task: str) -> str:
    slug = _SANITIZE.sub("-", task.strip().lower()).strip("-_")
    if not slug:
        raise ValueError(f"task id {task!r} has no usable characters")
    name = f"{PROJECT_PREFIX}{slug}"
    if not re.match(r"^[a-z0-9]", name):
        name = f"c{name}"
    return name


def _parse_short(entry: str):
    """Parse a short-form port string into (prefix_ip, published, tail).

    tail is the container-port portion, preserved verbatim (may carry /proto).
    Returns None when there is no fixed published host port to remap.
    """
    parts = entry.split(":")
    if len(parts) == 1:
        # "container[/proto]" — ephemeral host port, nothing to shift.
        return None
    if len(parts) == 2:
        published, tail = parts[0], parts[1]
        prefix_ip = ""
    elif len(parts) == 3:
        prefix_ip, published, tail = parts[0], parts[1], parts[2]
    else:
        raise ValueError(f"unsupported port syntax: {entry!r}")
    if "-" in published:
        raise ValueError(f"port ranges are not supported: {entry!r}")
    if not published.isdigit():
        raise ValueError(f"cannot parse published port in {entry!r}")
    return prefix_ip, int(published), tail


def remap_service_ports(ports, offset):
    """Return (new_port_list, mappings) for one service's `ports:` block.

    new_port_list uses the same syntax style as the input entries.
    mappings is a list of {published, target} for reporting.
    """
    new_list = []
    mappings = []
    for entry in ports:
        if isinstance(entry, dict):
            published = entry.get("published")
            target = entry.get("target")
            if published is None:
                continue  # ephemeral — leave to the base file
            new_pub = int(published) + offset
            new_entry = dict(entry)
            new_entry["published"] = new_pub
            new_list.append(new_entry)
            mappings.append({"published": new_pub, "target": target})
            continue

        parsed = _parse_short(str(entry))
        if parsed is None:
            continue
        prefix_ip, published, tail = parsed
        new_pub = published + offset
        container = tail.split("/")[0]
        rebuilt = f"{new_pub}:{tail}" if not prefix_ip else f"{prefix_ip}:{new_pub}:{tail}"
        new_list.append(rebuilt)
        mappings.append({"published": new_pub, "target": container})
    return new_list, mappings


def build_override(compose: dict, offset: int):
    services = {}
    report = {}
    for name, svc in (compose.get("services") or {}).items():
        ports = svc.get("ports")
        if not ports:
            continue
        new_list, mappings = remap_service_ports(ports, offset)
        if new_list:
            services[name] = {"ports": OverrideList(new_list)}
            report[name] = mappings
    return {"services": services}, report


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="qa-env-override",
        description="Generate a per-task docker-compose override for isolated QA.",
    )
    ap.add_argument("--task", required=True, help="task id, e.g. T-201")
    ap.add_argument("--slot", type=int, default=0,
                    help="wave slot (0,1,2,…); host offset = (slot+1) * offset-step, "
                         "so base ports stay free even at slot 0")
    ap.add_argument("--offset-step", type=int, default=10,
                    help="host-port band width per slot (default 10)")
    ap.add_argument("--smoke", metavar="SERVICE:PATH", default=None,
                    help="emit a smoke curl for this endpoint, e.g. "
                         "domain-service:/api/v1/people/1/experiences (no default)")
    ap.add_argument("--compose", default=str(REPO_ROOT / "docker-compose.dev.yml"),
                    help="base compose file (default: docker-compose.dev.yml)")
    ap.add_argument("--out-dir", default=str(REPO_ROOT),
                    help="where to write the override (default: repo root)")
    out_mode = ap.add_mutually_exclusive_group()
    out_mode.add_argument("--json", action="store_true",
                          help="write the file and print a machine-readable summary")
    out_mode.add_argument("--stdout", action="store_true",
                          help="print the override YAML to stdout, write no file")
    args = ap.parse_args(argv)

    if args.slot < 0:
        ap.error("--slot must be >= 0")

    compose_path = Path(args.compose)
    if not compose_path.is_file():
        ap.error(f"base compose not found: {compose_path}")

    try:
        proj = project_name(args.task)
    except ValueError as exc:
        ap.error(str(exc))

    # (slot + 1): reserve the base ports so a QA stack never displaces a manual
    # `docker compose up`, and slot 0 is already isolated.
    offset = (args.slot + 1) * args.offset_step
    base = yaml.safe_load(compose_path.read_text()) or {}
    override, report = build_override(base, offset)

    header = (
        f"# GENERATED by scripts/qa-env-override.py — do not edit by hand.\n"
        f"# task={args.task} slot={args.slot} offset=+{offset} "
        f"base={compose_path.name}\n"
        f"# Isolated QA stack for the /dev-loop pipeline (adapter §6).\n"
        f"# `!override` replaces the base ports (requires Docker Compose >= 2.24).\n"
        f"# Bring up:  COMPOSE_PROJECT_NAME={proj} \\\n"
        f"#   docker compose -f {compose_path.name} -f {{this file}} up --build\n"
    )
    body = yaml.safe_dump(override, sort_keys=False, default_flow_style=False)
    content = header + body

    override_name = f"docker-compose.override.{proj}.yml"
    override_path = Path(args.out_dir) / override_name

    if args.stdout:
        sys.stdout.write(content)
    else:
        override_path.write_text(content)

    up_cmd = (
        f"COMPOSE_PROJECT_NAME={proj} "
        f"docker compose -f {compose_path.name} -f {override_name} up --build -d"
    )
    down_cmd = (
        f"COMPOSE_PROJECT_NAME={proj} "
        f"docker compose -f {compose_path.name} -f {override_name} down -v"
    )
    # Where each service is reachable on the host, task-agnostic — QA builds its
    # own check from the task's acceptance criteria against these.
    endpoints = {svc: ms[0]["published"] for svc, ms in report.items() if ms}

    smoke = None
    if args.smoke is not None:
        svc, _, path = args.smoke.partition(":")
        if not svc or not path:
            ap.error("--smoke must be SERVICE:PATH, e.g. "
                     "domain-service:/api/v1/people/1/experiences")
        if svc not in endpoints:
            ap.error(f"--smoke service {svc!r} publishes no host port "
                     f"(choices: {', '.join(sorted(endpoints))})")
        if not path.startswith("/"):
            path = "/" + path
        smoke = f"curl -fsS http://localhost:{endpoints[svc]}{path}"

    if args.json:
        out = {
            "task": args.task,
            "slot": args.slot,
            "offset": offset,
            "project_name": proj,
            "override_file": str(override_path),
            "ports": {svc: ms for svc, ms in report.items()},
            "endpoints": {svc: f"localhost:{p}" for svc, p in endpoints.items()},
            "up": up_cmd,
            "down": down_cmd,
        }
        if smoke:
            out["smoke"] = smoke
        print(json.dumps(out, indent=2))
    elif not args.stdout:
        print(f"wrote {override_path}")
        print(f"project: {proj}  (slot {args.slot}, offset +{offset}; base ports left free)")
        for svc, ms in report.items():
            pairs = ", ".join(f"{m['published']}→{m['target']}" for m in ms)
            print(f"  {svc:<16} host→container  {pairs}")
        print(f"\nup:    {up_cmd}")
        print(f"down:  {down_cmd}")
        if smoke:
            print(f"smoke: {smoke}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
