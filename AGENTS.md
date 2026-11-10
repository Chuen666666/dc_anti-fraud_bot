# Repository Guide for AI Agents

## Project overview

- This is a Python 3.14 Discord moderation bot with a small Flask health endpoint for Render.
- `main.py` is the application entry point and contains the Discord event handling, configuration validation, and health server.
- Node.js 24 is recorded only as a local toolchain version. This repository is not a Node application and has no npm install or build step.

## Dependencies and lock files

- Edit runtime dependencies in `requirements.in` and development dependencies in `requirements-dev.in`.
- `requirements.txt` and `requirements-dev.txt` are generated, hash-locked files. Never edit them by hand.
- Regenerate both locks with:

```text
uv pip compile --generate-hashes --universal --python-version 3.14 --upgrade requirements.in -o requirements.txt
uv pip compile --generate-hashes --universal --python-version 3.14 --upgrade requirements-dev.in -o requirements-dev.txt
```

- Install production dependencies with `python -m pip install --require-hashes -r requirements.txt`.
- Install the development environment with `python -m pip install --require-hashes -r requirements-dev.txt`.

## Required checks

Run the same checks used by CI before opening a pull request:

```text
python -m compileall -q main.py
ruff check .
ruff format --check .
pre-commit run --all-files --show-diff-on-failure
```

Changes must go through a pull request. Do not push directly to `main`; the `CI` status check must pass before merging.

## Security and behavior constraints

- Never commit `token.env`, `config.json`, Discord tokens, channel IDs from a real server, or other credentials. Use only the example files in commits and tests.
- Do not start the real bot during automated checks; it requires credentials, Discord access, and server permissions.
- Preserve the administrator exemption and `WHITELIST_ROLE_IDS` exemption unless a task explicitly changes the moderation policy.
- The message-deletion lookback is intentionally fixed at five minutes and is not configurable through JSON.
- Notification settings are valid only when `INFO_CHANNEL` and `info_msg` are both present or both `null`. Keep startup validation fail-closed for mismatched settings.
- A guild absent from `config.json` must remain ignored.
- Keep the Render health endpoint available at `/`, and keep production installation hash-locked.

## Documentation

- Keep this agent-facing file in English.
- Preserve the README's Traditional Chinese language and update it when setup, configuration, permissions, deployment, or user-visible behavior changes.
