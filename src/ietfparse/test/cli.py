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
    from rich import console, panel, table
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
    results: list[runner.BenchmarkResultJson]


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
) -> RunPayload:
    """Build the stable JSON payload for `run` output."""
    return {
        'headers': list(header_ids),
        'workloads': list(workload_ids),
        'results': [runner.result_to_json(result) for result in results],
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
    results = runner.run_benchmarks(
        dataset,
        selection=runner.BenchmarkSelection(
            header_ids=header_ids,
            workload_ids=workload_ids,
            iterations=iterations,
            repeat=repeat,
        ),
    )
    payload = build_run_payload(
        results=results,
        header_ids=header_ids,
        workload_ids=workload_ids,
    )
    format_name = determine_output_format(
        requested=output_format,
        stream=sys.stdout,
    )
    if format_name is OutputFormat.json:
        _write_json(payload)
        return
    _render_rich_results(payload=payload, quiet=quiet)


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


def _write_json(payload: ListPayload | RunPayload) -> None:
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
                f'results={len(payload["results"])}'
            )
        )
    cons.print(tbl)
