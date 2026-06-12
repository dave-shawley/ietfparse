"""Typer-based CLI for packaged ``ietfparse`` parser benchmarks."""

from __future__ import annotations

import enum
import json
import pathlib  # noqa: TC003
import sys
import typing as t

if t.TYPE_CHECKING:
    from collections import abc

try:
    import typer
    from rich import console, panel, table, text
except ImportError as error:  # pragma: no cover -- env dependent
    raise RuntimeError(
        'The benchmark CLI requires optional dependencies. '
        'Install ietfparse[tests] to use it.'
    ) from error

from ietfparse.test import data, runner


class OutputFormat(str, enum.Enum):
    """Supported CLI output formats."""

    rich = 'rich'
    json = 'json'


class ListPayload(t.TypedDict):
    """Stable JSON schema for `list` output."""

    headers: list[str]
    workloads: list[str]
    sample_counts: dict[str, dict[str, int]]


class RunPayload(t.TypedDict):
    """Stable JSON schema for `run` output."""

    headers: list[data.SupportedHeader]
    workloads: list[data.SupportedWorkload]
    implementations: list[runner.SupportedImplementation]
    results: list[runner.BenchmarkResultJson]


class CompareLinkPayload(t.TypedDict):
    """Stable JSON schema for `compare link` output."""

    case_count: int
    results: list[runner.LinkComparisonJson]


class CompareAcceptPayload(t.TypedDict):
    """Stable JSON schema for `compare accept` output."""

    case_count: int
    results: list[runner.AcceptComparisonJson]


class CompareCacheControlPayload(t.TypedDict):
    """Stable JSON schema for `compare cache-control` output."""

    case_count: int
    results: list[runner.CacheControlComparisonJson]


class CompareImplementationRowJson(t.TypedDict):
    """Stable JSON schema for one implementation comparison row."""

    header: str
    workload: str
    ns_per_call: dict[str, float]
    vs_workspace: dict[str, float]


class CompareImplementationPayload(t.TypedDict):
    """Stable JSON schema for `compare implementation` output."""

    headers: list[data.SupportedHeader]
    workloads: list[data.SupportedWorkload]
    implementations: list[runner.SupportedImplementation]
    results: list[CompareImplementationRowJson]


class ImplementationDiffJson(t.TypedDict):
    """Stable JSON schema for one implementation timing diff."""

    old_ns_per_call: float
    new_ns_per_call: float
    delta_ns_per_call: float
    ratio: float
    percent_change: float


class CompareImplementationDiffRowJson(t.TypedDict):
    """Stable JSON schema for one compare-implementation diff row."""

    header: str
    workload: str
    implementations: dict[str, ImplementationDiffJson]


class CompareImplementationDiffPayload(t.TypedDict):
    """Stable JSON schema for `diff` output."""

    baseline_label: str
    candidate_label: str
    headers: list[data.SupportedHeader]
    workloads: list[data.SupportedWorkload]
    implementations: list[runner.SupportedImplementation]
    results: list[CompareImplementationDiffRowJson]


T = t.TypeVar('T')


def _normalize_values(
    label: str,
    valid: abc.Iterable[str],
    values: abc.Iterable[str] | None,
) -> tuple[str, ...]:
    if not values:
        values = valid
    invalid = [v for v in values if v.lower() not in valid]
    if invalid:
        detail = [repr(v) for v in invalid]
        raise ValueError(f'Unsupported {label} value: {", ".join(detail)}')
    return tuple(v.lower() for v in values)


def resolve_headers(
    selected: abc.Iterable[str] | None,
) -> tuple[data.SupportedHeader, ...]:
    """Normalize an optional header selection list."""
    return t.cast(
        'tuple[data.SupportedHeader, ...]',
        _normalize_values(
            label='header',
            valid=data.SUPPORTED_HEADERS,
            values=selected,
        ),
    )


def resolve_workloads(
    selected: abc.Iterable[str] | None,
) -> tuple[data.SupportedWorkload, ...]:
    """Normalize an optional workload selection list."""
    return t.cast(
        'tuple[data.SupportedWorkload, ...]',
        _normalize_values(
            label='workload',
            valid=data.SUPPORTED_WORKLOADS,
            values=selected,
        ),
    )


