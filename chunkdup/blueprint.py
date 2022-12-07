from itertools import islice
from math import ceil

from .utils import iter_steps
from .utils import ruler


class BPItem:
    def __init__(self, dire, width1, width2, ellipsis=False, ignore=False):
        self.dire = dire
        self.ellipsis = ellipsis
        self.ignore = ignore
        self.width1 = width1
        self.width2 = width2
        width = max(self.width1, self.width2)
        self.padding1 = width - self.width1 if width > self.width1 else 0
        self.padding2 = width - self.width2 if width > self.width2 else 0
        self.width = width if not ellipsis else 0

    def __repr__(self):
        return f"{self.dire, '...' if self.ellipsis else self.width}"

    def symbols(self):
        if self.ellipsis:
            if not self.ignore:
                return "...", "..."
            return "", ""
        return (
            [self.dire.ca * self.width1] + [" " * self.padding1],
            [self.dire.cb * self.width2] + [" " * self.padding2],
        )


class Blueprint:
    """
    >>> from .dire import Dire
    >>> dire = Dire.get(['a', 'b'], ['a', 'c'], [20, 10], [20, 10])
    >>> list(Blueprint(20, 30, dire))
    [(<EQUAL 20>, 13), (<REPLACE 10>, 7)]
    >>> assert sum([i.width for i in Blueprint(20, 30, dire)]) == 20
    >>> dire = Dire.loads('R10 E20 R10 D5 I5 E10 R10 E5 R5 E10')
    >>> Blueprint(15, 90, dire).debug()
    ----5----1----5
    -===-- ==--=-==
    +===+ +==++=+==
    >>> Blueprint(8, 90, dire).debug()
    ----5---
    -=-...-=
    +=+...+=
    """

    def __init__(self, width, total, dire):
        self.width = width
        self.total = total
        self.dire = dire

        # init
        self.__ellipsis = (-1, -1)
        self._prepare_bp()
        self._prepare_adj()
        self._adjust()
        self._final_bp()

    def _prepare_bp(self):
        zoom = self.width / self.total
        self.blueprint = []
        for di in self.dire:
            w1 = ceil(di.a * zoom)
            w2 = ceil(di.b * zoom)
            self.blueprint.append([w1, w2])

    def _prepare_adj(self):
        self.adjust_space = []
        for w1, w2 in self.blueprint:
            maxw = max(w1, w2)
            self.adjust_space.append((maxw - 1) if maxw > 1 else 0)

    def _shrink(self, index, delta=1):
        w1, w2 = self.blueprint[index]
        if w1:
            w1 = w1 - 1
        if w2:
            w2 = w2 - 1
        self.blueprint[index] = [w1, w2]

    def _ellipsis(self):
        half = (self.width - len("...")) / 2
        left = ceil(half)
        right = int(half)
        self.__ellipsis = (left, len(self.blueprint) - right)

    def _adjust(self):
        real_width = sum(max(x1, x2) for x1, x2 in self.blueprint)
        if real_width == self.width:
            return

        shrink_target = real_width - self.width

        for index in islice(iter_steps(self.adjust_space), shrink_target):
            self._shrink(index)

        if shrink_target > sum(self.adjust_space):
            self._ellipsis()

    def _final_bp(self):
        self.items = []
        for i, (di, (width1, width2)) in enumerate(zip(self.dire, self.blueprint)):
            ellipsis = self.ellipsis[0] <= i < self.ellipsis[1]
            ignore = i == self.ellipsis[0]
            self.items.append(BPItem(di, width1, width2, ellipsis, ignore))

    @property
    def ellipsis(self):
        return self.__ellipsis

    def __iter__(self):
        return iter(self.items)

    def symbols(self):
        line1, line2 = [], []
        for i in self:
            a, b = i.symbols()
            line1.extend(a)
            line2.extend(b)
        return "".join(line1), "".join(line2)

    def debug(self):
        print(ruler(self.width))
        a, b = self.symbols()
        print(f"{a}\n{b}")
