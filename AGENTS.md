# Agent instructions

## Project

This Home Assistant integration controls the Minthouz Fano fan by sending commands through Home Assistant's existing Infrared integration; it does not connect to the fan directly.

## Working in this repository

- Read `README.md` before changing supported commands, timing, or the required infrared emitter entity.
- Keep the remote-command mapping aligned with the README and avoid adding a direct hardware or network control path.
- Before changing CI, check [pschmitt/ci-workflows](https://github.com/pschmitt/ci-workflows) for reusable components and preserve this repository's existing checks.

## Validation

- Run `uvx ruff check .` and `uvx ruff format --check .` for Python changes.
- CI runs Hassfest and the shared Ruff checks; it currently has no test job.
