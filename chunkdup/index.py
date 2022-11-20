from chunksum.parser import parse_chunksums


class ChunksumIndex:
    """
    >>> import io
    >>> from pprint import pprint
    >>> chunksums = '''
    ... sum1  /A/1  fck0sha2!a:10,b:10
    ... sum2  /A/2  fck0sha2!c:10,d:10,e:10
    ... sum3  /A/3  fck0sha2!f:10,g:10
    ... sum4  /A/4  fck0sha2!h:10
    ... '''
    >>> file = io.StringIO(chunksums)
    >>> from chunksum.parser import parse_chunksums
    >>> sums = parse_chunksums(file)
    >>> index = ChunksumIndex(sums)
    >>> list(index.files)
    ['/A/1', '/A/2', '/A/3', '/A/4']
    >>> list(index.file_ids)
    [0, 1, 2, 3]
    >>> list(index.chunks)
    ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    >>> index.chunk2file_id
    {'a': [0], 'b': [0], 'c': [1], 'd': [1], 'e': [1], 'f': [2], 'g': [2], 'h': [3]}
    >>> index.file_id2chunk
    {0: ['a', 'b'], 1: ['c', 'd', 'e'], 2: ['f', 'g'], 3: ['h']}
    >>> index.chunk2size
    {'a': 10, 'b': 10, 'c': 10, 'd': 10, 'e': 10, 'f': 10, 'g': 10, 'h': 10}
    """

    def __init__(self, sums):
        self._files = {}  # file path -> file id and details
        self._file_ids = {}  # inverse: file id -> file path
        self._chunk2file_id = {}  # hash -> file id
        self._chunk2size = {}  # hash -> length of chunk
        self._file_id2chunk = {}  # file id -> hash
        file_id = 0
        for s in sums:
            self._files[s["path"]] = dict(
                id=file_id,
                checksum=s["checksum"],
                chunks=s["chunks"],
                size=sum([size for _, size in s["chunks"]]),
            )
            self._file_ids[file_id] = s["path"]
            self._file_id2chunk[file_id] = []
            for c, size in s["chunks"]:
                self._chunk2file_id.setdefault(c, []).append(file_id)
                self._chunk2size[c] = size
                self._file_id2chunk[file_id].append(c)
            file_id += 1

    @property
    def files(self):
        return self._files.keys()

    @property
    def file_ids(self):
        return self._file_ids.keys()

    @property
    def chunks(self):
        return self._chunk2file_id.keys()

    @property
    def chunk2file_id(self):
        return self._chunk2file_id

    @property
    def file_id2chunk(self):
        return self._file_id2chunk

    @property
    def chunk2size(self):
        return self._chunk2size


def get_index(chunksum_file):
    sums = parse_chunksums(chunksum_file)
    return ChunksumIndex(sums)
