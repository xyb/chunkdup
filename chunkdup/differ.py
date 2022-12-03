from functools import total_ordering
from itertools import islice
from math import ceil

from .diffbar import Bar
from .dire import Dire
from .utils import iter_steps


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
        >>> df = Differ(sums1, sums2)
        >>> len(df._pairs)
        4
        >>> len(df.dups)
        4
        >>> pprint(sorted(df.dups))
        [<CompareResult 0.4, /A/3 : /B/2>,
         <CompareResult 0.5, /A/3 : /B/3>,
         <CompareResult 0.6666666666666666, /A/2 : /B/2>,
         <CompareResult 1.0, /A/4 : /B/4>]

        >>> chunksum_repeat = '''
        ... bee1  a  fck0sha2!aa:1,aa:1,aa:1,bb:2
        ... bee2  b  fck0sha2!aa:1,bb:2
        ... bee3  c  fck0sha2!aa:1,aa:1,aa:1,bb:2
        ... '''
        >>> sums1 = Chunksums.parse(io.StringIO(chunksum_repeat))
        >>> sums2 = Chunksums.parse(io.StringIO(chunksum_repeat))
        >>> df = Differ(sums1, sums2)
        >>> len(df._pairs)
        9
        >>> len(df.dups)
        3
        >>> pprint(sorted(df.dups))
        [<CompareResult 0.75, b : c>,
         <CompareResult 0.75, a : b>,
         <CompareResult 1.0, a : c>]
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

            cr = self._compare(f1, f2)

            if f1.path == f2.path and cr.ratio == 1.0:
                continue
            dups[(f1.size, f1.path, f2.size, f2.path)] = cr
        self.__dups = list(dups.values())
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
        return self._compare(f1, f2)

    def _compare(self, file1, file2):
        dire = Dire.get(file1.hashes, file2.hashes, file1.sizes, file2.sizes)
        total = sum([x.value for x in dire])
        matches = sum([x.value for x in dire if x.type.name == "EQUAL"])
        ratio = (2 * matches) / (file1.size + file2.size)
        res = CompareResult(self, file1, file2, total, ratio, dire)
        return res


@total_ordering
class CompareResult:
    def __init__(self, differ, file1, file2, total, ratio, dire):
        self.differ = differ
        self.file1 = file1
        self.file2 = file2
        self.total = total
        self.ratio = ratio
        self.dire = dire

    def get_parts(self, bar_width):
        line1, line2 = fill_line(bar_width, self.total, self.dire)
        return line1, line2

    def get_bar(self, options):
        return Bar(self, options)

    @property
    def __key(self):
        return (
            self.ratio,
            self.file1.size,
            self.file1.path,
            self.file2.size,
            self.file2.path,
        )

    def __eq__(self, other):
        return self.__key == other.__key  # pragma: no cover

    def __lt__(self, other):
        return self.__key < other.__key

    def __repr__(self):
        return f"<CompareResult {self.ratio}, {self.file1.path} : {self.file2.path}>"


def fill_line(bar_width, total, dire):
    """
    >>> from .utils import ruler
    >>> r = lambda w: ruler(w) + '\\n'
    >>> pp = lambda w, s: print(r(w) + '\\n'.join([''.join(i) for i in s]))
    >>> dire = Dire.get(['a', 'b'], ['a', 'c'], [20, 10], [20, 10])
    >>> fill_line(20, 30, dire)
    (['=============', '-------'], ['=============', '+++++++'])
    >>> pp(20, fill_line(20, 30, dire))
    ----5----1----5----2
    =============-------
    =============+++++++
    >>> dire = Dire.loads('R10 E20 R10 D5 I5 E10 R10 E5 R5 E10')
    >>> pp(15, fill_line(15, 90, dire))
    ----5----1----5
    -===-- ==--=-==
    +===+ +==++=+==
    >>> pp(8, fill_line(8, 90, dire))
    ----5---
    -=-...-=
    +=+...+=
    """
    zoom = bar_width / total

    blueprint = []
    for di in dire:
        w1, w2, = ceil(
            di.a * zoom,
        ), ceil(di.b * zoom)
        blueprint.append([w1, w2])

    adjust_space = []
    for w1, w2 in blueprint:
        maxw = max(w1, w2)
        adjust_space.append((maxw - 1) if maxw > 1 else 0)

    def adjust_blueprint():  # fit for the char grid
        real_width = sum(max(x1, x2) for x1, x2 in blueprint)
        if real_width == bar_width:
            return blueprint

        shrink_target = real_width - bar_width

        def shrink(index, delta=1):
            w1, w2 = blueprint[index]
            if w1:
                w1 = w1 - 1
            if w2:
                w2 = w2 - 1
            blueprint[index] = [w1, w2]

        for index in islice(iter_steps(adjust_space), shrink_target):
            shrink(index)

        def ellipsis():
            half = (bar_width - len("...")) / 2
            left = ceil(half)
            right = int(half)
            for i in blueprint[left:-right]:
                i[0] = -1
                i[1] = -1

        if shrink_target > sum(adjust_space):
            ellipsis()

        return blueprint

    blueprint = adjust_blueprint()

    def char_bar(char, width, line):
        if width:
            line.append(char * width)

    def padding_bar(width, max_width, line):
        padding = max_width - width
        if padding:
            line.append(" " * padding)

    line1 = []
    line2 = []
    for di, (width1, width2) in zip(dire, blueprint):
        if width1 < 0 and width2 < 0:
            if line1[-1] != "...":
                line1.append("...")
                line2.append("...")
            continue
        char_bar(di.ca, width1, line1)
        char_bar(di.cb, width2, line2)
        width = max(width1, width2)
        padding_bar(width1, width, line1)
        padding_bar(width2, width, line2)

    return line1, line2
