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

Build context (T-028)
---------------------
The base compose builds each service from a fixed relative path (`./cv-domain-service`)
— the MAIN CHECKOUT, which sits on `master`. A dev-loop task runs on a git worktree,
so an un-repointed QA stack exercises code that does not contain the change under
test: a false PASS whenever the task modifies behaviour that already exists.

So this tool also repoints the build context at the worktree. The worktree→service
match is derived, never tabulated: `git -C <worktree> remote get-url origin` yields
the repo name (`cv-domain-service`), which is compared against the basename of each
service's build context. A hard-coded service→repo map is exactly the kind of thing
that drifted into this bug in the first place.

Zero matches is legitimate (a cv-database/cv-infra/docs task builds no service) and
is reported out loud — a silent zero is indistinguishable from the bug still being
there. An explicitly passed `--worktree` that does not exist is a hard error: falling
back quietly to the main checkout would recreate the defect.

Provenance is emitted as build LABELS (task/branch/commit/worktree), so QA proves
which tree was built with `docker inspect` — no service needs a /version endpoint,
and it works for modifying tasks that have no distinguishing endpoint.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except ModuleNotFoundError:
    sys.exit("qa-env-override: PyYAML is required (pip install pyyaml).")

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_PREFIX = "cvdl_"
# Conventional home of dev-loop worktrees (a convention, not a guarantee — tasks
# that declare `worktree: none` simply have no directory here).
WORKTREE_ROOT = REPO_ROOT.parent / "cvdl-worktrees"
# Namespace for the provenance labels stamped onto every repointed build.
LABEL_NS = "com.cvproject.dev-loop"
# The shared task board; frontmatter `branch:` is the authority on which branch a
# task's worktree is supposed to be on.
TASKS_DIR = REPO_ROOT / ".claude" / "tasks"
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


class WorktreeError(Exception):
    """Raised when a worktree cannot be resolved or identified. Always fatal:
    silently carrying on would build `master` and hand QA a false pass."""


