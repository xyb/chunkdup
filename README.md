# chunkdup

Find (partial content) duplicate files using [chunksum](https://github.com/xyb/chunksum) outputs.

[![test](https://github.com/xyb/chunkdup/actions/workflows/test.yml/badge.svg)](https://github.com/xyb/chunkdup/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/xyb/chunkdup/branch/main/graph/badge.svg?token=TVFUKMLFMX)](https://codecov.io/gh/xyb/chunkdup)
[![Maintainability](https://api.codeclimate.com/v1/badges/0935f557916da1fdcddb/maintainability)](https://codeclimate.com/github/xyb/chunkdup/maintainability)
[![Latest version](https://img.shields.io/pypi/v/chunkdup.svg)](https://pypi.org/project/chunkdup/)
[![Support python versions](https://img.shields.io/pypi/pyversions/chunkdup)](https://pypi.org/project/chunkdup/)

```
usage: chunkdup [-h] [chunksums1] [chunksums2]

Find (partial content) duplicate files.

positional arguments:
  chunksums1  path to chunksums
  chunksums2  path to chunksums

optional arguments:
  -h, --help  show this help message and exit

Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2
  $ chunkdup chunksums.dir1 chunksums.dir2
```

```
usage: chunkdiff [-h] [-b BAR] [-w BARWIDTH] [-n] [-s CHUNKSUMS]
                 [file1] [file2]

Show the difference of two files.

positional arguments:
  file1                 path to file
  file2                 path to file

optional arguments:
  -h, --help            show this help message and exit
  -b BAR, --bar BAR     the style of bar. default: oneline
  -w BARWIDTH, --barwidth BARWIDTH
                        the width of bar. default: 40
  -n, --nocolor         do not colorize output. default: False
  -s CHUNKSUMS, --chunksums CHUNKSUMS
                        path to chunksums file

Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2

  $ chunkdiff chunksums.dir1 chunksums.dir2 dir1/file1 dir2/file2

  $ chunkdiff chunksums chunksums ./file1 ./file2
```
