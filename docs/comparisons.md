---
title: Adjacent Technology Comparisons
---

# Adjacent Technology Comparisons

This page exists to compare `ietfparse` with similar functionality embedded in
other widely used libraries. The point is not to declare a single winner. The
point is to make the tradeoffs visible enough that maintainers and users can
choose intentionally.

These comparisons are meant to help answer three questions:

1. Is strict interpretation worth the added implementation and runtime cost?
2. How does `ietfparse` differ from other well-known libraries with respect to
   conformance, correctness, and performance?
3. What are the concrete costs and benefits of choosing a stricter parser?

In practice, the answer depends on the job:

- If the input is known-good and throughput dominates everything else, a more
  permissive parser may be a reasonable choice. `ietfparse` 1.x was used for
  well over a decade in production systems with a more permissive parser.
- If the input is untrusted, interoperability bugs are expensive, or the code
  needs to reflect RFC behavior rather than best-effort guessing, stricter
  parsing becomes much more attractive.

## How To Read These Comparisons

Each comparison should consider the same dimensions:

- **Conformance**: whether the implementation follows the relevant RFC grammar
  and semantics.
- **Correctness**: whether the implementation preserves information and rejects
  malformed input instead of silently changing it.
- **Performance**: how much runtime cost is paid for the behavior above.
- **Decision impact**: what kinds of systems benefit from the tradeoff.

The benchmark utility and comparison tooling in [Benchmarking Header
Parsers](benchmarks.md) are intended to make these comparisons repeatable
instead of anecdotal.

## `requests.utils.parse_header_links`

The standard comparison for `Link` parsing is
`requests.utils.parse_header_links`. It is widely available, easy to reach for,
and fast. It is also much more permissive than
[ietfparse.headers.parse_link][].

### Surface Differences

The two APIs solve related but different problems.

`ietfparse.headers.parse_link` returns structured
[ietfparse.datastructures.LinkHeader][] objects that preserve ordering and
multi-valued parameters. It also exposes normalized behavior such as semantic
handling of duplicate `rel`, `title`, `media`, and `type` parameters.

`requests.utils.parse_header_links` returns a list of dictionaries. That shape
is convenient, but it also means that duplicate parameter names collapse to a
single surviving value and some distinctions are lost.

### Conformance And Correctness

The current comparison suite shows a consistent pattern:

- `ietfparse` tries to parse `Link` according to its RFC-defined structure and
  raises `MalformedLinkValue` for malformed inputs.
- `requests` tends to accept malformed input and return a best-effort result.
- `ietfparse` preserves more information from valid-but-tricky inputs.
- `requests` is more willing to discard, truncate, or overwrite data while
  still returning a value.

Some representative examples:

| Case                                                      | `ietfparse`                             | `requests`                                                    |
|-----------------------------------------------------------|-----------------------------------------|---------------------------------------------------------------|
| Target contains semicolon: `<https://host/matrix;param/>` | Preserves the full target               | Truncates the target to `https://host/matrix`                 |
| Quoted parameter contains semicolon                       | Preserves `quoted; with semicolon`      | Truncates to `quoted`                                         |
| Missing angle brackets around the target                  | Raises `MalformedLinkValue`             | Accepts the value and returns a parsed dictionary             |
| Missing first semicolon before parameters                 | Raises `MalformedLinkValue`             | Accepts the input and folds the malformed text into the URL   |
| Invalid parameter like `weird=a=b`                        | Raises `MalformedLinkValue`             | Accepts the input and drops the malformed parameter           |
| Duplicate `rel` in strict mode                            | Keeps the first `rel` per RFC semantics | Keeps the last `rel` because later dictionary assignment wins |
| Non-strict duplicate semantic parameters                  | Preserves all values                    | Collapses to the last seen value                              |

That behavior difference matters most when `Link` headers are part of a stable
protocol boundary. A permissive parser can make bad data look usable, which is
convenient until the silent repair hides a server bug or causes a client to
traverse the wrong relation.

### Performance

The packaged benchmark suite can measure both implementations against the same
`Link` fixtures. In one local run while adding this document, `requests` was
faster across every packaged `Link` workload, while `ietfparse` spent more time
preserving structure and validating grammar.

As a rough expectation, that run puts `ietfparse` at about **5x to 10x slower**
than `requests` for `Link` parsing.

That is intentionally a round-number summary, not a statistically rigorous
claim. The point is to set expectations for readers: stricter parsing appears
to have a real cost, and that cost is not a few percentage points.

In the local run that informed this page, the three packaged workloads came out
to about:

- `realistic`: roughly `5x` slower
- `complex`: roughly `6x` slower
- `large`: roughly `9x` to `10x` slower

The summary range was produced in the simplest possible way:

1. Run the same packaged `Link` workloads through both implementations.
2. Divide the `ietfparse` runtime by the `requests` runtime for each workload.
3. Round those ratios to whole numbers.
4. Take the smallest and largest rounded values and describe the result as
   "between 5 and 10 times slower."

That should be interpreted as a tradeoff, not a defect:

