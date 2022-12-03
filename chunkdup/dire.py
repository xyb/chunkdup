from difflib import SequenceMatcher
from enum import Enum


class DiffType(Enum):
    DELETE = 1
    INSERT = 2
    REPLACE = 3
    EQUAL = 4


TAG_TYPE = {
    "delete": DiffType.DELETE,
    "insert": DiffType.INSERT,
    "replace": DiffType.REPLACE,
    "equal": DiffType.EQUAL,
}

A_VALUABLE = {
    "delete": True,
    "insert": False,
    "replace": True,
    "equal": True,
}
B_VALUABLE = {
    "delete": False,
    "insert": True,
    "replace": True,
    "equal": True,
}

TYPE_SYMBLES = {
    DiffType.DELETE: ("-", " "),
    DiffType.INSERT: (" ", "+"),
    DiffType.REPLACE: ("-", "+"),
    DiffType.EQUAL: ("=", "="),
}


class DiffItem:
    def __init__(self, type, a_value, b_value):
        self.type = type
        self.a = a_value
        self.b = b_value
        self.value = self.a if A_VALUABLE[type.name.lower()] else self.b
        self.ca, self.cb = TYPE_SYMBLES[type]

    def __repr__(self):
        """
        >>> DiffItem(DiffType.DELETE, 20, 20)
        <DELETE 20>
        """
        return f"<{self.type.name} {self.value}>"

    def __iter__(self):
        """
        >>> di = DiffItem(DiffType.DELETE, [10, 10], [10, 10])
        >>> list(di)
        [10, 10]
        """
        return iter(self.value)


class Dire:
    def __init__(self, seq):
        self.seq = seq

    @classmethod
    def get(cls, a, b, a_value, b_value, reduce=True):
        """
        >>> Dire.get(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'a'],
        ...          [10, 10, 10, 10], [10, 10, 10, 10], reduce=False)
        <Dire [<EQUAL [10, 10, 10, 10]>]>
        >>> Dire.get(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'b'],
        ...          [10, 10, 10, 10], [10, 10, 10, 10])
        <Dire [<EQUAL 30>, <REPLACE 10>]>
        >>> _.rows()
        [['=', 30, '=', 30], ['-', 10, '+', 10]]
        >>> Dire.get(['a', 'a', 'a', 'a'], ['c', 'a', 'a'],
        ...          [10, 10, 10, 10], [20, 10, 10])
        <Dire [<INSERT 20>, <EQUAL 20>, <DELETE 20>]>
        >>> _.rows()
        [[' ', 0, '+', 20], ['=', 20, '=', 20], ['-', 20, ' ', 0]]
        """
        seq = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b).get_opcodes():
            av, bv = (a_value[i1:i2], b_value[j1:j2])
            if reduce:
                av = sum(av)
                bv = sum(bv)
            seq.append(DiffItem(TAG_TYPE[tag], av, bv))
        return cls(seq)

    def __repr__(self):
        return f"<Dire {self.seq}>"

    def __iter__(self):
        yield from self.seq

    def dumps(self):
        """
        only work for reduced value.

        >>> Dire.get(['a', 'b', 'c', 'd', 'e'], ['i', 'a', 'd', 'r'],
        ...          [20, 10, 30, 40, 50], [10, 20, 40, 50]).dumps()
        'I10 E20 D40 E40 R50'
        """
        result = []
        for di in self:
            result.append(f"{di.type.name[0]}{di.value}")
        return " ".join(result)

    @classmethod
    def loads(cls, s):
        """
        only work for reduced value.

        >>> dire = Dire.loads('I10 E20 D40 E40 R50')
        >>> str(dire)
        '<Dire [<INSERT 10>, <EQUAL 20>, <DELETE 40>, <EQUAL 40>, <REPLACE 50>]>'
        >>> di = dire.seq[0]
        >>> di.a, di.b, di.value
        (0, 10, 10)
        """
        types = {n[0].upper(): t for n, t in TAG_TYPE.items()}
        seq = []
        for i in s.split(" "):
            name = i[0]
            value = int(i[1:])
            type = types[name]
            a = value if A_VALUABLE[type.name.lower()] else 0
            b = value if B_VALUABLE[type.name.lower()] else 0
            seq.append(DiffItem(type, a, b))
        return cls(seq)

    def rows(self):
        return [[x.ca, x.a, x.cb, x.b] for x in self]
