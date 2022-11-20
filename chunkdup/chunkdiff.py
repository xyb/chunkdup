import sys
from difflib import SequenceMatcher
from math import ceil

from chunksum.parser import parse_chunksums

from .chunkdup import CheckSumIndex


GREY = "\033[100m"
RED = "\033[101m"
GREEN = "\033[102m"
YELLOW = "\033[103m"
END = "\033[0m"


def get_info(chunksums_file1, chunksums_file2, path1, path2):
    sums1 = parse_chunksums(chunksums_file1)
    sums2 = parse_chunksums(chunksums_file2)
    index1 = CheckSumIndex(sums1)
    index2 = CheckSumIndex(sums2)

    id1 = index1._files.get(path1).get("id")
    id2 = index2._files.get(path2).get("id")

    chunks1 = index1.file_id2chunk[id1]
    chunks2 = index2.file_id2chunk[id2]

    sizes1 = [index1.chunk2size.get(id) for id in chunks1]
    sizes2 = [index2.chunk2size.get(id) for id in chunks2]

    return (chunks1, sizes1), (chunks2, sizes2)


def find_diff(chunks1, sizes1, chunks2, sizes2):
    s = SequenceMatcher(a=chunks1, b=chunks2)
    diff = []
    total = 0
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        size1 = sum([s for s in sizes1[i1:i2]])
        size2 = sum([s for s in sizes2[j1:j2]])
        size = max(size1, size2)
        total += size
        if tag == "equal":
            diff.append(["=", "=", size, size])
        elif tag == "replace":
            diff.append(["-", "+", size1, size2])
        elif tag == "delete":
            diff.append(["-", " ", size, 0])
        else:  # tag == 'insert'
            diff.append([" ", "+", 0, size2])

    return total, diff


def print_diff(
    chunksums_file1,
    chunksums_file2,
    path1,
    path2,
    bar_size=40,
    color=True,
):
    """
    >>> import tempfile
    >>> f1 = tempfile.NamedTemporaryFile()
    >>> _ = f1.write(b'sum1  ./a  fck0sha2!a:10,b:10,c:10,r:5,s:10\\n')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'sum2  ./b  fck0sha2!b:10,c:10,m:10,x:5,s:5,y:5\\n')
    >>> f2.flush()
    >>> print_diff(open(f1.name), open(f2.name), './a', './b', color=False)
            45  -------==============----      =======
            45         ==============++++++++++=======++++
    """
    (chunks1, sizes1), (chunks2, sizes2) = get_info(
        chunksums_file1,
        chunksums_file2,
        path1,
        path2,
    )

    total, diff = find_diff(chunks1, sizes1, chunks2, sizes2)

    zoom = bar_size / total
    line1 = []
    line2 = []
    for char1, char2, size1, size2 in diff:
        width1 = ceil(size1 * zoom)
        width2 = ceil(size2 * zoom)
        if width1:
            line1.append(char1 * width1)
        if width2:
            line2.append(char2 * width2)
        width = max(width1, width2)
        padding1 = width - width1
        padding2 = width - width2
        if padding1:
            line1.append(" " * padding1)
        if padding2:
            line2.append(" " * padding2)

    def colorful(line):
        colors = {
            "=": GREY,
            "-": RED,
            "+": GREEN,
            " ": YELLOW,
        }
        return [colors[s[0]] + s + END for s in line]

    if color:
        line1 = colorful(line1)
        line2 = colorful(line2)

    filesize1 = sum(sizes1)
    filesize2 = sum(sizes2)
    print("{:>10d}  {}".format(filesize1, "".join(line1)))
    print("{:>10d}  {}".format(filesize2, "".join(line2)))


def main():
    """
    >>> import tempfile
    >>> f1 = tempfile.NamedTemporaryFile()
    >>> _ = f1.write(b'sum1  ./a  fck0sha2!a:10,b:10,c:10,r:5,s:10\\n')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'sum2  ./b  fck0sha2!b:10,c:10,m:10,x:5,s:5,y:5\\n')
    >>> f2.flush()
    >>> sys.argv = ['chunkdiff', f1.name, f2.name, './a', './b']
    >>> main()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                45  ...
                45  ...
    """
    if len(sys.argv) == 5:
        sums_path1, sums_path2, path1, path2 = sys.argv[1:5]
        print_diff(open(sums_path1), open(sums_path2), path1, path2)
    else:
        pass


if __name__ == "__main__":
    main()  # pragma: no cover
