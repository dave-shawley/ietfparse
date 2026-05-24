"""Run packaged parser benchmarks and normalize their result payloads."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from ietfparse import errors
from ietfparse import headers as header_parsers
from ietfparse.test import data

Parser = Callable[[str], object]


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


WORKSPACE_IMPLEMENTATION = BenchmarkImplementation(
    name='workspace',
    parser_resolver=lambda parser_name: getattr(header_parsers, parser_name),
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
