# chunkdup

Find (partial content) duplicate files with [chunksum](https://github.com/xyb/chunksum) outputs.

[![test](https://github.com/xyb/chunkdup/actions/workflows/test.yml/badge.svg)](https://github.com/xyb/chunkdup/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/xyb/chunkdup/branch/main/graph/badge.svg?token=TVFUKMLFMX)](https://codecov.io/gh/xyb/chunkdup)
[![Maintainability](https://api.codeclimate.com/v1/badges/0935f557916da1fdcddb/maintainability)](https://codeclimate.com/github/xyb/chunkdup/maintainability)
[![Latest version](https://img.shields.io/pypi/v/chunkdup.svg)](https://pypi.org/project/chunkdup/)
[![Support python versions](https://img.shields.io/pypi/pyversions/chunkdup)](https://pypi.org/project/chunkdup/)

```
Find (partial content) duplicate files.

Usage: chunkdup <chunksums_file1> <chunksums_file2>

Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2
  $ chunkdup chunksums.dir1 chunksums.dir2
