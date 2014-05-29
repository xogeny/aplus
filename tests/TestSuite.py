# This is my attempt to translate the
# Javascript promises-aplus test suite
# (https://github.com/promises-aplus/promises-tests)
# into Python and then apply it to the
# promises library I've created.

from nose.tools import assert_equals
from aplus import Promise

class Counter:
    """
    A helper class with some side effects
    we can test.
    """
    def __init__(self):
        self.count = 0
    def tick(self):
        self.count = self.count+1
    def value(self):
        return self.count

def test_3_2_1():
    """
    Test that the arguments to 'then' are optional.
    """

    p1 = Promise()
    p2 = p1.then()
    p3 = Promise()
    p4 = p3.then()
    p1.fulfill(5)
    p3.reject("How dare you!")

def test_3_2_1_1():
    """
    That that the first argument to 'then' is ignored if it
    is not a function.
    """

    def testNonFunction(nonFunction, results):
        def foo(results, k, r):
            results[k] = r
        p1 = Promise()
        p2 = p1.then(nonFunction, lambda r: foo(results, str(nonFunction), r))
        p1.reject("Error: "+str(nonFunction))

    results = {}
    nonFunctions = [None, False, 5, {}, []]
    for v in nonFunctions:
        testNonFunction(v, results);

    for v in nonFunctions:
        assert_equals(results[str(v)], "Error: "+str(v))

def test_3_2_1_2():
    """
    That that the second argument to 'then' is ignored if it
    is not a function.
    """

    def testNonFunction(nonFunction, results):
        def foo(results, k, r):
            results[k] = r
        p1 = Promise()
        p2 = p1.then(lambda r: foo(results, str(nonFunction), r), nonFunction)
        p1.fulfill("Error: "+str(nonFunction))

    results = {}
    nonFunctions = [None, False, 5, {}, []]
    for v in nonFunctions:
        testNonFunction(v, results);

    for v in nonFunctions:
        assert_equals(results[str(v)], "Error: "+str(v))

def test_3_2_2_1():
    """
    The first argument to 'then' must be called when a promise is
    fulfilled.
    """

    c = Counter()
    def check(v, c):
        assert_equals(v, 5)
        c.tick()
    p1 = Promise()
    p2 = p1.then(lambda v: check(v, c))
    p1.fulfill(5)
    assert_equals(1, c.value())

def test_3_2_2_2():
    """
    Make sure callbacks are never called more than once.
    """

    c = Counter()
    p1 = Promise()
    p2 = p1.then(lambda v: c.tick())
    p1.fulfill(5)
    try:
        # I throw an exception
        p1.fulfill(5)
        assert False # Should not get here!
    except AssertionError:
        # This is expected
        pass
    assert_equals(1, c.value())

def test_3_2_2_3():
    """
    Make sure fulfilled callback never called if promise is rejected
    """

    cf = Counter()
    cr = Counter()
    p1 = Promise()
    p2 = p1.then(lambda v: cf.tick(), lambda r: cr.tick())
    p1.reject("Error")
    assert_equals(0, cf.value())
    assert_equals(1, cr.value())

def test_3_2_3_1():
    """
    The second argument to 'then' must be called when a promise is
    rejected.
    """

    c = Counter()
    def check(r, c):
        assert_equals(r, "Error")
        c.tick()
    p1 = Promise()
    p2 = p1.then(None, lambda r: check(r, c))
    p1.reject("Error")
    assert_equals(1, c.value())

def test_3_2_3_2():
    """
    Make sure callbacks are never called more than once.
    """

    c = Counter()
    p1 = Promise()
    p2 = p1.then(None, lambda v: c.tick())
    p1.reject("Error")
    try:
        # I throw an exception
        p1.reject("Error")
        assert False # Should not get here!
    except AssertionError:
        # This is expected
        pass
    assert_equals(1, c.value())

def test_3_2_3_3():
    """
    Make sure rejected callback never called if promise is fulfilled
    """

    cf = Counter()
    cr = Counter()
    p1 = Promise()
    p2 = p1.then(lambda v: cf.tick(), lambda r: cr.tick())
    p1.fulfill(5)
    assert_equals(0, cr.value())
    assert_equals(1, cf.value())

