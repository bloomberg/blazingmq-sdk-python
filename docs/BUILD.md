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

## Local Development with Docker

The BlazingMQ Python SDK provides a `Dockerfile` for setting up a
development environment, and a `docker/docker-compose.yaml` for
composing development and broker Docker containers for end-to-end
testing and development.

The following commands will bring up one container that runs the
BlazingMQ broker, and a second container that invokes `tox` to run all of the tests
across all supported interpreter versions. Once the tests are complete,
both containers will exit.

```shell
docker-compose -f docker/docker-compose.yaml up
```

You can also choose to run a subset of tests. For example, to
run lint with tests for Python versions 3.7 and 3.9:

```shell
docker-compose -f docker/docker-compose.yaml run bmq-test python3.9 -m tox -e lint,py39,py37
```

Check `... python3.9 -m tox -l` for all available tox environments.

### Working Interactively in Docker

The following command will start the `bmq-broker` and `bmq-test`
containers, and will replace the default `tox` command for the test container
with `bash`, giving you a command prompt, from where you can perform your development
using `make` targets and other commands.

```shell
docker-compose -f docker/docker-compose.yaml run bmq-test bash
```

## Working with Make Targets

When in an interactive Docker prompt, you can use the following `make`
targets to build and test the BlazingMQ Python SDK. Check the
sections below to set up the appropriate environment variables that may be
needed prior to running these commands (such as setting `PYEXEC`).

```shell
make test-install
make check
```

Additional `make` targets are provided, such as for test coverage.
Dependencies for these can be installed as follows:

```shell
python3.9 -m pip install -r requirements-dev.txt
```

And now you should be able to run `make coverage`.

Examine the `Makefile`, the GitHub Actions configuration, and the `tox.ini`
file to understand more about these targets and how to use them.
