from .dire import Dire


def find_diff(chunks1, chunks2, sizes1, sizes2):
    """
    >>> sizes = {'a': 10, 'b': 10, 'c': 20}
    >>> find_diff(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'a'],
    ...           [10, 10, 10, 10], [10, 10, 10, 10])
    (40, 1.0, <Dire [<EQUAL 40>]>)
    >>> find_diff(['a', 'a', 'a', 'a'], ['a', 'a', 'a', 'b'],
    ...           [10, 10, 10, 10], [10, 10, 10, 10])
    (40, 0.75, <Dire [<EQUAL 30>, <REPLACE 10>]>)
    >>> find_diff(['a', 'a', 'a', 'a'], ['c', 'a', 'a'],
    ...           [10, 10, 10, 10], [20, 10, 10])
    (60, 0.5, <Dire [<INSERT 20>, <EQUAL 20>, <DELETE 20>]>)
    """
    total = 0
    matches = 0
    dire = Dire.get(chunks1, chunks2, sizes1, sizes2)
    total = sum([x.value for x in dire])
    matches = sum([x.value for x in dire if x.type.name == "EQUAL"])
    ratio = (2 * matches) / (sum(sizes1) + sum(sizes2))

    return total, ratio, dire
