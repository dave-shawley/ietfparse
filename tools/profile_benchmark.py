# ruff: noqa: ANN401, D101, D103, INP001, PLR0913, S202, S603, S607, T201
"""Benchmark and profile one parser across git revisions or source trees."""

from __future__ import annotations

import argparse
import cProfile
import dataclasses
import importlib
import importlib.metadata
import io
import json
import pathlib
import pstats
import statistics
import subprocess
import sys
import tarfile
import tempfile
import timeit
import traceback
import typing as t

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover -- Python 3.10 fallback
    import tomli as tomllib


@dataclasses.dataclass(frozen=True)
class TargetSpec:
    label: str
    source_root: pathlib.Path
    resolved_revision: str | None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    default_dataset = (
        repo_root / 'src' / 'ietfparse' / 'test' / 'benchmarks.toml'
    )
    parser = argparse.ArgumentParser(
        description=(
            'Benchmark and profile a parser against the packaged benchmark '
            'dataset using the current workspace, arbitrary source trees, or '
            'archived git revisions.'
        )
    )
    parser.add_argument(
        'header',
        help='Header id from the benchmark dataset.',
    )
    parser.add_argument(
        'revisions',
        nargs='*',
        help=(
            'Git revisions to benchmark. Use "." or omit entirely to include '
            'the current workspace.'
        ),
    )
    parser.add_argument(
        '--source',
        action='append',
        default=[],
        help='Additional source tree paths to benchmark.',
    )
    parser.add_argument(
        '--dataset',
        default=str(default_dataset),
        help='Benchmark dataset TOML file to load.',
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=1_000,
        help='Benchmark loop count per repeat.',
    )
    parser.add_argument(
        '--repeat',
        type=int,
        default=5,
        help='Benchmark repeat count.',
    )
    parser.add_argument(
        '--profile-workload',
        action='append',
        default=[],
        help='Workload(s) to profile with cProfile. Defaults to large.',
    )
    parser.add_argument(
        '--profile-iterations',
        type=int,
        default=200,
        help='Loop count used for each profiling run.',
    )
    parser.add_argument(
        '--profile-top',
        type=int,
        default=12,
        help='Number of cumulative-time functions to keep per profile.',
    )
    parser.add_argument(
        '--format',
        choices=('table', 'json'),
        default='table',
        help='Output format.',
    )
    parser.add_argument(
        '--python',
        default=sys.executable,
        help='Python interpreter used for isolated worker subprocesses.',
    )
    parser.add_argument(
        '--git-root',
        default=str(repo_root),
        help='Git repository root used to resolve revisions.',
    )
    parser.add_argument(
        '--worker',
        action='store_true',
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--source-root',
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker:
        payload = run_worker(args)
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
        return 0

    dataset_path = pathlib.Path(args.dataset).resolve()
    git_root = pathlib.Path(args.git_root).resolve()
    header_dataset = load_header_dataset(dataset_path, args.header)
    targets = args.revisions or ['.']
    profile_workloads = args.profile_workload or ['large']

    with tempfile.TemporaryDirectory(prefix='ietfparse-profile-') as temp_dir:
        temp_root = pathlib.Path(temp_dir)
        payload = {
            'dataset': str(dataset_path),
            'header': args.header,
            'parser': header_dataset.parser,
            'iterations': args.iterations,
            'repeat': args.repeat,
            'profile_iterations': args.profile_iterations,
            'profile_workloads': profile_workloads,
            'targets': [],
        }
        for spec in iter_targets(
            targets=targets,
            sources=args.source,
            git_root=git_root,
            temp_root=temp_root,
        ):
            payload['targets'].append(
                invoke_worker(
                    python_executable=args.python,
                    dataset_path=dataset_path,
                    spec=spec,
                    header_id=args.header,
                    iterations=args.iterations,
                    repeat=args.repeat,
                    profile_workloads=profile_workloads,
                    profile_iterations=args.profile_iterations,
                    profile_top=args.profile_top,
                )
            )

    if args.format == 'json':
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
    else:
        render_table(payload)
    return 0


def iter_targets(
    *,
    targets: list[str],
    sources: list[str],
    git_root: pathlib.Path,
    temp_root: pathlib.Path,
) -> list[TargetSpec]:
    specs: list[TargetSpec] = []
    seen_paths: set[pathlib.Path] = set()

    for target in targets:
        if target == '.':
            source_root = git_root
            specs.append(
                TargetSpec(
                    label='workspace',
                    source_root=source_root,
                    resolved_revision=resolve_revision(git_root, 'HEAD'),
                )
            )
            seen_paths.add(source_root)
            continue

        resolved = resolve_revision(git_root, target)
        source_root = materialize_revision(
            git_root=git_root,
            revision=resolved,
            target_dir=temp_root / safe_label(target),
        )
        specs.append(
            TargetSpec(
                label=target,
                source_root=source_root,
                resolved_revision=resolved,
            )
        )

    for source in sources:
        source_root = pathlib.Path(source).resolve()
        if source_root in seen_paths:
            continue
        specs.append(
            TargetSpec(
                label=str(source_root),
                source_root=source_root,
                resolved_revision=None,
            )
        )
        seen_paths.add(source_root)
    return specs


def resolve_revision(git_root: pathlib.Path, revision: str) -> str:
    completed = subprocess.run(
        ['git', 'rev-parse', '--verify', f'{revision}^{{commit}}'],
        check=True,
        cwd=git_root,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def materialize_revision(
    *,
    git_root: pathlib.Path,
    revision: str,
    target_dir: pathlib.Path,
) -> pathlib.Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ['git', 'archive', '--format=tar', revision],
        check=True,
        cwd=git_root,
        capture_output=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tarball:
        extract_tarball(tarball=tarball, target_dir=target_dir)
    return target_dir


def invoke_worker(
    *,
    python_executable: str,
    dataset_path: pathlib.Path,
    spec: TargetSpec,
    header_id: str,
    iterations: int,
    repeat: int,
    profile_workloads: list[str],
    profile_iterations: int,
    profile_top: int,
) -> dict[str, t.Any]:
    command = [
        python_executable,
        __file__,
        '--worker',
        header_id,
        '--dataset',
        str(dataset_path),
        '--source-root',
        str(spec.source_root),
        '--iterations',
        str(iterations),
        '--repeat',
        str(repeat),
        '--profile-iterations',
        str(profile_iterations),
        '--profile-top',
        str(profile_top),
    ]
    for workload in profile_workloads:
        command.extend(['--profile-workload', workload])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {
            'status': 'worker-error',
            'error': completed.stderr.strip() or completed.stdout.strip(),
            'label': spec.label,
            'resolved_revision': spec.resolved_revision,
            'source_root': str(spec.source_root),
            'available_workloads': [],
            'results': [],
            'profiles': [],
        }
    payload = json.loads(completed.stdout)
    payload.setdefault('status', 'ok')
    payload['label'] = spec.label
    payload['resolved_revision'] = spec.resolved_revision
    payload['source_root'] = str(spec.source_root)
    return payload


def run_worker(args: argparse.Namespace) -> dict[str, t.Any]:
    source_root = pathlib.Path(args.source_root).resolve()
    dataset_path = pathlib.Path(args.dataset).resolve()
    import_root = package_import_root(source_root)
    sys.path.insert(0, str(import_root))
    patch_distribution_version()
    headers = importlib.import_module('ietfparse.headers')
    header_dataset = load_header_dataset(dataset_path, args.header)
    parser = getattr(headers, header_dataset.parser)
    dataset = header_dataset.workloads
    workloads = list(dataset.keys())
    profile_workloads = args.profile_workload or ['large']
    ensure_known_workloads(profile_workloads, workloads)

    return {
        'status': 'ok',
        'available_workloads': workloads,
        'results': [
            safe_benchmark_workload(
                workload_id=workload_id,
                samples=dataset[workload_id],
                parser=parser,
                iterations=args.iterations,
                repeat=args.repeat,
            )
            for workload_id in workloads
        ],
        'profiles': [
            safe_profile_workload(
                workload_id=workload_id,
                samples=dataset[workload_id],
                parser=parser,
                iterations=args.profile_iterations,
                top=args.profile_top,
                import_root=import_root,
            )
            for workload_id in profile_workloads
        ],
    }


def patch_distribution_version() -> None:
    original_version = importlib.metadata.version
    package_not_found = importlib.metadata.PackageNotFoundError

    def _version(distribution_name: str) -> str:
        try:
            return original_version(distribution_name)
        except package_not_found:
            if distribution_name == 'ietfparse':
                return '0+benchmark'
            raise

    importlib.metadata.version = _version  # ty:ignore[invalid-assignment]


def package_import_root(source_root: pathlib.Path) -> pathlib.Path:
    src_root = source_root / 'src'
    if (src_root / 'ietfparse').is_dir():
        return src_root
    if (source_root / 'ietfparse').is_dir():
        return source_root
    raise SystemExit(
        f'could not find an ietfparse package under {source_root}'
    )


def extract_tarball(
    *, tarball: tarfile.TarFile, target_dir: pathlib.Path
) -> None:
    if sys.version_info >= (3, 12):
        tarball.extractall(target_dir, filter='data')
        return
    tarball.extractall(target_dir)


@dataclasses.dataclass(frozen=True)
class HeaderDataset:
    parser: str
    workloads: dict[str, list[str]]


def load_header_dataset(
    dataset_path: pathlib.Path, header_id: str
) -> HeaderDataset:
    payload = tomllib.loads(dataset_path.read_text())
    try:
        header_payload = payload['headers'][header_id]
    except KeyError as error:
        raise SystemExit(f'unknown benchmark header: {header_id!r}') from error
    parser_name = header_payload.get('parser')
    if not isinstance(parser_name, str) or not parser_name:
        raise SystemExit(
            f'benchmark header {header_id!r} does not declare a parser'
        )
    return HeaderDataset(
        parser=parser_name,
        workloads={
            key: value['samples']
            for key, value in header_payload.items()
            if isinstance(value, dict) and 'samples' in value
        },
    )


def ensure_known_workloads(
    selected_workloads: list[str], available_workloads: list[str]
) -> None:
    unknown = sorted(
        workload
        for workload in selected_workloads
        if workload not in available_workloads
    )
    if unknown:
        detail = ', '.join(repr(workload) for workload in unknown)
        raise SystemExit(f'unknown workload(s): {detail}')


def format_exception_message(error: BaseException) -> str:
    return ''.join(traceback.format_exception_only(type(error), error)).strip()


def safe_benchmark_workload(
    *,
    workload_id: str,
    samples: list[str],
    parser: t.Any,
    iterations: int,
    repeat: int,
) -> dict[str, t.Any]:
    try:
        result = benchmark_workload(
            workload_id=workload_id,
            samples=samples,
            parser=parser,
            iterations=iterations,
            repeat=repeat,
        )
    except Exception as error:  # pragma: no cover -- exercised by old tags
        return {
            'status': 'error',
            'workload': workload_id,
            'sample_count': len(samples),
            'iterations': iterations,
            'repeat': repeat,
            'error': format_exception_message(error),
        }
    result['status'] = 'ok'
    return result


def benchmark_workload(
    *,
    workload_id: str,
    samples: list[str],
    parser: t.Any,
    iterations: int,
    repeat: int,
) -> dict[str, t.Any]:
    elapsed = timeit.repeat(
        stmt='for sample in samples:\n    parser(sample)',
        globals={'parser': parser, 'samples': samples},
        number=iterations,
        repeat=repeat,
    )
    total_calls = iterations * len(samples)
    median_seconds = statistics.median(elapsed)
    median_elapsed_ns = int(median_seconds * 1_000_000_000)
    return {
        'workload': workload_id,
        'sample_count': len(samples),
        'iterations': iterations,
        'repeat': repeat,
        'median_elapsed_ns': median_elapsed_ns,
        'ns_per_call': median_elapsed_ns / total_calls,
        'calls_per_second': total_calls / median_seconds,
    }


def safe_profile_workload(
    *,
    workload_id: str,
    samples: list[str],
    parser: t.Any,
    iterations: int,
    top: int,
    import_root: pathlib.Path,
) -> dict[str, t.Any]:
    try:
        result = profile_workload(
            workload_id=workload_id,
            samples=samples,
            parser=parser,
            iterations=iterations,
            top=top,
            import_root=import_root,
        )
    except Exception as error:  # pragma: no cover -- exercised by old tags
        return {
            'status': 'error',
            'workload': workload_id,
            'sample_count': len(samples),
            'iterations': iterations,
            'error': format_exception_message(error),
            'top_functions': [],
        }
    result['status'] = 'ok'
    return result


def profile_workload(
    *,
    workload_id: str,
    samples: list[str],
    parser: t.Any,
    iterations: int,
    top: int,
    import_root: pathlib.Path,
) -> dict[str, t.Any]:
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(iterations):
        for sample in samples:
            parser(sample)
    profiler.disable()

    stats = import_profile_stats(profiler, top, import_root=import_root)
    return {
        'workload': workload_id,
        'sample_count': len(samples),
        'iterations': iterations,
        'top_functions': stats,
    }


StatsValue = tuple[float, int, float, float, dict[str, str]]


class StatsInterface(t.Protocol):
    stats: dict[str, StatsValue]


def import_profile_stats(
    profiler: cProfile.Profile,
    top: int,
    *,
    import_root: pathlib.Path,
) -> list[dict[str, t.Any]]:
    stats = t.cast('StatsInterface', pstats.Stats(profiler))
    sorted_functions = sorted(
        stats.stats.items(),
        key=lambda key_and_value: (
            key_and_value[1][3],  # cumulative time (ct)
            key_and_value[1][2],  # total time (tt)
            key_and_value[1][1],  # total calls (nc)
            key_and_value[1][0],  # primitive calls (cc)
        ),
        reverse=True,
    )
    top_functions: list[dict[str, t.Any]] = []
    for function, function_stats in sorted_functions[:top]:
        # cc, nc, tt, ct, callers
        primitive_calls, total_calls, total_time, cumulative_time, _ = (
            function_stats
        )
        filename, line_number, function_name = function
        top_functions.append(
            {
                'function': format_profile_function(
                    filename=filename,
                    line_number=line_number,
                    function_name=function_name,
                    import_root=import_root,
                ),
                'primitive_calls': primitive_calls,
                'total_calls': total_calls,
                'total_time_s': total_time,
                'cumulative_time_s': cumulative_time,
            }
        )

    return top_functions


def format_profile_function(
    *,
    filename: str,
    line_number: int,
    function_name: str,
    import_root: pathlib.Path,
) -> str:
    path = pathlib.Path(filename)
    try:
        relative_path = path.resolve().relative_to(import_root)
    except (OSError, RuntimeError, ValueError):
        display_path = filename
    else:
        display_path = f'/{relative_path.as_posix()}'
    return f'{display_path}:{line_number}({function_name})'


def render_table(payload: dict[str, t.Any]) -> None:
    print(
        f'Dataset: {payload["dataset"]} | header={payload["header"]} | '
        f'parser={payload["parser"]}'
    )
    print(
        'Target'.ljust(18),
        'Workload'.ljust(10),
        'Samples'.rjust(7),
        'Median ms'.rjust(12),
        'ns/call'.rjust(12),
        'calls/s'.rjust(12),
    )
    print('-' * 75)
    for target in payload['targets']:
        if target.get('status') == 'worker-error':
            print(
                truncate(target['label'], 18).ljust(18),
                'FAILED'.ljust(10),
                ''.rjust(7),
                ''.rjust(12),
                ''.rjust(12),
                ''.rjust(12),
            )
            print(f'  worker error: {target["error"]}')
            continue
        for result in target['results']:
            if result.get('status') == 'error':
                print(
                    truncate(target['label'], 18).ljust(18),
                    result['workload'].ljust(10),
                    str(result['sample_count']).rjust(7),
                    'ERROR'.rjust(12),
                    ''.rjust(12),
                    ''.rjust(12),
                )
                print(f'  benchmark error: {result["error"]}')
                continue
            print(
                truncate(target['label'], 18).ljust(18),
                result['workload'].ljust(10),
                str(result['sample_count']).rjust(7),
                f'{result["median_elapsed_ns"] / 1_000_000:.3f}'.rjust(12),
                f'{result["ns_per_call"]:.1f}'.rjust(12),
                f'{result["calls_per_second"]:.1f}'.rjust(12),
            )
        if target['profiles']:
            print(f'\nProfile: {target["label"]}')
            for profile in target['profiles']:
                if profile.get('status') == 'error':
                    print(
                        f'  workload={profile["workload"]} '
                        f'samples={profile["sample_count"]} '
                        f'iterations={profile["iterations"]} '
                        f'FAILED: {profile["error"]}'
                    )
                    continue
                print(
                    f'  workload={profile["workload"]} '
                    f'samples={profile["sample_count"]} '
                    f'iterations={profile["iterations"]}'
                )
                for entry in profile['top_functions']:
                    print(
                        '   '
                        f'{entry["cumulative_time_s"] * 1_000:8.3f} ms '
                        f'{entry["total_calls"]:8d} calls '
                        f'{entry["function"]}'
                    )
            print()


def safe_label(value: str) -> str:
    return (
        ''.join(char if char.isalnum() else '-' for char in value).strip('-')
        or 'revision'
    )


def truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return f'{value[: width - 3]}...'


if __name__ == '__main__':
    raise SystemExit(main())
