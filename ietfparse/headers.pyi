from typing import Collection, Dict, List, Optional, Sequence, Union

from ietfparse import datastructures


def parse_accept(header_value: str, strict: bool = False) -> List[datastructures.ContentType]:
    ...


def parse_accept_charset(header_value: str) -> List[str]:
    ...


def parse_accept_encoding(header_value: str) -> List[str]:
    ...


def parse_accept_language(header_value: str) -> List[str]:
    ...


def parse_cache_control(header_value: str) -> Dict[str, Union[bool, str]]:
    ...


def parse_content_type(
    content_type: str,
    normalize_parameter_values: bool = True,
) -> datastructures.ContentType:
    ...


def parse_forwarded(
    header_value: str,
    only_standard_parameters: Optional[bool] = False,
) -> List[Dict[str, str]]:
    ...


def parse_link(
    header_value: str,
    strict: Optional[bool] = True,
) -> Sequence[datastructures.LinkHeader]:
    ...


def parse_list(value: str) -> Sequence[str]:
    ...
