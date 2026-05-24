"""Module entrypoint for ``python -m ietfparse.test``."""

if __name__ == '__main__':  # pragma: no cover
    from ietfparse.test import cli

    cli.app()
