"""Run packaged parser benchmarks and normalize their result payloads."""

from __future__ import annotations

import importlib
import statistics
import time
import typing
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from ietfparse import errors
from ietfparse import headers as header_parsers
from ietfparse.test import data, link_cases

Parser = Callable[[str], object]
SupportedImplementation = typing.Literal['workspace', 'requests', 'httpx']
SUPPORTED_IMPLEMENTATIONS: tuple[str, ...] = typing.get_args(
    SupportedImplementation
)


class BenchmarkResultJson(TypedDict):
    """Stable JSON schema for one benchmark result."""

    implementation: str
    header: str
    workload: str
    sample_count: int
    byte_count: int
    repeat: int
    iterations: int
    median_elapsed_ns: int
    ns_per_call: float
    calls_per_second: float


class ParserOutcomeJson(TypedDict):
    """Stable JSON schema for one parser outcome."""

    status: str
    result: object | None
    error_type: str | None
    error_message: str | None


class LinkComparisonJson(TypedDict):
    """Stable JSON schema for one link edge-case comparison."""

    case_id: str
    description: str
    sample: str
    strict: bool
    workspace: ParserOutcomeJson
    requests: ParserOutcomeJson
    httpx: ParserOutcomeJson


@dataclass(frozen=True)
class BenchmarkImplementation:
    """Adapter for a benchmarked implementation of the parser surface."""

    name: str
    parser_resolver: Callable[[str], Parser]

    def parser_for(self, parser_name: str) -> Parser:
        """Resolve the parser callable for `parser_name`."""
        return self.parser_resolver(parser_name)


@dataclass(frozen=True)
class BenchmarkResult:
    """Normalized metrics for one header/workload benchmark run."""

    implementation: str
    header: str
    workload: str
    sample_count: int
    byte_count: int
    repeat: int
    iterations: int
    median_elapsed_ns: int
    ns_per_call: float
    calls_per_second: float


@dataclass(frozen=True)
class BenchmarkSelection:
    """Requested benchmark slice and timing parameters."""

    header_ids: tuple[data.SupportedHeader, ...]
    workload_ids: tuple[data.SupportedWorkload, ...]
    iterations: int
    repeat: int


def _resolve_requests_parser(parser_name: str) -> Parser:
    if parser_name != 'parse_link':
        raise ValueError(
            'The requests implementation only supports parse_link'
        )
    try:
        parse_header_links = importlib.import_module(
            'requests.utils'
        ).parse_header_links
    except ImportError as error:  # pragma: no cover -- env dependent
        raise RuntimeError(
            'The requests benchmark implementation requires the requests '
            'package to be installed.'
        ) from error
    return parse_header_links


def _resolve_httpx_parser(parser_name: str) -> Parser:
    if parser_name != 'parse_link':
        raise ValueError('The httpx implementation only supports parse_link')
    try:
        httpx = importlib.import_module('httpx')
    except ImportError as error:  # pragma: no cover -- env dependent
        raise RuntimeError(
            'The httpx benchmark implementation requires the httpx package '
            'to be installed.'
        ) from error

    def _parse_with_response_links(value: str) -> object:
        return httpx.Response(200, headers={'Link': value}).links

    return _parse_with_response_links


WORKSPACE_IMPLEMENTATION = BenchmarkImplementation(
    name='workspace',
    parser_resolver=lambda parser_name: getattr(header_parsers, parser_name),
)
REQUESTS_IMPLEMENTATION = BenchmarkImplementation(
    name='requests',
    parser_resolver=_resolve_requests_parser,
)
HTTPX_IMPLEMENTATION = BenchmarkImplementation(
    name='httpx',
    parser_resolver=_resolve_httpx_parser,
)


def implementation_named(
    name: SupportedImplementation,
) -> BenchmarkImplementation:
    """Resolve a supported implementation by stable name."""
    if name == 'workspace':
        return WORKSPACE_IMPLEMENTATION
    if name == 'requests':
        return REQUESTS_IMPLEMENTATION
    if name == 'httpx':
        return HTTPX_IMPLEMENTATION
    raise ValueError(f'Unsupported implementation value: {name!r}')


def validate_implementation_support(
    *,
    implementation_name: SupportedImplementation,
    header_ids: tuple[data.SupportedHeader, ...],
) -> None:
    """Ensure that an implementation supports the selected headers."""
    if implementation_name not in ('requests', 'httpx'):
        return
    unsupported = sorted(
        header_id for header_id in header_ids if header_id != 'link'
    )
    if unsupported:
        raise ValueError(
            f'The {implementation_name} implementation only supports the '
            'link header. '
            'Unsupported header values: '
            f'{", ".join(repr(h) for h in unsupported)}'
        )


