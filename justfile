export UV_FROZEN := "1"

[default]
[private]
@help:
    just --list

[doc("Run lint & test disabling PYTEST_ADDOPTS")]
ci:
    #!/bin/sh
    unset PYTEST_ADDOPTS
    set -e
    just lint
    just test

[doc("Format one or more files; defaults to all files")]
format *FILES:
    uv run ruff format {{ FILES }}
    tombi format pyproject.toml
    just --fmt --unstable

[doc("Analyze one or more files; defaults to all files")]
lint *FILES:
    #!/usr/bin/env sh
    set -eu
    uv run ruff check --fix {{ FILES }}
    uv run ruff format {{ FILES }}
    uv run pyrefly check {{ FILES }}
    uv run ty check --output-format=concise --exit-zero {{ FILES }}

[doc("Run tests; defaults to all tests")]
test *ARGS:
    #!/usr/bin/env sh
    set -eu
    if [ '{{ ARGS }}' = '' ]; then
      uv run pytest --cov
    else
      uv run pytest {{ ARGS }}
    fi

[doc("Build the doc and wheel distributions")]
build:
    uv run zensical build --clean
    uv build --wheel --clear
