from copy import copy
from functools import wraps


def best_width(num):
    limit = 4
    s = f"{num:4.2f}"
    if len(s) > limit:
        s = s[:limit]
    if s[-1] == ".":
        s = s[:-1]
    return s


def humanize(num):
    """
    >>> humanize(0)
    '0B'
    >>> humanize(1023)
    '1023B'
    >>> humanize(1024)
    '1.00KB'
    >>> humanize(10240)
    '10.0KB'
    >>> humanize(102400)
    '100KB'
    >>> humanize(1024000)
    '1000KB'
    >>> humanize(987654321)
    '941MB'
    >>> humanize(987654321 * 100_000)
    '89.8TB'
    >>> humanize(987654321 * 1000_000 ** 3)
    '836575.8YB'
    """
    if num < 1024:
        return f"{num}B"
    for unit in ["K", "M", "G", "T", "P", "E", "Z"]:
        num /= 1024.0
        if abs(num) < 1024.0:
            return f"{best_width(num)!s}{unit}B"
    return f"{num:.1f}YB"


def get_order_indexes(list):
    """
    >>> get_order_indexes([1, 2, 3])
    [2, 1, 0]
    >>> get_order_indexes([1, 2, 1])
    [1, 0, 2]
    """
    return [
        i
        for _, i in sorted(
            [[v, i] for i, v in enumerate(list)],
            reverse=True,
            key=lambda x: x[0],
        )
    ]


def iter_steps(stairs):
    """
    climb all the stairs with minimal energy

         2            2
       1 2 3   sort   2 1 3     iter  from bottom to top
    --------- =====> --------- =====> [2, 1, 3, 2]
     0 1 2 3          2 1 3 0

    >>> list(iter_steps([0, 1, 2, 1]))
    [2, 1, 3, 2]
    >>> list(iter_steps([1, 2, 3]))
    [2, 1, 0, 2, 1, 2]
    >>> list(iter_steps([3, 2, 1]))
    [0, 1, 2, 0, 1, 0]
    >>> list(iter_steps([]))
    []
    """

    if not stairs:
        return

    steps = copy(stairs)
    order = get_order_indexes(steps)

    while steps[order[0]] > 0:
        for i in order:
            if steps[i] == 0:
                break
            steps[i] -= 1
            yield i


def ruler(length):
    """ascii ruler

    >>> print(ruler(60))
    ----5----1----5----2----5----3----5----4----5----5----5----6
    >>> print(ruler(142)[-50:])
    --5----0----5----1----5----2----5----3----5----4--
    """
    nodes = (length // 10) + 1
    return "".join(f"----5----{(i + 1) % 10}" for i in range(nodes))[:length]


def keep_once(iter, find):
    """
    >>> list(keep_once([1, 2, 2, 3], lambda x: x == 2))
    [1, 2, 3]
    """
    match = False
    for i in iter:
        if match:
            if not find(i):
                match = False
                yield i
            continue
        if find(i):
            yield i
            match = True
        else:
            yield i


def memoized_property(fget):
    """
    >>> class C(object):
    ...     load_name_count = 0
    ...     @memoized_property
    ...     def name(self):
    ...         "name's docstring"
    ...         self.load_name_count += 1
    ...         return "the name"
    >>> c = C()
    >>> c.load_name_count
    0
    >>> c.name
    'the name'
    >>> c.load_name_count
    1
    >>> c.name
    'the name'
    >>> c.load_name_count
    1
    """
    attr_name = f"_{fget.__name__}"

    @wraps(fget)
    def fget_memoized(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fget(self))
        return getattr(self, attr_name)

    return property(fget_memoized)
