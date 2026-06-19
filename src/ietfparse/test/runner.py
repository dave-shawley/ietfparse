"""Run packaged parser benchmarks and normalize their result payloads."""

from __future__ import annotations

import dataclasses
import importlib
import statistics
import time
import typing as t
from collections import abc

from ietfparse import _compat, algorithms, errors, headers
from ietfparse.test import accept_cases, cache_control_cases, data, link_cases

Parser = abc.Callable[[str], object]
SupportedImplementation = t.Literal[
    'workspace', 'werkzeug', 'requests', 'httpx'
]
SUPPORTED_IMPLEMENTATIONS: tuple[str, ...] = t.get_args(
    SupportedImplementation
)
IMPLEMENTATION_HEADERS: dict[
    SupportedImplementation, set[data.SupportedHeader]
] = {
    'workspace': set(data.SupportedHeader),
    'werkzeug': {
        data.SupportedHeader.ACCEPT,
        data.SupportedHeader.ACCEPT_CHARSET,
        data.SupportedHeader.ACCEPT_ENCODING,
        data.SupportedHeader.ACCEPT_LANGUAGE,
        data.SupportedHeader.CACHE_CONTROL,
    },
    'requests': {data.SupportedHeader.LINK},
    'httpx': {data.SupportedHeader.LINK},
}


class UnsupportedHeaderError(ValueError):
    """CLI received an unsupported header value."""

    def __init__(
        self,
        implementation: SupportedImplementation,
        unsupported_values: abc.Iterable[data.SupportedHeader],
    ) -> None:
        supported = IMPLEMENTATION_HEADERS[implementation]
        supported_detail = sorted(repr(header.value) for header in supported)
        unsupported_detail = sorted(
            repr(header.value) for header in unsupported_values
        )
        super().__init__(
            f'The {implementation} implementation only supports the '
            f'following headers: {", ".join(supported_detail)}. '
            f'Unsupported header values: {", ".join(unsupported_detail)}'
        )


class BenchmarkResultJson(t.TypedDict):
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


class ParserOutcomeJson(t.TypedDict):
    """Stable JSON schema for one parser outcome."""

    status: str
    result: object | None
    error_type: str | None
    error_message: str | None


class LinkComparisonJson(t.TypedDict):
    """Stable JSON schema for one link edge-case comparison."""

    case_id: str
    description: str
    sample: str
    strict: bool
    workspace: ParserOutcomeJson
    requests: ParserOutcomeJson
    httpx: ParserOutcomeJson


class AcceptComparisonJson(t.TypedDict):
    """Stable JSON schema for one Accept negotiation comparison."""

    case_id: str
    description: str
    accept: str
    available: list[str]
    default: str | None
    workspace: ParserOutcomeJson
    werkzeug: ParserOutcomeJson


class CacheControlComparisonJson(t.TypedDict):
    """Stable JSON schema for one Cache-Control parsing comparison."""

    case_id: str
    description: str
    sample: str
    workspace: ParserOutcomeJson
    werkzeug: ParserOutcomeJson


@dataclasses.dataclass(frozen=True)
class BenchmarkImplementation:
    """Adapter for a benchmarked implementation of the parser surface."""

    name: str
    parser_resolver: abc.Callable[[str], Parser]

    def parser_for(self, parser_name: str) -> Parser:
        """Resolve the parser callable for `parser_name`."""
        return self.parser_resolver(parser_name)


@dataclasses.dataclass(frozen=True)
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


@dataclasses.dataclass(frozen=True)
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


