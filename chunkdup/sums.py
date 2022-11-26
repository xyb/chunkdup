def load_hash(hash):
    if isinstance(hash, bytes):
        return hash
    else:
        return bytes.fromhex(hash)


class File:
    def __init__(self, hash, path, alg_name, chunks):
        self.hash = load_hash(hash)
        self.path = path
        self.alg_name = alg_name
        self._load_chunks(chunks)
        self.size = sum(self.sizes)

    def _load_chunks(self, chunks):
        if not chunks:
            self.hashes, self.sizes = [], []
        else:
            chunks = list(
                [(load_hash(hash), size) for hash, size in chunks],
            )
            self.hashes, self.sizes = list(zip(*chunks))

    def __repr__(self):
        """
        >>> File('beef', './file', 'fck0sha2', [])
        <File beef fck0sha2 './file'>
        """
        return f"<File {self.hash.hex()} {self.alg_name} {self.path!r}>"

    @property
    def chunks(self):
        return list(zip(self.hashes, self.sizes))

    def dumps(self):
        """
        >>> File(b'\\xbe\\xef', './file', 'fck0sha2', []).dumps()
        'beef  ./file  fck0sha2!'
        >>> File(b'\\xbe\\xef', './file', 'fck0sha2', [('f110', 5)]).dumps()
        'beef  ./file  fck0sha2!f110:5'
        """
        chunks = ",".join(
            [f"{digest.hex()}:{size}" for digest, size in zip(self.hashes, self.sizes)],
        )
        return f"{self.hash.hex()}  {self.path}  {self.alg_name}!{chunks}"

    @classmethod
    def parse(cls, line):
        """
        >>> File.parse('feed  ./a  fck0sha2!')
        <File feed fck0sha2 './a'>
        >>> File.parse('f00d  ./file1  fck0sha2!abcd:10')
        <File f00d fck0sha2 './file1'>
        >>> _.chunks
        [(b'\xab\xcd', 10)]
        >>> sums = 'c0c0  ./long  file name  fck0sha2!cafe:20,beef:30'
        >>> File.parse(sums)
        <File c0c0 fck0sha2 './long  file name'>
        >>> _.chunks
        [(b'\xca\xfe', 20), (b'\xbe\xef', 30)]
        >>> assert File.parse(sums).dumps() == sums
        """
        items = line.split("  ")
        checksum = bytes.fromhex(items[0])
        chunks = items[-1]
        if len(items) > 3:
            path = "  ".join(items[1:-1])
        else:
            path = items[1]
        alg_name, chunks = cls.parse_chunks(chunks)
        return File(
            hash=checksum,
            path=path,
            alg_name=alg_name,
            chunks=chunks,
        )

    @classmethod
    def parse_chunks(cls, data):
        alg_name, chunks = data.split("!")
        if chunks:
            chunks = [c.split(":") for c in chunks.split(",") if c]
            chunks = [(bytes.fromhex(id), int(size)) for id, size in chunks]
            return alg_name, chunks
        else:
            return alg_name, []


class Chunksums:
    def __init__(self, path=""):
        """
        >>> import io
        >>> cs = Chunksums.parse(io.StringIO('''
        ... bad0  ./a  fck0sha2!
        ... beaf  ./file1  fck0sha2!abcd:10
        ... f00d  ./file2  fck0sha2!c0c0:20,beef:30'''))
        >>> cs
        <Chunksums '', 3 files>
        >>> cs.hashes[b'\\xbe\\xaf']
        <File beaf fck0sha2 './file1'>
        >>> from pprint import pprint
        >>> chunks = cs.chunk2file_id
        >>> pprint(chunks)
        {(b'\xab\xcd', 10): [b'\xbe\xaf'],
         (b'\xbe\xef', 30): [b'\xf0\\r'],
         (b'\xc0\xc0', 20): [b'\xf0\\r']}
        >>> assert cs.chunk2file_id == chunks
        """
        self.path = path
        self.hashes = {}
        self.files = {}
        self._chunk2file_id = None

    def __repr__(self):
        return f"<Chunksums {self.path!r}, {len(self.files)} files>"

    def get_file(self, path):
        try:
            hash = self.files[path]
        except KeyError:
            raise FileNotFoundError(f"file path not found: {path}")
        return self.hashes[hash]

    @property
    def chunk2file_id(self):
        if self._chunk2file_id is not None:
            return self._chunk2file_id

        self._chunk2file_id = {}
        for chunksum, file in self.hashes.items():
            for c in file.chunks:
                self._chunk2file_id.setdefault(c, []).append(chunksum)

        return self._chunk2file_id

    @classmethod
    def parse(cls, file, path=""):
        cs = Chunksums(path)
        for line in file:
            line = line.strip()
            if not line:
                continue
            f = File.parse(line)
            cs.hashes[f.hash] = f
            cs.files[f.path] = f.hash
        return cs
