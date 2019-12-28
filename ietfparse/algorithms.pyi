from typing import Dict, List, Optional, Sequence, Tuple, Union

from ietfparse import datastructures

IDNA_SCHEMES: List[str]
USERINFO_SAFE_CHARS: bytes
HOST_SAFE_CHARS: bytes
PATH_SAFE_CHARS: bytes
FRAGMENT_SAFE_CHARS: bytes


class RemoveUrlAuthResult:
    auth: Tuple[str, str]
    url: str
    username: str
    password: str

    def __len__(self) -> int:
        ...

    def __getitem__(self, item: int) -> Union[str, Tuple[str, str]]:
        ...


def select_content_type(
    requested: Sequence[datastructures.ContentType],
    available: Sequence[datastructures.ContentType],
) -> Tuple[datastructures.ContentType, datastructures.ContentType]:
    ...


def rewrite_url(
        input_url: str,
        *,
        fragment: Optional[str] = None,
        host: Optional[str] = None,
        password: Optional[str] = None,
        path: Optional[str] = None,
        port: Optional[int] = None,
        query: Optional[Union[Dict[str, str], Sequence[Tuple[str, str]],
                              str]] = None,
        scheme: Optional[str] = None,
        user: Optional[str] = None,
        enable_long_host: bool = False,
        encode_with_idna: bool = False,
) -> str:
    ...


def remove_url_auth(url: str) -> RemoveUrlAuthResult:
    ...
