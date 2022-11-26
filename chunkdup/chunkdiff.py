import argparse
import sys
from difflib import SequenceMatcher
from itertools import groupby
from math import ceil

from .index import get_index


GREY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY_BG = "\033[100m"
RED_BG = "\033[101m"
GREEN_BG = "\033[102m"
YELLOW_BG = "\033[103m"
END = "\033[0m"


class FileNotExists(Exception):
    pass


def get_info(chunksums_file, path):
    index = get_index(chunksums_file)
    try:
        id = index._files.get(path).get("id")
    except AttributeError:
        raise FileNotExists(f"file path not found: {path}")
    chunks = index.file_id2chunk[id]
    sizes = [index.chunk2size.get(id) for id in chunks]
    return chunks, sizes


def find_diff(chunks1, sizes1, chunks2, sizes2):
    s = SequenceMatcher(a=chunks1, b=chunks2)
    diff = []
    total = 0
    tag_map = {
        "equal": ["=", "="],
        "replace": ["-", "+"],
        "delete": ["-", " "],
        "insert": [" ", "+"],
    }
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        size1 = sum([s for s in sizes1[i1:i2]])
        size2 = sum([s for s in sizes2[j1:j2]])
        total += max(size1, size2)
        diff.append(tag_map[tag] + [size1, size2])

    return total, diff


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


def get_bar_layer(chunksums_file1, chunksums_file2, path1, path2, bar_width=40):
    chunks1, sizes1 = get_info(chunksums_file1, path1)
    chunks2, sizes2 = get_info(chunksums_file2, path2)

    total, diff = find_diff(chunks1, sizes1, chunks2, sizes2)
    filesize1 = sum(sizes1)
    filesize2 = sum(sizes2)
    line1, line2 = fill_line(bar_width, total, diff)
    return line1, line2, filesize1, filesize2


def print_2lines_bar(
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
    >>> print_2lines_bar(line1, line2, 100, 70, color=False)
           100  -----==-----===
            70  ++   ==+    ===
    >>> print_2lines_bar(line1, line2, 100, 70)
    ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
           100  ...
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

    for size, line in ((filesize1, line1), (filesize2, line2)):
        print(
            "{:>10}  {}".format(size, "".join(line)),
            file=output or sys.stdout,
            flush=True,
        )


def print_1line_bar(
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
    >>> print_1line_bar(line1, line2, 100, 70, color=False)
    ▀100  ▄70  ██▀▀▀▒▒▄▄▄▄▄▒▒▒
    >>> print_1line_bar(line1, line2, 100, 70, color=True)
    ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ▀100  ▄70  ...
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
        "▀{}  ▄{}  {}".format(
            filesize1,
            filesize2,
            "".join(bar),
            file=output,
            flush=True,
        ),
    )


def print_diff(
    chunksums_file1,
    chunksums_file2,
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
    >>> _ = f1.write(b'sum1  ./a  fck0sha2!a:10,b:10,c:10,r:5,s:5,t:5\\n')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'sum2  ./b  fck0sha2!b:10,c:10,m:5,r:5,n:5,s:5,z:5\\n')
    >>> f2.flush()
    >>> a, b = open(f1.name), open(f2.name)
    >>> print_diff(a, b, './a', './b', color=False)
    ▀45  ▄45  ▀▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▄▄▄▄▒▒▒▒▄▄▄▄▒▒▒▒████
    >>> a, b = open(f1.name), open(f2.name)
    >>> print_diff(a, b, './a', './b', color=False, oneline=False)
            45  --------===============    ====    ====----
            45          ===============++++====++++====++++
    """

    line1, line2, filesize1, filesize2 = get_bar_layer(
        chunksums_file1,
        chunksums_file2,
        path1,
        path2,
        bar_width=bar_width,
    )
    if oneline:
        print_func = print_1line_bar
    else:
        print_func = print_2lines_bar
    print_func(
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
    ... b'sum1  ./a  fck0sha2!a:10,b:10,c:10,r:5,s:5,t:5\\n'
    ... b'sum2  ./b  fck0sha2!b:10,c:10,m:10,x:5,s:5,y:5\\n'
    ... )
    >>> f.flush()
    >>> s = f.name
    >>> sys.argv = ['chunkdiff', '-s', s, '-s', s, './a', './b', '--nocolor']
    >>> main()
    ▀45  ▄45  ▀▀▀▀▀▀▀▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒████▄▄▄▄▄▄▄▒▒▒▒████
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-w', '10']
    >>> main()
    ▀45  ▄45  ▀▀▒▒▒▒█▄▄▒█
    >>> sys.argv = ['chunkdiff', '-s', s, './a', './b', '-n', '-b', 'twolines']
    >>> main()
            45  --------===============----       ====----
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
            open(chunksums1),
            open(chunksums2),
            args.file1,
            args.file2,
            bar_width=args.barwidth,
            color=color,
            oneline=oneline,
        )
    except FileNotExists as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
