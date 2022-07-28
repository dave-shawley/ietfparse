from __future__ import annotations

version = '2.0.0.dev0'
version_info: list[str | int] = [int(c) for c in version.split('.')[:3]]
version_info += version.split('.')[3:]
