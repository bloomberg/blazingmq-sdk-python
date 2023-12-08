MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

# In case we run in virtualenv or tox this will work with the correct
# interpreter. Otherwise this should be set explicitly.
PYTHON ?= python
COVERAGE_FILE ?= coverage.xml
JUNIT_FILE ?= junit.xml

SETUP=$(PYTHON) setup.py -v
PIP_INSTALL=$(PYTHON) -m pip install
PACKAGE := blazingmq
PACKAGEDIR := $(subst .,/,$(PACKAGE))
TESTSDIR := tests

# Doc generation variables
UPSTREAM_GIT_REMOTE ?= origin
DOCSBUILDDIR := docs/_build
HTMLDIR := $(DOCSBUILDDIR)/html

# Use this to inject arbitrary commands before the make targets (e.g. docker)
ENV :=

# Optional arguments for pytest
PYTEST_ARGS ?= -vvv --showlocals

.PHONY: all
all: build


.PHONY: install-sdist
install-sdist: dist
	$(ENV) $(PIP_INSTALL) $(wildcard dist/*.tar.gz)

.PHONY: coverage-install
coverage-install:
	$(ENV) CYTHON_TEST_MACROS=1 $(PIP_INSTALL) -r requirements-test-coverage.txt
	$(ENV) CYTHON_TEST_MACROS=1 $(PIP_INSTALL) -e .

.PHONY: test-install
test-install:
	$(ENV) CYTHON_TEST_MACROS=1 $(PIP_INSTALL) -r requirements-test.txt
	$(ENV) CYTHON_TEST_MACROS=1 $(PIP_INSTALL) -e .

.PHONY: build
build:
	$(ENV) $(SETUP) build_ext --inplace

.PHONY: test-build
test-build:
	$(ENV) $(SETUP) build_ext --inplace --test-build

.PHONY: check
check:
	$(ENV) $(PYTHON) -m pytest $(PYTEST_ARGS) $(TESTSDIR)

.PHONY: dist
dist:
	$(SETUP) sdist

.PHONY: doc-deps
doc-deps:
	$(PIP_INSTALL) -r requirements-lint-docs.txt

.PHONY: docs
docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html


.PHONY: format
format:
	$(PYTHON) -m black --verbose src tests examples setup.py
	$(PYTHON) -m isort --settings-path=$(CURDIR)/.isort.cfg src tests examples setup.py
	clang-format --Werror -i src/cpp/*

.PHONY: lint
lint:
	$(PYTHON) -m black --check --verbose src tests examples setup.py
	$(PYTHON) -m flake8 --config=$(CURDIR)/.flake8.cython src
	$(PYTHON) -m flake8 --config=$(CURDIR)/.flake8 src
	$(PYTHON) -m flake8 --config=$(CURDIR)/tests/.flake8 tests
	$(PYTHON) -m flake8 --config=$(CURDIR)/tests/.flake8 examples
	$(PYTHON) -m isort --check-only --settings-path=$(CURDIR)/.isort.cfg src tests examples setup.py
	MYPYPATH=src $(PYTHON) -m mypy --strict examples src
	clang-format --Werror --dry-run src/cpp/*

# https://www.npmjs.com/package/markdownlint-cli
# tl;dr: npm install -g markdownlint-cli
.PHONY: lint-markdown
lint-markdown:
	markdownlint '**/*.md'

.PHONY: coverage
coverage:
	$(PYTHON) -m pytest $(PYTEST_ARGS) \
		--cov --cov-report=term-missing \
		--cov-fail-under=100 \
		--cov-append \
		--cov-report=xml:$(COVERAGE_FILE) \
		--junitxml=$(JUNIT_FILE)

.PHONY: gen-news
gen-news:
	$(PYTHON) -m towncrier build

gh-pages:
	$(eval GIT_REMOTE := $(shell git remote get-url $(UPSTREAM_GIT_REMOTE)))
	$(eval COMMIT_HASH := $(shell git rev-parse HEAD))
	touch $(HTMLDIR)/.nojekyll
	@echo -n "Documentation ready, push to $(GIT_REMOTE)? [Y/n] " && read ans && [ $${ans:-Y} == Y ]
	git init $(HTMLDIR)
	GIT_DIR=$(HTMLDIR)/.git GIT_WORK_TREE=$(HTMLDIR) git add -A
	GIT_DIR=$(HTMLDIR)/.git git commit -m "Documentation for commit $(COMMIT_HASH)"
	GIT_DIR=$(HTMLDIR)/.git git push $(GIT_REMOTE) HEAD:gh-pages --force
	rm -rf $(HTMLDIR)/.git

.PHONY: clean
clean:
	$(RM) MANIFEST
	$(RM) -r dist
	$(RM) -r .pytest_cache
	$(RM) -r src/$(PACKAGE).egg-info
	$(RM) -r .coverage
	$(RM) junit.xml coverage.xml
	find src tests -type d -name '__pycache__' -exec rm -r {} +
	find src tests -type f -name '*.pyc' -exec rm -r {} +
	find src/blazingmq/ -type f \( -name '*.cpp' -o -name '*.c' -o -name '*.h' -o -name '*.so' \) -exec rm {} +
	@rm -rf build
