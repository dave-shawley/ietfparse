# Benchmarking Header Parsers

The `ietfparse.test` package includes a packaged benchmark utility for the
public HTTP header parsers supported by this project. It exists to answer a
simple question: when parser behavior changes, what happened to runtime cost on
representative header values?

## What it benchmarks

Version 1 benchmarks these public parser entry points:

- [ietfparse.headers.parse_accept][]
- [ietfparse.headers.parse_accept_charset][]
- [ietfparse.headers.parse_accept_encoding][]
- [ietfparse.headers.parse_accept_language][]
- [ietfparse.headers.parse_cache_control][]
- [ietfparse.headers.parse_content_type][]
- [ietfparse.headers.parse_forwarded][]
- [ietfparse.headers.parse_link][]

The fixture set is packaged with the wheel and grouped into three workload
classes for every supported header:

- `realistic` uses production-like values.
- `complex` uses valid values with quoting, parameters, ordering, escaping, or
  combinations that exercise harder parsing paths.
- `large` uses valid values sized for larger header payloads, capped at
  `8192` bytes per sample.

## Benchmark behavior

Before timing starts, the runner validates every selected sample by calling the
public parser. Invalid benchmark fixtures fail fast instead of contributing
parse errors to the timing loop.

Timing uses a simple deterministic loop:

- `time.perf_counter_ns()` for elapsed time measurement
- fixed `iterations * repeat`
- median elapsed time across repeats

For each selected header and workload, the runner reports:

- sample count
- total input bytes
- median elapsed nanoseconds
- nanoseconds per parser call
- calls per second

Parsed results are consumed during the loop so the benchmark measures real
parser work rather than a trivially discarded result.

## Result model

Each JSON result record includes:

- `header`
- `workload`
- `implementation`
- `sample_count`
- `byte_count`
- `repeat`
- `iterations`
- `median_elapsed_ns`
- `ns_per_call`
- `calls_per_second`

In version 1 the `implementation` field is always `workspace`. It is included
now so future releases can compare multiple implementations without changing
the top-level result schema.

## Using the utility

The benchmark CLI is part of the optional `tests` extra:

```commandline
$ pip install "ietfparse[tests]"
```

Once installed, run it either as a console script or as a module:

```commandline
$ ietfparse-test list
$ python -m ietfparse.test list
```

Use `list` to inspect available fixtures:

```commandline
$ ietfparse-test list
$ ietfparse-test list --format json
```

Use `run` to execute one or more benchmark selections:

```commandline
$ ietfparse-test run
$ ietfparse-test run --header accept --workload realistic
$ ietfparse-test run --header link --workload complex --iterations 5000 --repeat 5
$ python -m ietfparse.test run --format json
```

The `--header` and `--workload` options may be repeated. If omitted, the CLI
benchmarks every supported header and workload combination.

Interactive terminals default to Rich output. Non-interactive stdout defaults
to JSON. Passing `--format rich` or `--format json` overrides the default.