def _resolve_werkzeug_parser(parser_name: str) -> Parser:
    accept_classes = {
        'parse_accept': 'MIMEAccept',
        'parse_accept_charset': 'CharsetAccept',
        'parse_accept_encoding': 'Accept',
        'parse_accept_language': 'LanguageAccept',
    }
    class_name = accept_classes.get(parser_name)
    try:
        http_module = importlib.import_module('werkzeug.http')
    except ImportError as error:  # pragma: no cover -- env dependent
        raise RuntimeError(
            'The werkzeug benchmark implementation requires the werkzeug '
            'package to be installed.'
        ) from error

    if parser_name == 'parse_cache_control':
        return http_module.parse_cache_control_header

    if class_name is None:
        raise ValueError(
            'The werkzeug implementation only supports the Accept-family '
            'headers and Cache-Control'
        )
    datastructures_module = importlib.import_module('werkzeug.datastructures')
    parse_accept_header = http_module.parse_accept_header
    accept_class = getattr(datastructures_module, class_name)

    def _parse_accept_header(value: str) -> object:
        return parse_accept_header(value, cls=accept_class)

    return _parse_accept_header


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
    parser_resolver=lambda parser_name: getattr(headers, parser_name),
)
WERKZEUG_IMPLEMENTATION = BenchmarkImplementation(
    name='werkzeug',
    parser_resolver=_resolve_werkzeug_parser,
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
    match name:
        case 'workspace':
            return WORKSPACE_IMPLEMENTATION
        case 'werkzeug':
            return WERKZEUG_IMPLEMENTATION
        case 'requests':
            return REQUESTS_IMPLEMENTATION
        case 'httpx':
            return HTTPX_IMPLEMENTATION
        case _ as unexpected:
            _compat.assert_never(unexpected)
            raise AssertionError('unreachable')


def validate_implementation_support(
    *,
    implementation_name: SupportedImplementation,
    header_ids: abc.Iterable[data.SupportedHeader],
) -> None:
    """Ensure that an implementation supports the selected headers."""
    supported_headers = IMPLEMENTATION_HEADERS[implementation_name]
    unsupported = sorted(
        header_id
        for header_id in header_ids
        if header_id not in supported_headers
    )
    if unsupported:
        raise UnsupportedHeaderError(implementation_name, unsupported)


def common_supported_headers(
    implementation_names: t.Iterable[SupportedImplementation],
) -> tuple[data.SupportedHeader, ...]:
    """Return headers supported by every selected implementation."""
    names = tuple(implementation_names)
    if not names:
        return ()
    supported = [
        IMPLEMENTATION_HEADERS[implementation_name]
        for implementation_name in names
    ]
    common = set.intersection(*supported)
    return tuple(
        header_id for header_id in data.SupportedHeader if header_id in common
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
            if not samples:
                continue
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
                lambda case=case: headers.parse_link(
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


def compare_accept_cases() -> list[AcceptComparisonJson]:
    """Run curated Accept negotiation cases through both implementations."""
    werkzeug_parser = implementation_named('werkzeug').parser_for(
        'parse_accept'
    )
    return [
        AcceptComparisonJson(
            case_id=case.case_id,
            description=case.description,
            accept=case.accept,
            available=list(case.available),
            default=case.default,
            workspace=_capture_outcome(
                lambda case=case: algorithms.select_content_type(
                    case.accept,
                    case.available,
                    default=case.default,
                ),
                _normalize_workspace_accept_result,
            ),
            werkzeug=_capture_outcome(
                lambda case=case: _select_werkzeug_best_match(
                    parser=werkzeug_parser,
                    accept=case.accept,
                    available=case.available,
                    default=case.default,
                ),
                _normalize_werkzeug_accept_result,
            ),
        )
        for case in accept_cases.CASES
    ]


def compare_cache_control_cases() -> list[CacheControlComparisonJson]:
    """Run curated Cache-Control cases through both implementations."""
    werkzeug_parser = implementation_named('werkzeug').parser_for(
        'parse_cache_control'
    )
    return [
        CacheControlComparisonJson(
            case_id=case.case_id,
            description=case.description,
            sample=case.sample,
            workspace=_capture_outcome(
                lambda case=case: headers.parse_cache_control(case.sample),
                _normalize_cache_control_result,
            ),
            werkzeug=_capture_outcome(
                lambda case=case: werkzeug_parser(case.sample),
                _normalize_werkzeug_cache_control_result,
            ),
        )
        for case in cache_control_cases.CASES
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
            samples = benchmark.samples_for(workload)
            if not samples:
                continue
            _validate_samples(
                header_id=benchmark.header_id,
                workload=workload,
                samples=samples,
                parser=parser,
            )


def _validate_samples(
    *,
    header_id: str,
    workload: str,
    samples: tuple[str, ...],
    parser: Parser,
) -> None:
    probe: str | None = None
    try:
        for sample in samples:
            probe = sample
            parser(sample)
    except (errors.RootException, ValueError) as error:
        raise ValueError(
            f'invalid benchmark fixture for {header_id}/{workload}: {probe!r}'
        ) from error


def _run_once(
    *, samples: tuple[str, ...], parser: Parser, iterations: int
) -> tuple[int, int]:
    start = time.perf_counter_ns()
    checksum = 0
    for _ in range(iterations):
        for sample in samples:
            checksum += len(repr(parser(sample)))
    return time.perf_counter_ns() - start, checksum


def _capture_outcome(
    parser: abc.Callable[[], object],
    normalize: abc.Callable[[object], object],
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
    links = t.cast('list[t.Any]', parsed)
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
    return [dict(link) for link in t.cast('list[dict[str, str]]', parsed)]


def _normalize_httpx_link_result(parsed: object) -> object:
    return dict(t.cast('dict[str | None, dict[str, str]]', parsed))


def _select_werkzeug_best_match(
    *,
    parser: Parser,
    accept: str,
    available: tuple[str, ...],
    default: str | None,
) -> object:
    parsed = parser(accept)
    return t.cast(
        't.Any',
        parsed,
    ).best_match(list(available), default=default)


def _normalize_workspace_accept_result(parsed: object) -> object:
    selected, matched = t.cast(
        'tuple[t.Any, t.Any]',
        parsed,
    )
    return {
        'selected': str(selected),
        'matched': str(matched),
    }


def _normalize_werkzeug_accept_result(parsed: object) -> object:
    selected = t.cast('str | None', parsed)
    return {'selected': selected}


def _normalize_cache_control_result(parsed: object) -> object:
    return dict(t.cast('dict[str, str | int | bool | None]', parsed).items())


def _normalize_werkzeug_cache_control_result(parsed: object) -> object:
    return dict(t.cast('t.Any', parsed).items())


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
