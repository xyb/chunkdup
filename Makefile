test: unittest

unittest:
	pytest --doctest-modules --last-failed --durations=3

format:
	autoflake -i chunkdup/*.py
	isort chunkdup/*.py
