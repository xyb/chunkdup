from difflib import SequenceMatcher


DIFF_ASCII = {
    "equal": ["=", "="],
    "replace": ["-", "+"],
    "delete": ["-", " "],
    "insert": [" ", "+"],
}


def find_diff(chunks1, chunks2, sizes1, sizes2):
    """
    >>> sizes = {'a': 10, 'b': 10, 'c': 20}
    >>> find_diff(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'a'],
    ...           [10, 10, 10, 10], [10, 10, 10, 10])
    (40, 1.0, [['=', '=', 40, 40]])
    >>> find_diff(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'b'],
    ...           [10, 10, 10, 10], [10, 10, 10, 10])
    (40, 0.75, [['=', '=', 30, 30], ['-', '+', 10, 10]])
    >>> find_diff(['a', 'a', 'a', 'a'], ['c', 'a', 'a'],
    ...           [10, 10, 10, 10], [10, 20, 10])
    (60, 0.5, [[' ', '+', 0, 10], ['=', '=', 20, 30], ['-', ' ', 20, 0]])
    """
    diff = []
    total = 0
    matches = 0
    s = SequenceMatcher(a=chunks1, b=chunks2)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        size1 = sum([s for s in sizes1[i1:i2]])
        size2 = sum([s for s in sizes2[j1:j2]])
        total += max(size1, size2)
        if tag == "equal":
            matches += size1
        diff.append(DIFF_ASCII[tag] + [size1, size2])

    ratio = (2 * matches) / (sum(sizes1) + sum(sizes2))

    return total, ratio, diff