def test_3_2_5_1_when():
    """
    Then can be called multiple times on the same promise
    and callbacks must be called in the order of the
    then calls.
    """

    def add(l, v):
        l.append(v)
    p1 = Promise()
    order = []
    p2 = p1.then(lambda v: add(order, "p2"))
    p3 = p1.then(lambda v: add(order, "p3"))
    p1.fulfill(2)
    assert_equals(2, len(order))
    assert_equals("p2", order[0])
    assert_equals("p3", order[1])

def test_3_2_5_1_if():
    """
    Then can be called multiple times on the same promise
    and callbacks must be called in the order of the
    then calls.
    """

    def add(l, v):
        l.append(v)
    p1 = Promise()
    p1.fulfill(2)
    order = []
    p2 = p1.then(lambda v: add(order, "p2"))
    p3 = p1.then(lambda v: add(order, "p3"))
    assert_equals(2, len(order))
    assert_equals("p2", order[0])
    assert_equals("p3", order[1])

def test_3_2_5_2_when():
    """
    Then can be called multiple times on the same promise
    and callbacks must be called in the order of the
    then calls.
    """

    def add(l, v):
        l.append(v)
    p1 = Promise()
    order = []
    p2 = p1.then(None, lambda v: add(order, "p2"))
    p3 = p1.then(None, lambda v: add(order, "p3"))
    p1.reject("Error")
    assert_equals(2, len(order))
    assert_equals("p2", order[0])
    assert_equals("p3", order[1])

def test_3_2_5_2_if():
    """
    Then can be called multiple times on the same promise
    and callbacks must be called in the order of the
    then calls.
    """

    def add(l, v):
        l.append(v)
    p1 = Promise()
    p1.reject("Error")
    order = []
    p2 = p1.then(None, lambda v: add(order, "p2"))
    p3 = p1.then(None, lambda v: add(order, "p3"))
    assert_equals(2, len(order))
    assert_equals("p2", order[0])
    assert_equals("p3", order[1])

def test_3_2_6_1():
    """
    Promises returned by then must be fulfilled when the promise
    they are chained from is fulfilled IF the fulfillment value
    is not a promise.
    """

    p1 = Promise()
    pf = p1.then(lambda v: v*v)
    p1.fulfill(5)
    assert_equals(pf.value, 25)

    p2 = Promise()
    pr = p2.then(None, lambda r: 5)
    p2.reject("Error")
    assert_equals(5, pr.value)

def test_3_2_6_2_when():
    """
    Promises returned by then must be rejected when any of their
    callbacks throw an exception.
    """

    def fail(v):
        raise AssertionError("Exception Message")
    p1 = Promise()
    pf = p1.then(fail)
    p1.fulfill(5)
    assert pf.isRejected()
    assert isinstance(pf.reason, AssertionError)
    assert_equals("Exception Message", str(pf.reason))

    p2 = Promise()
    pr = p2.then(None, fail)
    p2.reject("Error")
    assert pr.isRejected()
    assert isinstance(pr.reason, AssertionError)
    assert_equals("Exception Message", str(pr.reason))

def test_3_2_6_2_if():
    """
    Promises returned by then must be rejected when any of their
    callbacks throw an exception.
    """

    def fail(v):
        raise AssertionError("Exception Message")
    p1 = Promise()
    p1.fulfill(5)
    pf = p1.then(fail)
    assert pf.isRejected()
    assert isinstance(pf.reason, AssertionError)
    assert_equals("Exception Message", str(pf.reason))

    p2 = Promise()
    p2.reject("Error")
    pr = p2.then(None, fail)
    assert pr.isRejected()
    assert isinstance(pr.reason, AssertionError)
    assert_equals("Exception Message", str(pr.reason))

def test_3_2_6_3_when_fulfilled():
    """
    Testing return of pending promises to make
    sure they are properly chained.

    This covers the case where the root promise
    is fulfilled after the chaining is defined.
    """

    p1 = Promise()
    pending = Promise()
    pf = p1.then(lambda r: pending)
    assert pending.isPending()
    assert pf.isPending()
    p1.fulfill(10)
    pending.fulfill(5)
    assert pending.isFulfilled()
    assert_equals(5, pending.value)
    assert pf.isFulfilled()
    assert_equals(5, pf.value)

    p2 = Promise()
    bad = Promise()
    pr = p2.then(lambda r: bad)
    assert bad.isPending()
    assert pr.isPending()
    p2.fulfill(10)
    bad.reject("Error")
    assert bad.isRejected()
    assert_equals("Error", bad.reason)
    assert pr.isRejected()
    assert_equals("Error", pr.reason)


