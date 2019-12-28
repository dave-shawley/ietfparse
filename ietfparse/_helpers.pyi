from typing import Dict, List, Sequence, Tuple, Union


class ParameterParser:
    strict: bool
    _rfc_values: Dict[str, Union[str, None]]
    _values: List[Tuple[str, str]]

    def __init__(self, strict: bool = True):
        ...

    def add_value(self, name: str, value: str) -> None:
        ...

    @property
    def values(self) -> Sequence[Tuple[str, str]]:
        ...
