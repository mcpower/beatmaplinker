from functools import reduce


def remove_dups(iterable):
    """Creates a generator to get unique elements from iterable.

    Items in iterable must be hashable.
    """
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


def mapf(func):
    """Creates a function to map func over an iterable.

    mapf(func)(iter) is equivalent to map(func, iter).
    """
    return lambda a: map(func, a)


def truthies(iterable):
    """Helper function for applying filter(None) over an iterable."""
    return filter(None, iterable)


def compose(*funcs):
    """Composes many one-argument functions together to one.

    Functions are applied the order they are defined.
    For example, compose(f, g)(x) is equivalent to g(f(x)).
    """
    return lambda a: reduce(lambda x, f: f(x), funcs, a)
