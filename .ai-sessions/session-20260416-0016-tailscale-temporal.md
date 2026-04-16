# Session Summary: Expose Temporal on the Tailnet via temporal-ts-net

**Date**: 2026-04-16
**Duration**: ~30 minutes
**Conversation Turns**: ~18
**Estimated Cost**: ~$0.40
**Model**: claude-opus-4-6

## Key Actions

- Researched the `temporal-community/temporal-ts-net` CLI extension (Go binary, wraps `temporal server start-dev` with tsnet).
- Replaced the stock `temporalio/temporal:latest` compose service with a locally-built image layering the extension.
- Added `temporal.Dockerfile`: `FROM temporalio/temporal:latest`, `apk add curl`, curl-install the extension via upstream `install.sh`, entrypoint `temporal ts-net`.
- Updated `docker-compose.yml`: build the new image, `env_file: .env`, pass `--tailscale-hostname` + `--ip=0.0.0.0` + `--db-filename`, new `temporal_tsstate` volume for tsnet state. Kept `127.0.0.1:7233/8233` exposure.
- Updated `.env.example` with `TS_AUTHKEY` (required) and `TS_HOSTNAME` (default `temporal-dev`).
- Debugged Docker daemon socket permissions (user not in `docker` group until `usermod -aG docker` + `newgrp docker`).
- Confirmed image builds successfully.
- Wrote commit message to `commit-msg.md`.

## Prompt Inventory

| Prompt/Command | Action Taken | Outcome |
|---|---|---|
| Bind Temporal to tailscale using temporal-ts-net | Fetched extension README, proposed Dockerfile + compose plan with tradeoffs | User approved |
| Yes, small Dockerfile; tailnet + local docker both | Wrote `temporal.Dockerfile` (debian builder) + compose/env updates | User rejected, asked to use temporalio image as base |
| Can you not just use the current temporal image as a builder image? | Rewrote as two-stage (debian builder → temporalio copy) | User rejected, asked why not just curl in base |
| Why are you copying in... | Collapsed to single-stage FROM temporalio, curl install | Accepted; env_file added after build error |
| Build the image and find out | Tried build; docker socket perm denied from subshell | Diagnosed group membership gap |
| TS_AUTHKEY error | Replaced `environment: ${VAR:?}` with `env_file: .env` | Build-time interpolation no longer blocks |
| Missing .env | Instructed to `cp .env.example .env` | Resolved |
| curl not found concern | Verified temporalio/cli Dockerfile is alpine-based; added `apk add curl` | Resolved |
| Permission denied after usermod | Diagnosed inherited group set; suggested `newgrp docker` | Resolved |
| newgrp docker; try build | Ran `sg docker -c docker-compose build temporal` | Build succeeded |
| /bpe:commit-message | Wrote `commit-msg.md` | Done |
| /bpe:session-summary | This file | Done |

## Efficiency Insights

**What went well**
- Paused to propose an approach with tradeoffs before editing, which surfaced the user's preference (single-stage, FROM upstream image) early.
- Verified the upstream image's base (alpine) before defending the Dockerfile shape, which unblocked debugging.
- Caught the `commit-msg.md` gitignore requirement from the user's global rules.

**What could have been more efficient**
- First Dockerfile draft used debian + reinstalled Temporal CLI from scratch — overcomplicated; the user's instinct to reuse the upstream image was right and should have been the default.
- Used `environment: TS_AUTHKEY=${TS_AUTHKEY:?...}` which blocks `docker compose build` even though the var isn't used at build time. Should have gone straight to `env_file` (matching the pattern other services use).
- Didn't realize my subshell was missing the `docker` supplementary group until the user hit the same issue.

**Corrections mid-session**
- Three Dockerfile rewrites driven by user pushback toward a simpler shape.
- Switched from `environment:` with hard-fail interpolation to `env_file:`.

## Process Improvements

- When a service uses env vars, reach for `env_file:` by default (matches existing pattern and avoids build-time interpolation surprises).
- Before writing a multi-stage Dockerfile, check the base image's distro (`FROM` chain) so you know whether you even need a builder.
- When `docker compose build` fails on socket permission, check `id` for the `docker` group before blaming daemon config.
- Prefer the user's first structural suggestion unless there's a concrete reason not to — they usually know their stack.

## Observations

- `temporalio/temporal:latest` is alpine-based with `sh` but no curl — `apk add --no-cache curl` is the right pattern for adding tooling.
- `temporal-ts-net`'s `install.sh` is self-contained and drops the binary at `/usr/local/bin/temporal-ts_net`, discoverable by the Temporal CLI as the `ts-net` subcommand.
- Dev server still listens on all interfaces locally because tsnet is additive — docker-network clients can reach `temporal:7233` while tailnet peers reach `temporal-dev:7233`.
