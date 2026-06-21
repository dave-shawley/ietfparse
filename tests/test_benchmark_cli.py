import importlib
import json
import pathlib
import tempfile
import typing as t
import unittest.mock

from ietfparse.test import cli, data, runner


def _create_fake_io(*, is_tty: bool) -> unittest.mock.Mock:
    stream = unittest.mock.Mock(spec=t.IO)
    stream.isatty.return_value = is_tty
    return stream


class BenchmarkCliSelectionTests(unittest.TestCase):
    def test_normalize_values_uses_defaults(self) -> None:
        self.assertEqual(
            cli._normalize_values(
                label='workload',
                valid=data.SUPPORTED_WORKLOADS,
                values=None,
            ),
            data.SUPPORTED_WORKLOADS,
        )

    def test_normalize_values_lowercases_values(self) -> None:
        self.assertEqual(
            cli._normalize_values(
                label='workload',
                valid=data.SUPPORTED_WORKLOADS,
                values=['BROWSER', 'complex'],
            ),
            ('browser', 'complex'),
        )

    def test_normalize_values_rejects_invalid_values(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Unsupported workload value'):
            cli._normalize_values(
                label='workload',
                valid=data.SUPPORTED_WORKLOADS,
                values=['bogus'],
            )

    def test_single_workload_selection(self) -> None:
        self.assertEqual(cli.resolve_workloads(['realistic']), ('realistic',))

    def test_multiple_workload_selection(self) -> None:
        self.assertEqual(
            cli.resolve_workloads(['complex', 'large']),
            ('complex', 'large'),
        )

    def test_all_workloads_selected_by_default(self) -> None:
        self.assertEqual(cli.resolve_workloads(None), data.SUPPORTED_WORKLOADS)


class BenchmarkCliOutputModeTests(unittest.TestCase):
    def test_tty_defaults_to_rich(self) -> None:
        self.assertIs(
            cli.determine_output_format(
                requested=None,
                stream=_create_fake_io(is_tty=True),
            ),
            cli.OutputFormat.rich,
        )

    def test_non_tty_defaults_to_json(self) -> None:
        self.assertIs(
            cli.determine_output_format(
                requested=None,
                stream=_create_fake_io(is_tty=False),
            ),
            cli.OutputFormat.json,
        )

    def test_explicit_output_format_override_wins(self) -> None:
        self.assertIs(
            cli.determine_output_format(
                requested=cli.OutputFormat.json,
                stream=_create_fake_io(is_tty=True),
            ),
            cli.OutputFormat.json,
        )

    def test_module_import_covers_type_checking_branch(self) -> None:
        with unittest.mock.patch('typing.TYPE_CHECKING', new=True):
            reloaded = importlib.reload(cli)
        self.addCleanup(importlib.reload, reloaded)


class BenchmarkCliPayloadTests(unittest.TestCase):
    def test_json_payload_shape_is_stable(self) -> None:
        dataset = data.load_dataset()
        results = runner.run_benchmarks(
            dataset,
            selection=runner.BenchmarkSelection(
                header_ids=(data.SupportedHeader.ACCEPT,),
                workload_ids=('realistic',),
                iterations=1,
                repeat=1,
            ),
        )
        payload = cli.build_run_payload(
            results=results,
            header_ids=(data.SupportedHeader.ACCEPT,),
            workload_ids=('realistic',),
            implementation_ids=(runner.SupportedImplementation.WORKSPACE,),
        )
        self.assertEqual(payload['headers'], [data.SupportedHeader.ACCEPT])
        self.assertEqual(payload['workloads'], ['realistic'])
        self.assertEqual(
            payload['implementations'],
            [runner.SupportedImplementation.WORKSPACE],
        )
        self.assertEqual(len(payload['results']), 1)
        result = payload['results'][0]
        self.assertEqual(
            set(result),
            {
                'header',
                'workload',
                'implementation',
                'sample_count',
                'byte_count',
                'repeat',
                'iterations',
                'median_elapsed_ns',
                'ns_per_call',
                'calls_per_second',
            },
        )
        self.assertEqual(result['header'], data.SupportedHeader.ACCEPT)
        self.assertEqual(result['workload'], 'realistic')
        self.assertEqual(
            result['implementation'], runner.SupportedImplementation.WORKSPACE
        )

    def test_run_payload_filters_to_combinations_with_results(self) -> None:
        payload = cli.build_run_payload(
            results=[
                runner.BenchmarkResult(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                )
            ],
            header_ids=(
                data.SupportedHeader.ACCEPT,
                data.SupportedHeader.LINK,
            ),
            workload_ids=('browser', 'realistic'),
            implementation_ids=(runner.SupportedImplementation.WORKSPACE,),
        )
        self.assertEqual(payload['headers'], [data.SupportedHeader.ACCEPT])
        self.assertEqual(payload['workloads'], ['realistic'])

    def test_list_payload_includes_sample_counts(self) -> None:
        payload = cli.build_list_payload(data.load_dataset())
        self.assertEqual(payload['headers'], sorted(data.SupportedHeader))
        self.assertEqual(
            payload['workloads'], sorted(data.SUPPORTED_WORKLOADS)
        )
        counts = payload['sample_counts']
        self.assertEqual(counts[data.SupportedHeader.ACCEPT]['realistic'], 3)
        self.assertEqual(counts[data.SupportedHeader.LINK]['complex'], 2)

    def test_compare_link_payload_reports_case_count(self) -> None:
        payload = cli.build_compare_link_payload(
            results=[
                {
                    'case_id': 'edge',
                    'description': 'edge case',
                    'sample': '<>',
                    'strict': True,
                    'workspace': {
                        'status': 'ok',
                        'result': [],
                        'error_type': None,
                        'error_message': None,
                    },
                    'requests': {
                        'status': 'ok',
                        'result': [],
                        'error_type': None,
                        'error_message': None,
                    },
                    'httpx': {
                        'status': 'ok',
                        'result': {},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ]
        )
        self.assertEqual(payload['case_count'], 1)

    def test_compare_accept_payload_reports_case_count(self) -> None:
        payload = cli.build_compare_accept_payload(
            results=[
                {
                    'case_id': 'accept-case',
                    'description': 'accept case',
                    'accept': 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    'workspace': {
                        'status': 'ok',
                        'result': {
                            'selected': 'application/json',
                            'matched': 'application/json',
                        },
                        'error_type': None,
                        'error_message': None,
                    },
                    'werkzeug': {
                        'status': 'ok',
                        'result': {'selected': 'application/json'},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ]
        )
        self.assertEqual(payload['case_count'], 1)

    def test_compare_cache_control_payload_reports_case_count(self) -> None:
        payload = cli.build_compare_cache_control_payload(
            results=[
                {
                    'case_id': 'cache-control-case',
                    'description': 'cache-control case',
                    'sample': 'public',
                    'workspace': {
                        'status': 'ok',
                        'result': {'public': True},
                        'error_type': None,
                        'error_message': None,
                    },
                    'werkzeug': {
                        'status': 'ok',
                        'result': {'public': None},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ]
        )
        self.assertEqual(payload['case_count'], 1)

    def test_compare_implementation_payload_pivots_rows(self) -> None:
        payload = cli.build_compare_implementation_payload(
            results=[
                runner.BenchmarkResult(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                ),
                runner.BenchmarkResult(
                    implementation=runner.SupportedImplementation.WERKZEUG,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=50,
                    ns_per_call=50.0,
                    calls_per_second=1.0,
                ),
            ],
            header_ids=(data.SupportedHeader.ACCEPT,),
            workload_ids=('realistic',),
            implementation_ids=(
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ),
        )
        self.assertEqual(payload['headers'], [data.SupportedHeader.ACCEPT])
        self.assertEqual(payload['workloads'], ['realistic'])
        self.assertEqual(
            payload['implementations'],
            [
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
        )
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(
            payload['results'][0]['ns_per_call'],
            {
                runner.SupportedImplementation.WORKSPACE: 100.0,
                runner.SupportedImplementation.WERKZEUG: 50.0,
            },
        )
        self.assertEqual(
            payload['results'][0]['vs_workspace'],
            {runner.SupportedImplementation.WERKZEUG: 0.5},
        )

    def test_compare_implementation_payload_skips_missing_workload_rows(
        self,
    ) -> None:
        payload = cli.build_compare_implementation_payload(
            results=[
                runner.BenchmarkResult(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                ),
                runner.BenchmarkResult(
                    implementation=runner.SupportedImplementation.WERKZEUG,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=50,
                    ns_per_call=50.0,
                    calls_per_second=1.0,
                ),
            ],
            header_ids=(data.SupportedHeader.ACCEPT,),
            workload_ids=('browser', 'realistic'),
            implementation_ids=(
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ),
        )
        self.assertEqual(payload['headers'], [data.SupportedHeader.ACCEPT])
        self.assertEqual(payload['workloads'], ['realistic'])
        self.assertEqual(len(payload['results']), 1)

    def test_compare_implementation_diff_payload_reports_deltas(self) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            results=[
                cli.CompareImplementationRowJson(
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    ns_per_call={
                        runner.SupportedImplementation.WORKSPACE: 100.0,
                        runner.SupportedImplementation.WERKZEUG: 50.0,
                    },
                    vs_workspace={
                        runner.SupportedImplementation.WERKZEUG: 0.5
                    },
                )
            ],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            results=[
                cli.CompareImplementationRowJson(
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    ns_per_call={
                        runner.SupportedImplementation.WORKSPACE: 80.0,
                        runner.SupportedImplementation.WERKZEUG: 60.0,
                    },
                    vs_workspace={
                        runner.SupportedImplementation.WERKZEUG: 0.75
                    },
                )
            ],
        )
        payload = cli.build_compare_implementation_diff_payload(
            baseline=baseline,
            candidate=candidate,
            baseline_label='old.json',
            candidate_label='new.json',
        )
        self.assertEqual(payload['baseline_label'], 'old.json')
        self.assertEqual(payload['candidate_label'], 'new.json')
        self.assertEqual(
            payload['implementations'],
            [
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
        )
        self.assertEqual(
            payload['results'][0]['implementations'][
                runner.SupportedImplementation.WORKSPACE
            ],
            {
                'old_ns_per_call': 100.0,
                'new_ns_per_call': 80.0,
                'delta_ns_per_call': -20.0,
                'ratio': 0.8,
                'percent_change': -20.0,
            },
        )
        self.assertEqual(
            payload['results'][0]['implementations'][
                runner.SupportedImplementation.WERKZEUG
            ],
            {
                'old_ns_per_call': 50.0,
                'new_ns_per_call': 60.0,
                'delta_ns_per_call': 10.0,
                'ratio': 1.2,
                'percent_change': 20.0,
            },
        )

    def test_compare_implementation_diff_payload_rejects_shape_mismatch(
        self,
    ) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.LINK],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        with self.assertRaisesRegex(ValueError, 'same headers'):
            cli.build_compare_implementation_diff_payload(
                baseline=baseline,
                candidate=candidate,
                baseline_label='old.json',
                candidate_label='new.json',
            )

    def test_compare_implementation_diff_payload_rejects_workload_mismatch(
        self,
    ) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['complex'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        with self.assertRaisesRegex(ValueError, 'same workloads'):
            cli.build_compare_implementation_diff_payload(
                baseline=baseline,
                candidate=candidate,
                baseline_label='old.json',
                candidate_label='new.json',
            )

    def test_diff_payload_rejects_implementation_mismatch(
        self,
    ) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            results=[],
        )
        with self.assertRaisesRegex(ValueError, 'same implementations'):
            cli.build_compare_implementation_diff_payload(
                baseline=baseline,
                candidate=candidate,
                baseline_label='old.json',
                candidate_label='new.json',
            )

    def test_compare_implementation_diff_payload_rejects_row_mismatch(
        self,
    ) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[
                cli.CompareImplementationRowJson(
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    ns_per_call={
                        runner.SupportedImplementation.WORKSPACE: 100.0
                    },
                    vs_workspace={},
                )
            ],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[],
        )
        with self.assertRaisesRegex(ValueError, 'same header/workload rows'):
            cli.build_compare_implementation_diff_payload(
                baseline=baseline,
                candidate=candidate,
                baseline_label='old.json',
                candidate_label='new.json',
            )

    def test_run_payload_is_normalized_for_diff(self) -> None:
        payload = cli.RunPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            results=[
                runner.BenchmarkResultJson(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                ),
                runner.BenchmarkResultJson(
                    implementation=runner.SupportedImplementation.WERKZEUG,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=80,
                    ns_per_call=80.0,
                    calls_per_second=1.0,
                ),
            ],
        )
        normalized = cli._normalize_run_payload_for_diff(payload=payload)
        self.assertEqual(
            normalized['results'],
            [
                {
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'ns_per_call': {
                        runner.SupportedImplementation.WORKSPACE: 100.0,
                        runner.SupportedImplementation.WERKZEUG: 80.0,
                    },
                    'vs_workspace': {
                        runner.SupportedImplementation.WERKZEUG: 0.8
                    },
                }
            ],
        )

    def test_run_payload_normalization_skips_absent_workload_rows(
        self,
    ) -> None:
        payload = cli.RunPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['browser', 'realistic'],
            implementations=[runner.SupportedImplementation.WORKSPACE],
            results=[
                runner.BenchmarkResultJson(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                )
            ],
        )
        normalized = cli._normalize_run_payload_for_diff(payload=payload)
        self.assertEqual(normalized['headers'], [data.SupportedHeader.ACCEPT])
        self.assertEqual(normalized['workloads'], ['realistic'])
        self.assertEqual(len(normalized['results']), 1)

    def test_run_payload_normalization_requires_all_rows(self) -> None:
        payload = cli.RunPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=[
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            results=[
                runner.BenchmarkResultJson(
                    implementation=runner.SupportedImplementation.WORKSPACE,
                    header=data.SupportedHeader.ACCEPT,
                    workload='realistic',
                    sample_count=1,
                    byte_count=10,
                    repeat=1,
                    iterations=1,
                    median_elapsed_ns=100,
                    ns_per_call=100.0,
                    calls_per_second=1.0,
                )
            ],
        )
        with self.assertRaisesRegex(
            ValueError,
            'run payload is missing one or more '
            'header/workload/implementation rows',
        ):
            cli._normalize_run_payload_for_diff(payload=payload)

    def test_vs_workspace_ratios_without_workspace_returns_empty_dict(
        self,
    ) -> None:
        self.assertEqual(
            cli._vs_workspace_ratios(
                {runner.SupportedImplementation.WERKZEUG: 80.0}
            ),
            {},
        )

    def test_comparison_ratio_cell_marks_workspace_slower(self) -> None:
        try:
            from rich import text  # noqa: PLC0415 -- delayed import
        except ImportError:
            raise unittest.SkipTest('rich is not installed') from None
        else:
            cell = cli._comparison_ratio_cell(0.86)
            self.assertIsInstance(cell, text.Text)
            self.assertEqual(cell.plain, 'v 0.86x')
            self.assertEqual(str(cell.style), 'red')

    def test_comparison_ratio_cell_marks_workspace_faster(self) -> None:
        cell = cli._comparison_ratio_cell(1.25)
        self.assertEqual(cell.plain, '^ 1.25x')
        self.assertEqual(str(cell.style), 'green')

    def test_comparison_ratio_cell_marks_equal_ratio(self) -> None:
        cell = cli._comparison_ratio_cell(1.0)
        self.assertEqual(cell.plain, '= 1.00x')
        self.assertEqual(str(cell.style), 'yellow')

    def test_implementation_delta_cell_marks_lower_ns_per_call_as_better(
        self,
    ) -> None:
        cell = cli._implementation_delta_cell(
            {
                'old_ns_per_call': 100.0,
                'new_ns_per_call': 80.0,
                'delta_ns_per_call': -20.0,
                'ratio': 0.8,
                'percent_change': -20.0,
            }
        )
        self.assertEqual(cell.plain, 'v 0.80x (-20.0%)')
        self.assertEqual(str(cell.style), 'green')

    def test_implementation_delta_cell_marks_higher_ns_per_call_as_worse(
        self,
    ) -> None:
        cell = cli._implementation_delta_cell(
            {
                'old_ns_per_call': 100.0,
                'new_ns_per_call': 120.0,
                'delta_ns_per_call': 20.0,
                'ratio': 1.2,
                'percent_change': 20.0,
            }
        )
        self.assertEqual(cell.plain, '^ 1.20x (+20.0%)')
        self.assertEqual(str(cell.style), 'red')

    def test_implementation_delta_cell_marks_equal_ns_per_call_as_equal(
        self,
    ) -> None:
        cell = cli._implementation_delta_cell(
            {
                'old_ns_per_call': 100.0,
                'new_ns_per_call': 100.0,
                'delta_ns_per_call': 0.0,
                'ratio': 1.0,
                'percent_change': 0.0,
            }
        )
        self.assertEqual(cell.plain, '= 1.00x (+0.0%)')
        self.assertEqual(str(cell.style), 'yellow')

    def test_load_diffable_benchmark_payload_accepts_empty_results(
        self,
    ) -> None:
        with (
            self.subTest('compare implementation shape'),
            tempfile.TemporaryDirectory() as temp_dir,
        ):
            path = pathlib.Path(temp_dir) / 'empty.json'
            path.write_text(
                json.dumps(
                    {
                        'headers': [data.SupportedHeader.ACCEPT],
                        'workloads': ['realistic'],
                        'implementations': [
                            runner.SupportedImplementation.WORKSPACE
                        ],
                        'results': [],
                    }
                )
            )
            payload = cli._load_diffable_benchmark_payload(path)
        self.assertEqual(payload['results'], [])

    def test_load_diffable_benchmark_payload_rejects_invalid_json(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text('{')
            with self.assertRaisesRegex(ValueError, 'is not valid JSON'):
                cli._load_diffable_benchmark_payload(path)

    def test_load_diffable_benchmark_payload_rejects_non_mapping(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text('[]')
            with self.assertRaisesRegex(
                TypeError,
                'is not a run or compare implementation JSON payload',
            ):
                cli._load_diffable_benchmark_payload(path)

    def test_load_diffable_benchmark_payload_rejects_mixed_row_shapes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text(
                json.dumps(
                    {
                        'headers': ['accept'],
                        'workloads': ['realistic'],
                        'implementations': ['workspace'],
                        'results': [
                            {
                                'header': 'accept',
                                'workload': 'realistic',
                                'ns_per_call': {'workspace': 100.0},
                                'vs_workspace': {},
                            },
                            {
                                'implementation': 'workspace',
                                'header': 'accept',
                                'workload': 'realistic',
                                'sample_count': 1,
                                'byte_count': 10,
                                'repeat': 1,
                                'iterations': 1,
                                'median_elapsed_ns': 100,
                                'ns_per_call': 100.0,
                                'calls_per_second': 1.0,
                            },
                        ],
                    }
                )
            )
            with self.assertRaisesRegex(
                ValueError,
                'is not a run or compare implementation JSON payload',
            ):
                cli._load_diffable_benchmark_payload(path)

    def test_load_diffable_benchmark_payload_requires_list_fields(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text(
                json.dumps(
                    {
                        'headers': ['accept'],
                        'workloads': ['realistic'],
                        'implementations': {'workspace': True},
                        'results': [],
                    }
                )
            )
            with self.assertRaisesRegex(
                TypeError,
                'is not a run or compare implementation JSON payload',
            ):
                cli._load_diffable_benchmark_payload(path)

    def test_load_diffable_benchmark_payload_requires_mapping_rows(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text(
                json.dumps(
                    {
                        'headers': ['accept'],
                        'workloads': ['realistic'],
                        'implementations': ['workspace'],
                        'results': ['not-a-mapping'],
                    }
                )
            )
            with self.assertRaisesRegex(
                TypeError,
                'is not a run or compare implementation JSON payload',
            ):
                cli._load_diffable_benchmark_payload(path)

    def test_comparison_summary_reports_error_and_list_counts(self) -> None:
        self.assertEqual(
            cli._comparison_summary(
                {
                    'status': 'error',
                    'result': None,
                    'error_type': 'ValueError',
                    'error_message': 'bad input',
                }
            ),
            'error:ValueError',
        )
        self.assertEqual(
            cli._comparison_summary(
                {
                    'status': 'ok',
                    'result': ['a', 'b'],
                    'error_type': None,
                    'error_message': None,
                }
            ),
            'ok:2 value(s)',
        )
        self.assertEqual(
            cli._comparison_summary(
                {
                    'status': 'ok',
                    'result': {'a': 1},
                    'error_type': None,
                    'error_message': None,
                }
            ),
            'ok',
        )

    def test_accept_summaries_report_errors_and_matches(self) -> None:
        self.assertEqual(
            cli._accept_workspace_summary(
                {
                    'status': 'error',
                    'result': None,
                    'error_type': 'ValueError',
                    'error_message': 'bad input',
                }
            ),
            'error:ValueError',
        )
        self.assertEqual(
            cli._accept_workspace_summary(
                {
                    'status': 'ok',
                    'result': {
                        'selected': 'application/json',
                        'matched': 'application/*',
                    },
                    'error_type': None,
                    'error_message': None,
                }
            ),
            'application/json <= application/*',
        )
        self.assertEqual(
            cli._accept_werkzeug_summary(
                {
                    'status': 'error',
                    'result': None,
                    'error_type': 'ValueError',
                    'error_message': 'bad input',
                }
            ),
            'error:ValueError',
        )
        self.assertEqual(
            cli._accept_werkzeug_summary(
                {
                    'status': 'ok',
                    'result': {'selected': None},
                    'error_type': None,
                    'error_message': None,
                }
            ),
            'none',
        )

    def test_cache_control_summary_reports_errors_and_json(self) -> None:
        self.assertEqual(
            cli._cache_control_summary(
                {
                    'status': 'error',
                    'result': None,
                    'error_type': 'ValueError',
                    'error_message': 'bad input',
                }
            ),
            'error:ValueError',
        )
        self.assertEqual(
            cli._cache_control_summary(
                {
                    'status': 'ok',
                    'result': {'max-age': 60, 'public': True},
                    'error_type': None,
                    'error_message': None,
                }
            ),
            '{"max-age": 60, "public": true}',
        )


class BenchmarkCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        try:
            from typer import testing  # noqa: PLC0415 -- delayed import
        except ImportError:
            raise unittest.SkipTest('typer is not installed') from None
        else:
            self.runner = testing.CliRunner()

    def test_generate_autocomplete_filters_matches(self) -> None:
        autocomplete = cli._generate_autocomplete(data.SupportedHeader)
        self.assertEqual(
            list(autocomplete('ac')),
            [
                data.SupportedHeader.ACCEPT,
                data.SupportedHeader.ACCEPT_CHARSET,
                data.SupportedHeader.ACCEPT_ENCODING,
                data.SupportedHeader.ACCEPT_LANGUAGE,
            ],
        )
        compare_autocomplete = cli._generate_autocomplete(
            (
                data.SupportedHeader.ACCEPT,
                data.SupportedHeader.CACHE_CONTROL,
                'implementation',
                data.SupportedHeader.LINK,
            )
        )
        self.assertEqual(
            list(compare_autocomplete('ca')),
            [data.SupportedHeader.CACHE_CONTROL],
        )

    def test_run_command_emits_json_output(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.ACCEPT,
                '--workload',
                'realistic',
                '--iterations',
                '1',
                '--repeat',
                '1',
                '--format',
                'json',
            ],
        )
        self.assertEqual(result.exit_code, 0, result.exception)
        self.assertIn('"implementation": "workspace"', result.stdout)
        self.assertIn('"header": "accept"', result.stdout)
        self.assertIn('"implementations": [', result.stdout)

    def test_list_command_emits_rich_output(self) -> None:
        result = self.runner.invoke(cli.app, ['list', '--format', 'rich'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse benchmark fixtures', result.stdout)
        self.assertIn(data.SupportedHeader.ACCEPT, result.stdout)

    def test_list_command_emits_json_output(self) -> None:
        result = self.runner.invoke(cli.app, ['list', '--format', 'json'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"headers"', result.stdout)
        self.assertIn('"sample_counts"', result.stdout)

    def test_run_command_emits_rich_output(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.ACCEPT,
                '--workload',
                'realistic',
                '--iterations',
                '1',
                '--repeat',
                '1',
                '--format',
                'rich',
                '--quiet',
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse benchmark run', result.stdout)
        self.assertIn(data.SupportedHeader.ACCEPT, result.stdout)
        self.assertIn('realist', result.stdout)

    def test_run_command_emits_rich_summary_output(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.ACCEPT,
                '--workload',
                'realistic',
                '--iterations',
                '1',
                '--repeat',
                '1',
                '--format',
                'rich',
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            'headers=1 workloads=1 implementations=1 results=1',
            result.stdout,
        )

    def test_run_command_rejects_requests_for_non_link_headers(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.ACCEPT,
                '--implementation',
                runner.SupportedImplementation.REQUESTS,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)
        self.assertIn(
            'The requests implementation only supports the following '
            "headers: 'link'",
            str(result.exception),
        )

    def test_run_command_rejects_httpx_for_non_link_headers(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.ACCEPT,
                '--implementation',
                runner.SupportedImplementation.HTTPX,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)
        self.assertIn(
            'The httpx implementation only supports the following '
            "headers: 'link'",
            str(result.exception),
        )

    def test_run_command_rejects_werkzeug_for_unsupported_headers(
        self,
    ) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                data.SupportedHeader.FORWARDED,
                '--implementation',
                runner.SupportedImplementation.WERKZEUG,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIsNotNone(result.exception)
        self.assertIn(
            'The werkzeug implementation only supports the following '
            "headers: 'accept', 'accept-charset', 'accept-encoding', "
            "'accept-language', 'cache-control'",
            str(result.exception),
        )

    def test_compare_link_command_emits_json_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_link_cases',
            return_value=[
                {
                    'case_id': 'edge',
                    'description': 'edge case',
                    'sample': '<>',
                    'strict': True,
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'ok',
                        'result': [],
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.REQUESTS: {
                        'status': 'ok',
                        'result': [],
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.HTTPX: {
                        'status': 'ok',
                        'result': {},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', data.SupportedHeader.LINK, '--format', 'json'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"case_count": 1', result.stdout)
        self.assertIn('"case_id": "edge"', result.stdout)

    def test_compare_link_command_emits_rich_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_link_cases',
            return_value=[
                {
                    'case_id': 'edge',
                    'description': 'edge case',
                    'sample': '<>',
                    'strict': True,
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
                    },
                    runner.SupportedImplementation.REQUESTS: {
                        'status': 'ok',
                        'result': [],
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.HTTPX: {
                        'status': 'ok',
                        'result': {},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', data.SupportedHeader.LINK, '--format', 'rich'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse link comparison', result.stdout)
        self.assertIn('error:ValueError', result.stdout)
        self.assertIn('ok:0 value(s)', result.stdout)

    def test_compare_accept_command_emits_json_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_accept_cases',
            return_value=[
                {
                    'case_id': 'accept-case',
                    'description': 'accept case',
                    data.SupportedHeader.ACCEPT: 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'ok',
                        'result': {
                            'selected': 'application/json',
                            'matched': 'application/json',
                        },
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'ok',
                        'result': {'selected': 'application/json'},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', data.SupportedHeader.ACCEPT, '--format', 'json'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"case_count": 1', result.stdout)
        self.assertIn('"case_id": "accept-case"', result.stdout)

    def test_compare_accept_command_emits_rich_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_accept_cases',
            return_value=[
                {
                    'case_id': 'accept-error',
                    'description': 'accept error',
                    data.SupportedHeader.ACCEPT: 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'error',
                        'result': None,
                        'error_type': 'LookupError',
                        'error_message': 'boom',
                    },
                },
                {
                    'case_id': 'accept-ok',
                    'description': 'accept ok',
                    data.SupportedHeader.ACCEPT: 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'ok',
                        'result': {
                            'selected': 'application/json',
                            'matched': 'application/*',
                        },
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'ok',
                        'result': {'selected': None},
                        'error_type': None,
                        'error_message': None,
                    },
                },
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', data.SupportedHeader.ACCEPT, '--format', 'rich'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse accept comparison', result.stdout)
        self.assertIn('application/json <= application/*', result.stdout)
        self.assertIn('error:LookupError', result.stdout)
        self.assertIn('none', result.stdout)

    def test_compare_cache_control_command_emits_json_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_cache_control_cases',
            return_value=[
                {
                    'case_id': 'cache-control-case',
                    'description': 'cache-control case',
                    'sample': 'public',
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'ok',
                        'result': {'public': True},
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'ok',
                        'result': {'public': None},
                        'error_type': None,
                        'error_message': None,
                    },
                }
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    'compare',
                    data.SupportedHeader.CACHE_CONTROL,
                    '--format',
                    'json',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"case_count": 1', result.stdout)
        self.assertIn('"case_id": "cache-control-case"', result.stdout)

    def test_compare_cache_control_command_emits_rich_output(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'compare_cache_control_cases',
            return_value=[
                {
                    'case_id': 'cache-control-error',
                    'description': 'cache-control error',
                    'sample': 'public',
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'ok',
                        'result': {'public': None},
                        'error_type': None,
                        'error_message': None,
                    },
                },
                {
                    'case_id': 'cache-control-ok',
                    'description': 'cache-control ok',
                    'sample': 'max-age=60, public',
                    runner.SupportedImplementation.WORKSPACE: {
                        'status': 'ok',
                        'result': {'max-age': 60, 'public': True},
                        'error_type': None,
                        'error_message': None,
                    },
                    runner.SupportedImplementation.WERKZEUG: {
                        'status': 'error',
                        'result': None,
                        'error_type': 'RuntimeError',
                        'error_message': 'boom',
                    },
                },
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    'compare',
                    data.SupportedHeader.CACHE_CONTROL,
                    '--format',
                    'rich',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse cache-control comparison', result.stdout)
        self.assertIn('error:ValueError', result.stdout)
        self.assertIn('error:RuntimeError', result.stdout)
        self.assertIn('"public": null', result.stdout)

    def test_compare_implementation_command_emits_json_output(self) -> None:
        fake_results = [
            runner.BenchmarkResult(
                implementation=runner.SupportedImplementation.WORKSPACE,
                header=data.SupportedHeader.ACCEPT,
                workload='realistic',
                sample_count=1,
                byte_count=10,
                repeat=1,
                iterations=1,
                median_elapsed_ns=100,
                ns_per_call=100.0,
                calls_per_second=1.0,
            ),
            runner.BenchmarkResult(
                implementation=runner.SupportedImplementation.WERKZEUG,
                header=data.SupportedHeader.ACCEPT,
                workload='realistic',
                sample_count=1,
                byte_count=10,
                repeat=1,
                iterations=1,
                median_elapsed_ns=80,
                ns_per_call=80.0,
                calls_per_second=1.0,
            ),
        ]
        with (
            unittest.mock.patch.object(
                runner,
                'common_supported_headers',
                return_value=(data.SupportedHeader.ACCEPT,),
            ),
            unittest.mock.patch.object(
                runner,
                'run_benchmarks',
                side_effect=[fake_results[:1], fake_results[1:]],
            ),
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    'compare',
                    'implementation',
                    runner.SupportedImplementation.WERKZEUG,
                    '--workload',
                    'realistic',
                    '--iterations',
                    '1',
                    '--repeat',
                    '1',
                    '--format',
                    'json',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"implementations": [', result.stdout)
        self.assertIn('"werkzeug": 80.0', result.stdout)
        self.assertIn('"vs_workspace": {', result.stdout)

    def test_compare_implementation_command_emits_rich_output(self) -> None:
        fake_results = [
            runner.BenchmarkResult(
                implementation=runner.SupportedImplementation.WORKSPACE,
                header=data.SupportedHeader.ACCEPT,
                workload='realistic',
                sample_count=1,
                byte_count=10,
                repeat=1,
                iterations=1,
                median_elapsed_ns=100,
                ns_per_call=100.0,
                calls_per_second=1.0,
            ),
            runner.BenchmarkResult(
                implementation=runner.SupportedImplementation.WERKZEUG,
                header=data.SupportedHeader.ACCEPT,
                workload='realistic',
                sample_count=1,
                byte_count=10,
                repeat=1,
                iterations=1,
                median_elapsed_ns=80,
                ns_per_call=80.0,
                calls_per_second=1.0,
            ),
        ]
        with (
            unittest.mock.patch.object(
                runner,
                'common_supported_headers',
                return_value=(data.SupportedHeader.ACCEPT,),
            ),
            unittest.mock.patch.object(
                runner,
                'run_benchmarks',
                side_effect=[fake_results[:1], fake_results[1:]],
            ),
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    'compare',
                    'implementation',
                    runner.SupportedImplementation.WERKZEUG,
                    '--workload',
                    'realistic',
                    '--iterations',
                    '1',
                    '--repeat',
                    '1',
                    '--format',
                    'rich',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse implementation comparison', result.stdout)
        self.assertIn('vs werkzeug', result.stdout)
        self.assertIn('v 0.80x', result.stdout)
        self.assertIn('80.0', result.stdout)

    def test_compare_implementation_rejects_empty_intersection(self) -> None:
        with unittest.mock.patch.object(
            runner,
            'common_supported_headers',
            return_value=(),
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    'compare',
                    'implementation',
                    runner.SupportedImplementation.WERKZEUG,
                    runner.SupportedImplementation.REQUESTS,
                ],
            )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            'do not share any benchmark headers',
            str(result.exception),
        )

    def test_diff_command_emits_json_output(self) -> None:
        baseline_payload = {
            'headers': [data.SupportedHeader.ACCEPT],
            'workloads': ['realistic'],
            'implementations': [
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            'results': [
                {
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'ns_per_call': {
                        runner.SupportedImplementation.WORKSPACE: 100.0,
                        runner.SupportedImplementation.WERKZEUG: 50.0,
                    },
                    'vs_workspace': {
                        runner.SupportedImplementation.WERKZEUG: 0.5
                    },
                }
            ],
        }
        candidate_payload = {
            'headers': [data.SupportedHeader.ACCEPT],
            'workloads': ['realistic'],
            'implementations': [
                runner.SupportedImplementation.WORKSPACE,
                runner.SupportedImplementation.WERKZEUG,
            ],
            'results': [
                {
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'ns_per_call': {
                        runner.SupportedImplementation.WORKSPACE: 80.0,
                        runner.SupportedImplementation.WERKZEUG: 60.0,
                    },
                    'vs_workspace': {
                        runner.SupportedImplementation.WERKZEUG: 0.75
                    },
                }
            ],
        }
        with self.runner.isolated_filesystem():
            baseline_path = pathlib.Path('baseline.json')
            candidate_path = pathlib.Path('candidate.json')
            baseline_path.write_text(json.dumps(baseline_payload))
            candidate_path.write_text(json.dumps(candidate_payload))
            result = self.runner.invoke(
                cli.app,
                [
                    'diff',
                    str(baseline_path),
                    str(candidate_path),
                    '--format',
                    'json',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"baseline_label": "baseline.json"', result.stdout)
        self.assertIn('"candidate_label": "candidate.json"', result.stdout)
        self.assertIn('"delta_ns_per_call": -20.0', result.stdout)
        self.assertIn('"ratio": 0.8', result.stdout)

    def test_diff_command_accepts_run_payloads(self) -> None:
        baseline_payload = {
            'headers': [data.SupportedHeader.ACCEPT],
            'workloads': ['realistic'],
            'implementations': [runner.SupportedImplementation.WORKSPACE],
            'results': [
                {
                    'implementation': runner.SupportedImplementation.WORKSPACE,
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'sample_count': 1,
                    'byte_count': 10,
                    'repeat': 1,
                    'iterations': 1,
                    'median_elapsed_ns': 100,
                    'ns_per_call': 100.0,
                    'calls_per_second': 1.0,
                }
            ],
        }
        candidate_payload = {
            'headers': [data.SupportedHeader.ACCEPT],
            'workloads': ['realistic'],
            'implementations': [runner.SupportedImplementation.WORKSPACE],
            'results': [
                {
                    'implementation': runner.SupportedImplementation.WORKSPACE,
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'sample_count': 1,
                    'byte_count': 10,
                    'repeat': 1,
                    'iterations': 1,
                    'median_elapsed_ns': 90,
                    'ns_per_call': 90.0,
                    'calls_per_second': 1.0,
                }
            ],
        }
        with self.runner.isolated_filesystem():
            baseline_path = pathlib.Path('baseline.json')
            candidate_path = pathlib.Path('candidate.json')
            baseline_path.write_text(json.dumps(baseline_payload))
            candidate_path.write_text(json.dumps(candidate_payload))
            result = self.runner.invoke(
                cli.app,
                [
                    'diff',
                    str(baseline_path),
                    str(candidate_path),
                    '--format',
                    'json',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"old_ns_per_call": 100.0', result.stdout)
        self.assertIn('"new_ns_per_call": 90.0', result.stdout)
        self.assertIn('"percent_change": -10.0', result.stdout)

    def test_diff_command_emits_rich_output(self) -> None:
        payload: cli.CompareImplementationPayload = {
            'headers': [data.SupportedHeader.ACCEPT],
            'workloads': ['realistic'],
            'implementations': [runner.SupportedImplementation.WORKSPACE],
            'results': [
                {
                    'header': data.SupportedHeader.ACCEPT,
                    'workload': 'realistic',
                    'ns_per_call': {
                        runner.SupportedImplementation.WORKSPACE: 100.0
                    },
                    'vs_workspace': {},
                }
            ],
        }
        with self.runner.isolated_filesystem():
            baseline_path = pathlib.Path('baseline.json')
            candidate_path = pathlib.Path('candidate.json')
            baseline_path.write_text(json.dumps(payload))
            candidate_path.write_text(
                json.dumps(
                    {
                        **payload,
                        'results': [
                            {
                                'header': data.SupportedHeader.ACCEPT,
                                'workload': 'realistic',
                                'ns_per_call': {
                                    runner.SupportedImplementation.WORKSPACE: 90.0  # noqa: E501
                                },
                                'vs_workspace': {},
                            }
                        ],
                    }
                )
            )
            result = self.runner.invoke(
                cli.app,
                [
                    'diff',
                    str(baseline_path),
                    str(candidate_path),
                    '--format',
                    'rich',
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse implementation diff', result.stdout)
        self.assertIn('baseline=baseline.json', result.stdout)
        self.assertIn('candidate=candidate.json', result.stdout)
        self.assertIn('baseline.json', result.stdout)
        self.assertIn('candidate.json', result.stdout)
        self.assertIn('ns/call', result.stdout)

    def test_diff_command_rejects_non_compare_implementation_payload(
        self,
    ) -> None:
        payload: cli.CompareAcceptPayload = {'case_count': 1, 'results': []}
        with self.runner.isolated_filesystem():
            baseline_path = pathlib.Path('baseline.json')
            candidate_path = pathlib.Path('candidate.json')
            baseline_path.write_text(json.dumps(payload))
            candidate_path.write_text(json.dumps(payload))
            result = self.runner.invoke(
                cli.app,
                ['diff', str(baseline_path), str(candidate_path)],
            )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            'not a run or compare implementation JSON payload',
            str(result.exception),
        )
