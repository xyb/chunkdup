from math import ceil

from .diff import find_diff
from .diffbar import Bar


def diff_ratio(a, b, sizes1, sizes2):
    """
    >>> sizes = {'a': 10, 'b': 10, 'c': 20}
    >>> diff_ratio(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'a'],
    ...            [10, 10, 10, 10], [10, 10, 10, 10])
    1.0
    >>> diff_ratio(['a', 'a', 'a', 'a'], ['a', 'a', 'b', 'a'],
    ...            [10, 10, 10, 10], [10, 10, 10, 10])
    0.75
    >>> diff_ratio(['a', 'a', 'a', 'a'], ['a', 'c', 'a'],
    ...            [10, 10, 10, 10], [10, 20, 10])
    0.5
    """
    _, ratio, _ = find_diff(a, b, sizes1, sizes2)
    return ratio


class Differ:
    def __init__(self, chunksums1=None, chunksums2=None):
        self.chunksums1 = chunksums1
        self.chunksums2 = chunksums2
        self.__pairs = None
        self.__dups = None

    @property
    def _pairs(self):
        """get dup file id pairs"""
        if self.__pairs is not None:
            return self.__pairs

        chunks1 = self.chunksums1.chunk2file_id
        chunks2 = self.chunksums2.chunk2file_id
        same_chunks = set(chunks1) & set(chunks2)

        same_file_ids1 = {c: chunks1[c] for c in same_chunks}
        same_file_ids2 = {c: chunks2[c] for c in same_chunks}

        file_id_pairs = []
        for c in same_chunks:
            ids1 = same_file_ids1[c]
            ids2 = same_file_ids2[c]
            file_id_pairs.extend([(x, y) for x in ids1 for y in ids2])
        self.__pairs = sorted(set(file_id_pairs))
        return self.__pairs

    @property
    def dups(self):
        """
        >>> import io
        >>> from pprint import pprint
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
        >>> from .sums import Chunksums
        >>> sums1 = Chunksums.parse(io.StringIO(chunksum1))
        >>> sums2 = Chunksums.parse(io.StringIO(chunksum2))
        >>> pprint(Differ(sums1, sums2).dups)
        [[1.0, 10, '/A/4', 10, '/B/4'],
         [0.6666666666666666, 30, '/A/2', 30, '/B/2'],
         [0.5, 20, '/A/3', 20, '/B/3'],
         [0.4, 20, '/A/3', 30, '/B/2']]

        >>> chunksum_repeat = '''
        ... bee1  a  fck0sha2!aa:1,aa:1,aa:1,bb:2
        ... bee2  b  fck0sha2!aa:1,bb:2
        ... bee3  c  fck0sha2!aa:1,aa:1,aa:1,bb:2
        ... '''
        >>> sums1 = Chunksums.parse(io.StringIO(chunksum_repeat))
        >>> sums2 = Chunksums.parse(io.StringIO(chunksum_repeat))
        >>> pprint(Differ(sums1, sums2).dups)
        [[1.0, 5, 'a', 5, 'c'], [0.75, 5, 'a', 3, 'b'], [0.75, 3, 'b', 5, 'c']]
        """
        if self.__dups is not None:
            return self.__dups

        dups = {}
        for hash1, hash2 in self._pairs:
            f1 = self.chunksums1.hashes[hash1]
            f2 = self.chunksums2.hashes[hash2]
            # avoid compare two files twice
            if (f2.size, f2.path, f1.size, f1.path) in dups:
                continue

            ratio = diff_ratio(
                f1.hashes,
                f2.hashes,
                f1.sizes,
                f2.sizes,
            )
            if f1.path == f2.path and ratio == 1.0:
                continue
            dups[(f1.size, f1.path, f2.size, f2.path)] = ratio
        self.__dups = sorted(
            [[ratio] + list(key) for key, ratio in dups.items()],
            reverse=True,
        )
        return self.__dups

    def compare(self, path1, path2):
        """
        >>> import sys
        >>> import tempfile
        >>> f1 = tempfile.NamedTemporaryFile()
        >>> _ = f1.write(b'bee1  ./a  fck0sha2!aa:10,bb:10,cc:5,dd:5,f1:5\\n')
        >>> f1.flush()
        >>> f2 = tempfile.NamedTemporaryFile()
        >>> _ = f2.write(b'bee2  ./b  fck0sha2!bb:10,f2:5,cc:5,f3:5,dd:5,f4:10\\n')
        >>> f2.flush()
        >>> from .sums import Chunksums
        >>> sums1 = Chunksums.parse(open(f1.name))
        >>> sums2 = Chunksums.parse(open(f2.name))
        >>> from pprint import pprint
        >>> pprint(Differ(sums1, sums2).compare('./a', './b').get_parts(20))
        (['----', '====', '  ', '==', '  ', '==', '--', '  '],
         ['    ', '====', '++', '==', '++', '==', '++++'])
        """
        f1 = self.chunksums1.get_file(path1)
        f2 = self.chunksums2.get_file(path2)

        total, ratio, diff = find_diff(f1.hashes, f2.hashes, f1.sizes, f2.sizes)
        res = CompareResult(self, f1, f2, total, ratio, diff)
        return res


class CompareResult:
    def __init__(self, differ, file1, file2, total, ratio, detail):
        self.differ = differ
        self.file1 = file1
        self.file2 = file2
        self.total = total
        self.ratio = ratio
        self.detail = detail

    def get_parts(self, bar_width):
        line1, line2 = fill_line(bar_width, self.total, self.detail)
        return line1, line2

    def get_bar(self, width, options):
        return Bar(self, width, options)


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
