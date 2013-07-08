# coding: utf-8
"""
    tests.test_utils
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from kurrent.utils import (
    PushableIterator, TransactionIterator, TransactionFailure
)

import pytest


class IteratorTest(object):
    iterator_cls = None

    def test_basic(self):
        i = self.iterator_cls([1, 2, 3])
        assert i is iter(i)
        assert next(i) == 1
        assert next(i) == 2
        assert next(i) == 3
        with pytest.raises(StopIteration):
            next(i)


class TestPushableIterator(IteratorTest):
    iterator_cls = PushableIterator

    def test_push(self):
        i = PushableIterator([])
        i.push(1)
        assert next(i) == 1

    def test_push_many(self):
        i = PushableIterator([])
        i.push_many([2, 1])
        assert list(i) == [1, 2]


class TestTransactionIterator(IteratorTest):
    iterator_cls = TransactionIterator

    def test_transaction(self):
        i = TransactionIterator([1, 2])
        with i.transaction() as transaction:
            assert transaction.items == []
            assert next(i) == 1
            assert transaction.items == [1]
            assert not transaction.committed
        assert transaction.committed
        assert next(i) == 2

        i = TransactionIterator([1, 2])
        with i.transaction() as transaction:
            assert transaction.items == []
            assert next(i) == 1
            assert transaction.items == [1]
            assert not transaction.committed
            raise TransactionFailure()
        assert not transaction.committed
        assert next(i) == 1

    def test_transaction_with_failure_exc(self):
        i = TransactionIterator([1, 2])
        with i.transaction(failure_exc=RuntimeError):
            assert next(i) == 1
            raise RuntimeError()
        assert next(i) == 1

        i = TransactionIterator([1, 2])
        with pytest.raises(TransactionFailure):
            with i.transaction(failure_exc=RuntimeError):
                assert next(i) == 1
                raise TransactionFailure()

    def test_transaction_with_clean(self):
        i = TransactionIterator([1, 2])
        with i.transaction(clean=lambda x: x + 1):
            assert next(i) == 1
        assert next(i) == 2

        i = TransactionIterator([1, 2, 3])
        with i.transaction(clean=lambda x: x + 1):
            assert next(i) == 1
            raise TransactionFailure()
        assert list(i) == [2, 2, 3]

    def test_lookahead(self):
        i = TransactionIterator([1, 2])
        assert i.lookahead() == [1]
        assert next(i) == 1

        i = TransactionIterator([1, 2])
        assert i.lookahead(n=2) == [1, 2]
        assert i.lookahead(n=3) == [1, 2]

    def test_lookahead_with_silent(self):
        i = TransactionIterator([1])
        assert i.lookahead(silent=False) == [1]
        with pytest.raises(StopIteration):
            i.lookahead(n=2, silent=False)

    def test_replace(self):
        i = TransactionIterator([1])
        i.replace(2)
        assert next(i) == 2
        with pytest.raises(StopIteration):
            next(i)
