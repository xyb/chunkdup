test: unittest

unittest:
	pytest --doctest-modules --last-failed --durations=3

format:
	pre-commit run --all-files
