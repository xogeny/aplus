# This exercises some capabilities above and beyond
# the Promises/A+ test suite

from nose.tools import assert_equals, assert_is_instance, assert_raises
from aplus import Promise, listPromise, dictPromise, spawn
from threading import Thread
import time


def assert_exception(exception, expected_exception_cls, expected_message):
    assert_is_instance(exception, expected_exception_cls)
    assert_equals(str(exception), expected_message)


class DelayedFulfill(Thread):
    def __init__(self, d, p, v):
        self.delay = d
        self.promise = p
        self.value = v
        Thread.__init__(self)

    def run(self):
        time.sleep(self.delay)
        self.promise.fulfill(self.value)


class DelayedRejection(Thread):
    def __init__(self, d, p, r):
        self.delay = d
        self.promise = p
        self.reason = r
        Thread.__init__(self)

    def run(self):
        time.sleep(self.delay)
        self.promise.reject(self.reason)


class FakePromise():
    def then(self, s=None, f=None):
        raise Exception("FakePromise raises in 'then'")


def df(value, dtime):
    p = Promise()
    t = DelayedFulfill(dtime, p, value)
    t.start()

    return p


def dr(reason, dtime):
    p = Promise()
    t = DelayedRejection(dtime, p, reason)
    t.start()

    return p


# Static methods
def test_fulfilled():
    p = Promise.fulfilled(4)
    assert p.isFulfilled
    assert_equals(p.value, 4)


def test_rejected():
    p = Promise.rejected(Exception("Static rejected"))
    assert p.isRejected
    assert_exception(p.reason, Exception, "Static rejected")


# Fulfill
def test_fulfill_self():
    p = Promise()
    assert_raises(TypeError, p.fulfill, p)


# Exceptions
def test_exceptions():
    def throws(v):
        assert False

    p1 = Promise()
    p1.addCallback(throws)
    p1.fulfill(5)

    p2 = Promise()
    p2.addErrback(throws)
    p2.reject(Exception())

    assert_raises(Exception, p2.get)


def test_fake_promise():
    p = Promise()
    p.fulfill(FakePromise())
    assert p.isRejected
    assert_exception(p.reason, Exception, "FakePromise raises in 'then'")


# WAIT
def test_wait_when():
    p1 = df(5, 0.1)
    assert p1.isPending
    p1.wait()
    assert p1.isFulfilled


def test_wait_if():
    p1 = Promise()
    p1.fulfill(5)
    p1.wait()
    assert p1.isFulfilled


def test_wait_timeout():
    p1 = df(5, 3.0)
    assert p1.isPending
    p1.wait(timeout=1.0)
    assert p1.isPending
    p1.wait()
    assert p1.isFulfilled


# GET
def test_get_when():
    p1 = df(5, 0.1)
    assert p1.isPending
    v = p1.get()
    assert p1.isFulfilled
    assert_equals(5, v)


def test_get_if():
    p1 = Promise()
    p1.fulfill(5)
    v = p1.get()
    assert p1.isFulfilled
    assert_equals(5, v)


def test_get_timeout():
    p1 = df(5, 3.0)
    assert p1.isPending
    try:
        v = p1.get(timeout=1.0)
        assert False
    except ValueError:
        pass  # We expect this
    assert p1.isPending
    v = p1.get()
    assert p1.isFulfilled
    assert_equals(5, v)


# listPromise
def test_list_promise_when():
    p1 = Promise()
    p2 = Promise()
    pl = listPromise(p1, p2)
    assert p1.isPending
    assert p2.isPending
    assert pl.isPending
    p1.fulfill(5)
    assert p1.isFulfilled
    assert p2.isPending
    assert pl.isPending
    p2.fulfill(10)
    assert p1.isFulfilled
    assert p2.isFulfilled
    assert pl.isFulfilled
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pl.value[0])
    assert_equals(10, pl.value[1])


def test_list_promise_if():
    p1 = Promise()
    p2 = Promise()
    pd1 = listPromise([p1, p2])
    pd2 = listPromise([p1])
    pd3 = listPromise([])
    assert p1.isPending
    assert p2.isPending
    assert pd1.isPending
    assert pd2.isPending
    assert pd3.isFulfilled
    p1.fulfill(5)
    assert p1.isFulfilled
    assert p2.isPending
    assert pd1.isPending
    assert pd2.isFulfilled
    p2.fulfill(10)
    assert p1.isFulfilled
    assert p2.isFulfilled
    assert pd1.isFulfilled
    assert pd2.isFulfilled
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pd1.value[0])
    assert_equals(5, pd2.value[0])
    assert_equals(10, pd1.value[1])
    assert_equals([], pd3.value)


