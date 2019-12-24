from typing import Any, Dict, Optional, Sequence, Tuple


class ContentType:
    content_type: str
    content_subtype: str
    content_suffix: Optional[str]
    parameters: Dict[str, str]

    def __init__(
            self,
            content_type: str,
            content_subtype: str,
            parameters: Optional[Dict[str, str]] = None,
            content_suffix: Optional[str] = None,
    ) -> None:
        ...


class LinkHeader:
    target: str
    parameters: Sequence[Tuple[str, str]]

    def __init__(
            self,
            target: str,
            parameters: Optional[Sequence[Tuple[str, str]]],
    ) -> None:
        ...
