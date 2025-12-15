# Build instructions for the BlazingMQ Python SDK

Running the entire test-suite with all supported interpreters on all
supported architectures is difficult to do, and should already be set
up with GitHub Actions. We advise testing with a single version of
Python on a single architecture locally, and using the GitHub Actions
CI to test on all other combinations in your pull request. See
`.github/workflows/build.yaml` for more details on how we build and
test on all supported interpreters and architectures.

Before following any of the instructions, make sure to `git clone` the project onto the host machine.

## Using `tox`

The recommended way to build, test, lint, and format is through `tox`.
It manages isolated environments and dependencies automatically.
Run `tox -l` to see all available environments.

Key environments:

| Command | Description |
|---|---|
| `tox run -e py313` | Run tests under Python 3.13 |
| `tox run -e lint` | Run all linters (black, flake8, isort, mypy, clang-format) |
| `tox run -e format` | Auto-format Python and C++ files |
| `tox run -e docs` | Build Sphinx documentation |
| `tox run -e dist` | Build source distribution |
| `tox run -e gen-news` | Generate changelog with towncrier |

## Local Development

The BlazingMQ Python SDK provides a `bin/build-manylinux.sh` script and a
`bin/build-macos-universal.sh` script for building the C++ dependencies.
These need to be run once before building the extension.

For fast in-tree iteration without tox, you can also use `make`:

```shell
make build         # Build extension in-place
make test-build    # Build with test/coverage instrumentation
```

## Running Tests

To run unit tests (no broker needed):

```shell
tox run -e py313
```

To run integration tests, start a broker at `tcp://localhost:30114` first:

```shell
mkdir -p bmq/logs
mkdir -p bmq/storage/archive
./build/blazingmq/src/applications/bmqbrkr/bmqbrkr.tsk ./tests/broker-config
```

Then run:

```shell
BMQ_BROKER_URI=tcp://localhost:30114 tox run -e py313
```

Note that on macOS, the
`tests/integration/test_deadlock_detection.py::test_deadlock_detection_warning`
test may display a dialog warning you of a crashed Python process,
depending on your system configuration. This crash is intentional and
is part of the test.

## Coverage

Install dependencies and run coverage:

```shell
python3.9 -m pip install -r requirements-dev.txt
make coverage
```

Examine the `tox.ini` file and the GitHub Actions configuration for more
details on available workflows.
