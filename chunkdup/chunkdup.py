#!/usr/bin/env python
import argparse
import signal
import sys

from .differ import Differ
from .sums import Chunksums
from .utils import humanize


def find_dup(chunksums1, chunksums2):
    return Differ(chunksums1, chunksums2).dups


def print_plain_report(dups, output_file):
    """
    >>> import io
    >>> chunksum1 = '''
    ... bee1  /A/1  fck0sha2!aa:10,bb:10
    ... bee2  /A/2  fck0sha2!cc:10,dd:10,ee:10
    ... bee3  /A/3  fck0sha2!ff:10,f0:10
    ... bee4  /A/4  fck0sha2!f1:10
    ... '''
    >>> chunksum2 = '''
    ... bee5  /B/1  fck0sha2!a1:10,a2:10
    ... bee6  /B/2  fck0sha2!cc:10,dd:10,ff:10
    ... bee7  /B/3  fck0sha2!ff:10,a3:10
    ... bee8  /B/4  fck0sha2!f1:10
    ... '''
    >>> file1 = Chunksums.parse(io.StringIO(chunksum1))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum2))
    >>> dups = find_dup(file1, file2)
    >>> print_plain_report(dups, sys.stdout)
    100.00%  /A/4 (10B)  /B/4 (10B)
     66.67%  /A/2 (30B)  /B/2 (30B)
     50.00%  /A/3 (20B)  /B/3 (20B)
     40.00%  /A/3 (20B)  /B/2 (30B)

    >>> chunksum_repeat = '''
    ... bee1  a  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... bee2  b  fck0sha2!aa:1,bb:2
    ... bee3  c  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... '''
    >>> file1 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> dups = find_dup(file1, file2)
    >>> print_plain_report(dups, sys.stdout)
    100.00%  a (5B)  c (5B)
     75.00%  a (5B)  b (3B)
     75.00%  b (3B)  c (5B)
    """
    for ratio, size1, file1, size2, file2 in dups:
        print(
            "{:>6.2f}%  {} ({})  {} ({})".format(
                ratio * 100,
                file1,
                humanize(size1),
                file2,
                humanize(size2),
            ),
            file=output_file,
            flush=True,
        )


command_desc = "Find (partial content) duplicate files."
command_long_desc = """
Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2
  $ %(prog)s chunksums.dir1 chunksums.dir2
"""


def main():
    """
    >>> sys.argv = ['chunkdup']
    >>> try:
    ...     main()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... except:
    ...     pass
    usage: chunkdup ...
    Find ...
    ...

    >>> import tempfile
    >>> f1 = tempfile.NamedTemporaryFile()
    >>> _ = f1.write(b'bee1  /A/1  fck0sha2!aa:1000,bb:1000')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'bee2  /B/1  fck0sha2!cc:1000,bb:1000')
    >>> f2.flush()
    >>> sys.argv = ['chunkdup', f1.name, f2.name]
    >>> main()
     50.00%  /A/1 (1.95KB)  /B/1 (1.95KB)
    """

    # Don't turn these signal into exceptions, just die.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description=command_desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=command_long_desc,
    )

    parser.add_argument("chunksums1", nargs="?", help="path to chunksums")
    parser.add_argument("chunksums2", nargs="?", help="path to chunksums")
    args = parser.parse_args()

    if not args.chunksums1 or not args.chunksums2:
        parser.print_help()
        sys.exit()

    dups = find_dup(
        Chunksums.parse(open(args.chunksums1)),
        Chunksums.parse(open(args.chunksums2)),
    )
    print_plain_report(dups, sys.stdout)


if __name__ == "__main__":
    main()  # pragma: no cover
