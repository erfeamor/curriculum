# devcontainers/

Shared, multi-stack devcontainer definitions for working across the whole `cv-project` workspace at once (all repos mounted, all toolchains installed).

- `full-stack/devcontainer.json` — Java 17, Node 20, Docker-in-Docker, Terraform, AWS CLI. Runs `clone-all.sh` on create so every sibling repo is present.

This folder is intentionally **not** named `.devcontainer` — it holds one global, opt-in config, not the repo's default. To use it:

1. VS Code Command Palette → **Dev Containers: Reopen in Container...**
2. Choose **"From 'devcontainers' folder"** (or point the `Dev Containers: devcontainer.json Path` picker at `devcontainers/full-stack/devcontainer.json`).

Each product repo also ships its own `.devcontainer/devcontainer.json` scoped to just its stack (lighter weight, used by that repo's own CI/onboarding) — use the global one here only when you need to touch multiple layers in one session.
