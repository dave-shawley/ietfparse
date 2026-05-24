# ietfparse.test benchmark utility

The `ietfparse.test` package provides the benchmark CLI described in the
[Benchmarking Header Parsers](../benchmarks.md) guide.

It is part of the optional `tests` extra because the CLI depends on
[`typer`](https://typer.tiangolo.com/) and
[`rich`](https://rich.readthedocs.io/).

```commandline
$ pip install "ietfparse[tests]"
```

Once installed, you can run it either as a console script or as a module:

```commandline
$ ietfparse-test list
$ python -m ietfparse.test list
```

## Commands

Use the `list` command to inspect the packaged fixture set.

```commandline
$ ietfparse-test list
$ ietfparse-test list --format json
```

Use the `run` command to execute the selected benchmarks.

```commandline
$ ietfparse-test run
$ ietfparse-test run --header accept --workload realistic
$ ietfparse-test run --header link --workload complex --iterations 5000 --repeat 5
$ python -m ietfparse.test run --format json
```

## Options

The `run` command supports:

- repeated `--header`
- repeated `--workload`
- `--iterations`
- `--repeat`
- `--format`
- `--quiet`

Interactive terminals default to Rich output. Non-interactive stdout defaults
to JSON. Passing `--format rich` or `--format json` overrides the default.