def resolve_implementations(
    selected: abc.Iterable[str] | None,
) -> tuple[runner.SupportedImplementation, ...]:
    """Normalize an optional implementation selection list."""
    if not selected:
        return ('workspace',)
    return t.cast(
        'tuple[runner.SupportedImplementation, ...]',
        _normalize_values(
            label='implementation',
            valid=runner.SUPPORTED_IMPLEMENTATIONS,
            values=selected,
        ),
    )


def resolve_compare_implementations(
    selected: abc.Iterable[str],
) -> tuple[runner.SupportedImplementation, ...]:
    """Normalize comparison implementations with workspace always included."""
    normalized = _normalize_values(
        label='implementation',
        valid=runner.SUPPORTED_IMPLEMENTATIONS,
        values=selected,
    )
    unique = tuple(dict.fromkeys(('workspace', *normalized)))
    if unique == ('workspace',):
        raise ValueError(
            'compare implementation requires at least one non-workspace '
            'implementation'
        )
    return t.cast('tuple[runner.SupportedImplementation, ...]', unique)


def determine_output_format(
    *, requested: OutputFormat | None, stream: t.IO[str]
) -> OutputFormat:
    """Choose an output format from explicit selection or TTY detection."""
    if requested is not None:
        return requested
    return OutputFormat.rich if stream.isatty() else OutputFormat.json


def build_list_payload(dataset: data.BenchmarkDataset) -> ListPayload:
    """Build the stable JSON payload for `list` output."""
    return {
        'headers': sorted(data.SUPPORTED_HEADERS),
        'workloads': sorted(data.SUPPORTED_WORKLOADS),
        'sample_counts': dataset.sample_counts(),
    }


def build_run_payload(
    *,
    results: abc.Iterable[runner.BenchmarkResult],
    header_ids: abc.Sequence[data.SupportedHeader],
    workload_ids: abc.Sequence[data.SupportedWorkload],
    implementation_ids: abc.Sequence[runner.SupportedImplementation],
) -> RunPayload:
    """Build the stable JSON payload for `run` output."""
    return {
        'headers': list(header_ids),
        'workloads': list(workload_ids),
        'implementations': list(implementation_ids),
        'results': [runner.result_to_json(result) for result in results],
    }


def build_compare_link_payload(
    *,
    results: abc.Sequence[runner.LinkComparisonJson],
) -> CompareLinkPayload:
    """Build the stable JSON payload for `compare link` output."""
    return {
        'case_count': len(results),
        'results': list(results),
    }


def build_compare_accept_payload(
    *,
    results: abc.Sequence[runner.AcceptComparisonJson],
) -> CompareAcceptPayload:
    """Build the stable JSON payload for `compare accept` output."""
    return {
        'case_count': len(results),
        'results': list(results),
    }


def build_compare_cache_control_payload(
    *,
    results: abc.Sequence[runner.CacheControlComparisonJson],
) -> CompareCacheControlPayload:
    """Build the stable JSON payload for `compare cache-control` output."""
    return {
        'case_count': len(results),
        'results': list(results),
    }


def build_compare_implementation_payload(
    *,
    results: abc.Iterable[runner.BenchmarkResult],
    header_ids: abc.Sequence[data.SupportedHeader],
    workload_ids: abc.Sequence[data.SupportedWorkload],
    implementation_ids: abc.Sequence[runner.SupportedImplementation],
) -> CompareImplementationPayload:
    """Build the stable JSON payload for `compare implementation` output."""
    result_map = {
        (result.header, result.workload, result.implementation): result
        for result in results
    }
    comparison_rows: list[CompareImplementationRowJson] = []
    for header_id in header_ids:
        for workload_id in workload_ids:
            workspace_result = result_map[
                (header_id, workload_id, 'workspace')
            ]
            row_results = {
                implementation_id: result_map[
                    (header_id, workload_id, implementation_id)
                ]
                for implementation_id in implementation_ids
            }
            comparison_rows.append(
                CompareImplementationRowJson(
                    header=header_id,
                    workload=workload_id,
                    ns_per_call={
                        implementation_id: row_results[
                            implementation_id
                        ].ns_per_call
                        for implementation_id in implementation_ids
                    },
                    vs_workspace={
                        implementation_id: row_results[
                            implementation_id
                        ].ns_per_call
                        / workspace_result.ns_per_call
                        for implementation_id in implementation_ids
                        if implementation_id != 'workspace'
                    },
                )
            )
    return {
        'headers': list(header_ids),
        'workloads': list(workload_ids),
        'implementations': list(implementation_ids),
        'results': comparison_rows,
    }


