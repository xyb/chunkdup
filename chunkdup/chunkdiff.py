import argparse
import sys

from .differ import Differ
from .sums import Chunksums


def print_diff(
    chunksums1,
    chunksums2,
    path1,
    path2,
    output=None,
    bar_width=40,
    color=True,
    oneline=True,
):
    """
    >>> import sys
    >>> import tempfile
    >>> f1 = tempfile.NamedTemporaryFile()
    >>> _ = f1.write(b'bee1  ./a  fck0sha2!aa:10,bb:10,cc:5,dd:5,f1:5\\n')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'bee2  ./b  fck0sha2!bb:10,f2:5,cc:5,f3:5,dd:5,f4:5\\n')
    >>> f2.flush()
    >>> a = Chunksums.parse(open(f1.name))
    >>> b = Chunksums.parse(open(f2.name))
    >>> print_diff(a, b, './a', './b', color=False)
     57.14%  ▀35B  ▄35B  ▀▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▄▄▄▄▒▒▒▒▒▄▄▄▄▄▒▒▒▒▒█████
    >>> print_diff(a, b, './a', './b', color=False, oneline=False)
     57.14%     35B  --------========    =====     =====-----
                35B          ========++++=====+++++=====+++++
    """

    differ = Differ(chunksums1, chunksums2)
    options = dict(
        color=color,
        width=bar_width,
        type="oneline" if oneline else "twolines",
    )
    bar = differ.compare(path1, path2).get_bar(options)
    print(str(bar), file=output or sys.stdout, flush=True)


command_desc = "Show the difference of two files."
command_long_desc = """
Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2

  $ %(prog)s chunksums.dir1 chunksums.dir2 dir1/file1 dir2/file2

  $ %(prog)s chunksums chunksums ./file1 ./file2
"""


def main():
    """
    >>> sys.argv = ['chunkdiff']
    >>> try:
    ...     main()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... except:
    ...     pass
    usage: chunkdiff ...
    Show the difference ...
    ...

    >>> import tempfile
    >>> f = tempfile.NamedTemporaryFile()
    >>> _ = f.write(
    ... b'bee1  ./a  fck0sha2!aa:1000,bb:1000,cc:1000,f1:500,dd:500,f2:500\\n'
    ... b'bee2  ./b  fck0sha2!bb:1000,cc:1000,f3:1000,f4:500,dd:500,f5:500\\n'
    ... )
    >>> f.flush()
    >>> s = f.name
    >>> sys.argv = ['chunkdiff', '-s', s, '-s', s, './a', './b', '--nocolor']
    >>> main()
     55.56%  ▀4.39KB  ▄4.39KB  ▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒███▄▄▄▄▄▄▄▄▄▒▒▒███
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-w', '10']
    >>> main()
     55.56%  ▀4.39KB  ▄4.39KB  ▀▀▒▒▒█▄▄▒█
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-b', 'twolines']
    >>> main()
     55.56%  4.39KB  -------===============---         ===---
             4.39KB         ===============++++++++++++===+++

    >>> sys.argv = ['chunkdiff', '-s', s, './bad', './beef']
    >>> try:
    ...     main()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... except:
    ...     pass
    file path not found: ./bad
    """
    parser = argparse.ArgumentParser(
        description=command_desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=command_long_desc,
    )
    parser.add_argument(
        "-b",
        "--bar",
        default="oneline",
        help="the style of bar. default: %(default)s",
    )
    parser.add_argument(
        "-w",
        "--barwidth",
        default=40,
        type=int,
        help="the width of bar. default: %(default)s",
    )
    parser.add_argument(
        "-n",
        "--nocolor",
        action="store_true",
        help="do not colorize output. default: False",
    )
    parser.add_argument(
        "-s",
        "--chunksums",
        action="append",
        help="path to chunksums file",
    )
    parser.add_argument("file1", nargs="?", help="path to file")
    parser.add_argument("file2", nargs="?", help="path to file")
    args = parser.parse_args()

    if not (args.chunksums and args.file1 and args.file2):
        parser.print_help()
        sys.exit()

    chunksums1 = chunksums2 = args.chunksums[0]
    if len(args.chunksums) > 1:
        chunksums2 = args.chunksums[1]

    color = not args.nocolor
    oneline = args.bar == "oneline"

    try:
        print_diff(
            Chunksums.parse(open(chunksums1)),
            Chunksums.parse(open(chunksums2)),  # FIXME open same file only once
            args.file1,
            args.file2,
            bar_width=args.barwidth,
            color=color,
            oneline=oneline,
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