- `requests` appears optimized for quick, permissive extraction of link-like
  values.
- `ietfparse` pays additional cost for stricter interpretation and richer
  results.

Exact timings depend on the Python version, machine, `requests` version, and
the specific header mix. Users should run the packaged benchmark utility in
their own environment before drawing hard conclusions from any single result,
but "expect something like 5x to 10x slower" is a fair directional summary of
what this local run showed.

### Cost Versus Benefit

If your application only needs "good enough" extraction from mostly well-formed
headers, `requests.utils.parse_header_links` may be sufficient and may be
faster.

If your application needs to distinguish valid from invalid inputs, preserve
parameters faithfully, or reason about RFC semantics instead of best-effort
heuristics, `ietfparse.headers.parse_link` is the safer choice.

That is the core tradeoff this project is making: spend more implementation
effort and more runtime work in exchange for clearer semantics, better failure
modes, and more predictable behavior at protocol boundaries.

### Reproducing The Comparison

Use the benchmark CLI to compare performance:

```commandline
$ ietfparse-test run --header link --implementation workspace --implementation requests
```

Use the dedicated comparison command to inspect edge-case behavior:

```commandline
$ ietfparse-test compare-link --format json
```

## `httpx.Response.links`

`httpx` does not expose a standalone public `Link` parser in the same style as
`requests.utils.parse_header_links`. Its adjacent functionality is the
`Response.links` property, which parses the `Link` header on demand and returns
a mapping.

That makes the comparison slightly different:

- `ietfparse` exposes an explicit parser API.
- `requests` exposes an explicit parser helper.
- `httpx` exposes parsed links through a response convenience property.

The comparison here is therefore based on the public `httpx.Response.links`
surface rather than its internal helper.

### Surface Differences

`httpx.Response.links` returns a dictionary keyed by `rel` when one exists, or
by the URL otherwise.

That is convenient for quick client code, but it is also the most lossy of the
three surfaces discussed on this page:

- duplicate parameter names still collapse, as with `requests`
- repeated links with the same `rel` overwrite each other in the outer mapping
- ordering is not preserved in the same way as `ietfparse`

For example, two `next` links collapse to one entry when accessed through
`Response.links`.

### Conformance And Correctness

Behaviorally, `httpx` is much closer to `requests` than to `ietfparse`.

In the local comparison run used for this page:

- `httpx` accepted malformed inputs that `ietfparse` rejected
- `httpx` truncated or discarded data in the same kinds of cases as `requests`
- `httpx` added another layer of information loss because the public result is
  keyed by relation or URL

Representative examples:

| Case                                                      | `ietfparse`                             | `httpx`                                                 |
|-----------------------------------------------------------|-----------------------------------------|---------------------------------------------------------|
| Target contains semicolon: `<https://host/matrix;param/>` | Preserves the full target               | Truncates to `https://host/matrix`                      |
| Quoted parameter contains semicolon                       | Preserves `quoted; with semicolon`      | Truncates to `quoted`                                   |
| Missing angle brackets around the target                  | Raises `MalformedLinkValue`             | Accepts the value and returns a parsed mapping          |
| Missing first semicolon before parameters                 | Raises `MalformedLinkValue`             | Accepts the input and folds malformed text into the URL |
| Invalid parameter like `weird=a=b`                        | Raises `MalformedLinkValue`             | Accepts the input and drops the malformed parameter     |
| Duplicate `rel` in a single link                          | Keeps the first `rel` per RFC semantics | Keeps the last `rel`                                    |
| Two separate links with the same `rel`                    | Preserves both links                    | Outer mapping keeps only the last link for that `rel`   |

So the `httpx` tradeoff is not just permissive parsing. It also favors a
client-convenience result shape over faithful preservation of the header.

### Performance

The single local benchmark run used here showed a more mixed result for `httpx`
than for `requests`.

As a rough expectation:

- on the smaller packaged `Link` workloads, `ietfparse` and `httpx` were in the
  same general range
- on the large packaged workload, `ietfparse` was roughly an order of magnitude
  slower than `httpx`

Using the same rough method as above, that single run came out to about:

- `realistic`: roughly `1x` slower
- `complex`: roughly `1x` slower
- `large`: roughly `13x` slower

That should be read as "performance depends heavily on the workload and the
surface being measured", not as a precise claim that `httpx` is always faster.
The public `Response.links` API is doing a different job than
`ietfparse.headers.parse_link`, and the large packaged header particularly
favored `httpx` in this run.

### Cost Versus Benefit

If you are already using `httpx` responses and want convenient access to
link-by-relation lookups, `Response.links` is pragmatic and likely sufficient
for tolerant client code.

If you need to preserve the exact number of links, preserve ordering, detect
malformed input, or reason about RFC semantics instead of convenience mapping
behavior, `ietfparse.headers.parse_link` is the better fit.

That is the key distinction: `httpx.Response.links` is optimized for client
ergonomics, while `ietfparse.headers.parse_link` is optimized for explicit,
structured parsing.
