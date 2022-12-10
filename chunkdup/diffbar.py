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
        self.compare_result = compare_result
        self.options = options

    def __str__(self):
        return self.format()

    def get_formatter(self):
        cls = BarFormatter.get(self.options.type)
        return cls(self)

    def format(self):
        return self.get_formatter().format()

    def format_bar(self):
        return self.get_formatter().format_bar()


class BarOptions:
    def __init__(self, width=40, color=True, type="default"):
        self.width = width
        self.color = color
        self.type = type


class BarFormatter:
    def __init__(
        self,
        bar,
    ):
        self.bar = bar
        self.width = bar.options.width
        self.color = bar.options.color
        self.blueprint = bar.compare_result.get_blueprint(self.width)
        self.ratio = bar.compare_result.ratio
        self.file1size = bar.compare_result.file1.size
        self.file2size = bar.compare_result.file2.size

    @classmethod
    def get(cls, type):
        """
        >>> BarFormatter.get('oneline')
        <class 'chunkdup.diffbar.OneLineFormatter'>
        >>> try:
        ...     BarFormatter.get('nothing')
        ... except:
        ...     print('error')
        error
        """
        cls = FORMATTERS.get(type)
        if cls:
            return cls
        else:
            raise Exception(f"no such type formatter: {type}")


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
        >>> s = '''bee1  ./a  fck0sha2!aa:10,bb:10,cc:5,dd:5,f1:10
        ... bee2  ./b  fck0sha2!bb:10,f2:5,cc:5,f3:5,dd:5,f4:10'''
        >>> from .differ import CompareResult
        >>> cr = CompareResult.loads(s)
        >>> bo = BarOptions(width=20, color=False, type='oneline')
        >>> fmt = OneLineFormatter(cr.get_bar(bo))
        >>> print(fmt.format())
         50.00%  ▀40B  ▄40B  ▀▀▀▀▒▒▒▒▄▄▒▒▄▄▒▒████
        >>> bo = BarOptions(width=20, color=True, type='oneline')
        >>> fmt = OneLineFormatter(cr.get_bar(bo))
        >>> print(fmt.format())
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
         50.00%  ▀40B  ▄40B  ...
        """
        return f"{self.format_prefix()}  {self.format_bar()}"

    def format_bar(self):
        line1, line2 = self.blueprint.lines()
        pairs = list("".join(x) for x in zip("".join(line1), "".join(line2)))
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
        >>> s = '''bee1  ./a  fck0sha2!aa:10,bb:10,cc:5,dd:5,f1:10
        ... bee2  ./b  fck0sha2!bb:10,f2:5,cc:5,f3:5,dd:5,f4:10'''
        >>> from .differ import CompareResult
        >>> cr = CompareResult.loads(s)
        >>> bo = BarOptions(width=20, color=False, type='twolines')
        >>> fmt = TwoLinesFormatter(cr.get_bar(bo))
        >>> print(fmt.format())
         50.00%     40B  ----====  ==  ==----
                    40B      ====++==++==++++
        >>> bo = BarOptions(width=20, color=True, type='twolines')
        >>> fmt = TwoLinesFormatter(cr.get_bar(bo))
        >>> print(fmt.format())
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
         50.00%     40B  ...
                    40B  ...
        """

        def colorful(line):
            return [self.colors[s[0]] + s + END for s in line]

        line1, line2 = self.blueprint.lines()

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
