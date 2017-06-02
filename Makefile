WATCH_EVENTS=modify,close_write,moved_to,create

.PHONY: watch docs

init:  ## setup environment
	pip install pipenv
	pipenv install --dev

help:
	@for f in $(MAKEFILE_LIST) ; do \
		echo "$$f:" ; \
		grep -E '^[a-zA-Z_-%]+:.*?## .*$$' $$f | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' ; \
	done ; \

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build:  ## remove build artifacts
	rm -rf build/ dist/ .eggs/
	find -name '*.egg-info' -delete
	find -name '*.egg' -delete

clean-pyc:  ## remove Python file artifacts
	find -name '*.pyc' -delete
	find -name '*.pyo' -delete
	find -name '*~' -delete
	find -name '__pycache__' -delete

clean-test:  ## remove test and coverage artifacts
	rm -rf .tox/ .coverage htmlcov/

lint:  ## check style with flake8
	pipenv run flake8

coverage: ## check code coverage quickly with the default Python
	pipenv run py.test \
		--cov-report html \
		--cov-report term \
		--cov=rest_witchcraft tests

test:  ## run tests
	pipenv run py.test tests

check:  ## run all tests
	tox

release: clean  ## package and upload a release
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean  ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

watch:  ## watch file changes to run a command, e.g. make watch test
	@if ! type "inotifywait" > /dev/null; then \
		echo "Please install inotify-tools" ; \
	fi; \
	echo "Watching $(pwd) to run: $(WATCH_ARGS)" ; \
	while true; do \
		make $(WATCH_ARGS) ; \
		inotifywait -e $(WATCH_EVENTS) -r --exclude '.*(git|~)' . ; \
	done \

# If the first argument is "watch"...
ifeq (watch,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "watch"
  WATCH_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(WATCH_ARGS):;@:)
endif
