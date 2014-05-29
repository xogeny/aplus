from threading import Thread

class Promise:
    """
    This is a class that attempts to comply with the
    Promises/A+ specification and test suite:

    http://promises-aplus.github.io/promises-spec/
    """

    # These are the potential states of a promise
    PENDING = -1
    REJECTED = 0
    FULFILLED = 1

    def __init__(self):
        """
        Initialize the Promise into a pending state.
        """
        self._state = self.PENDING;
        self.value = None;
        self.reason = None;
        self._callbacks = [];
        self._errbacks = [];

    def fulfill(self, value):
        """
        Fulfill the promise with a given value.
        """

        assert self._state==self.PENDING

        self._state=self.FULFILLED;
        self.value = value
        for callback in self._callbacks:
            try:
                callback(value)
            except Exception:
                # Ignore errors in callbacks
                pass
        # We will never call these callbacks again, so allow
        # them to be garbage collected.  This is important since
        # they probably include closures which are binding variables
        # that might otherwise be garbage collected.
        self._callbacks = []

    def reject(self, reason):
        """
        Reject this promise for a given reason.
        """
        assert self._state==self.PENDING

        self._state=self.REJECTED;
        self.reason = reason
        for errback in self._errbacks:
            try:
                errback(reason)
            except Exception:
                # Ignore errors in callbacks
                pass

        # We will never call these errbacks again, so allow
        # them to be garbage collected.  This is important since
        # they probably include closures which are binding variables
        # that might otherwise be garbage collected.
        self._errbacks = []

    def isPending(self):
        """Indicate whether the Promise is still pending."""
        return self._state==self.PENDING

    def isFulfilled(self):
        """Indicate whether the Promise has been fulfilled."""
        return self._state==self.FULFILLED

    def isRejected(self):
        """Indicate whether the Promise has been rejected."""
        return self._state==self.REJECTED

    def get(self, timeout=None):
        """Get the value of the promise, waiting if necessary."""
        self.wait(timeout)
        if self._state==self.FULFILLED:
            return self.value
        else:
            raise ValueError("Calculation didn't yield a value")

    def wait(self, timeout=None):
        """
        An implementation of the wait method which doesn't involve
        polling but instead utilizes a "real" synchronization
        scheme.
        """
        import threading

        if self._state!=self.PENDING:
            return

        e = threading.Event()
        self.addCallback(lambda v: e.set())
        self.addErrback(lambda r: e.set())
        e.wait(timeout)

    def addCallback(self, f):
        """
        Add a callback for when this promis is fulfilled.  Note that
        if you intend to use the value of the promise somehow in
        the callback, it is more convenient to use the 'then' method.
        """
        self._callbacks.append(f)

    def addErrback(self, f):
        """
        Add a callback for when this promis is rejected.  Note that
        if you intend to use the rejection reason of the promise
        somehow in the callback, it is more convenient to use
        the 'then' method.
        """
        self._errbacks.append(f)

    def then(self, success=None, failure=None):
        """
        This method takes two optional arguments.  The first argument
        is used if the "self promise" is fulfilled and the other is
        used if the "self promise" is rejected.  In either case, this
        method returns another promise that effectively represents
        the result of either the first of the second argument (in the
        case that the "self promise" is fulfilled or rejected,
        respectively).

        Each argument can be either:
          * None - Meaning no action is taken
          * A function - which will be called with either the value
            of the "self promise" or the reason for rejection of
            the "self promise".  The function may return:
            * A value - which will be used to fulfill the promise
              returned by this method.
            * A promise - which, when fulfilled or rejected, will
              cascade its value or reason to the promise returned
              by this method.
          * A value - which will be assigned as either the value
            or the reason for the promise returned by this method
            when the "self promise" is either fulfilled or rejected,
            respectively.
        """
        ret = Promise()

        def callAndFulfill(v):
            """
            A callback to be invoked if the "self promise"
            is fulfilled.
            """
            try:
                # From 3.2.1, don't call non-functions values
                if _isFunction(success):
                    newvalue = success(v)
                    if _isPromise(newvalue):
                        newvalue.then(lambda v: ret.fulfill(v),
                                      lambda r: ret.reject(r))
                    else:
                        ret.fulfill(newvalue)
                elif success!=None:
                    # From 3.2.6.4
                    ret.fulfill(v)
                else:
                    pass
            except Exception as e:
                ret.reject(e)

        def callAndReject(r):
            """
            A callback to be invoked if the "self promise"
            is rejected.
            """
            try:
                if _isFunction(failure):
                    newvalue = failure(r)
                    if _isPromise(newvalue):
                        newvalue.then(lambda v: ret.fulfill(v),
                                      lambda r: ret.reject(r))
                    else:
                        ret.fulfill(newvalue)
                elif failure!=None:
                    # From 3.2.6.5
                    ret.reject(r)
                else:
                    pass
            except Exception as e:
                ret.reject(e)
        
        if self._state==self.PENDING:
            """
            If this is still pending, then add callbacks to the
            existing promise that call either the success or
            rejected functions supplied and then fulfill the
            promise being returned by this method
            """
            if success!=None:
                self._callbacks.append(callAndFulfill)
            if failure!=None:
                self._errbacks.append(callAndReject)

        elif self._state==self.FULFILLED:
            """
            If this promise was already fulfilled, then
            we need to use the first argument to this method
            to determine the value to use in fulfilling the
            promise that we return from this method.
            """
            try:
                if _isFunction(success):
                    newvalue = success(self.value)
                    if _isPromise(newvalue):
                        newvalue.then(lambda v: ret.fulfill(v),
                                      lambda r: ret.reject(r))
                    else:
                        ret.fulfill(newvalue)
                elif success!=None:
                    # From 3.2.6.4
                    ret.fulfill(self.value)
                else:
                    pass
            except Exception as e:
                ret.reject(e)
        elif self._state==self.REJECTED:
            """
            If this promise was already rejected, then
            we need to use the second argument to this method
            to determine the value to use in fulfilling the
            promise that we return from this method.
            """
            try:
                if _isFunction(failure):
                    newvalue = failure(self.reason)
                    if _isPromise(newvalue):
                        newvalue.then(lambda v: ret.fulfill(v),
                                      lambda r: ret.reject(r))
                    else:
                        ret.fulfill(newvalue)
                elif failure!=None:
                    # From 3.2.6.5
                    ret.reject(self.reason)
                else:
                    pass
            except Exception as e:
                ret.reject(e)

        return ret