def build_compare_implementation_diff_payload(
    *,
    baseline: CompareImplementationPayload,
    candidate: CompareImplementationPayload,
    baseline_label: str,
    candidate_label: str,
) -> CompareImplementationDiffPayload:
    """Build the stable JSON payload for `diff` output."""
    implementations = _validate_diff_dimensions(
        baseline=baseline,
        candidate=candidate,
    )
    baseline_rows = _index_compare_implementation_rows(baseline)
    candidate_rows = _index_compare_implementation_rows(candidate)
    if baseline_rows.keys() != candidate_rows.keys():
        raise ValueError(
            'diff requires both payloads to have the same header/workload rows'
        )

    result_rows: list[CompareImplementationDiffRowJson] = []
    for header_id in baseline['headers']:
        for workload_id in baseline['workloads']:
            row_key = (header_id, workload_id)
            baseline_row = baseline_rows[row_key]
            candidate_row = candidate_rows[row_key]
            result_rows.append(
                CompareImplementationDiffRowJson(
                    header=header_id,
                    workload=workload_id,
                    implementations={
                        implementation_id: ImplementationDiffJson(
                            old_ns_per_call=baseline_row['ns_per_call'][
                                implementation_id
                            ],
                            new_ns_per_call=candidate_row['ns_per_call'][
                                implementation_id
                            ],
                            delta_ns_per_call=(
                                candidate_row['ns_per_call'][implementation_id]
                                - baseline_row['ns_per_call'][
                                    implementation_id
                                ]
                            ),
                            ratio=(
                                candidate_row['ns_per_call'][implementation_id]
                                / baseline_row['ns_per_call'][
                                    implementation_id
                                ]
                            ),
                            percent_change=(
                                (
                                    candidate_row['ns_per_call'][
                                        implementation_id
                                    ]
                                    - baseline_row['ns_per_call'][
                                        implementation_id
                                    ]
                                )
                                / baseline_row['ns_per_call'][
                                    implementation_id
                                ]
                            )
                            * 100,
                        )
                        for implementation_id in implementations
                    },
                )
            )
    return {
        'baseline_label': baseline_label,
        'candidate_label': candidate_label,
        'headers': list(baseline['headers']),
        'workloads': list(baseline['workloads']),
        'implementations': list(implementations),
        'results': result_rows,
    }


def _generate_autocomplete(
    values: abc.Iterable[str],
) -> abc.Callable[[str], t.Iterable[str]]:
    def _autocomplete(needle: str) -> t.Iterable[str]:
        for value in values:
            if value.startswith(needle):
                yield value

    return _autocomplete


app = typer.Typer(no_args_is_help=True)
compare_app = typer.Typer(
    help='Compare performance against different implementations.',
    no_args_is_help=True,
)
app.add_typer(compare_app, name='compare')


