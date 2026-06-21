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

The field stays stable whether the benchmark runs the workspace parser or a
compatible third-party implementation.

## Comparing implementations

The benchmark CLI can compare multiple implementations when compatible parser
surfaces exist. Today that includes:

- `workspace` for every packaged benchmark fixture
- `werkzeug` for the Accept-family headers via
  `werkzeug.http.parse_accept_header` and for `Cache-Control` via
  `werkzeug.http.parse_cache_control_header`
- `requests` for `requests.utils.parse_header_links`
- `httpx` for `httpx.Response.links`

Use `--implementation` one or more times to select implementations:

```commandline
$ ietfparse-test run --header accept --implementation workspace --implementation werkzeug
$ ietfparse-test run --header accept-language --implementation workspace --implementation werkzeug
$ ietfparse-test run --header link --implementation workspace --implementation requests
$ ietfparse-test run --header link --implementation workspace --implementation httpx
```

If omitted, `run` defaults to the workspace parser implementation.

The `werkzeug` implementation only supports `accept`, `accept-charset`,
`accept-encoding`, `accept-language`, and `cache-control`. The `requests` and
`httpx` implementations only support `link`. Selecting any implementation for
other headers fails fast with a validation error.

To compare multiple implementations only on the headers they all support, use
`compare implementation`. It always includes `workspace`, computes the shared
header set automatically, and reports one row per header/workload with
per-implementation `ns/call` plus ratios against `workspace`:

```commandline
$ ietfparse-test compare implementation werkzeug
$ ietfparse-test compare implementation werkzeug --workload realistic
```

To summarize release-to-release timing changes from saved
`run --format json` or `compare implementation --format json` outputs, use
`diff`. It compares the same header/workload rows across two files and reports
old/new `ns/call` plus the ratio and percentage change for each implementation:

```commandline
$ ietfparse-test diff old.json new.json
$ ietfparse-test diff old.json new.json --format json
```

For behavioral comparisons, use the dedicated comparison commands:

- `compare link` runs curated `Link` parsing edge cases through the available
  parser implementations.
- `compare accept` runs curated `Accept` negotiation cases through
  [ietfparse.algorithms.select_content_type][] and Werkzeug's
  `Accept.best_match`.
- `compare cache-control` runs curated `Cache-Control` parsing cases through
  `ietfparse.headers.parse_cache_control` and Werkzeug's
  `parse_cache_control_header`.

Both commands emit either Rich summary output or detailed JSON:

```commandline
$ ietfparse-test compare link
$ ietfparse-test compare link --format json
$ ietfparse-test compare accept
$ ietfparse-test compare accept --format json
$ ietfparse-test compare cache-control
$ ietfparse-test compare cache-control --format json
```

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
$ ietfparse-test run --header accept --implementation workspace --implementation werkzeug
$ ietfparse-test run --header link --workload complex --iterations 5000 --repeat 5
$ ietfparse-test run --header link --implementation workspace --implementation requests
$ ietfparse-test run --header link --implementation workspace --implementation httpx
$ ietfparse-test compare implementation werkzeug --format json
$ ietfparse-test diff old.json new.json
$ ietfparse-test compare link --format json
$ ietfparse-test compare accept --format json
$ ietfparse-test compare cache-control --format json
$ python -m ietfparse.test run --format json
```

The `--header` and `--workload` options may be repeated. If omitted, the CLI
benchmarks every supported header and workload combination.

Interactive terminals default to Rich output. Non-interactive stdout defaults
to JSON. Passing `--format rich` or `--format json` overrides the default.
