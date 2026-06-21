import contextlib
import importlib.util
import io
import pathlib
import sys
import tempfile
import types
import typing as t
import unittest
import unittest.mock


def _load_profile_benchmark() -> types.ModuleType:
    module_name = 'profile_benchmark_test_module'
    module_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / 'tools'
        / 'profile_benchmark.py'
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'failed to load {module_path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


profile_benchmark = _load_profile_benchmark()


class GithubProfileBenchmarkRenderTests(unittest.TestCase):
    def test_render_github_emits_markdown_summary(self) -> None:
        payload = {
            'header': 'accept',
            'parser': 'parse_accept',
            'targets': [
                {
                    'label': 'origin/main',
                    'resolved_revision': 'abc1234',
                    'results': [
                        {
                            'status': 'ok',
                            'workload': 'realistic',
                            'ns_per_call': 120.0,
                        },
                        {
                            'status': 'ok',
                            'workload': 'large',
                            'ns_per_call': 800.0,
                        },
                    ],
                },
                {
                    'label': 'workspace',
                    'resolved_revision': 'def5678',
                    'results': [
                        {
                            'status': 'ok',
                            'workload': 'realistic',
                            'ns_per_call': 90.0,
                        },
                        {
                            'status': 'ok',
                            'workload': 'large',
                            'ns_per_call': 960.0,
                        },
                    ],
                },
            ],
        }

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            profile_benchmark.render_github(payload)

        rendered = stdout.getvalue()
        self.assertIn('## `accept` benchmark (main vs head)', rendered)
        self.assertIn('| Target | Revision |', rendered)
        self.assertIn(
            '| Workload | main ns/call | head ns/call | Result |',
            rendered,
        )
        self.assertIn('| realistic | 120.0 | 90.0 | 25.0% faster |', rendered)
        self.assertIn('| large | 800.0 | 960.0 | 20.0% slower |', rendered)
        self.assertNotIn('Profile:', rendered)

    def test_render_github_reports_failures_below_table(self) -> None:
        empty_results: list[dict[str, t.Any]] = []
        payload = {
            'header': 'content-type',
            'parser': 'parse_content_type',
            'targets': [
                {
                    'label': 'main',
                    'resolved_revision': 'abc1234',
                    'results': [
                        {
                            'status': 'error',
                            'workload': 'large',
                            'error': 'boom',
                        }
                    ],
                },
                {
                    'label': 'workspace',
                    'resolved_revision': 'def5678',
                    'results': empty_results,
                    'status': 'worker-error',
                    'error': 'worker exited 1',
                },
            ],
        }

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            profile_benchmark.render_github(payload)

        rendered = stdout.getvalue()
        self.assertIn('Failures:', rendered)
        self.assertIn('- `main` `large` benchmark error: boom', rendered)
        self.assertIn('- `head` worker error: worker exited 1', rendered)


class GithubProfileBenchmarkMainTests(unittest.TestCase):
    def test_main_skips_profile_collection_for_github_format(self) -> None:
        dataset_file = pathlib.Path(tempfile.gettempdir()) / 'bench.toml'
        dataset_file.write_text('')
        targets = [
            profile_benchmark.TargetSpec(
                label='origin/main',
                source_root=pathlib.Path(__file__).resolve().parents[1],
                resolved_revision='abc1234',
            )
        ]

        with (
            unittest.mock.patch.object(
                profile_benchmark,
                'load_header_dataset',
                return_value=profile_benchmark.HeaderDataset(
                    parser='parse_accept',
                    workloads={'large': ['x']},
                ),
            ),
            unittest.mock.patch.object(
                profile_benchmark, 'iter_targets', return_value=targets
            ),
            unittest.mock.patch.object(
                profile_benchmark,
                'invoke_worker',
                return_value={
                    'status': 'ok',
                    'results': [],
                    'profiles': [],
                },
            ) as invoke_worker,
            unittest.mock.patch.object(profile_benchmark, 'render_github'),
        ):
            exit_code = profile_benchmark.main(
                [
                    'accept',
                    'origin/main',
                    '--dataset',
                    str(dataset_file),
                    '--format',
                    'github',
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            invoke_worker.call_args.kwargs['profile_workloads'],
            [],
        )