def test_3_2_6_3_if_fulfilled():
    """
    Testing return of pending promises to make
    sure they are properly chained.

    This covers the case where the root promise
    is fulfilled before the chaining is defined.
    """

    p1 = Promise()
    p1.fulfill(10)
    pending = Promise()
    pending.fulfill(5)
    pf = p1.then(lambda r: pending)
    assert pending.isFulfilled()
    assert_equals(5, pending.value)
    assert pf.isFulfilled()
    assert_equals(5, pf.value)

    p2 = Promise()
    p2.fulfill(10)
    bad = Promise()
    bad.reject("Error")
    pr = p2.then(lambda r: bad)
    assert bad.isRejected()
    assert_equals("Error", bad.reason)
    assert pr.isRejected()
    assert_equals("Error", pr.reason)

def test_3_2_6_3_when_rejected():
    """
    Testing return of pending promises to make
    sure they are properly chained.

    This covers the case where the root promise
    is rejected after the chaining is defined.
    """

    p1 = Promise()
    pending = Promise()
    pr = p1.then(None, lambda r: pending)
    assert pending.isPending()
    assert pr.isPending()
    p1.reject("Error")
    pending.fulfill(10)
    assert pending.isFulfilled()
    assert_equals(10, pending.value)
    assert pr.isFulfilled()
    assert_equals(10, pr.value)

    p2 = Promise()
    bad = Promise()
    pr = p2.then(None, lambda r: bad)
    assert bad.isPending()
    assert pr.isPending()
    p2.reject("Error")
    bad.reject("Assertion")
    assert bad.isRejected()
    assert_equals("Assertion", bad.reason)
    assert pr.isRejected()
    assert_equals("Assertion", pr.reason)

def test_3_2_6_3_if_rejected():
    """
    Testing return of pending promises to make
    sure they are properly chained.

    This covers the case where the root promise
    is rejected before the chaining is defined.
    """

    p1 = Promise()
    p1.reject("Error")
    pending = Promise()
    pending.fulfill(10)
    pr = p1.then(None, lambda r: pending)
    assert pending.isFulfilled()
    assert_equals(10, pending.value)
    assert pr.isFulfilled()
    assert_equals(10, pr.value)

    p2 = Promise()
    p2.reject("Error")
    bad = Promise()
    bad.reject("Assertion")
    pr = p2.then(None, lambda r: bad)
    assert bad.isRejected()
    assert_equals("Assertion", bad.reason)
    assert pr.isRejected()
    assert_equals("Assertion", pr.reason)

def test_3_2_6_4_pending():
    """
    Handles the case where the arguments to then
    are not functions or promises.
    """
    p1 = Promise()
    p2 = p1.then(5)
    p1.fulfill(10)
    assert_equals(10, p1.value)
    assert p2.isFulfilled()
    assert_equals(10, p2.value)

def test_3_2_6_4_fulfilled():
    """
    Handles the case where the arguments to then
    are values, not functions or promises.
    """
    p1 = Promise()
    p1.fulfill(10)
    p2 = p1.then(5)
    assert_equals(10, p1.value)
    assert p2.isFulfilled()
    assert_equals(10, p2.value)

def test_3_2_6_5_pending():
    """
    Handles the case where the arguments to then
    are values, not functions or promises.
    """
    p1 = Promise()
    p2 = p1.then(None, 5)
    p1.reject("Error")
    assert_equals("Error", p1.reason)
    assert p2.isRejected()
    assert_equals("Error", p2.reason)

def test_3_2_6_5_rejected():
    """
    Handles the case where the arguments to then
    are values, not functions or promises.
    """
    p1 = Promise()
    p1.reject("Error")
    p2 = p1.then(None, 5)
    assert_equals("Error", p1.reason)
    assert p2.isRejected()
    assert_equals("Error", p2.reason)