@app.command()
def run(  # noqa: PLR0913
    *,
    header: t.Annotated[
        list[str] | None,
        typer.Option(
            '--header',
            help='Header id to benchmark. May be specified multiple times.',
            autocompletion=_generate_autocomplete(data.SUPPORTED_HEADERS),
        ),
    ] = None,
    workload: t.Annotated[
        list[str] | None,
        typer.Option(
            '--workload',
            help='Workload to benchmark. May be specified multiple times.',
            autocompletion=_generate_autocomplete(data.SUPPORTED_WORKLOADS),
        ),
    ] = None,
    iterations: t.Annotated[
        int,
        typer.Option(
            '--iterations',
            min=1,
            help='Passes over each sample set per repeat.',
        ),
    ] = 1_000,
    repeat: t.Annotated[
        int,
        typer.Option(
            '--repeat',
            min=1,
            help='Number of timing repeats to execute.',
        ),
    ] = 5,
    implementation: t.Annotated[
        list[str] | None,
        typer.Option(
            '--implementation',
            help=(
                'Implementation id to benchmark. '
                'May be specified multiple times.'
            ),
            autocompletion=_generate_autocomplete(
                runner.SUPPORTED_IMPLEMENTATIONS
            ),
        ),
    ] = None,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
    quiet: t.Annotated[
        bool,
        typer.Option(
            '--quiet',
            help='Reduce non-essential rich output.',
        ),
    ] = False,
) -> None:
    """Run one or more benchmark suite."""
    dataset = data.load_dataset()
    header_ids = resolve_headers(header)
    workload_ids = resolve_workloads(workload)
    implementation_ids = resolve_implementations(implementation)
    results: list[runner.BenchmarkResult] = []
    selection = runner.BenchmarkSelection(
        header_ids=header_ids,
        workload_ids=workload_ids,
        iterations=iterations,
        repeat=repeat,
    )
    for implementation_name in implementation_ids:
        runner.validate_implementation_support(
            implementation_name=implementation_name,
            header_ids=header_ids,
        )
        results.extend(
            runner.run_benchmarks(
                dataset,
                selection=selection,
                implementation=runner.implementation_named(
                    implementation_name
                ),
            )
        )
    payload = build_run_payload(
        results=results,
        header_ids=header_ids,
        workload_ids=workload_ids,
        implementation_ids=implementation_ids,
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_results(payload=payload, quiet=quiet)


@compare_app.command(name='link')
def compare_link(
    *,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """Compare curated Link header cases across implementations."""
    payload = build_compare_link_payload(results=runner.compare_link_cases())
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_link_comparison(payload)


@compare_app.command(name='accept')
def compare_accept(
    *,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """Compare curated Accept negotiation cases across implementations."""
    payload = build_compare_accept_payload(
        results=runner.compare_accept_cases()
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_accept_comparison(payload)


@compare_app.command(name='cache-control')
def compare_cache_control(
    *,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """Compare curated Cache-Control parsing cases across implementations."""
    payload = build_compare_cache_control_payload(
        results=runner.compare_cache_control_cases()
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_cache_control_comparison(payload)


@compare_app.command(name='implementation')
def compare_implementation(
    implementation: t.Annotated[
        list[str],
        typer.Argument(
            help=(
                'One or more non-workspace implementations to compare '
                'against workspace.'
            ),
            autocompletion=_generate_autocomplete(
                runner.SUPPORTED_IMPLEMENTATIONS
            ),
        ),
    ],
    *,
    workload: t.Annotated[
        list[str] | None,
        typer.Option(
            '--workload',
            help='Workload to benchmark. May be specified multiple times.',
            autocompletion=_generate_autocomplete(data.SUPPORTED_WORKLOADS),
        ),
    ] = None,
    iterations: t.Annotated[
        int,
        typer.Option(
            '--iterations',
            min=1,
            help='Passes over each sample set per repeat.',
        ),
    ] = 1_000,
    repeat: t.Annotated[
        int,
        typer.Option(
            '--repeat',
            min=1,
            help='Number of timing repeats to execute.',
        ),
    ] = 5,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """Compare benchmark timings on headers shared by all implementations."""
    dataset = data.load_dataset()
    workload_ids = resolve_workloads(workload)
    implementation_ids = resolve_compare_implementations(implementation)
    header_ids = runner.common_supported_headers(implementation_ids)
    if not header_ids:
        raise ValueError(
            'The selected implementations do not share any benchmark headers.'
        )
    results: list[runner.BenchmarkResult] = []
    selection = runner.BenchmarkSelection(
        header_ids=header_ids,
        workload_ids=workload_ids,
        iterations=iterations,
        repeat=repeat,
    )
    for implementation_name in implementation_ids:
        results.extend(
            runner.run_benchmarks(
                dataset,
                selection=selection,
                implementation=runner.implementation_named(
                    implementation_name
                ),
            )
        )
    payload = build_compare_implementation_payload(
        results=results,
        header_ids=header_ids,
        workload_ids=workload_ids,
        implementation_ids=implementation_ids,
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_implementation_comparison(payload)


@app.command()
def diff(
    baseline_path: t.Annotated[
        pathlib.Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help='Baseline run or compare implementation JSON file.',
        ),
    ],
    candidate_path: t.Annotated[
        pathlib.Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help='Candidate run or compare implementation JSON file.',
        ),
    ],
    *,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """Summarize differences between saved benchmark JSON outputs."""
    baseline = _load_diffable_benchmark_payload(baseline_path)
    candidate = _load_diffable_benchmark_payload(candidate_path)
    payload = build_compare_implementation_diff_payload(
        baseline=baseline,
        candidate=candidate,
        baseline_label=baseline_path.name,
        candidate_label=candidate_path.name,
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_implementation_diff(payload)


@app.command(name='list')
def list_command(
    *,
    output_format: t.Annotated[
        OutputFormat | None,
        typer.Option(
            '--format',
            case_sensitive=False,
            help='Output format.',
        ),
    ] = None,
) -> None:
    """List available benchmark fixtures."""
    dataset = data.load_dataset()
    payload = build_list_payload(dataset)
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_listing(dataset)


def _write_json(
    payload: (
        ListPayload
        | RunPayload
        | CompareLinkPayload
        | CompareAcceptPayload
        | CompareCacheControlPayload
        | CompareImplementationPayload
        | CompareImplementationDiffPayload
    ),
) -> None:
    sys.stdout.write(f'{json.dumps(payload, indent=2, sort_keys=True)}\n')


def _render_rich_listing(dataset: data.BenchmarkDataset) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse benchmark fixtures')
    tbl.add_column('Header')
    tbl.add_column('Description')
    for workload in data.SUPPORTED_WORKLOADS:
        tbl.add_column(workload, justify='right')
    for header_id in data.SUPPORTED_HEADERS:
        benchmark = dataset.headers[header_id]
        tbl.add_row(
            header_id,
            benchmark.description,
            *[
                str(benchmark.sample_count(workload))
                for workload in data.SUPPORTED_WORKLOADS
            ],
        )
    cons.print(tbl)


def _render_rich_results(*, payload: RunPayload, quiet: bool) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse benchmark run')
    tbl.add_column('Header')
    tbl.add_column('Workload')
    tbl.add_column('Impl')
    tbl.add_column('Samples', justify='right')
    tbl.add_column('Bytes', justify='right')
    tbl.add_column('Median ns', justify='right')
    tbl.add_column('ns/call', justify='right')
    tbl.add_column('calls/s', justify='right')
    for row in payload['results']:
        tbl.add_row(
            row['header'],
            row['workload'],
            row['implementation'],
            str(row['sample_count']),
            str(row['byte_count']),
            str(row['median_elapsed_ns']),
            f'{row["ns_per_call"]:.1f}',
            f'{row["calls_per_second"]:.0f}',
        )
    if not quiet:
        cons.print(
            panel.Panel(
                f'headers={len(payload["headers"])} '
                f'workloads={len(payload["workloads"])} '
                f'implementations={len(payload["implementations"])} '
                f'results={len(payload["results"])}'
            )
        )
    cons.print(tbl)


def _render_rich_link_comparison(payload: CompareLinkPayload) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse link comparison')
    tbl.add_column('Case')
    tbl.add_column('Strict')
    tbl.add_column('Workspace')
    tbl.add_column('Requests')
    tbl.add_column('HTTPX')
    for row in payload['results']:
        tbl.add_row(
            row['case_id'],
            'yes' if row['strict'] else 'no',
            _comparison_summary(row['workspace']),
            _comparison_summary(row['requests']),
            _comparison_summary(row['httpx']),
        )
    cons.print(panel.Panel(f'cases={payload["case_count"]}'))
    cons.print(tbl)


def _render_rich_accept_comparison(payload: CompareAcceptPayload) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse accept comparison')
    tbl.add_column('Case')
    tbl.add_column('Workspace')
    tbl.add_column('Werkzeug')
    for row in payload['results']:
        tbl.add_row(
            row['case_id'],
            _accept_workspace_summary(row['workspace']),
            _accept_werkzeug_summary(row['werkzeug']),
        )
    cons.print(panel.Panel(f'cases={payload["case_count"]}'))
    cons.print(tbl)


def _render_rich_cache_control_comparison(
    payload: CompareCacheControlPayload,
) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse cache-control comparison')
    tbl.add_column('Case')
    tbl.add_column('Workspace')
    tbl.add_column('Werkzeug')
    for row in payload['results']:
        tbl.add_row(
            row['case_id'],
            _cache_control_summary(row['workspace']),
            _cache_control_summary(row['werkzeug']),
        )
    cons.print(panel.Panel(f'cases={payload["case_count"]}'))
    cons.print(tbl)


def _render_rich_implementation_comparison(
    payload: CompareImplementationPayload,
) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse implementation comparison')
    tbl.add_column('Header')
    tbl.add_column('Workload')
    for implementation_id in payload['implementations']:
        if implementation_id != 'workspace':
            tbl.add_column(f'vs {implementation_id}', justify='right')
    for implementation_id in payload['implementations']:
        tbl.add_column(f'{implementation_id} ns/call', justify='right')
    for row in payload['results']:
        cells = [row['header'], row['workload']]
        cells.extend(
            _comparison_ratio_cell(row['vs_workspace'][implementation_id])
            for implementation_id in payload['implementations']
            if implementation_id != 'workspace'
        )
        cells.extend(
            f'{row["ns_per_call"][implementation_id]:.1f}'
            for implementation_id in payload['implementations']
        )
        tbl.add_row(*cells)
    cons.print(
        panel.Panel(
            f'headers={len(payload["headers"])} '
            f'workloads={len(payload["workloads"])} '
            f'implementations={len(payload["implementations"])} '
            f'results={len(payload["results"])}'
        )
    )
    cons.print(tbl)


def _render_rich_implementation_diff(
    payload: CompareImplementationDiffPayload,
) -> None:
    cons = console.Console()
    tbl = table.Table(title='ietfparse implementation diff')
    tbl.add_column('Header')
    tbl.add_column('Workload')
    for implementation_id in payload['implementations']:
        tbl.add_column(f'{implementation_id} delta', justify='right')
    for implementation_id in payload['implementations']:
        tbl.add_column(
            f'{implementation_id} {payload["baseline_label"]} ns/call',
            justify='right',
        )
    for implementation_id in payload['implementations']:
        tbl.add_column(
            f'{implementation_id} {payload["candidate_label"]} ns/call',
            justify='right',
        )
    for row in payload['results']:
        cells = [row['header'], row['workload']]
        cells.extend(
            _implementation_delta_cell(
                row['implementations'][implementation_id]
            )
            for implementation_id in payload['implementations']
        )
        cells.extend(
            f'{row["implementations"][implementation_id]["old_ns_per_call"]:.1f}'
            for implementation_id in payload['implementations']
        )
        cells.extend(
            f'{row["implementations"][implementation_id]["new_ns_per_call"]:.1f}'
            for implementation_id in payload['implementations']
        )
        tbl.add_row(*cells)
    cons.print(
        panel.Panel(
            f'baseline={payload["baseline_label"]} '
            f'candidate={payload["candidate_label"]} '
            f'headers={len(payload["headers"])} '
            f'workloads={len(payload["workloads"])} '
            f'implementations={len(payload["implementations"])} '
            f'results={len(payload["results"])}'
        )
    )
    cons.print(tbl)


def _comparison_ratio_cell(ratio: float) -> text.Text:
    if ratio < 1:
        indicator = 'v'
        style = 'red'
    elif ratio > 1:
        indicator = '^'
        style = 'green'
    else:
        indicator = '='
        style = 'yellow'
    return text.Text(f'{indicator} {ratio:.2f}x', style=style)


def _implementation_delta_cell(
    payload: ImplementationDiffJson,
) -> text.Text:
    ratio = payload['ratio']
    percent_change = payload['percent_change']
    if ratio < 1:
        indicator = 'v'
        style = 'green'
    elif ratio > 1:
        indicator = '^'
        style = 'red'
    else:
        indicator = '='
        style = 'yellow'
    return text.Text(
        f'{indicator} {ratio:.2f}x ({percent_change:+.1f}%)',
        style=style,
    )


def _load_diffable_benchmark_payload(
    path: pathlib.Path,
) -> CompareImplementationPayload:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f'{path} is not valid JSON') from error
    if not isinstance(payload, dict):
        raise TypeError(
            f'{path} is not a run or compare implementation JSON payload'
        )
    if set(payload) != {'headers', 'implementations', 'results', 'workloads'}:
        raise ValueError(
            f'{path} is not a run or compare implementation JSON payload'
        )
    implementations = payload.get('implementations')
    results = payload.get('results')
    if not isinstance(implementations, list) or not isinstance(results, list):
        raise TypeError(
            f'{path} is not a run or compare implementation JSON payload'
        )
    if not results:
        return t.cast('CompareImplementationPayload', payload)

    compare_implementation_row_keys = {
        'header',
        'ns_per_call',
        'vs_workspace',
        'workload',
    }
    run_row_keys = {
        'byte_count',
        'calls_per_second',
        'header',
        'implementation',
        'iterations',
        'median_elapsed_ns',
        'ns_per_call',
        'repeat',
        'sample_count',
        'workload',
    }

    for row in results:
        if not isinstance(row, dict):
            raise TypeError(
                f'{path} is not a run or compare implementation JSON payload'
            )

    row_keys = {frozenset(row) for row in results}
    if row_keys == {frozenset(compare_implementation_row_keys)}:
        return t.cast('CompareImplementationPayload', payload)
    if row_keys == {frozenset(run_row_keys)}:
        return _normalize_run_payload_for_diff(
            payload=t.cast('RunPayload', payload)
        )

    raise ValueError(
        f'{path} is not a run or compare implementation JSON payload'
    )


def _normalize_run_payload_for_diff(
    *, payload: RunPayload
) -> CompareImplementationPayload:
    result_map: dict[tuple[str, str, str], runner.BenchmarkResultJson] = {}
    for row in payload['results']:
        row_key = (row['header'], row['workload'], row['implementation'])
        result_map[row_key] = row

    comparison_rows: list[CompareImplementationRowJson] = []
    for header_id in payload['headers']:
        for workload_id in payload['workloads']:
            ns_per_call: dict[str, float] = {}
            for implementation_id in payload['implementations']:
                row_key = (header_id, workload_id, implementation_id)
                try:
                    ns_per_call[implementation_id] = result_map[row_key][
                        'ns_per_call'
                    ]
                except KeyError as error:
                    raise ValueError(
                        'run payload is missing one or more '
                        'header/workload/implementation rows'
                    ) from error
            comparison_rows.append(
                CompareImplementationRowJson(
                    header=header_id,
                    workload=workload_id,
                    ns_per_call=ns_per_call,
                    vs_workspace=_vs_workspace_ratios(ns_per_call),
                )
            )
    return CompareImplementationPayload(
        headers=list(payload['headers']),
        workloads=list(payload['workloads']),
        implementations=list(payload['implementations']),
        results=comparison_rows,
    )


def _vs_workspace_ratios(
    ns_per_call: dict[str, float],
) -> dict[str, float]:
    if 'workspace' not in ns_per_call:
        return {}
    workspace_ns_per_call = ns_per_call['workspace']
    return {
        implementation_id: (implementation_ns_per_call / workspace_ns_per_call)
        for (
            implementation_id,
            implementation_ns_per_call,
        ) in ns_per_call.items()
        if implementation_id != 'workspace'
    }


def _validate_diff_dimensions(
    *,
    baseline: CompareImplementationPayload,
    candidate: CompareImplementationPayload,
) -> list[runner.SupportedImplementation]:
    if baseline['headers'] != candidate['headers']:
        raise ValueError(
            'diff requires both payloads to have the same headers '
            'in the same order'
        )
    if baseline['workloads'] != candidate['workloads']:
        raise ValueError(
            'diff requires both payloads to have the same workloads '
            'in the same order'
        )
    if baseline['implementations'] != candidate['implementations']:
        raise ValueError(
            'diff requires both payloads to have the same implementations'
        )
    return list(candidate['implementations'])


def _index_compare_implementation_rows(
    payload: CompareImplementationPayload,
) -> dict[tuple[str, str], CompareImplementationRowJson]:
    rows: dict[tuple[str, str], CompareImplementationRowJson] = {}
    for row in payload['results']:
        rows[(row['header'], row['workload'])] = row
    return rows


def _comparison_summary(payload: runner.ParserOutcomeJson) -> str:
    if payload['status'] == 'error':
        return f'error:{payload["error_type"]}'
    result = payload['result']
    if isinstance(result, list):
        return f'ok:{len(result)} value(s)'
    return 'ok'


def _accept_workspace_summary(payload: runner.ParserOutcomeJson) -> str:
    if payload['status'] == 'error':
        return f'error:{payload["error_type"]}'
    result = t.cast('dict[str, str]', payload['result'])
    return f'{result["selected"]} <= {result["matched"]}'


def _accept_werkzeug_summary(payload: runner.ParserOutcomeJson) -> str:
    if payload['status'] == 'error':
        return f'error:{payload["error_type"]}'
    result = t.cast('dict[str, str | None]', payload['result'])
    return result['selected'] or 'none'


def _cache_control_summary(payload: runner.ParserOutcomeJson) -> str:
    if payload['status'] == 'error':
        return f'error:{payload["error_type"]}'
    result = t.cast('dict[str, object]', payload['result'])
    return json.dumps(result, sort_keys=True)
