from functools import total_ordering

from .blueprint import Blueprint
from .diffbar import Bar
from .dire import DiffType
from .dire import Dire
from .sums import File


class Differ:
    def __init__(self, chunksums1=None, chunksums2=None):
        self.chunksums1 = chunksums1
        self.chunksums2 = chunksums2
        self.__pairs = None
        self.__dups = None

    def _prepare_same_files(self):
        self.chunks1 = self.chunksums1.chunk2file_id
        self.chunks2 = self.chunksums2.chunk2file_id
        self.same_chunks = set(self.chunks1) & set(self.chunks2)
        self.same_file_ids1 = {c: self.chunks1[c] for c in self.same_chunks}
        self.same_file_ids2 = {c: self.chunks2[c] for c in self.same_chunks}

    @property
    def _pairs(self):
        """get dup file id pairs"""
        if self.__pairs is not None:
            return self.__pairs

        self._prepare_same_files()
        file_id_pairs = []
        for c in self.same_chunks:
            ids1, ids2 = self.same_file_ids1[c], self.same_file_ids2[c]
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

        self.__dups = {}
        for hash1, hash2 in self._pairs:
            self._compare(hash1, hash2)

        self.__dups = list(self.__dups.values())
        return self.__dups

    def _compare(self, hash1, hash2):
        f1 = self.chunksums1.hashes[hash1]
        f2 = self.chunksums2.hashes[hash2]
        # avoid compare two files twice
        if (f2.size, f2.path, f1.size, f1.path) in self.__dups:
            return

        cr = self.compare_file(f1, f2)

        if f1.path == f2.path and cr.ratio == 1.0:
            return
        self.__dups[(f1.size, f1.path, f2.size, f2.path)] = cr

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
        >>> pprint(Differ(sums1, sums2).compare('./a', './b').get_blueprint(20).lines())
        (['----', '====', '  ', '==', '  ', '==', '--', '  '],
         ['    ', '====', '++', '==', '++', '==', '++++'])
        """
        f1 = self.chunksums1.get_file(path1)
        f2 = self.chunksums2.get_file(path2)
        return self.compare_file(f1, f2)

    def compare_file(self, file1, file2):
        return CompareResult(file1, file2)


@total_ordering
class CompareResult:
    """
    >>> s = '''bee1  ./a  fck0sha2!aa:10,bb:10,cc:5,dd:5,f1:5
    ... bee2  ./b  fck0sha2!bb:10,f2:5,cc:5,f3:5,dd:5,f4:10'''
    >>> cr = CompareResult.loads(s)
    >>> cr
    <CompareResult 0.5333333333333333, ./a : ./b>
    >>> cr.total
    45
    >>> cr.dumps() == s
    True
    """

    def __init__(self, file1, file2):
        self.file1 = file1
        self.file2 = file2
        dire = Dire.get(file1.hashes, file2.hashes, file1.sizes, file2.sizes)
        self.total = sum([x.value for x in dire])
        matches = sum([x.value for x in dire if x.type is DiffType.EQUAL])
        self.ratio = (2 * matches) / (file1.size + file2.size)
        self.dire = dire

    def get_blueprint(self, bar_width):
        return Blueprint(bar_width, self.total, self.dire)

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

    def dumps(self):
        return f"{self.file1.dumps()}\n{self.file2.dumps()}"

    @classmethod
    def loads(cls, s):
        s1, s2 = s.split("\n")
        return cls(File.loads(s1), File.loads(s2))
