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

   $ pyvenv env

If you are developing against something earlier than Python 3.4, then I
highly recommend using `virtualenv`_ to create the environment.  The
earlier versions of ``pyvenv`` were slightly broken.  The next step is
to install the development tools that you will need.

*dev-requirements.txt* is a pip-formatted requirements file that will
install everything that you need::

   $ env/bin/pip install -qr dev-requirements.txt
   $ env/bin/pip freeze
   Fluent-Test==3.0.0
   Jinja2==2.7.3
   MarkupSafe==0.23
   Pygments==1.6
   Sphinx==1.2.3
   coverage==3.7.1
   docutils==0.12
   flake8==2.2.3
   mccabe==0.2.1
   mock==1.0.1
   nose==1.3.4
   pep8==1.5.7
   pyflakes==0.8.1
   sphinx-rtd-theme==0.1.6

As usual, *setup.py* is the swiss-army knife in the development tool
chest.  The following commands are the ones that you will be using most
often:

**./setup.py nosetests**
   Run the test suite using `nose`_ and generate a coverage report.

**./setup.py build_sphinx**
   Generate the documentation suite into *build/sphinx/html*

**./setup.py flake8**
   Run the `flake8`_ over the code and report any style violations.

**./setup.py clean**
   Remove generated files.  By default, this will remove any top-level
   egg-related files and the *build* directory.

Running tests
-------------
The easiest way to run the test suite is with *setup.py nosetests*.
It will run the test suite with the currently installed python version
and report the result of the test run as well as the coverage::

   $ env/bin/python setup.py nosetests

   running nosetests
   running egg_info
   writing dependency_links to ietfparse.egg-info/dependency_links.txt
   writing top-level names to ietfparse.egg-info/top_level.txt
   writing ietfparse.egg-info/PKG-INFO
   reading manifest file 'ietfparse.egg-info/SOURCES.txt'
   reading manifest template 'MANIFEST.in'
   warning: no previously-included files matching '__pycache__'...
   warning: no previously-included files matching '*.swp' found ...
   writing manifest file 'ietfparse.egg-info/SOURCES.txt'
   test_that_differing_parameters_is_acceptable_as_weak_match ...
   ...

   Name                       Stmts   Miss Branch BrMiss  Cover   Missing
   ----------------------------------------------------------------------
   ietfparse                      0      0      0      0   100%   
   ietfparse.algorithms          36      1     24      1    97%   98
   ietfparse.datastructures      26      0     21      0   100%   
   ietfparse.errors               4      0      0      0   100%   
   ietfparse.headers             29      1     14      1    95%   82
   ----------------------------------------------------------------------
   TOTAL                         95      2     59      2    97%   
   ----------------------------------------------------------------------
   Ran 44 tests in 0.054s

   OK

Before you can call the code complete, you really need to make sure that
it works across the supported python versions.  Travis-CI will take care
of making sure that this is the case when the code is pushed to github
but you should do this before you push.  The easiest way to do this is
to install ``detox`` and run it::

   $ env/bin/python install -q detox
   $ env/bin/detox
   py27 recreate: /.../ietfparse/build/tox/py27
   GLOB sdist-make: /.../ietfparse/setup.py
   py33 recreate: /.../ietfparse/build/tox/py33
   py34 recreate: /.../ietfparse/build/tox/py34
   py27 installdeps: -rtest-requirements.txt, mock
   py33 installdeps: -rtest-requirements.txt
   py34 installdeps: -rtest-requirements.txt
   py27 inst: /.../ietfparse/build/tox/dist/ietfparse-0.0.0.zip
   py27 runtests: PYTHONHASHSEED='2156646470'
   py27 runtests: commands[0] | /../ietfparse/build/tox/py27/bin/nosetests
   py33 inst: /../ietfparse/.build/tox/dist/ietfparse-0.0.0.zip
   py34 inst: /../ietfparse/.build/tox/dist/ietfparse-0.0.0.zip
   py33 runtests: PYTHONHASHSEED='2156646470'
   py33 runtests: commands[0] | /.../ietfparse/build/tox/py33/bin/nosetests
   py34 runtests: PYTHONHASHSEED='2156646470'
   py34 runtests: commands[0] | /.../ietfparse/build/tox/py34/bin/nosetests
   _________________________________ summary _________________________________
     py27: commands succeeded
     py33: commands succeeded
     py34: commands succeeded
     congratulations :)

This is what you want to see.  Tests passing across the board.  Time to
submit a PR.

Submitting a Pull Request
-------------------------
The first thing to do is to fork the repository and set up a nice shiny
environment in it.  Once you can run the tests, it's time to write some.
I developed this library using a test-first methodology.  If you are
fixing a defect, then write a test that verifies the correct behavior.
It should fail.  Now, fix the defect making the test pass in the process.
New functionality follows a similar path.  Write a test that verifies the
correct behavior of the new functionality.  Then add enough functionality
to make the test pass.  Then, on to the next test.  This is *test driven
development* at its core.  This actually is pretty important since **pull
requests that are not tested will not be merged**.  This is why `nose`_
is configured to report coverage.  The coverage doesn't have to be 100%
but it should be pretty close.  Anything that isn't covered is usually
scrutinized.

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

.. _flake8: http://flake8.readthedocs.org/
.. _nose: http://nose.readthedocs.org/
.. _sphinx: http://sphinx-doc.org/
.. _virtualenv: http://virtualenv.pypa.io/

.. _Documentation is King: http://www.kennethreitz.org/documentation-is-king/
