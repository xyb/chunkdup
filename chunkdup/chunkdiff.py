import argparse
import sys
from itertools import groupby
from math import ceil

from .diff import find_diff
from .sums import Chunksums


GREY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY_BG = "\033[100m"
RED_BG = "\033[101m"
GREEN_BG = "\033[102m"
YELLOW_BG = "\033[103m"
END = "\033[0m"


def fill_line(bar_width, total, diff):
    zoom = bar_width / total

    def char_bar(char, size, line):
        width = ceil(size * zoom)
        if width:
            line.append(char * width)
        return width

    def padding_bar(width, max_width, line):
        padding = max_width - width
        if padding:
            line.append(" " * padding)

    line1 = []
    line2 = []
    for char1, char2, size1, size2 in diff:
        width1 = char_bar(char1, size1, line1)
        width2 = char_bar(char2, size2, line2)
        width = max(width1, width2)
        padding_bar(width1, width, line1)
        padding_bar(width2, width, line2)
    return line1, line2


def get_bar_layer(chunksums1, chunksums2, path1, path2, bar_width=40):
    f1 = chunksums1.get_file(path1)
    f2 = chunksums2.get_file(path2)

    total, ratio, diff = find_diff(f1.hashes, f2.hashes, f1.sizes, f2.sizes)
    line1, line2 = fill_line(bar_width, total, diff)
    return ratio, line1, line2, f1.size, f2.size


def print_2lines_bar(
    ratio,
    line1,
    line2,
    filesize1,
    filesize2,
    output=None,
    bar_width=40,
    color=True,
):
    """
    >>> line1 = ['-----', '==', '-----', '===']
    >>> line2 = ['++', '   ', '==', '+', '    ', '===']
    >>> print_2lines_bar(0.5, line1, line2, 100, 70, color=False)
     50.00%     100  -----==-----===
                 70  ++   ==+    ===
    >>> print_2lines_bar(0.5, line1, line2, 100, 70)
    ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
     50.00%     100  ...
                 70  ...
    """

    def colorful(line):
        colors = {
            "=": GREY_BG,
            "-": RED_BG,
            "+": GREEN_BG,
            " ": YELLOW_BG,
        }
        return [colors[s[0]] + s + END for s in line]

    if color:
        line1 = colorful(line1)
        line2 = colorful(line2)

    percent = f"{ratio * 100:>6.2f}%"
    for pre, size, line in ((percent, filesize1, line1), ("", filesize2, line2)):
        print(
            "{:>7s}  {:>6}  {}".format(pre, size, "".join(line)),
            file=output or sys.stdout,
            flush=True,
        )


def print_1line_bar(
    ratio,
    line1,
    line2,
    filesize1,
    filesize2,
    output=None,
    bar_width=40,
    color=True,
):
    """
    >>> line1 = ['-----', '==', '     ', '===']
    >>> line2 = ['++', '   ', '==', '+++++', '===']
    >>> print_1line_bar(0.6, line1, line2, 100, 70, color=False)
     60.00%  ▀100  ▄70  ██▀▀▀▒▒▄▄▄▄▄▒▒▒
    >>> print_1line_bar(0.6, line1, line2, 100, 70, color=True)
    ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
     60.00%  ▀100  ▄70  ...
    """

    pairs = list("".join(x) for x in zip("".join(line1), "".join(line2)))
    chars = {
        "==": "▒",
        "-+": "█",
        "- ": "▀",
        " +": "▄",
    }
    colors = {
        "==": ["▒", GREY + GREY_BG],  # fg: grey, bg: grey
        "-+": ["▀", RED + GREEN_BG],  # fg/top half: red, bg/bottom half: green
        "- ": ["▀", RED + YELLOW_BG],  # fg: red, bg: yellow
        " +": ["▀", YELLOW + GREEN_BG],  # fg: yellow, bg: green
    }
    bar = []
    for key, group in groupby(pairs):
        width = len(list(group))
        if color:
            char, color_ = colors[key]
            item = color_ + char * width + END
        else:
            item = chars[key] * width
        bar.append(item)

    print(
        "{:>6.2f}%  ▀{}  ▄{}  {}".format(
            ratio * 100,
            filesize1,
            filesize2,
            "".join(bar),
            file=output,
            flush=True,
        ),
    )


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
     57.14%  ▀35  ▄35  ▀▀▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▒▄▄▄▄▄▒▒▒▒▒▄▄▄▄▄▒▒▒▒▒█████
    >>> print_diff(a, b, './a', './b', color=False, oneline=False)
     57.14%      35  ---------=========     =====     =====-----
                 35           =========+++++=====+++++=====+++++
    """

    ratio, line1, line2, filesize1, filesize2 = get_bar_layer(
        chunksums1,
        chunksums2,
        path1,
        path2,
        bar_width=bar_width,
    )
    if oneline:
        print_func = print_1line_bar
    else:
        print_func = print_2lines_bar
    print_func(
        ratio,
        line1,
        line2,
        filesize1,
        filesize2,
        output=output or sys.stdout,
        bar_width=bar_width,
        color=color,
    )


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
    ... b'bee1  ./a  fck0sha2!aa:10,bb:10,cc:10,f1:5,dd:5,f2:5\\n'
    ... b'bee2  ./b  fck0sha2!bb:10,cc:10,f3:10,f4:5,dd:5,f5:5\\n'
    ... )
    >>> f.flush()
    >>> s = f.name
    >>> sys.argv = ['chunkdiff', '-s', s, '-s', s, './a', './b', '--nocolor']
    >>> main()
     55.56%  ▀45  ▄45  ▀▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒████▄▄▄▄▄▄▄▒▒▒▒████
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-w', '10']
    >>> main()
     55.56%  ▀45  ▄45  ▀▀▒▒▒▒█▄▄▒█
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-b', 'twolines']
    >>> main()
     55.56%      45  --------===============----       ====----
                 45          ===============+++++++++++====++++

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
