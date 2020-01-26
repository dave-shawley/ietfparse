Contributing to ietfparse
=========================
Do you want to contribute extensions, fixes, improvements?

    **Awesome!** and *thank you very much*

This is a nice little open source project that is released under the
permissive BSD license so you don't have to push your changes back if
you do not want to.  But if you do, they will be more than welcome.

Set up a development environment
--------------------------------
The first thing that you need to do is set up a development environment
so that you can run the test suite.  The easiest way to do that is to
create a virtual environment for your endeavours::

   $ python -mvenv env

If you are developing against something earlier than Python 3.4, then I
highly recommend using `virtualenv`_ to create the environment.  Otherwise,
use the :mod:`venv` module.  The next step is to install the development
tools that you will need.  These are included in the setuptools *extra*
``.[dev]``::

   $ env/bin/pip install -qe '.[dev]'
   $ env/bin/pip freeze
   alabaster==0.7.12
   Babel==2.8.0
   certifi==2019.11.28
   chardet==3.0.4
   coverage==5.0.3
   docutils==0.16
   entrypoints==0.3
   filelock==3.0.12
   flake8==3.7.9
   idna==2.8
   -e git+git@github.com:dave-shawley/ietfparse.git@...#egg=ietfparse
   imagesize==1.2.0
   Jinja2==2.10.3
   MarkupSafe==1.1.1
   mccabe==0.6.1
   mypy==0.761
   mypy-extensions==0.4.3
   packaging==20.1
   ...

Running tests
-------------
The easiest way to run the test suite is with *python -m unittest*.
It will run the test suite with the currently installed python version
and report the result of the test run::

   $ env/bin/python -munittest
   ......................................................................
   ......................................................................
   .........................
   ----------------------------------------------------------------------
   Ran 165 tests in 0.016s

   OK

If you want to see the test coverage, then use the excellent `coverage`_
utility::

   $ env/bin/coverage -munittest
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

Time to address the elephant in the room ... I decided to stop using the
venerable *nosetests* since it is unmaintained and will likely stop working
in `a future version of python`_ likely quite soon.  I used to suggest using
*setup.py* as the developer's swiss army knife.  I have recently changed my
opinion on that as well.  *Just use the tools directly.*

The more interesting pivot is that I *did not choose to use pytest* or any
other replacement for nose.  The :mod:`unittest` module together with the
`coverage`_ utility is more than capable of handling the task at hand without
depending on yet another utility.

.. _a future version of python: https://mail.python.org/archives/list
   /python-dev@python.org/thread/EYLXCGGJOUMZSE5X35ILW3UNTJM3MCRE
   /#5PTA432JSFSNRU3QAKXM727KDK6ZI7UX

Before you can call the code complete, you really need to make sure that it
works across the supported python versions.  My CI pipeline will take care of
making sure that this is the case when the code is pushed to github but you
should do this before you push.  The easiest way to do this is
to run `tox`_::

   $ env/bin/tox -p auto
   GLOB sdist-make: /Users/daveshawley/Source/python/ietfparse/setup.py
   ✔ OK py38 in 8.701 seconds
   ✔ OK py37 in 8.746 seconds
   ✔ OK py36 in 9.008 seconds
   ✔ OK py27 in 9.02 seconds
   ✔ OK coverage in 9.546 seconds
   ✔ OK py35 in 9.69 seconds
   ✔ OK lint in 23.357 seconds
   _______________________________ summary _______________________________
     py27: commands succeeded
     py35: commands succeeded
     py36: commands succeeded
     py37: commands succeeded
     py38: commands succeeded
     lint: commands succeeded
     coverage: commands succeeded
     congratulations :)

This is what you want to see.  Tests passing across the board.  Time to
submit a PR.

Submitting a Pull Request
-------------------------
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

The easiest way to check coverage is to use ``tox -e coverage`` which runs
the tests with coverage enabled and reports the coverage.  It will fail if
you have less than 100% coverage.

Once you have a few tests are written and some functionality is working,
you should probably commit your work.  If you are not comfortable with
rebasing in git or cleaning up a commit history, your best bet is to
create small commits -- *commit early, commit often*.  The smaller the
commit is, the easier it will be to squash and rearrange them.

When your change is written and tested, make sure to update and/or add
documentation as needed.  The documentation suite is written using
ReStructuredText and the excellent `sphinx`_ utility.  If you don't think
that documentation matters, read Kenneth Reitz's `Documentation is King`_
presentation.  Pull requests that are not simply bug fixes will almost
always require some documentation.

After the tests are written, code is complete, and documents are up to
date, it is time to push your code back to github.com and submit a pull
request against the upstream repository.

.. _coverage: https://coverage.readthedocs.io/
.. _flake8: https://flake8.readthedocs.io/
.. _sphinx: https://www.sphinx-doc.org/
.. _tox: https://tox.readthedocs.io/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/

.. _Documentation is King: https://www.kennethreitz.org/documentation-is-king/
