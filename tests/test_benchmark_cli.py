import importlib
import json
import pathlib
import tempfile
import typing as t
import unittest.mock

from rich.text import Text
from typer.testing import CliRunner

from ietfparse.test import cli, data, runner


def _create_fake_io(*, is_tty: bool) -> unittest.mock.Mock:
    stream = unittest.mock.Mock(spec=t.IO)
    stream.isatty.return_value = is_tty
    return stream


class BenchmarkCliSelectionTests(unittest.TestCase):
    def test_normalize_values_uses_defaults(self) -> None:
        normalize_values = vars(cli)['_normalize_values']
        self.assertEqual(
            normalize_values(
                label='header',
                valid=data.SUPPORTED_HEADERS,
                values=None,
            ),
            data.SUPPORTED_HEADERS,
        )

    def test_normalize_values_lowercases_values(self) -> None:
        normalize_values = vars(cli)['_normalize_values']
        self.assertEqual(
            normalize_values(
                label='header',
                valid=data.SUPPORTED_HEADERS,
                values=['ACCEPT', 'Link'],
            ),
            ('accept', 'link'),
        )

    def test_normalize_values_rejects_invalid_values(self) -> None:
        normalize_values = vars(cli)['_normalize_values']
        with self.assertRaisesRegex(ValueError, 'Unsupported header value'):
            normalize_values(
                label='header',
                valid=data.SUPPORTED_HEADERS,
                values=['bogus'],
            )

    def test_single_header_selection(self) -> None:
        self.assertEqual(cli.resolve_headers(['accept']), ('accept',))

    def test_multiple_header_selection(self) -> None:
        self.assertEqual(
            cli.resolve_headers(['accept', 'link']),
            ('accept', 'link'),
        )

    def test_all_headers_selected_by_default(self) -> None:
        self.assertEqual(cli.resolve_headers(None), data.SUPPORTED_HEADERS)

    def test_single_workload_selection(self) -> None:
        self.assertEqual(cli.resolve_workloads(['realistic']), ('realistic',))

    def test_multiple_workload_selection(self) -> None:
        self.assertEqual(
            cli.resolve_workloads(['complex', 'large']),
            ('complex', 'large'),
        )

    def test_all_workloads_selected_by_default(self) -> None:
        self.assertEqual(cli.resolve_workloads(None), data.SUPPORTED_WORKLOADS)

    def test_implementation_selection_defaults_to_workspace(self) -> None:
        self.assertEqual(cli.resolve_implementations(None), ('workspace',))

    def test_multiple_implementation_selection(self) -> None:
        self.assertEqual(
            cli.resolve_implementations(
                ['WORKSPACE', 'werkzeug', 'requests', 'HTTPX']
            ),
            ('workspace', 'werkzeug', 'requests', 'httpx'),
        )

    def test_compare_implementation_selection_adds_workspace(self) -> None:
        self.assertEqual(
            cli.resolve_compare_implementations(['werkzeug', 'workspace']),
            ('workspace', 'werkzeug'),
        )

    def test_compare_implementation_selection_requires_non_workspace(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            'requires at least one non-workspace implementation',
        ):
            cli.resolve_compare_implementations(['workspace'])


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
            implementation_ids=('workspace',),
        )
        self.assertEqual(payload['headers'], ['accept'])
        self.assertEqual(payload['workloads'], ['realistic'])
        self.assertEqual(payload['implementations'], ['workspace'])
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
        self.assertEqual(result['header'], 'accept')
        self.assertEqual(result['workload'], 'realistic')
        self.assertEqual(result['implementation'], 'workspace')

    def test_list_payload_includes_sample_counts(self) -> None:
        payload = cli.build_list_payload(data.load_dataset())
        self.assertEqual(payload['headers'], sorted(data.SUPPORTED_HEADERS))
        self.assertEqual(
            payload['workloads'], sorted(data.SUPPORTED_WORKLOADS)
        )
        counts = payload['sample_counts']
        self.assertEqual(counts['accept']['realistic'], 3)
        self.assertEqual(counts['link']['complex'], 2)

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
                    implementation='workspace',
                    header='accept',
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
                    implementation='werkzeug',
                    header='accept',
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
            implementation_ids=('workspace', 'werkzeug'),
        )
        self.assertEqual(payload['headers'], ['accept'])
        self.assertEqual(payload['workloads'], ['realistic'])
        self.assertEqual(payload['implementations'], ['workspace', 'werkzeug'])
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(
            payload['results'][0]['ns_per_call'],
            {'workspace': 100.0, 'werkzeug': 50.0},
        )
        self.assertEqual(
            payload['results'][0]['vs_workspace'],
            {'werkzeug': 0.5},
        )

    def test_compare_implementation_diff_payload_reports_deltas(self) -> None:
        baseline = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=['workspace', 'werkzeug'],
            results=[
                cli.CompareImplementationRowJson(
                    header='accept',
                    workload='realistic',
                    ns_per_call={'workspace': 100.0, 'werkzeug': 50.0},
                    vs_workspace={'werkzeug': 0.5},
                )
            ],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=['workspace', 'werkzeug'],
            results=[
                cli.CompareImplementationRowJson(
                    header='accept',
                    workload='realistic',
                    ns_per_call={'workspace': 80.0, 'werkzeug': 60.0},
                    vs_workspace={'werkzeug': 0.75},
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
        self.assertEqual(payload['implementations'], ['workspace', 'werkzeug'])
        self.assertEqual(
            payload['results'][0]['implementations']['workspace'],
            {
                'old_ns_per_call': 100.0,
                'new_ns_per_call': 80.0,
                'delta_ns_per_call': -20.0,
                'ratio': 0.8,
                'percent_change': -20.0,
            },
        )
        self.assertEqual(
            payload['results'][0]['implementations']['werkzeug'],
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
            implementations=['workspace'],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.LINK],
            workloads=['realistic'],
            implementations=['workspace'],
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
            implementations=['workspace'],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['complex'],
            implementations=['workspace'],
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
            implementations=['workspace'],
            results=[],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=['workspace', 'werkzeug'],
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
            implementations=['workspace'],
            results=[
                cli.CompareImplementationRowJson(
                    header='accept',
                    workload='realistic',
                    ns_per_call={'workspace': 100.0},
                    vs_workspace={},
                )
            ],
        )
        candidate = cli.CompareImplementationPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=['workspace'],
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
            implementations=['workspace', 'werkzeug'],
            results=[
                runner.BenchmarkResultJson(
                    implementation='workspace',
                    header='accept',
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
                    implementation='werkzeug',
                    header='accept',
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
        normalized = vars(cli)['_normalize_run_payload_for_diff'](
            payload=payload
        )
        self.assertEqual(
            normalized['results'],
            [
                {
                    'header': 'accept',
                    'workload': 'realistic',
                    'ns_per_call': {'workspace': 100.0, 'werkzeug': 80.0},
                    'vs_workspace': {'werkzeug': 0.8},
                }
            ],
        )

    def test_run_payload_normalization_requires_all_rows(self) -> None:
        payload = cli.RunPayload(
            headers=[data.SupportedHeader.ACCEPT],
            workloads=['realistic'],
            implementations=['workspace', 'werkzeug'],
            results=[
                runner.BenchmarkResultJson(
                    implementation='workspace',
                    header='accept',
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
            vars(cli)['_normalize_run_payload_for_diff'](payload=payload)

    def test_vs_workspace_ratios_without_workspace_returns_empty_dict(
        self,
    ) -> None:
        self.assertEqual(
            vars(cli)['_vs_workspace_ratios']({'werkzeug': 80.0}),
            {},
        )

    def test_comparison_ratio_cell_marks_workspace_slower(self) -> None:
        cell = vars(cli)['_comparison_ratio_cell'](0.86)
        self.assertIsInstance(cell, Text)
        self.assertEqual(cell.plain, 'v 0.86x')
        self.assertEqual(str(cell.style), 'red')

    def test_comparison_ratio_cell_marks_workspace_faster(self) -> None:
        cell = vars(cli)['_comparison_ratio_cell'](1.25)
        self.assertEqual(cell.plain, '^ 1.25x')
        self.assertEqual(str(cell.style), 'green')

    def test_comparison_ratio_cell_marks_equal_ratio(self) -> None:
        cell = vars(cli)['_comparison_ratio_cell'](1.0)
        self.assertEqual(cell.plain, '= 1.00x')
        self.assertEqual(str(cell.style), 'yellow')

    def test_implementation_delta_cell_marks_lower_ns_per_call_as_better(
        self,
    ) -> None:
        cell = vars(cli)['_implementation_delta_cell'](
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
        cell = vars(cli)['_implementation_delta_cell'](
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
        cell = vars(cli)['_implementation_delta_cell'](
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
                        'headers': ['accept'],
                        'workloads': ['realistic'],
                        'implementations': ['workspace'],
                        'results': [],
                    }
                )
            )
            payload = vars(cli)['_load_diffable_benchmark_payload'](path)
        self.assertEqual(payload['results'], [])

    def test_load_diffable_benchmark_payload_rejects_invalid_json(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'invalid.json'
            path.write_text('{')
            with self.assertRaisesRegex(ValueError, 'is not valid JSON'):
                vars(cli)['_load_diffable_benchmark_payload'](path)

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
                vars(cli)['_load_diffable_benchmark_payload'](path)

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
                vars(cli)['_load_diffable_benchmark_payload'](path)

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
                vars(cli)['_load_diffable_benchmark_payload'](path)

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
                vars(cli)['_load_diffable_benchmark_payload'](path)

    def test_comparison_summary_reports_error_and_list_counts(self) -> None:
        comparison_summary = vars(cli)['_comparison_summary']
        self.assertEqual(
            comparison_summary(
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
            comparison_summary(
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
            comparison_summary(
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
        accept_workspace_summary = vars(cli)['_accept_workspace_summary']
        accept_werkzeug_summary = vars(cli)['_accept_werkzeug_summary']
        self.assertEqual(
            accept_workspace_summary(
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
            accept_workspace_summary(
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
            accept_werkzeug_summary(
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
            accept_werkzeug_summary(
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
        cache_control_summary = vars(cli)['_cache_control_summary']
        self.assertEqual(
            cache_control_summary(
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
            cache_control_summary(
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
        self.runner = CliRunner()

    def test_generate_autocomplete_filters_matches(self) -> None:
        generate_autocomplete = vars(cli)['_generate_autocomplete']
        autocomplete = generate_autocomplete(data.SUPPORTED_HEADERS)
        self.assertEqual(
            list(autocomplete('ac')),
            [
                'accept',
                'accept-charset',
                'accept-encoding',
                'accept-language',
            ],
        )
        compare_autocomplete = generate_autocomplete(
            ('accept', 'cache-control', 'implementation', 'link')
        )
        self.assertEqual(
            list(compare_autocomplete('ca')),
            ['cache-control'],
        )

    def test_run_command_emits_json_output(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                'accept',
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
        self.assertIn('"implementation": "workspace"', result.stdout)
        self.assertIn('"header": "accept"', result.stdout)
        self.assertIn('"implementations": [', result.stdout)

    def test_list_command_emits_rich_output(self) -> None:
        result = self.runner.invoke(cli.app, ['list', '--format', 'rich'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse benchmark fixtures', result.stdout)
        self.assertIn('accept', result.stdout)

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
                'accept',
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
        self.assertIn('accept', result.stdout)
        self.assertIn('realist', result.stdout)

    def test_run_command_emits_rich_summary_output(self) -> None:
        result = self.runner.invoke(
            cli.app,
            [
                'run',
                '--header',
                'accept',
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
                'accept',
                '--implementation',
                'requests',
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
                'accept',
                '--implementation',
                'httpx',
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
                'forwarded',
                '--implementation',
                'werkzeug',
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
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', 'link', '--format', 'json'],
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
                    'workspace': {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
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
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', 'link', '--format', 'rich'],
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
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', 'accept', '--format', 'json'],
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
                    'accept': 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    'workspace': {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
                    },
                    'werkzeug': {
                        'status': 'error',
                        'result': None,
                        'error_type': 'LookupError',
                        'error_message': 'boom',
                    },
                },
                {
                    'case_id': 'accept-ok',
                    'description': 'accept ok',
                    'accept': 'application/json',
                    'available': ['application/json'],
                    'default': None,
                    'workspace': {
                        'status': 'ok',
                        'result': {
                            'selected': 'application/json',
                            'matched': 'application/*',
                        },
                        'error_type': None,
                        'error_message': None,
                    },
                    'werkzeug': {
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
                ['compare', 'accept', '--format', 'rich'],
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
            ],
        ):
            result = self.runner.invoke(
                cli.app,
                ['compare', 'cache-control', '--format', 'json'],
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
                    'workspace': {
                        'status': 'error',
                        'result': None,
                        'error_type': 'ValueError',
                        'error_message': 'bad input',
                    },
                    'werkzeug': {
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
                    'workspace': {
                        'status': 'ok',
                        'result': {'max-age': 60, 'public': True},
                        'error_type': None,
                        'error_message': None,
                    },
                    'werkzeug': {
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
                ['compare', 'cache-control', '--format', 'rich'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ietfparse cache-control comparison', result.stdout)
        self.assertIn('error:ValueError', result.stdout)
        self.assertIn('error:RuntimeError', result.stdout)
        self.assertIn('"public": null', result.stdout)

    def test_compare_implementation_command_emits_json_output(self) -> None:
        fake_results = [
            runner.BenchmarkResult(
                implementation='workspace',
                header='accept',
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
                implementation='werkzeug',
                header='accept',
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
                return_value=('accept',),
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
                    'werkzeug',
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
                implementation='workspace',
                header='accept',
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
                implementation='werkzeug',
                header='accept',
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
                return_value=('accept',),
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
                    'werkzeug',
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
                ['compare', 'implementation', 'werkzeug', 'requests'],
            )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            'do not share any benchmark headers',
            str(result.exception),
        )

    def test_diff_command_emits_json_output(self) -> None:
        baseline_payload = {
            'headers': ['accept'],
            'workloads': ['realistic'],
            'implementations': ['workspace', 'werkzeug'],
            'results': [
                {
                    'header': 'accept',
                    'workload': 'realistic',
                    'ns_per_call': {'workspace': 100.0, 'werkzeug': 50.0},
                    'vs_workspace': {'werkzeug': 0.5},
                }
            ],
        }
        candidate_payload = {
            'headers': ['accept'],
            'workloads': ['realistic'],
            'implementations': ['workspace', 'werkzeug'],
            'results': [
                {
                    'header': 'accept',
                    'workload': 'realistic',
                    'ns_per_call': {'workspace': 80.0, 'werkzeug': 60.0},
                    'vs_workspace': {'werkzeug': 0.75},
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
            'headers': ['accept'],
            'workloads': ['realistic'],
            'implementations': ['workspace'],
            'results': [
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
                }
            ],
        }
        candidate_payload = {
            'headers': ['accept'],
            'workloads': ['realistic'],
            'implementations': ['workspace'],
            'results': [
                {
                    'implementation': 'workspace',
                    'header': 'accept',
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
            'implementations': ['workspace'],
            'results': [
                {
                    'header': 'accept',
                    'workload': 'realistic',
                    'ns_per_call': {'workspace': 100.0},
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
                                'header': 'accept',
                                'workload': 'realistic',
                                'ns_per_call': {'workspace': 90.0},
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