def _isFunction(v):
    """
    A utility function to determine if the specified
    value is a function.
    """
    if v==None:
        return False
    if hasattr(v, "__call__"):
        return True
    return False

def _isPromise(obj):
    """
    A utility function to determine if the specified
    object is a promise using "duck typing".
    """
    return hasattr(obj, "fulfill") and \
        _isFunction(getattr(obj, "fulfill")) and \
        hasattr(obj, "reject") and \
        _isFunction(getattr(obj, "reject")) and \
        hasattr(obj, "then") and \
        _isFunction(getattr(obj, "then"))

def listPromise(*args):
    """
    A special function that takes a bunch of promises
    and turns them into a promise for a vector of values.
    In other words, this turns an list of promises for values
    into a promise for a list of values.
    """
    ret = Promise()

    def handleSuccess(v, ret):
        for arg in args:
            if not arg.isFulfilled():
                return

        value = map(lambda p: p.value, args)
        ret.fulfill(value)

    for arg in args:
        arg.addCallback(lambda v: handleSuccess(v, ret))
        arg.addErrback(lambda r: ret.reject(r))

    # Check to see if all the promises are already fulfilled
    handleSuccess(None, ret)

    return ret

def dictPromise(m):
    """
    A special function that takes a dictionary of promises
    and turns them into a promise for a dictionary of values.
    In other words, this turns an dictionary of promises for values
    into a promise for a dictionary of values.
    """
    ret = Promise()

    def handleSuccess(v, ret):
        for p in m.values():
            if not p.isFulfilled():
                return

        value = {}
        for k in m:
            value[k] = m[k].value
        ret.fulfill(value)

    for p in m.values():
        p.addCallback(lambda v: handleSuccess(v, ret))
        p.addErrback(lambda r: ret.reject(r))

    # Check to see if all the promises are already fulfilled
    handleSuccess(None, ret)

    return ret

class BackgroundThread(Thread):
    def __init__(self, promise, func):
        self.promise = promise;
        self.func = func;
        Thread.__init__(self)
    def run(self):
        try:
            val = self.func()
            self.promise.fulfill(val)
        except Exception as e:
            self.promise.reject(e)

def background(f):
    p = Promise()
    t = BackgroundThread(p, f)
    t.start()
    return p

def spawn(f):
    from gevent import spawn
    
    def process(p, f):
        try:
            val = f()
            p.fulfill(val)
        except Exception as e:
            p.reject(e)

    p = Promise()
    g = spawn(lambda: process(p, f))
    return p