def _git(path: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise WorktreeError(
            f"git {' '.join(args)} failed in {path}: "
            f"{(proc.stderr or proc.stdout).strip()}"
        )
    return proc.stdout.strip()


def resolve_worktree(task: str, explicit: str | None, root: Path):
    """Return (Path | None, note).

    An explicit --worktree must exist: falling back to the main checkout because
    the caller's path was wrong is precisely the failure this tool exists to stop.
    With no --worktree we probe the conventional path and, only when it is absent,
    fall back to the main checkout (reported as None, no build override).
    """
    if explicit is not None:
        if not explicit.strip():
            raise WorktreeError(
                "--worktree was given an empty value (an unset shell variable?); "
                "it would resolve to the current directory")
        path = Path(explicit).expanduser()
        if not path.is_dir():
            raise WorktreeError(
                f"--worktree path does not exist: {path}\n"
                f"       refusing to fall back to the main checkout — that would "
                f"build master and silently exercise the wrong code."
            )
        return path.resolve(), "explicit --worktree"
    conventional = (root / task).expanduser()
    if conventional.is_dir():
        return conventional.resolve(), f"conventional path {conventional}"
    return None, f"no worktree at {conventional}"


def repo_identity(path: Path) -> dict:
    """Identify the repo checked out at `path` from git itself (ruling 2).

    The origin URL's basename is the repo name — the same string the compose
    build context ends in — so no service→repo table is needed anywhere.
    """
    # `git -C` walks UPWARD, so a subdirectory of a checkout answers with its
    # parent's origin: ~/work/curriculum/scripts reports the meta repo, and
    # ~/work/curriculum/cv-domain-service (the MAIN checkout, on master) reports
    # cv-domain-service and would be stamped as the tree under test. Require the
    # path to *be* the work-tree root, not merely live inside one.
    toplevel = Path(_git(path, "rev-parse", "--show-toplevel")).resolve()
    if toplevel != path.resolve():
        raise WorktreeError(
            f"{path} is not the root of a git work tree — git resolves it to "
            f"{toplevel}.\n"
            f"       Pass the work-tree root itself; a subdirectory would be "
            f"labelled as the tree under test while building something else.")
    url = _git(path, "remote", "get-url", "origin")
    name = url.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    if not name:
        raise WorktreeError(f"cannot derive a repo name from origin url {url!r} in {path}")
    branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":  # detached worktree — say so rather than label it "HEAD"
        branch = "(detached)"
    commit = _git(path, "rev-parse", "--short", "HEAD")
    dirty = bool(_git(path, "status", "--porcelain"))
    return {"repo": name, "path": str(path), "branch": branch,
            "commit": commit, "dirty": dirty}


def service_build_contexts(compose: dict) -> dict:
    """{service: build context} for every buildable service, long or short form."""
    out = {}
    for name, svc in (compose.get("services") or {}).items():
        build = (svc or {}).get("build")
        if not build:
            continue
        context = build if isinstance(build, str) else build.get("context")
        if context:
            out[name] = str(context)
    return out


def match_build_services(compose: dict, repo: str) -> list:
    """Services whose build-context basename equals the worktree's repo name."""
    return sorted(
        name for name, ctx in service_build_contexts(compose).items()
        if Path(ctx.rstrip("/")).name == repo
    )


def split_short_volume(entry: str):
    """('source', 'rest') for a short-form volume, or None when there is no host
    source (an anonymous volume, "/data")."""
    parts = entry.split(":")
    if len(parts) < 2:
        return None
    return parts[0], ":".join(parts[1:])


def is_bind_source(source: str) -> bool:
    """A host path, as opposed to a named volume. Compose treats anything that
    is not a bare name as a bind mount."""
    return source.startswith((".", "/", "~"))


def rewrite_mount_source(source: str, repo: str, worktree: Path):
    """Repoint a host bind-mount source at the worktree, or explain why not.

    Returns (new_source | None, reason). The match is the same basename idea used
    for build contexts, applied to any path component: `./cv-database/sql` under
    repo `cv-database` becomes `<worktree>/sql`. Only the host side moves — the
    container path and any `:ro` flags are the caller's to preserve.
    """
    if "$" in source:
        # Compose interpolates at up-time; we cannot resolve it here without
        # reimplementing that, and guessing is how this bug happened.
        return None, "unresolvable (contains ${...} interpolation)"
    if not is_bind_source(source):
        return None, "named volume"
    parts = [x for x in PurePosixPath(source).parts if x not in (".", "/")]
    if repo not in parts:
        return None, "does not point into the task repo"
    tail = parts[parts.index(repo) + 1:]
    return str(worktree.joinpath(*tail)), "repointed"


def match_mount_services(compose: dict, repo: str, worktree: Path):
    """({service: rewritten_volumes_list}, [rewrite records], [exposure records]).

    Ruling 3 said a repo with no build context has nothing under test. That is
    FALSE for a repo the stack bind-mounts from the main checkout: `flyway`
    mounts ./cv-database/sql and `grafana` mounts ./cv-observability/... — a
    cv-database task (T-151) would migrate and seed from master while the
    generator reported "nothing to repoint". This closes that hole.

    An `exposure` is a mount into the task repo we could NOT rewrite; it must be
    named out loud rather than silently skipped.
    """
    services, rewrites, exposures = {}, [], []
    for name, svc in (compose.get("services") or {}).items():
        volumes = (svc or {}).get("volumes")
        if not volumes:
            continue
        new_list, touched = [], False
        for entry in volumes:
            if isinstance(entry, dict):
                source = entry.get("source")
                if not source or entry.get("type", "bind") != "bind":
                    new_list.append(entry)
                    continue
                new_source, reason = rewrite_mount_source(str(source), repo, worktree)
                if new_source is None:
                    if reason.startswith("unresolvable") and repo in str(source):
                        exposures.append({"service": name, "source": str(source),
                                          "reason": reason})
                    new_list.append(entry)
                    continue
                replacement = dict(entry)
                replacement["source"] = new_source
                new_list.append(replacement)
                rewrites.append({"service": name, "from": str(source),
                                 "to": new_source})
                touched = True
                continue

            text = str(entry)
            parsed = split_short_volume(text)
            if parsed is None:
                new_list.append(text)
                continue
            source, rest = parsed
            new_source, reason = rewrite_mount_source(source, repo, worktree)
            if new_source is None:
                if reason.startswith("unresolvable") and repo in source:
                    exposures.append({"service": name, "source": source,
                                      "reason": reason})
                new_list.append(text)
                continue
            new_list.append(f"{new_source}:{rest}")
            rewrites.append({"service": name, "from": source, "to": new_source})
            touched = True
        if touched:
            services[name] = new_list
    return services, rewrites, exposures


def mount_exposures(compose: dict, repo: str):
    """Every bind mount that points into `repo`, regardless of rewritability —
    used to describe the exposure when we are NOT repointing it."""
    found = []
    for name, svc in (compose.get("services") or {}).items():
        for entry in ((svc or {}).get("volumes") or []):
            source = (entry.get("source") if isinstance(entry, dict)
                      else (split_short_volume(str(entry)) or ("", ""))[0])
            if not source or not is_bind_source(str(source)):
                continue
            if repo in [x for x in PurePosixPath(str(source)).parts if x not in (".", "/")]:
                found.append({"service": name, "source": str(source)})
    return found


def declared_branch(task: str, tasks_dir: Path = TASKS_DIR):
    """(branch, task_file) from the board's frontmatter, or (None, None).

    Finding 2: labels that merely agree with the tree they were stamped from are
    self-consistent, not corroborating. The board says which branch the task is
    supposed to be on; comparing against it is an exact check, not a heuristic.
    """
    try:
        candidates = sorted(tasks_dir.glob(f"{task}-*.md")) + \
            sorted(tasks_dir.glob(f"{task}.md"))
    except OSError:
        return None, None
    for path in candidates:
        text = path.read_text()
        if not text.startswith("---"):
            continue
        try:
            front = yaml.safe_load(text.split("---", 2)[1]) or {}
        except yaml.YAMLError:
            continue
        branch = front.get("branch")
        if branch and str(branch).strip():
            return str(branch).strip(), path
    return None, None


def provenance_labels(task: str, ident: dict) -> dict:
    """Build labels that let `docker inspect` prove which tree produced an image.
    Values are strings: Compose rejects non-string label values."""
    return {
        f"{LABEL_NS}.task": task,
        f"{LABEL_NS}.repo": ident["repo"],
        f"{LABEL_NS}.branch": ident["branch"],
        f"{LABEL_NS}.commit": ident["commit"],
        f"{LABEL_NS}.dirty": "true" if ident["dirty"] else "false",
        f"{LABEL_NS}.worktree": ident["path"],
    }


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


def build_override(compose: dict, offset: int, build_target=None, mount_target=None):
    """(override_doc, port_report, build_report, mount_report).

    build_target is None or {"services": [...], "context": str, "labels": {...}}.
    mount_target is None or {service: [rewritten volume entries]} — emitted with
    `!override` for the same reason ports are: a plain merge would leave the base
    (main-checkout) mount in place beside the repointed one.

    The port remapping is unconditional, so repointing never costs isolation.
    """
    services = {}
    report = {}
    for name, svc in (compose.get("services") or {}).items():
        ports = (svc or {}).get("ports")
        if not ports:
            continue
        new_list, mappings = remap_service_ports(ports, offset)
        if new_list:
            services[name] = {"ports": OverrideList(new_list)}
            report[name] = mappings

    build_report = None
    if build_target:
        for name in build_target["services"]:
            entry = services.setdefault(name, {})
            entry["build"] = {
                "context": build_target["context"],
                "labels": dict(build_target["labels"]),
            }
        build_report = {
            "services": list(build_target["services"]),
            "context": build_target["context"],
            "labels": dict(build_target["labels"]),
        }

    mount_report = None
    if mount_target:
        for name, vols in mount_target.items():
            entry = services.setdefault(name, {})
            entry["volumes"] = OverrideList(list(vols))
        mount_report = {"services": sorted(mount_target)}
    return {"services": services}, report, build_report, mount_report


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
    ap.add_argument("--worktree", metavar="PATH", default=None,
                    help="git worktree under test; the compose service whose build "
                         "context matches that repo is built from here instead of "
                         "the main checkout (which sits on master). Default: "
                         "<worktree-root>/<task> when it exists, otherwise the main "
                         "checkout. An explicit path that does not exist is an "
                         "error — never a silent fallback")
    ap.add_argument("--require-worktree", action="store_true",
                    help="fail non-zero unless the task repo was actually "
                         "repointed (build context or bind mount). For pipeline "
                         "use: the worktree convention is otherwise unenforced, "
                         "so a mistyped directory yields a normal-looking "
                         "override of a master build")
    ap.add_argument("--expect-branch", metavar="BRANCH", default=None,
                    help="require the worktree to be on this branch. Default: "
                         "the `branch:` field of the task's board file, when it "
                         "declares one. A worktree left on master resolves, "
                         "builds and stamps labels that agree with themselves")
    ap.add_argument("--no-branch-check", action="store_true",
                    help="skip the expected-branch check (detached HEAD, "
                         "throwaway probes, tasks whose board entry is stale)")
    ap.add_argument("--worktree-root", default=str(WORKTREE_ROOT),
                    help=f"where conventional per-task worktrees live "
                         f"(default: {WORKTREE_ROOT})")
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

    # --- build context (T-028) -------------------------------------------
    # Resolve the worktree, identify its repo from git, and repoint the compose
    # service whose build-context basename matches. Any failure here is fatal:
    # a stack that quietly builds master hands QA a false pass.
    try:
        worktree, wt_note = resolve_worktree(
            args.task, args.worktree, Path(args.worktree_root).expanduser())
        ident = repo_identity(worktree) if worktree else None
    except WorktreeError as exc:
        sys.exit(f"qa-env-override: {exc}")

    # Finding 2: the branch the labels record is only self-consistent. The board
    # declares which branch the task lives on; compare against it.
    expect_branch, expect_source = None, None
    if not args.no_branch_check:
        if args.expect_branch:
            expect_branch, expect_source = args.expect_branch, "--expect-branch"
        else:
            declared, task_file = declared_branch(args.task)
            if declared:
                expect_branch, expect_source = declared, f"{task_file.name} frontmatter"
    if ident and expect_branch and ident["branch"] != expect_branch:
        sys.exit(
            f"qa-env-override: worktree branch mismatch\n"
            f"       {ident['path']} is on {ident['branch']!r}, but {args.task} "
            f"declares {expect_branch!r} ({expect_source}).\n"
            f"       Refusing: the build would be stamped with provenance labels "
            f"that agree with themselves while exercising the wrong tree.\n"
            f"       Check out the branch, or pass --expect-branch/--no-branch-check.")

    matched = match_build_services(base, ident["repo"]) if ident else []
    build_target = None
    if matched:
        build_target = {
            "services": matched,
            "context": ident["path"],
            "labels": provenance_labels(args.task, ident),
        }

    # Finding 1: repos the stack bind-mounts instead of building (cv-database via
    # flyway, cv-observability via grafana) are just as much "under test".
    mount_services, mount_rewrites, mount_exposed = (
        match_mount_services(base, ident["repo"], worktree) if ident else ({}, [], []))

    override, report, build_report, mount_report = build_override(
        base, offset, build_target, mount_services or None)

    # Ruling 3: say which of the three outcomes happened, always. A silent zero
    # is indistinguishable from the bug not being fixed.
    notes = []
    if build_report or mount_report:
        stamp = f"{ident['branch']} @ {ident['commit']}" + (" +dirty" if ident["dirty"] else "")
        if build_report:
            notes.append(f"repointed build {', '.join(matched)} → {ident['path']}  ({stamp})")
        for rw in mount_rewrites:
            notes.append(f"repointed mount {rw['service']}: {rw['from']} → {rw['to']}")
    elif ident:
        buildable = ", ".join(sorted(service_build_contexts(base))) or "none"
        notes.append(f"no service repointed: task repo {ident['repo']!r} is neither "
                     f"built nor bind-mounted by {compose_path.name} "
                     f"(buildable: {buildable})")
    else:
        notes.append(f"no service repointed: {wt_note}; every service builds from the "
                     f"MAIN CHECKOUT (master) — correct only for a task with no worktree")

    # The sibling main checkouts are a directory away from the worktree root and
    # are a plausible slip (finding 3): they are valid work-tree roots, so the
    # toplevel guard passes and only the branch check would catch them. Say it.
    if worktree and worktree.parent == REPO_ROOT.resolve():
        notes.append(f"WARNING: {worktree} is the MAIN CHECKOUT of {ident['repo']}, "
                     f"not a worktree — it holds whatever branch that checkout is on")

    # An exposure we could not rewrite must be NAMED, never implied away: a
    # reassuring "nothing to repoint" over a live main-checkout mount is the
    # very false pass this task exists to kill.
    if ident:
        unrepointed = [e for e in mount_exposures(base, ident["repo"])
                       if e["service"] not in mount_services]
        for e in unrepointed:
            notes.append(
                f"WARNING: {e['service']} bind-mounts {e['source']} from the MAIN "
                f"CHECKOUT and was NOT repointed — this stack will not contain your "
                f"change to that path")
    note = "\n       ".join(notes)

    if args.require_worktree and not (build_report or mount_report):
        sys.exit(f"qa-env-override: --require-worktree: nothing was repointed.\n"
                 f"       {note}")

    header = (
        f"# GENERATED by scripts/qa-env-override.py — do not edit by hand.\n"
        f"# task={args.task} slot={args.slot} offset=+{offset} "
        f"base={compose_path.name}\n"
        f"# Isolated QA stack for the /dev-loop pipeline (adapter §6).\n"
        f"# `!override` replaces the base ports (requires Docker Compose >= 2.24).\n"
        f"# Bring up:  COMPOSE_PROJECT_NAME={proj} \\\n"
        f"#   docker compose -f {compose_path.name} -f {{this file}} up --build\n"
    )
    # The note goes in the file itself, in ALL cases (finding 4). This file is
    # generated once and -f'd repeatedly; without it a reader cannot tell "the
    # generator considered the worktree and found nothing" from "this file
    # predates T-028".
    header += "# Worktree repoint (T-028):\n"
    for line in notes:
        header += f"#   {line}\n"
    if ident:
        header += (f"#   worktree: {ident['path']} "
                   f"({ident['branch']} @ {ident['commit']}"
                   f"{', dirty' if ident['dirty'] else ''})\n")
    body = yaml.safe_dump(override, sort_keys=False, default_flow_style=False)
    content = header + body

    override_name = f"docker-compose.override.{proj}.yml"
    override_path = Path(args.out_dir) / override_name

    if args.stdout:
        sys.stdout.write(content)
        # stdout stays pure YAML for piping; the ruling-3 note still has to be
        # said out loud, so it goes to stderr.
        print(f"build: {note}", file=sys.stderr)
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

    # Provenance is a build LABEL, not an endpoint (ruling 5): it works for every
    # service, including modifying tasks with no distinguishing endpoint.
    provenance = [
        f"docker inspect --format '{{{{json .Config.Labels}}}}' {proj}-{svc}"
        for svc in (build_report["services"] if build_report else [])
    ]
    # A repointed bind mount carries no image label — its provenance is the
    # container's own mount table.
    provenance += [
        f"docker inspect --format '{{{{json .Mounts}}}}' {proj}-{svc}-1"
        for svc in (mount_report["services"] if mount_report else [])
    ]

    if args.json:
        out = {
            "task": args.task,
            "slot": args.slot,
            "offset": offset,
            "project_name": proj,
            "override_file": str(override_path),
            "ports": {svc: ms for svc, ms in report.items()},
            "endpoints": {svc: f"localhost:{p}" for svc, p in endpoints.items()},
            "worktree": ident,
            "worktree_note": wt_note,
            "expect_branch": expect_branch,
            "build": build_report,
            "mounts": mount_rewrites,
            "unrepointed_exposures": (
                [e for e in mount_exposures(base, ident["repo"])
                 if e["service"] not in mount_services] if ident else []),
            "note": note,
            "up": up_cmd,
            "down": down_cmd,
            "provenance": provenance,
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
        print(f"\nbuild: {note}")
        print(f"\nup:    {up_cmd}")
        print(f"down:  {down_cmd}")
        if smoke:
            print(f"smoke: {smoke}")
        for cmd in provenance:
            print(f"prov:  {cmd}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
