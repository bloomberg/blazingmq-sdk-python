# Build instructions for the BlazingMQ Python SDK

Running the entire test-suite with all supported interpreters on all
supported architectures is difficult to do, and should already be set
up with GitHub Actions. We advise testing with a single version of
Python on a single architecture locally, and using the GitHub Actions
CI to test on all other combinations in your pull request. See
`.github/workflows/build.yaml` for more details on how we build and
test on all supported interpreters and architectures.

The instructions below assume `PYEXEC=python3.9` and will focus on Linux only.
This should be sufficient in most cases.

Before following any of the instructions, make sure to `git clone` the project onto the host machine.

## Using `make` vs. `tox`

Once the build environment is properly initialized, the project can
be built in-tree (in the project's working directory tree) using
`make build`. This is useful to iterate quickly. However, it has the
disadvantages of having to install all of the required
build/test/lint dependencies, along with the potential to
accidentally test against the wrong artifact due to the in-tree build.

For a more comprehensive, self-contained setup, use `tox` to build the project
and run the entire test suite targeting a specific version of the interpreter.
Run `tox -l` to see all available `tox` environments.

## Local Development

The BlazingMQ Python SDK provides a `./build-manylinux.sh` script and a
`./build-macosx-universal.sh` script for setting up a development environment.

## Working with Make Targets

When in an interactive command line prompt, you can use the following `make`
targets to build and test the BlazingMQ Python SDK. Check the
appropriate GitHub Actions configuration to set up the appropriate environment
variables that may be needed prior to running these commands (such as setting
`PYEXEC`).  With a BlazingMQ broker running at `tcp://localhost:30114`, the
following targets build and test the Python SDK:

```shell
make test-install
BMQ_BROKER_URI=tcp://localhost:30114 make check
```

Note that on OSX, the
`tests/integration/test_deadlock_detection.py::test_deadlock_detection_warning`
test may display a dialog warning you of a crashed Python process,
depending on your system configuration.  This crash is intentional, and
is part of the test.

Additional `make` targets are provided, such as for test coverage.
Dependencies for these can be installed as follows:

```shell
python3.9 -m pip install -r requirements-dev.txt
```

And now you should be able to run `make coverage`.

Examine the `Makefile`, the GitHub Actions configuration, and the `tox.ini`
file to understand more about these targets and how to use them.
