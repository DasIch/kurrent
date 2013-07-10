# coding: utf-8
"""
    kurrent.utils
    ~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from contextlib import contextmanager

from ._compat import implements_iterator


@implements_iterator
class PushableIterator(object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)
        self.remaining = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining:
            return self.remaining.pop()
        return next(self._iterator)

    def push(self, item):
        self.remaining.append(item)

    def push_many(self, items):
        for item in items:
            self.push(item)


class TransactionFailure(Exception):
    pass


class Transaction(object):
    def __init__(self):
        self.items = []
        self.remaining = []
        self.committed = False

    def record(self, item):
        self.items.append(item)

    def commit(self, pushable_iterator):
        for item, _ in reversed(self.remaining):
            pushable_iterator.push(item)
        self.committed = True

    def rollback(self, pushable_iterator, clean=None):
        for item in reversed(self.items):
            if clean is not None:
                item = clean(item)
            pushable_iterator.push(item)


@implements_iterator
class TransactionIterator(object):
    default_failure_exc = TransactionFailure

    def __init__(self, iterable, pushable_iterator_cls=PushableIterator):
        self._iterator = pushable_iterator_cls(iterable)

        self.transactions = []
        self.remaining = []

    def __iter__(self):
        return self

    def __next__(self):
        pushed = False
        if self.remaining:
            rv = self.remaining.pop()
        elif self.transactions and self.transactions[-1].remaining:
            rv, pushed = self.transactions[-1].remaining.pop()
        else:
            rv = next(self._iterator)
        if self.transactions and not pushed:
            self.transactions[-1].record(rv)
        return rv

    @contextmanager
    def transaction(self, failure_exc=None, clean=None):
        if failure_exc is None:
            failure_exc = self.default_failure_exc
        transaction = Transaction()
        self.transactions.append(transaction)
        try:
            yield transaction
        except failure_exc:
            transaction.rollback(self._iterator, clean=clean)
        else:
            transaction.commit(self._iterator)
        finally:
            assert self.transactions.pop() is transaction

    def lookahead(self, n=1, silent=True):
        with self.transaction():
            rv = []
            for _ in range(n):
                try:
                    rv.append(next(self))
                except StopIteration:
                    if silent:
                        break
                    else:
                        raise
            raise self.default_failure_exc()
        return rv

    def push(self, item):
        if self.transactions:
            self.transactions[-1].remaining.append((item, True))
        else:
            self.remaining.append(item)
