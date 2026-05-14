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

This project uses [uv] to manage the project and [just] to run tasks,
so you should install both to make your life easier. I recommend installing
them as binaries instead of using the python package wrappers. Choose
your favorite installation method from:

* https://just.systems/man/en/pre-built-binaries.html
* https://docs.astral.sh/uv/getting-started/installation/

Once you have just & uv installed, you are ready to start writing code.

## pre-commit hooks

Before you start modifying things, install the pre-commit hooks so you
don't have to remember to run the style checks manually... _nothing is
more annoying than pushing a PR only to have it fail for something being
incorrectly formatted._

```commandline
$ uv run --frozen pre-commit install --install-hooks --overwrite
```

## Running tests

This project uses [pytest] as my test runner of choice. However, I do not use
it as a testing framework so please continue to use the assertions exposed by
the [unittest.UnitTest] class instead of raw `assert` statements. Running the
test suite is as easy as `just test`. The nice thing about just and uv is that
you do not need to manually activate the environment or worry about out-of-date
dependencies.

```commandline
$ just test
=================================================================== test session starts ===================================================================
platform darwin -- Python 3.12.7, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/daveshawley/Source/python/ietfparse
configfile: pyproject.toml
plugins: cov-7.1.0
collected 132 items
run-last-failure: no previously failed tests, not deselecting items.

tests/test_algorithm.py ....................                                                                                                        [ 15%]
tests/test_datastructure.py ....................                                                                                                    [ 30%]
tests/test_headers_cache_control.py ....                                                                                                            [ 33%]
tests/test_headers_content_type.py ..............                                                                                                   [ 43%]
tests/test_headers_forwarded.py ......                                                                                                              [ 48%]
tests/test_headers_link.py .............................                                                                                            [ 70%]
tests/test_headers_list.py ....                                                                                                                     [ 73%]
tests/test_headers_parse_accept.py ..............................                                                                                   [ 96%]
tests/test_helpers.py .....                                                                                                                         [100%]

===================================================================== tests coverage ======================================================================
____________________________________________________ coverage: platform darwin, python 3.12.7-final-0 _____________________________________________________

Name                              Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------------------
src/ietfparse/__init__.py             3      0      0      0   100%
src/ietfparse/_helpers.py            39      0     14      0   100%
src/ietfparse/algorithms.py          57      0     32      0   100%
src/ietfparse/constants.py           20      0      0      0   100%
src/ietfparse/datastructures.py     107      0     30      0   100%
src/ietfparse/errors.py              11      0      0      0   100%
src/ietfparse/headers.py            165      0     74      0   100%
-----------------------------------------------------------------------------
TOTAL                               402      0    150      0   100%
=================================================================== 132 passed in 0.20s ===================================================================
```

The "lint" recipe will run the pre-commit hooks that invoke [ruff] for style
and format checks, followed by [pyrefly] and [ty] for static type checks. It
is a useful target when you are refactoring since it is a little faster than
running the entire test suite.

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

The easiest way to check coverage is to run `just test` which runs the
tests with coverage enabled and reports the coverage.  It will fail if
you have less than 100% coverage.

Once you have a few tests are written and some functionality is working,
you should probably commit your work.  If you are not comfortable with
rebasing in git or cleaning up a commit history, your best bet is to
create small commits -- *commit early, commit often*.  The smaller the
commit is, the easier it will be to squash and rearrange them.

### Don't forget about docs

When your change is written and tested, make sure to update and/or add
documentation as needed.  The documentation suite is written using
Markdown and the [zensical] utility.  If you don't think that documentation
matters, read Kenneth Reitz's [Documentation is King] presentation.  Pull
requests that are not simply bug fixes will almost always require some
documentation... _updates to the changelog at the very least_.

[zensical] makes it easy to write documentation by running a small
development web server, rebuilding documentation when files change, and
using a nifty web-socket to refresh the web browser as well.

```commandline
$ uv run --frozen zensical serve
...
INFO    -  [08:01:22] Serving on http://127.0.0.1:8000/
```

After the tests are written, code is complete, and documents are up to
date, it is time to push your code back to github.com and submit a pull
request against the upstream repository.

[just]: https://just.systems
[pyrefly]: https://pyrefly.org/
[ruff]: https://docs.astral.sh/ruff/
[ty]: https://docs.astral.sh/ty/
[unittest.TestCase]: https://docs.python.org/3/library/unittest.html#unittest.TestCase
[uv]: https://docs.astral.sh/uv/
[zensical]: https://zensical.org/docs/get-started/

[Documentation is King]: https://www.kennethreitz.org/documentation-is-king/
