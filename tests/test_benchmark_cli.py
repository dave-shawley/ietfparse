import importlib
import typing
import unittest.mock

from typer.testing import CliRunner

from ietfparse.test import cli, data, runner


def _create_fake_io(*, is_tty: bool) -> unittest.mock.Mock:
    stream = unittest.mock.Mock(spec=typing.IO)
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
            cli.resolve_implementations(['WORKSPACE', 'requests', 'HTTPX']),
            ('workspace', 'requests', 'httpx'),
        )


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
                header_ids=('accept',),
                workload_ids=('realistic',),
                iterations=1,
                repeat=1,
            ),
        )
        payload = cli.build_run_payload(
            results=results,
            header_ids=('accept',),
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
            'The requests implementation only supports the link header',
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
            'The httpx implementation only supports the link header',
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
                ['compare-link', '--format', 'json'],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('"case_count": 1', result.stdout)
        self.assertIn('"case_id": "edge"', result.stdout)
