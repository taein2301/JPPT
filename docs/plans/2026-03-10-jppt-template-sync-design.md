# JPPT Template Sync Design

**Context**

`JPPT` is the base template. `jupbc-cat` was derived from it and contains both template-level infrastructure changes and product-specific trading code. This design covers only template-common changes that can be applied to files that already exist in `JPPT`.

**Scope**

- Update shared CLI/runtime behavior in existing files only.
- Carry over logging, configuration, shell-script, and notifier improvements that are not tied to trading-domain modules.
- Do not add new files from `jupbc-cat`.
- Do not port domain-specific code such as trading engines, storage backends, scanners, or Supabase-specific runtime modules.

**Selected Approach**

Use a manual selective merge over existing `JPPT` files.

This is preferred over broad file replacement because:
- `JPPT` has local edits in `scripts/create_app.sh`.
- `jupbc-cat` includes domain logic in some overlapping areas.
- The goal is to preserve template structure while lifting common infrastructure improvements.

**Planned Changes**

1. CLI/runtime updates
- Let `--verbose` force `DEBUG`.
- Let `--log-level` override the config level instead of always defaulting to `INFO`.
- Log a short loaded-config summary at process startup.

2. Logging/config updates
- Add `logging.json_logs` to example configs and logger setup.
- Preserve console color formatting while avoiding markup corruption.
- Keep YAML-only config loading behavior aligned with current template implementation.

3. Script/notifier updates
- Improve `run.sh` log-path handling and runtime messaging.
- Add GitHub CLI `repo` scope validation to `scripts/create_app.sh` without overwriting unrelated local edits.
- Treat Telegram timeout separately from generic errors.

4. Test coverage
- Update and extend tests around CLI log-level behavior, logger formatting, config defaults, and Telegram timeout handling.

**Verification**

Run targeted pytest commands for the touched modules after the edits.
