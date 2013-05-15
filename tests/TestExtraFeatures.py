# This exercises some capabilities above and beyond
# the Promises/A+ test suite

from nose.tools import assert_equals
from aplus import Promise, listPromise, dictPromise
from threading import Thread

class DelayedFulfill(Thread):
    def __init__(self, d, p, v):
        self.delay = d
        self.promise = p
        self.value = v
        Thread.__init__(self)
    def run(self):
        import time
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

# Exceptions
def test_exceptions():
    def throws(v):
        assert False

    p1 = Promise()
    p1.addCallback(throws)
    p1.fulfill(5)

    p2 = Promise()
    p2.addErrback(throws)
    p2.reject("Error")

# WAIT
def test_wait_when():
    p1 = df(5, 0.1)
    assert p1.isPending()
    p1.wait()
    assert p1.isFulfilled()

def test_wait_if():
    p1 = Promise()
    p1.fulfill(5)
    p1.wait()
    assert p1.isFulfilled()

def test_wait_timeout():
    p1 = df(5, 3.0)
    assert p1.isPending()
    p1.wait(timeout=1.0)
    assert p1.isPending()
    p1.wait()
    assert p1.isFulfilled()

# GET
def test_get_when():
    p1 = df(5, 0.1)
    assert p1.isPending()
    v = p1.get()
    assert p1.isFulfilled()
    assert_equals(5, v)

def test_get_if():
    p1 = Promise()
    p1.fulfill(5)
    v = p1.get()
    assert p1.isFulfilled()
    assert_equals(5, v)

def test_get_timeout():
    p1 = df(5, 3.0)
    assert p1.isPending()
    try:
        v = p1.get(timeout=1.0)
        assert False
    except ValueError:
        pass # We expect this
    assert p1.isPending()
    v = p1.get()
    assert p1.isFulfilled()
    assert_equals(5, v)

# listPromise
def test_list_promise_when():
    p1 = Promise()
    p2 = Promise()
    pl = listPromise(p1, p2)
    assert p1.isPending()
    assert p2.isPending()
    assert pl.isPending()
    p1.fulfill(5)
    assert p1.isFulfilled()
    assert p2.isPending()
    assert pl.isPending()
    p2.fulfill(10)
    assert p1.isFulfilled()
    assert p2.isFulfilled()
    assert pl.isFulfilled()
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pl.value[0])
    assert_equals(10, pl.value[1])

def test_list_promise_if():
    p1 = Promise()
    p1.fulfill(5)
    p2 = Promise()
    p2.fulfill(10)
    pl = listPromise(p1, p2)
    assert p1.isFulfilled()
    assert p2.isFulfilled()
    assert pl.isFulfilled()
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pl.value[0])
    assert_equals(10, pl.value[1])
    
# dictPromise
def test_dict_promise_when():
    p1 = Promise()
    p2 = Promise()
    d = {"a": p1, "b": p2}
    pd = dictPromise(d)
    assert p1.isPending()
    assert p2.isPending()
    assert pd.isPending()
    p1.fulfill(5)
    assert p1.isFulfilled()
    assert p2.isPending()
    assert pd.isPending()
    p2.fulfill(10)
    assert p1.isFulfilled()
    assert p2.isFulfilled()
    assert pd.isFulfilled()
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pd.value["a"])
    assert_equals(10, pd.value["b"])

def test_dict_promise_if():
    p1 = Promise()
    p2 = Promise()
    d = {"a": p1, "b": p2}
    pd = dictPromise(d)
    assert p1.isPending()
    assert p2.isPending()
    assert pd.isPending()
    p1.fulfill(5)
    assert p1.isFulfilled()
    assert p2.isPending()
    assert pd.isPending()
    p2.fulfill(10)
    assert p1.isFulfilled()
    assert p2.isFulfilled()
    assert pd.isFulfilled()
    assert_equals(5, p1.value)
    assert_equals(10, p2.value)
    assert_equals(5, pd.value["a"])
    assert_equals(10, pd.value["b"])

