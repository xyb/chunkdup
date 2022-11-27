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
