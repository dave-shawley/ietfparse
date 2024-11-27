---
title: Contributing back
---
# Contributing to ietfparse

Do you want to contribute extensions, fixes, improvements?

> **Awesome!** and *thank you very much*

This is a nice little open source project that is released under the
permissive BSD license so you don't have to push your changes back if
you do not want to.  But if you do, they will be more than welcome.

## Set up a development environment

This project uses the [hatch] project manager, so you should install it
to make your life easier. I usually install it as a "user install".
Make sure that you have the target directory in your path.

```commandline
$ python3 -m pip install --user hatch
$ echo "Installed hatch into $(python3 -m site --user-base)/bin"
```

Once you have hatch installed, you are ready to starting writing code.

```commandline
$ hatch shell
(ietfparse) $
```
## pre-commit hooks

Before you start modifying things, install the pre-commit hooks so you
don't have to remember to run the style checks manually... _nothing is
more annoying than pushing a PR only to have it fail for something being
incorrectly formatted._

```commandline
(ietfparse) $ pre-commit install --install-hooks
```

## Running tests

This project uses [pytest] as my test runner of choice. However, I do not use
it as a testing framework so please continue to use the assertions exposed by
the [unittest.UnitTest] class instead of raw `assert` statements.
Running the test suite is as easy as `hatch run test`. The nice thing
about hatch is that you do not need to manually activate the environment or
worry about out of date dependencies.

```commandline
$ hatch run test
cmd [1] | pre-commit run --all-files
... lint & formatting checks omitted
cmd [2] | mypy -p ietfparse -p tests
Success: no issues found in 15 source files
cmd [3] | python -m coverage run -m pytest tests
========================== test session starts ==========================
platform darwin -- Python 3.12.7, pytest-7.1.2, pluggy-1.5.0
... pytest output omitted
=================== 120 passed, 120 warnings in 0.10s ===================
cmd [4] | python -m coverage report
Name                          Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------
ietfparse/__init__.py             4      0      0      0   100%
ietfparse/_helpers.py            30      0     14      0   100%
ietfparse/algorithms.py          42      0     22      0   100%
ietfparse/datastructures.py     100      0     26      0   100%
ietfparse/errors.py               8      0      0      0   100%
ietfparse/headers.py            162      0     74      0   100%
-------------------------------------------------------------------------
TOTAL                           346      0    136      0   100%
```

The "lint" script will run the pre-commit hooks that invoke [ruff] for style
and format checks, followed by [mypy] for static type checks. It is a useful
target when you are refactoring since it is a little faster.

## Submitting a Pull Request

The first thing to do is to fork the repository and set up a nice shiny
environment for it.  Once you can run the tests, it's time to write some.
I developed this library using a test-first methodology.  If you are
fixing a defect, then write a test that verifies the correct (desired)
behavior.  It should fail.  Now, fix the defect making the test pass in
the process.  New functionality follows a similar path.  Write a test that
verifies the correct behavior of the new functionality.  Then add enough
functionality to make the test pass.  Then, on to the next test.  This is
*test driven development* at its core.  This actually is pretty important
since **pull requests that are not tested will not be merged**.

The easiest way to check coverage is to run `hatch run test` which runs
the tests with coverage enabled and reports the coverage.  It will fail if
you have less than 100% coverage.

Once you have a few tests are written and some functionality is working,
you should probably commit your work.  If you are not comfortable with
rebasing in git or cleaning up a commit history, your best bet is to
create small commits -- *commit early, commit often*.  The smaller the
commit is, the easier it will be to squash and rearrange them.

### Don't forget about docs

When your change is written and tested, make sure to update and/or add
documentation as needed.  The documentation suite is written using
Markdown and the [mkdocs] utility.  If you don't think that documentation
matters, read Kenneth Reitz's [Documentation is King] presentation.  Pull
requests that are not simply bug fixes will almost always require some
documentation... _updates to the changelog at the very least_.

[mkdocs] makes it easy to write documentation by running a small
development web server, rebuilding documentation when fiels change, and
using a nifty web-socket to refresh the web browser as well.

```commandline
$ hatch run serve-docs
...
INFO    -  [08:01:22] Serving on http://127.0.0.1:8000/
```

After the tests are written, code is complete, and documents are up to
date, it is time to push your code back to github.com and submit a pull
request against the upstream repository.

[hatch]: https://hatch.pypa.io/
[mkdocs]: https://www.mkdocs.org/
[mypy]: https://mypy.readthedocs.io/en/stable/
[ruff]: https://docs.astral.sh/ruff/
[unittest.TestCase]: https://docs.python.org/3/library/unittest.html#unittest.TestCase

[Documentation is King]: https://www.kennethreitz.org/documentation-is-king/
