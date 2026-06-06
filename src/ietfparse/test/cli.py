"""Typer-based CLI for packaged ``ietfparse`` parser benchmarks."""

from __future__ import annotations

import enum
import json
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
        | CompareImplementationPayload
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
