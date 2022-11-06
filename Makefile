pre-commit:
	pre-commit run --all-files

test: unittest

unittest:
	pytest --doctest-modules --last-failed --durations=3
