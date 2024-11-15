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

The first thing that you need to do is set up a development environment
so that you can run the test suite.  The easiest way to do that is to
create a virtual environment for your endeavours:

```
$ python -mvenv env
```

!!! note
    If you want to continue using `pip`, then you will need a fairly modern
    version of pip (at least pip version 21.3) for [PEP-660] support.  You
    can also use `hatch` by running `hatch env create` instead.  I recommend
    using `pip` since it is a more comfortable workflow for most developers.

[hatch]: https://hatch.pypa.io/

The next step is to install the development tools that you will need.  These
are included in the *extra* `.[dev]`:

```
$ env/bin/pip install -qe '.[dev]'
```

THe last step is to install the git pre-commit hooks so you don't have to
remember to run the style checks... _nothing is more annoying than pushing
a PR only to have it fail for formatting differences._

```
$ env/bin/pre-commit install --install-hooks
```

## Running tests

The easiest way to run the test suite is with *python -m unittest*.
It will run the test suite with the currently installed python version
and report the result of the test run:

```
$ env/bin/python -munittest
......................................................................
......................................................................
.........................
   ----------------------------------------------------------------------
Ran 165 tests in 0.016s

OK
```

If you want to see the test coverage, then use the excellent [coverage] utility:

```
$ env/bin/coverage run -munittest
......................................................................
......................................................................
.........................
   ----------------------------------------------------------------------
Ran 165 tests in 0.023s

OK
$ env/bin/coverage report
Name                                  Stmts   Miss Branch BrPart  Cover   Missing
   ---------------------------------------------------------------------------------
ietfparse/__init__.py                     2      0      2      0   100%
ietfparse/_helpers.py                    30      0     16      0   100%
ietfparse/algorithms.py                 147      0     80      0   100%
ietfparse/compat/__init__.py              0      0      0      0   100%
ietfparse/compat/parse.py                 4      0      0      0   100%
ietfparse/datastructures.py              47      0     32      0   100%
ietfparse/errors.py                      11      0      0      0   100%
ietfparse/headers.py                    155      0     76      0   100%
tests/__init__.py                         0      0      0      0   100%
tests/test_algorithm.py                  76      0      8      0   100%
tests/test_datastructure.py              43      0      0      0   100%
tests/test_headers_cache_control.py      19      0      2      0   100%
tests/test_headers_content_type.py       39      0      0      0   100%
tests/test_headers_deprecation.py        22      0      0      0   100%
tests/test_headers_forwarded.py          28      0      0      0   100%
tests/test_headers_link.py               80      0      0      0   100%
tests/test_headers_list.py               11      0      0      0   100%
tests/test_headers_parse_accept.py       68      0      2      0   100%
tests/test_url.py                       125      0      0      0   100%
   ---------------------------------------------------------------------------------
TOTAL                                   907      0    218      0   100%
```

Time to address the elephant in the room ... I decided to stop using the
venerable *nosetests* since it is unmaintained. I used to suggest using
*setup.py* as the developer's swiss army knife. I have recently changed my
opinion on that as well. *Just use the tools directly.*

The more interesting pivot is that I *did not choose to use pytest* or any
other replacement for nose.  The [unittest][] module together with the
[coverage] utility is more than capable of handling the task at hand without
depending on yet another utility. In full transparency, I do use pytest in
my development environment.

Before you can call the code complete, you should make sure that it works
across the supported python versions. My CI pipeline will take care of
making sure that this is the case when you create a pull request.  If you
want to do this before submitting, then you will have to install [hatch].
The easiest way to do this is to install it using `pip install --user`.
Hatch will store virtual environments somewhere in your home directory
(see [Hatch Configuration](https://hatch.pypa.io/latest/config/hatch/)
and [User Installs] for additional information).

```
$ python3.9 -m pip install --user hatch
$ python3.9 -m hatch run all:test
```

If the tests all pass, then it is time to submit a PR.

## Submitting a Pull Request

The first thing to do is to fork the repository and set up a nice shiny
environment in it.  Once you can run the tests, it's time to write some.
I developed this library using a test-first methodology.  If you are
fixing a defect, then write a test that verifies the correct (desired)
behavior.  It should fail.  Now, fix the defect making the test pass in
the process.  New functionality follows a similar path.  Write a test that
verifies the correct behavior of the new functionality.  Then add enough
functionality to make the test pass.  Then, on to the next test.  This is
*test driven development* at its core.  This actually is pretty important
since **pull requests that are not tested will not be merged**.

The easiest way to check coverage is to use `tox -e coverage` which runs
the tests with coverage enabled and reports the coverage.  It will fail if
you have less than 100% coverage.

Once you have a few tests are written and some functionality is working,
you should probably commit your work.  If you are not comfortable with
rebasing in git or cleaning up a commit history, your best bet is to
create small commits -- *commit early, commit often*.  The smaller the
commit is, the easier it will be to squash and rearrange them.

When your change is written and tested, make sure to update and/or add
documentation as needed.  The documentation suite is written using
ReStructuredText and the excellent [sphinx] utility.  If you don't think
that documentation matters, read Kenneth Reitz's [Documentation is King]
presentation.  Pull requests that are not simply bug fixes will almost
always require some documentation.

After the tests are written, code is complete, and documents are up to
date, it is time to push your code back to github.com and submit a pull
request against the upstream repository.

## Using hatch

I replaced setuptools & [tox] with [hatch] to manage project metadata,
dependencies, and provide developer-friendly scripts.  Best of all is that it
does not require that you use it unless you want to!  I did have to change
this guide since I replaced tox with hatch environments.  So I lied a little
bit... if you want to test across multiple python versions, then you will need
to install hatch (or let the CI pipeline take care of it).  I installed the
hatch utility using the "--user" option since that makes it available
regardless of which environment is activated::

```
$ python3.9 -m pip install --user hatch
```

If you want to run the `hatch` utility as a CLI utility instead of a module,
then you need to add the "user installation" directory to your path. You can
find the user installation root using::

```
$ python3.9 -m site --user-base
/Users/daveshawley/.local
```

Simply add the *bin* directory to your path and you can run `hatch`
instead of `python3.9 -m hatch`.  If you are unfamiliar with "user
installs", then read [User Installs] for the detailed version.

Once you have hatch installed and available, running any of the `hatch`
commands will result in the creation of a new virtual environment or updating
the existing one.  For example::

```
$ hatch run test
```

will ensure that the virtual environment exists and run the "test" script
which is `python -m unittest discover -f tests`.  You can see the available
scripts with `hatch env show`.  The `all` environment can be used to run
the commands across all supported Python versions (e.g., `hatch run all:test`).

[coverage]: https://coverage.readthedocs.io/
[flake8]: https://flake8.readthedocs.io/
[hatch]: https://hatch.pypa.io/
[sphinx]: https://www.sphinx-doc.org/
[tox]: https://tox.readthedocs.io/
[virtualenv]: https://virtualenv.pypa.io/en/stable/

[Documentation is King]: https://www.kennethreitz.org/documentation-is-king/
[User Installs]: https://pip.pypa.io/en/stable/user_guide/#user-installs
