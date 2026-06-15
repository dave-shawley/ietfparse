import typing as t
import unittest.mock

from ietfparse import headers
from ietfparse.test import data, runner


class BenchmarkDatasetTests(unittest.TestCase):
    def test_loading_packaged_dataset(self) -> None:
        dataset = data.load_dataset()
        self.assertEqual(dataset.header_ids(), data.SUPPORTED_HEADERS)

    def test_every_supported_header_has_every_workload(self) -> None:
        dataset = data.load_dataset()
        for header_id in data.SUPPORTED_HEADERS:
            benchmark = dataset.headers[header_id]
            self.assertEqual(
                tuple(benchmark.workloads),
                data.SUPPORTED_WORKLOADS,
            )

    def test_large_samples_are_bounded(self) -> None:
        dataset = data.load_dataset()
        for benchmark in dataset.headers.values():
            for sample in benchmark.samples_for('large'):
                self.assertLessEqual(len(sample.encode()), 8192)

    def test_fixture_validation_succeeds_against_public_parsers(self) -> None:
        dataset = data.load_dataset()
        runner.validate_dataset(dataset)

    def test_parser_names_match_public_header_surface(self) -> None:
        dataset = data.load_dataset()
        for benchmark in dataset.headers.values():
            self.assertTrue(hasattr(headers, benchmark.parser_name))


class BenchmarkDatasetValidationTests(unittest.TestCase):
    def test_header_benchmark_reports_byte_count(self) -> None:
        dataset = data.load_dataset()
        benchmark = dataset.headers['accept']
        expected = sum(
            len(sample.encode())
            for sample in benchmark.samples_for('realistic')
        )
        self.assertEqual(benchmark.byte_count('realistic'), expected)

    def test_headers_section_requires_mapping(self) -> None:
        headers_section = vars(data)['_headers_section']
        with self.assertRaises(TypeError):
            headers_section({})

    def test_validate_header_ids_rejects_unexpected_headers(self) -> None:
        validate_header_ids = vars(data)['_validate_header_ids']
        with self.assertRaisesRegex(ValueError, 'unexpected header ids'):
            validate_header_ids({'accept': object(), 'bogus': object()})

    def test_validate_header_ids_rejects_missing_headers(self) -> None:
        validate_header_ids = vars(data)['_validate_header_ids']
        with self.assertRaisesRegex(ValueError, 'missing header ids'):
            validate_header_ids({'accept': object()})

    def test_parse_header_benchmark_requires_table_payload(self) -> None:
        parse_header_benchmark = vars(data)['_parse_header_benchmark']
        with self.assertRaises(TypeError):
            parse_header_benchmark(header_id='accept', payload='bad')

    def test_required_string_rejects_missing_values(self) -> None:
        required_string = vars(data)['_required_string']
        with self.assertRaisesRegex(ValueError, 'must define parser'):
            required_string(None, 'accept', 'parser')

    def test_parse_workload_samples_requires_table_payload(self) -> None:
        parse_workload_samples = vars(data)['_parse_workload_samples']
        with self.assertRaises(TypeError):
            parse_workload_samples(
                header_id='accept',
                workload='realistic',
                payload='bad',
            )

    def test_parse_workload_samples_requires_non_empty_samples(self) -> None:
        parse_workload_samples = vars(data)['_parse_workload_samples']
        with self.assertRaisesRegex(ValueError, 'must define samples'):
            parse_workload_samples(
                header_id='accept',
                workload='realistic',
                payload={'samples': []},
            )

    def test_parse_workload_samples_requires_string_samples(self) -> None:
        parse_workload_samples = vars(data)['_parse_workload_samples']
        with self.assertRaisesRegex(ValueError, 'samples must be strings'):
            parse_workload_samples(
                header_id='accept',
                workload='realistic',
                payload={'samples': ['ok', 3]},
            )

    def test_validate_large_samples_rejects_oversized_sample(self) -> None:
        validate_large_samples = vars(data)['_validate_large_samples']
        with self.assertRaisesRegex(ValueError, 'oversized samples'):
            validate_large_samples(
                header_id='accept',
                samples=['x' * (data.MAX_LARGE_SAMPLE_BYTES + 1)],
            )