# dictPromise
def test_dict_promise_when():
    p1 = Promise()
    p2 = Promise()
    d = {"a": p1, "b": p2}
    pd1 = dictPromise(d)
    pd2 = dictPromise({"a": p1})
    pd3 = dictPromise({})
    assert p1.isPending
    assert p2.isPending
    assert pd1.isPending
    assert pd2.isPending
    assert pd3.isFulfilled
    p1.fulfill(5)
    assert p1.isFulfilled
    assert p2.isPending
    assert pd1.isPending
    assert pd2.isFulfilled
    p2.fulfill(10)
    assert p1.isFulfilled
    assert p2.isFulfilled
    assert pd1.isFulfilled
    assert pd2.isFulfilled
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pd1.value["a"])
    assert_equals(5, pd2.value["a"])
    assert_equals(10, pd1.value["b"])
    assert_equals({}, pd3.value)


def test_dict_promise_if():
    p1 = Promise()
    p2 = Promise()
    d = {"a": p1, "b": p2}
    pd = dictPromise(d)
    assert p1.isPending
    assert p2.isPending
    assert pd.isPending
    p1.fulfill(5)
    assert p1.isFulfilled
    assert p2.isPending
    assert pd.isPending
    p2.fulfill(10)
    assert p1.isFulfilled
    assert p2.isFulfilled
    assert pd.isFulfilled
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pd.value["a"])
    assert_equals(10, pd.value["b"])


def test_spawn():
    def slow_or_blocking(x):
        print("evaluation started")
        time.sleep(2.0)
        return x * x

    def slow_or_blocking_error(x):
        print("evaluation started")
        time.sleep(2.0)
        raise ValueError("Something went wrong")

    p1 = spawn(lambda: slow_or_blocking(5))
    p2 = spawn(lambda: slow_or_blocking_error(5))

    assert p1.isPending
    assert p2.isPending

    try:
        import gevent

        gevent.sleep(2.5)
    except ImportError:
        time.sleep(2.5)

    assert p1.isFulfilled
    assert p2.isRejected
    assert_equals(25, p1.value)
    assert isinstance(p2.reason, ValueError)
    assert_equals("Something went wrong", str(p2.reason))


def test_done():
    counter = [0]

    def inc(_):
        counter[0] += 1

    def dec(_):
        counter[0] -= 1

    p = Promise()
    p.done(inc, dec)
    p.fulfill(4)

    assert_equals(counter[0], 1)

    p = Promise()
    p.done(inc, dec)
    p.done(inc, dec)
    p.reject(Exception())

    assert_equals(counter[0], -1)


def test_done_all():
    counter = [0]

    def inc(_):
        counter[0] += 1

    def dec(_):
        counter[0] -= 1

    p = Promise()
    p.done_all()
    p.done_all((inc, dec))
    p.done_all([
        (inc, dec),
        (inc, dec),
        {'success': inc, 'failure': dec},
    ])
    p.fulfill(4)

    assert_equals(counter[0], 4)

    p = Promise()
    p.done_all()
    p.done_all((inc, dec))
    p.done_all([
        (inc, dec),
        {'success': inc, 'failure': dec},
    ])
    p.reject(Exception())

    assert_equals(counter[0], 1)


def test_then_all():
    p = Promise()

    handlers = [
        ((lambda x: x * x), (lambda r: 1)),
        {'success': (lambda x: x + x), 'failure': (lambda r: 2)},
    ]

    results = p.then_all() + p.then_all(((lambda x: x * x), (lambda r: 1))) + p.then_all(handlers)

    p.fulfill(4)

    assert_equals(results[0].value, 16)
    assert_equals(results[1].value, 16)
    assert_equals(results[2].value, 8)

    p = Promise()

    handlers = [
        ((lambda x: x * x), (lambda r: 1)),
        {'success': (lambda x: x + x), 'failure': (lambda r: 2)},
    ]

    results = p.then_all() + p.then_all(((lambda x: x * x), (lambda r: 1))) + p.then_all(handlers)

    p.reject(Exception())

    assert_equals(results[0].value, 1)
    assert_equals(results[1].value, 1)
    assert_equals(results[2].value, 2)
