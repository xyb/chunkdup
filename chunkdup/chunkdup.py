#!/usr/bin/env python
import argparse
import signal
import sys

from .diff import find_diff
from .sums import Chunksums


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


def get_dup_file_id_pairs(chunksums1, chunksums2):
    chunks1 = chunksums1.chunk2file_id
    chunks2 = chunksums2.chunk2file_id
    same_chunks = set(chunks1) & set(chunks2)

    same_file_ids1 = {c: chunks1[c] for c in same_chunks}
    same_file_ids2 = {c: chunks2[c] for c in same_chunks}

    file_id_pairs = []
    for c in same_chunks:
        ids1 = same_file_ids1[c]
        ids2 = same_file_ids2[c]
        file_id_pairs.extend([(x, y) for x in ids1 for y in ids2])
    return sorted(set(file_id_pairs))


def find_dup_files(chunksums1, chunksums2):
    file_id_pairs = get_dup_file_id_pairs(chunksums1, chunksums2)

    dups = {}
    for hash1, hash2 in file_id_pairs:
        f1 = chunksums1.hashes[hash1]
        f2 = chunksums2.hashes[hash2]
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
    return [[ratio] + list(key) for key, ratio in dups.items()]


def find_dup(chunksums1, chunksums2):
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
    >>> file1 = Chunksums.parse(io.StringIO(chunksum1))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum2))
    >>> pprint(find_dup(file1, file2))
    [[1.0, 10, '/A/4', 10, '/B/4'],
     [0.6666666666666666, 30, '/A/2', 30, '/B/2'],
     [0.5, 20, '/A/3', 20, '/B/3'],
     [0.4, 20, '/A/3', 30, '/B/2']]

    >>> chunksum_repeat = '''
    ... bee1  a  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... bee2  b  fck0sha2!aa:1,bb:2
    ... bee3  c  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... '''
    >>> file1 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> pprint(find_dup(file1, file2))
    [[1.0, 5, 'a', 5, 'c'], [0.75, 5, 'a', 3, 'b'], [0.75, 3, 'b', 5, 'c']]
    """
    dups = sorted(find_dup_files(chunksums1, chunksums2), reverse=True)
    return dups


def print_plain_report(dups, output_file):
    """
    >>> import io
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
    >>> file1 = Chunksums.parse(io.StringIO(chunksum1))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum2))
    >>> dups = find_dup(file1, file2)
    >>> print_plain_report(dups, sys.stdout)
    100.00%  /A/4 (10B)  /B/4 (10B)
     66.67%  /A/2 (30B)  /B/2 (30B)
     50.00%  /A/3 (20B)  /B/3 (20B)
     40.00%  /A/3 (20B)  /B/2 (30B)

    >>> chunksum_repeat = '''
    ... bee1  a  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... bee2  b  fck0sha2!aa:1,bb:2
    ... bee3  c  fck0sha2!aa:1,aa:1,aa:1,bb:2
    ... '''
    >>> file1 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> file2 = Chunksums.parse(io.StringIO(chunksum_repeat))
    >>> dups = find_dup(file1, file2)
    >>> print_plain_report(dups, sys.stdout)
    100.00%  a (5B)  c (5B)
     75.00%  a (5B)  b (3B)
     75.00%  b (3B)  c (5B)
    """
    for ratio, size1, file1, size2, file2 in dups:
        print(
            "{:>6.2f}%  {} ({}B)  {} ({}B)".format(
                ratio * 100,
                file1,
                size1,
                file2,
                size2,
            ),
            file=output_file,
            flush=True,
        )


command_desc = "Find (partial content) duplicate files."
command_long_desc = """
Examples:

  $ chunksum dir1/ -f chunksums.dir1
  $ chunksum dir2/ -f chunksums.dir2
  $ %(prog)s chunksums.dir1 chunksums.dir2
"""


def main():
    """
    >>> sys.argv = ['chunkdup']
    >>> try:
    ...     main()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ... except:
    ...     pass
    usage: chunkdup ...
    Find ...
    ...

    >>> import tempfile
    >>> f1 = tempfile.NamedTemporaryFile()
    >>> _ = f1.write(b'bee1  /A/1  fck0sha2!aa:10,bb:10')
    >>> f1.flush()
    >>> f2 = tempfile.NamedTemporaryFile()
    >>> _ = f2.write(b'bee2  /B/1  fck0sha2!cc:10,bb:10')
    >>> f2.flush()
    >>> sys.argv = ['chunkdup', f1.name, f2.name]
    >>> main()
     50.00%  /A/1 (20B)  /B/1 (20B)
    """

    # Don't turn these signal into exceptions, just die.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        description=command_desc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=command_long_desc,
    )

    parser.add_argument("chunksums1", nargs="?", help="path to chunksums")
    parser.add_argument("chunksums2", nargs="?", help="path to chunksums")
    args = parser.parse_args()

    if not args.chunksums1 or not args.chunksums2:
        parser.print_help()
        sys.exit()

    dups = find_dup(
        Chunksums.parse(open(args.chunksums1)),
        Chunksums.parse(open(args.chunksums2)),
    )
    print_plain_report(dups, sys.stdout)


if __name__ == "__main__":
    main()  # pragma: no cover