class BenchmarkRunnerTests(unittest.TestCase):
    def test_supported_implementations_are_stable(self) -> None:
        self.assertEqual(
            runner.SUPPORTED_IMPLEMENTATIONS,
            ('workspace', 'werkzeug', 'requests', 'httpx'),
        )

    def test_headers_supported_by_returns_workspace_headers(self) -> None:
        self.assertSetEqual(
            runner.IMPLEMENTATION_HEADERS['workspace'],
            {data.SupportedHeader(v) for v in data.SUPPORTED_HEADERS},
        )

    def test_common_supported_headers_uses_intersection(self) -> None:
        self.assertEqual(
            runner.common_supported_headers(('workspace', 'werkzeug')),
            (
                'accept',
                'accept-charset',
                'accept-encoding',
                'accept-language',
                'cache-control',
            ),
        )
        self.assertEqual(
            runner.common_supported_headers(
                ('workspace', 'werkzeug', 'requests')
            ),
            (),
        )

    def test_validate_samples_raises_for_invalid_fixture(self) -> None:
        validate_samples = vars(runner)['_validate_samples']
        with self.assertRaisesRegex(ValueError, 'invalid benchmark fixture'):
            validate_samples(
                header_id='accept',
                workload='realistic',
                samples=('bad',),
                parser=lambda _: (_ for _ in ()).throw(ValueError('bad')),
            )

    def test_run_once_returns_elapsed_time_and_checksum(self) -> None:
        run_once = vars(runner)['_run_once']
        elapsed_ns, checksum = run_once(
            samples=('a', 'bb'),
            parser=lambda value: value.upper(),
            iterations=2,
        )
        self.assertGreaterEqual(elapsed_ns, 0)
        self.assertGreater(checksum, 0)

    def test_werkzeug_parser_uses_accept_class_for_header_family(self) -> None:
        parse_accept_header = unittest.mock.Mock(return_value=object())
        parse_cache_control_header = unittest.mock.Mock(return_value=object())
        mime_accept = object()
        charset_accept = object()
        accept = object()
        language_accept = object()

        def fake_import_module(name: str) -> object:
            if name == 'werkzeug.http':
                return unittest.mock.Mock(
                    parse_accept_header=parse_accept_header,
                    parse_cache_control_header=parse_cache_control_header,
                )
            if name == 'werkzeug.datastructures':
                return unittest.mock.Mock(
                    MIMEAccept=mime_accept,
                    CharsetAccept=charset_accept,
                    Accept=accept,
                    LanguageAccept=language_accept,
                )
            raise AssertionError(name)

        with unittest.mock.patch.object(
            runner.importlib,
            'import_module',
            side_effect=fake_import_module,
        ):
            mime_parser = runner.implementation_named('werkzeug').parser_for(
                'parse_accept'
            )
            charset_parser = runner.implementation_named(
                'werkzeug'
            ).parser_for('parse_accept_charset')
            encoding_parser = runner.implementation_named(
                'werkzeug'
            ).parser_for('parse_accept_encoding')
            language_parser = runner.implementation_named(
                'werkzeug'
            ).parser_for('parse_accept_language')
            cache_control_parser = runner.implementation_named(
                'werkzeug'
            ).parser_for('parse_cache_control')

        mime_parser('text/html')
        charset_parser('utf-8')
        encoding_parser('gzip')
        language_parser('en')
        cache_control_parser('public')

        self.assertEqual(
            parse_accept_header.call_args_list,
            [
                unittest.mock.call('text/html', cls=mime_accept),
                unittest.mock.call('utf-8', cls=charset_accept),
                unittest.mock.call('gzip', cls=accept),
                unittest.mock.call('en', cls=language_accept),
            ],
        )
        parse_cache_control_header.assert_called_once_with('public')

    def test_werkzeug_implementation_rejects_non_accept_headers(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            'only supports the following headers',
        ):
            runner.validate_implementation_support(
                implementation_name='werkzeug',
                header_ids=(data.SupportedHeader.FORWARDED,),
            )

    def test_werkzeug_implementation_rejects_unsupported_parser_name(
        self,
    ) -> None:
        with (
            unittest.mock.patch.object(
                runner.importlib,
                'import_module',
                return_value=unittest.mock.Mock(),
            ),
            self.assertRaisesRegex(
                ValueError,
                'only supports the Accept-family headers and Cache-Control',
            ),
        ):
            runner.implementation_named('werkzeug').parser_for('parse_link')

    def test_requests_implementation_rejects_non_link_headers(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "only supports the following headers: 'link'",
        ):
            runner.validate_implementation_support(
                implementation_name='requests',
                header_ids=(data.SupportedHeader.ACCEPT,),
            )

    def test_requests_implementation_rejects_unsupported_parser_name(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            'only supports parse_link',
        ):
            runner.implementation_named('requests').parser_for('parse_accept')

    def test_httpx_implementation_rejects_non_link_headers(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "only supports the following headers: 'link'",
        ):
            runner.validate_implementation_support(
                implementation_name='httpx',
                header_ids=(data.SupportedHeader.ACCEPT,),
            )

    def test_httpx_implementation_rejects_unsupported_parser_name(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            'only supports parse_link',
        ):
            runner.implementation_named('httpx').parser_for('parse_accept')

    def test_implementation_named_rejects_unknown_name(self) -> None:
        with self.assertRaises(AssertionError):
            runner.implementation_named(
                t.cast('runner.SupportedImplementation', 'bogus')
            )

    def test_compare_link_cases_returns_curated_results(self) -> None:
        results = runner.compare_link_cases()
        self.assertGreater(len(results), 0)
        self.assertIn('case_id', results[0])
        self.assertIn('workspace', results[0])
        self.assertIn('requests', results[0])
        self.assertIn('httpx', results[0])

    def test_compare_accept_cases_returns_curated_results(self) -> None:
        class FakeWerkzeugAccept:
            def best_match(
                self,
                matches: list[str],
                default: str | None = None,
            ) -> str | None:
                return matches[0] if matches else default

        implementation = runner.BenchmarkImplementation(
            name='werkzeug',
            parser_resolver=lambda _: lambda _: FakeWerkzeugAccept(),
        )

        with unittest.mock.patch.object(
            runner,
            'implementation_named',
            return_value=implementation,
        ):
            results = runner.compare_accept_cases()

        self.assertGreater(len(results), 0)
        self.assertIn('case_id', results[0])
        self.assertIn('accept', results[0])
        self.assertIn('available', results[0])
        self.assertIn('workspace', results[0])
        self.assertIn('werkzeug', results[0])

    def test_compare_cache_control_cases_returns_curated_results(self) -> None:
        implementation = runner.BenchmarkImplementation(
            name='werkzeug',
            parser_resolver=lambda _: lambda _: {'public': None},
        )

        with unittest.mock.patch.object(
            runner,
            'implementation_named',
            return_value=implementation,
        ):
            results = runner.compare_cache_control_cases()

        self.assertGreater(len(results), 0)
        self.assertIn('case_id', results[0])
        self.assertIn('sample', results[0])
        self.assertIn('workspace', results[0])
        self.assertIn('werkzeug', results[0])
