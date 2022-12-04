from itertools import islice
from math import ceil

from .utils import iter_steps
from .utils import ruler


class Blueprint:
    def __init__(self, width, total, dire):
        self.width = width
        self.total = total
        self.dire = dire

    def _prepare_bp(self):
        zoom = self.width / self.total
        blueprint = []
        for di in self.dire:
            w1 = ceil(di.a * zoom)
            w2 = ceil(di.b * zoom)
            blueprint.append([w1, w2])
        return blueprint

    def _prepare_adj(self, blueprint):
        adjust_space = []
        for w1, w2 in blueprint:
            maxw = max(w1, w2)
            adjust_space.append((maxw - 1) if maxw > 1 else 0)
        return adjust_space

    def _shrink(self, blueprint, index, delta=1):
        w1, w2 = blueprint[index]
        if w1:
            w1 = w1 - 1
        if w2:
            w2 = w2 - 1
        blueprint[index] = [w1, w2]

    def _ellipsis(self, blueprint):
        half = (self.width - len("...")) / 2
        left = ceil(half)
        right = int(half)
        for i in blueprint[left:-right]:
            i[0] = -1
            i[1] = -1

    def _adjust(self, blueprint, adjust_space):
        # fit for the char grid
        real_width = sum(max(x1, x2) for x1, x2 in blueprint)
        if real_width == self.width:
            return blueprint

        shrink_target = real_width - self.width

        for index in islice(iter_steps(adjust_space), shrink_target):
            self._shrink(blueprint, index)

        if shrink_target > sum(adjust_space):
            self._ellipsis(blueprint)

        return blueprint

    def _final_bp(self, blueprint):
        def char_bar(char, width, line):
            if width:
                line.append(char * width)

        def padding_bar(width, max_width, line):
            padding = max_width - width
            if padding:
                line.append(" " * padding)

        line1 = []
        line2 = []
        for di, (width1, width2) in zip(self.dire, blueprint):
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

    def lines(self):
        """
        >>> from .dire import Dire
        >>> dire = Dire.get(['a', 'b'], ['a', 'c'], [20, 10], [20, 10])
        >>> Blueprint(20, 30, dire).lines()
        (['=============', '-------'], ['=============', '+++++++'])
        >>> Blueprint.debug_lines(Blueprint(20, 30, dire).lines(), 20)
        ----5----1----5----2
        =============-------
        =============+++++++
        >>> dire = Dire.loads('R10 E20 R10 D5 I5 E10 R10 E5 R5 E10')
        >>> Blueprint.debug_lines(Blueprint(15, 90, dire).lines(), 15)
        ----5----1----5
        -===-- ==--=-==
        +===+ +==++=+==
        >>> Blueprint.debug_lines(Blueprint(8, 90, dire).lines(), 8)
        ----5---
        -=-...-=
        +=+...+=
        """

        blueprint = self._prepare_bp()
        adjust_space = self._prepare_adj(blueprint)
        blueprint = self._adjust(blueprint, adjust_space)
        return self._final_bp(blueprint)

    @classmethod
    def debug_lines(cls, lines, width):
        print(ruler(width))
        print("\n".join(["".join(i) for i in lines]))