def run_benchmarks(
    dataset: data.BenchmarkDataset,
    *,
    selection: BenchmarkSelection,
    implementation: BenchmarkImplementation = WORKSPACE_IMPLEMENTATION,
) -> list[BenchmarkResult]:
    """Benchmark the selected header/workload combinations."""
    results: list[BenchmarkResult] = []
    for header_id in selection.header_ids:
        benchmark = dataset.headers[header_id]
        parser = implementation.parser_for(benchmark.parser_name)
        for workload in selection.workload_ids:
            samples = benchmark.samples_for(workload)
            _validate_samples(
                header_id=header_id,
                workload=workload,
                samples=samples,
                parser=parser,
            )
            timings: list[int] = []
            for _ in range(selection.repeat):
                elapsed_ns, _ = _run_once(
                    samples=samples,
                    parser=parser,
                    iterations=selection.iterations,
                )
                timings.append(elapsed_ns)
            call_count = len(samples) * selection.iterations
            median_elapsed_ns = int(statistics.median(timings))
            ns_per_call = median_elapsed_ns / call_count
            results.append(
                BenchmarkResult(
                    implementation=implementation.name,
                    header=header_id,
                    workload=workload,
                    sample_count=len(samples),
                    byte_count=sum(len(sample.encode()) for sample in samples),
                    repeat=selection.repeat,
                    iterations=selection.iterations,
                    median_elapsed_ns=median_elapsed_ns,
                    ns_per_call=ns_per_call,
                    calls_per_second=1_000_000_000 / ns_per_call,
                )
            )
    return results


def compare_link_cases() -> list[LinkComparisonJson]:
    """Run curated Link header edge cases through both implementations."""
    requests_parser = implementation_named('requests').parser_for('parse_link')
    httpx_parser = implementation_named('httpx').parser_for('parse_link')
    return [
        LinkComparisonJson(
            case_id=case.case_id,
            description=case.description,
            sample=case.sample,
            strict=case.strict,
            workspace=_capture_outcome(
                lambda case=case: header_parsers.parse_link(
                    case.sample,
                    strict=case.strict,
                ),
                _normalize_workspace_link_result,
            ),
            requests=_capture_outcome(
                lambda case=case: requests_parser(case.sample),
                _normalize_requests_link_result,
            ),
            httpx=_capture_outcome(
                lambda case=case: httpx_parser(case.sample),
                _normalize_httpx_link_result,
            ),
        )
        for case in link_cases.CASES
    ]


def validate_dataset(
    dataset: data.BenchmarkDataset,
    *,
    implementation: BenchmarkImplementation = WORKSPACE_IMPLEMENTATION,
) -> None:
    """Validate that every packaged sample parses successfully."""
    for benchmark in dataset.headers.values():
        parser = implementation.parser_for(benchmark.parser_name)
        for workload in data.SUPPORTED_WORKLOADS:
            _validate_samples(
                header_id=benchmark.header_id,
                workload=workload,
                samples=benchmark.samples_for(workload),
                parser=parser,
            )


def _validate_samples(
    *,
    header_id: str,
    workload: str,
    samples: tuple[str, ...],
    parser: Parser,
) -> None:
    for sample in samples:
        error = _sample_error(parser, sample)
        if error is not None:
            raise ValueError(
                f'invalid benchmark fixture for {header_id}/{workload}: '
                f'{sample!r}'
            ) from error


def _sample_error(parser: Parser, sample: str) -> Exception | None:
    try:
        parser(sample)
    except (errors.RootException, ValueError) as error:
        return error
    return None


def _run_once(
    *, samples: tuple[str, ...], parser: Parser, iterations: int
) -> tuple[int, int]:
    start = time.perf_counter_ns()
    checksum = 0
    for _ in range(iterations):
        for sample in samples:
            checksum += _consume(parser(sample))
    return time.perf_counter_ns() - start, checksum


def _consume(parsed: object) -> int:
    return len(repr(parsed))


def _capture_outcome(
    parser: Callable[[], object],
    normalize: Callable[[object], object],
) -> ParserOutcomeJson:
    try:
        parsed = parser()
    except Exception as error:  # noqa: BLE001
        return ParserOutcomeJson(
            status='error',
            result=None,
            error_type=type(error).__name__,
            error_message=str(error),
        )
    return ParserOutcomeJson(
        status='ok',
        result=normalize(parsed),
        error_type=None,
        error_message=None,
    )


def _normalize_workspace_link_result(parsed: object) -> object:
    links = typing.cast('list[typing.Any]', parsed)
    return [
        {
            'target': link.target,
            'parameters': list(link.parameters),
            'rel': link.rel,
            'text': str(link),
        }
        for link in links
    ]


def _normalize_requests_link_result(parsed: object) -> object:
    return [dict(link) for link in typing.cast('list[dict[str, str]]', parsed)]


def _normalize_httpx_link_result(parsed: object) -> object:
    return dict(typing.cast('dict[str | None, dict[str, str]]', parsed))


def result_to_json(result: BenchmarkResult) -> BenchmarkResultJson:
    """Serialize a benchmark result using the stable JSON schema."""
    return {
        'implementation': result.implementation,
        'header': result.header,
        'workload': result.workload,
        'sample_count': result.sample_count,
        'byte_count': result.byte_count,
        'repeat': result.repeat,
        'iterations': result.iterations,
        'median_elapsed_ns': result.median_elapsed_ns,
        'ns_per_call': result.ns_per_call,
        'calls_per_second': result.calls_per_second,
    }
