#!/usr/bin/env python

import sys

from chunksum.parser import parse_chunksums


class CheckSumIndex:
    def __init__(self, sums):
        self._files = {}  # file path -> file id
        self._file_ids = {}  # inverse: file id -> file path
        self._chunk2file_id = {}  # hash -> file id
        self._file_id2chunk = {}  # file id -> hash
        file_id = 0
        for s in sums:
            self._files[s['path']] = dict(
                id=file_id,
                checksum=s['checksum'],
                chunks=s['chunks'],
                size=sum([size for _, size in s['chunks']])
            )
            self._file_ids[file_id] = s['path']
            cids = [c for c, _ in s['chunks']]
            for c in cids:
                self._chunk2file_id.setdefault(c, []).append(file_id)
            self._file_id2chunk[file_id] = cids
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
    def chunk2fileid(self):
        return self._chunk2file_id

    @property
    def fileid2chunk(self):
        return self._file_id2chunk


def find_dup_files(index1, index2):
    chunks1 = index1.chunk2fileid
    fileids1 = index1.fileid2chunk
    chunks2 = index2.chunk2fileid
    fileids2 = index2.fileid2chunk

    same_chunks = set(chunks1) & set(chunks2)

    same_file_ids1 = {c: chunks1[c] for c in same_chunks}
    same_file_ids2 = {c: chunks2[c] for c in same_chunks}

    file_id_pairs = []
    for c in same_chunks:
        ids1 = same_file_ids1[c]
        ids2 = same_file_ids2[c]
        file_id_pairs.extend([(x, y) for x in ids1 for y in ids2])
    file_id_pairs = list(set(file_id_pairs))

    def dup_rate(file_id1, file_id2):
        ids1 = fileids1[file_id1]
        ids2 = fileids2[file_id2]
        dup = len(ids1) + len(ids2) - len(set(ids1) | set(ids2))
        rate = dup / max(len(ids1), len(ids2))
        return rate

    dups = []
    for f1, f2 in file_id_pairs:
        rate = dup_rate(f1, f2)
        path1 = index1._file_ids[f1]
        path2 = index2._file_ids[f2]
        size1 = index1._files[path1]['size']
        size2 = index2._files[path2]['size']
        dups.append((rate, size1, path1, size2, path2))
    return dups


def find_dup(chunksum_file1, chunksum_file2):
    """
    >>> import io
    >>> chunksum1 = '''
    ... sum1  /A/1  fck0sha2!a:10,b:10
    ... sum2  /A/2  fck0sha2!c:10,d:10,e:10
    ... sum3  /A/3  fck0sha2!f:10,g:10
    ... sum4  /A/4  fck0sha2!h:10
    ... '''
    >>> chunksum2 = '''
    ... sum5  /B/1  fck0sha2!m:10,n:10
    ... sum6  /B/2  fck0sha2!c:10,d:10,f:10
    ... sum7  /B/3  fck0sha2!f:10,x:10
    ... sum8  /B/4  fck0sha2!h:10
    ... '''
    >>> file1 = io.StringIO(chunksum1)
    >>> file2 = io.StringIO(chunksum2)
    >>> from pprint import pprint
    >>> pprint(find_dup(file1, file2))
    [(1.0, 10, '/A/4', 10, '/B/4'),
     (0.6666666666666666, 30, '/A/2', 30, '/B/2'),
     (0.5, 20, '/A/3', 20, '/B/3'),
     (0.3333333333333333, 20, '/A/3', 30, '/B/2')]
    """
    sums1 = parse_chunksums(chunksum_file1)
    sums2 = parse_chunksums(chunksum_file2)
    index1 = CheckSumIndex(sums1)
    index2 = CheckSumIndex(sums2)
    dups = sorted(find_dup_files(index1, index2), reverse=True)
    return dups


def print_plain_report(dups, output_file):
    """
    >>> import io
    >>> chunksum1 = '''
    ... sum1  /A/1  fck0sha2!a:10,b:10
    ... sum2  /A/2  fck0sha2!c:10,d:10,e:10
    ... sum3  /A/3  fck0sha2!f:10,g:10
    ... sum4  /A/4  fck0sha2!h:10
    ... '''
    >>> chunksum2 = '''
    ... sum5  /B/1  fck0sha2!m:10,n:10
    ... sum6  /B/2  fck0sha2!c:10,d:10,f:10
    ... sum7  /B/3  fck0sha2!f:10,x:10
    ... sum8  /B/4  fck0sha2!h:10
    ... '''
    >>> file1 = io.StringIO(chunksum1)
    >>> file2 = io.StringIO(chunksum2)
    >>> dups = find_dup(file1, file2)
    >>> print_plain_report(dups, sys.stdout)
    100.00%  /A/4 (10B)  /B/4 (10B)
     66.67%  /A/2 (30B)  /B/2 (30B)
     50.00%  /A/3 (20B)  /B/3 (20B)
     33.33%  /A/3 (20B)  /B/2 (30B)
    """
    for rate, size1, file1, size2, file2 in dups:
        print(
            '{:>6.2f}%  {} ({}B)  {} ({}B)'.format(
                rate * 100, file1, size1, file2, size2),
            file=output_file,
            flush=True,
        )


def help():
    print('''Find (partial content) duplicate files.

Usage: {cmd} <chunksums_file1> <chunksums_file2>

Examples:

  $ chunksum dir1/ > chunksum.dir1
  $ chunksum dir2/ > chunksum.dir2
  $ {cmd} chunksum.dir1 chunksum.dir2
'''.format(cmd=sys.argv[0]))


def main():
    if len(sys.argv) != 3:
        help()
        sys.exit()
    path1, path2 = sys.argv[1:3]
    dups = find_dup(open(path1), open(path2))
    print_plain_report(dups, sys.stdout)


if __name__ == '__main__':
    main()
