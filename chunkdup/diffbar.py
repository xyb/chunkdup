from itertools import groupby

from .utils import humanize

GREY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY_BG = "\033[100m"
RED_BG = "\033[101m"
GREEN_BG = "\033[102m"
YELLOW_BG = "\033[103m"
END = "\033[0m"


class Bar:
    def __init__(self, compare_result, options):
        self.cr = compare_result
        self.options = options

    def __str__(self):
        return self.format()

    def get_formatter(self):
        type = self.options.get("type", "default")
        cls = FORMATTERS.get(type)
        if cls:
            return cls(self.cr, self)

    def format(self):
        return self.get_formatter().format()

    def format_bar(self):
        return self.get_formatter().format_bar()


class BarFormatter:
    def __init__(
        self,
        compare_result,
        bar,
        ratio=None,
        width=None,
        line1=None,
        line2=None,
        file1size=None,
        file2size=None,
        color=None,
    ):
        self.cr = compare_result
        self.bar = bar
        if width is not None:
            self.width = width
        else:
            self.width = bar.options["width"]
        if line1 is not None and line2 is not None:
            self.line1, self.line2 = line1, line2
        else:
            # lazy load?
            self.line1, self.line2 = self.cr.get_blueprint(self.width).lines()
        if ratio is not None:
            self.ratio = ratio
        else:
            self.ratio = self.cr.ratio
        self.file1size = file1size or self.cr.file1.size
        self.file2size = file2size or self.cr.file2.size
        if color is not None:
            self.color = color
        else:
            self.color = self.bar.options["color"]


class OneLineFormatter(BarFormatter):
    chars = {
        "==": "▒",
        "-+": "█",
        "- ": "▀",
        " +": "▄",
        "..": ".",
    }
    colors = {
        "==": ["▒", GREY + GREY_BG],  # fg: grey, bg: grey
        "-+": ["▀", RED + GREEN_BG],  # fg/top half: red, bg/bottom half: green
        "- ": ["▀", RED + YELLOW_BG],  # fg: red, bg: yellow
        " +": ["▀", YELLOW + GREEN_BG],  # fg: yellow, bg: green
        "..": [".", GREY_BG],
    }

    def format(self):
        """
        >>> partial = lambda *args, **kwargs: OneLineFormatter(
        ...           None, None, *args, **kwargs).format()
        >>> line1 = ['-----', '==', '     ', '===']
        >>> line2 = ['++', '   ', '==', '+++++', '===']
        >>> partial(0.6, 40, line1, line2, 100, 70, color=False)
        ' 60.00%  ▀100B  ▄70B  ██▀▀▀▒▒▄▄▄▄▄▒▒▒'
        >>> partial(0.6, 40, line1, line2, 100, 70, color=True)
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        ' 60.00%  ▀100B  ▄70B  ...'
        """
        return f"{self.format_prefix()}  {self.format_bar()}"

    def format_bar(self):
        pairs = list("".join(x) for x in zip("".join(self.line1), "".join(self.line2)))
        bar = []
        for key, group in groupby(pairs):
            width = len(list(group))
            if self.color:
                char, color_ = self.colors[key]
                item = color_ + char * width + END
            else:
                item = self.chars[key] * width
            bar.append(item)

        return "".join(bar)

    def format_prefix(self):
        return "{:>6.2f}%  ▀{}  ▄{}".format(
            self.ratio * 100,
            humanize(self.file1size),
            humanize(self.file2size),
        )


class TwoLinesFormatter(BarFormatter):
    colors = {
        "=": GREY_BG,
        "-": RED_BG,
        "+": GREEN_BG,
        " ": YELLOW_BG,
        ".": "",
    }

    def format(self):
        """
        >>> partial = lambda *args, **kwargs: TwoLinesFormatter(
        ...           None, None, *args, **kwargs).format()
        >>> line1 = ['-----', '==', '-----', '===']
        >>> line2 = ['++', '   ', '==', '+', '    ', '===']
        >>> print(partial(0.5, 40, line1, line2, 100, 70, color=False))
         50.00%    100B  -----==-----===
                    70B  ++   ==+    ===
        >>> print(partial(0.5, 40, line1, line2, 100, 70, color=True))
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
         50.00%    100B  ...
                    70B  ...
        """

        def colorful(line):
            return [self.colors[s[0]] + s + END for s in line]

        line1, line2 = self.line1, self.line2

        if self.color:
            line1 = colorful(line1)
            line2 = colorful(line2)

        percent = f"{self.ratio * 100:>6.2f}%"
        lines = []
        for pre, size, line in (
            (percent, self.file1size, line1),
            ("", self.file2size, line2),
        ):
            lines.append(
                "{:>7s}  {:>6}  {}".format(
                    pre,
                    humanize(size),
                    "".join(line),
                ),
            )
        return "\n".join(lines)


FORMATTERS = {
    "default": OneLineFormatter,
    "oneline": OneLineFormatter,
    "twolines": TwoLinesFormatter,
}
