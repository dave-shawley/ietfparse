"""Load packaged benchmark fixtures for the ``ietfparse`` test CLI."""

from __future__ import annotations

import dataclasses
import typing as t
from importlib import resources

from ietfparse import _compat


class SupportedHeader(_compat.StrEnum):
    """Supported header names."""

    ACCEPT = 'accept'
    ACCEPT_CHARSET = 'accept-charset'
    ACCEPT_ENCODING = 'accept-encoding'
    ACCEPT_LANGUAGE = 'accept-language'
    CACHE_CONTROL = 'cache-control'
    CONTENT_TYPE = 'content-type'
    FORWARDED = 'forwarded'
    LINK = 'link'


SupportedWorkload = t.Literal['browser', 'realistic', 'complex', 'large']
SUPPORTED_WORKLOADS: tuple[str] = t.get_args(SupportedWorkload)
MAX_LARGE_SAMPLE_BYTES = 8192


@dataclasses.dataclass(frozen=True)
class HeaderBenchmark:
    """Fixture set for one supported header parser."""

    header_id: str
    parser_name: str
    description: str
    workloads: dict[str, tuple[str, ...]]

    def samples_for(self, workload: str) -> tuple[str, ...]:
        """Return the packaged samples for `workload`."""
        return self.workloads.get(workload, ())

    def sample_count(self, workload: str) -> int:
        """Return the number of packaged samples for `workload`."""
        return len(self.samples_for(workload))

    def byte_count(self, workload: str) -> int:
        """Return the total input size for `workload` in bytes."""
        return sum(
            len(sample.encode()) for sample in self.samples_for(workload)
        )


@dataclasses.dataclass(frozen=True)
class BenchmarkDataset:
    """All packaged benchmark fixtures keyed by header id."""

    headers: dict[str, HeaderBenchmark]

    def header_ids(self) -> tuple[str, ...]:
        """Return the supported header ids in benchmark order."""
        return tuple(self.headers)

    def sample_counts(self) -> dict[str, dict[str, int]]:
        """Return sample counts for every header and workload."""
        return {
            header_id: {
                workload: benchmark.sample_count(workload)
                for workload in SUPPORTED_WORKLOADS
            }
            for header_id, benchmark in self.headers.items()
        }


def load_dataset() -> BenchmarkDataset:
    """Load and validate the packaged benchmark dataset."""
    raw = t.cast(
        'dict[str, object]', _compat.tomllib.loads(_read_dataset_text())
    )
    return _parse_dataset(raw)


def _read_dataset_text() -> str:
    return (
        resources.files('ietfparse.test')
        .joinpath('benchmarks.toml')
        .read_text(encoding='utf-8')
    )


def _parse_dataset(raw: dict[str, object]) -> BenchmarkDataset:
    headers_section = _headers_section(raw)
    _validate_header_ids(headers_section)
    return BenchmarkDataset(
        headers={
            header_id: _parse_header_benchmark(
                header_id=header_id,
                payload=headers_section[header_id],
            )
            for header_id in SupportedHeader
        }
    )


def _headers_section(raw: dict[str, object]) -> dict[str, object]:
    headers_section = raw.get('headers')
    if not isinstance(headers_section, dict):
        raise TypeError('benchmark dataset must contain a [headers] table')
    return t.cast('dict[str, object]', headers_section)


def _validate_header_ids(headers_section: dict[str, object]) -> None:
    unexpected = set(headers_section) - set(SupportedHeader)
    missing = set(SupportedHeader) - set(headers_section)
    if unexpected:
        raise ValueError(
            f'unexpected header ids in dataset: {sorted(unexpected)!r}'
        )
    if missing:
        raise ValueError(f'missing header ids in dataset: {sorted(missing)!r}')


def _parse_header_benchmark(
    *, header_id: str, payload: object
) -> HeaderBenchmark:
    if not isinstance(payload, dict):
        raise TypeError(f'{header_id!r} must be a table')
    payload_dict = t.cast('dict[str, object]', payload)

    parser_name = _required_string(
        payload_dict.get('parser'), header_id, 'parser'
    )
    description = _required_string(
        payload_dict.get('description'), header_id, 'description'
    )
    return HeaderBenchmark(
        header_id=header_id,
        parser_name=parser_name,
        description=description,
        workloads=_parse_workloads(
            header_id=header_id, payload_dict=payload_dict
        ),
    )


def _required_string(value: object, header_id: str, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f'{header_id!r} must define {field_name}')
    return value


def _parse_workloads(
    *, header_id: str, payload_dict: dict[str, object]
) -> dict[str, tuple[str, ...]]:
    workloads: dict[str, tuple[str, ...]] = {}
    for workload in SUPPORTED_WORKLOADS:
        samples = _parse_workload_samples(
            header_id=header_id,
            workload=workload,
            payload=payload_dict.get(workload),
        )
        if samples:
            workloads[workload] = samples
    return workloads


def _parse_workload_samples(
    *, header_id: str, workload: str, payload: object
) -> tuple[str, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, dict):
        raise TypeError(f'{header_id!r}.{workload!r} must be a table')
    payload_dict = t.cast('dict[str, object]', payload)

    samples = payload_dict.get('samples')
    if samples is None or samples == []:
        return ()
    if not isinstance(samples, list):
        raise TypeError(f'{header_id!r}.{workload!r} must define samples')
    if not all(isinstance(sample, str) and sample for sample in samples):
        raise ValueError(f'{header_id!r}.{workload!r} samples must be strings')
    sample_list = t.cast('list[str]', samples)
    if workload == 'large':
        _validate_large_samples(header_id=header_id, samples=sample_list)
    return tuple(sample_list)


def _validate_large_samples(*, header_id: str, samples: list[str]) -> None:
    oversized = [
        len(sample.encode())
        for sample in samples
        if len(sample.encode()) > MAX_LARGE_SAMPLE_BYTES
    ]
    if oversized:
        raise ValueError(
            f'{header_id!r}.large contains oversized samples: {oversized!r}'
        )
