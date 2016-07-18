import gevent
from gevent.event import Event
from collections import defaultdict
from contextlib import contextmanager


class CircuitBroken(Exception):
    pass


class CircuitBreaker(object):
    def __init__(self, reset=60.0, threshold=5):
        self.tripped = False
        self.fails = 0

        self.reset = reset
        self.threshold = threshold
        self.event = Event()
        self.timer_task = None

    def clear(self):
        """
        When a task successfully completes, reset the breaker completely.

        Kill any outstanding timers, reset the trip state, and notify
        any waiters that the breaker is now closed.
        """
        self.tripped = False
        self.fails = 0
        if self.timer_task:
            self.timer_task.kill()
            self.timer_task = None
        self.event.set()

    def fault(self):
        """
        Register a failure on a breaker.

        Checks if the trip threshold has been reached and if so, open the
        breaker and start a timer task for eventual reset.
        """
        self.fails += 1
        if self.fails >= self.threshold:
            self.tripped = True
            self.event.clear()
            if not self.timer_task:
                self.timer_task = gevent.spawn(self.reset_timer)

    def wait(self):
        """
        Wait on the breaker to reset.
        """
        self.event.wait()

    def reset_timer(self):
        """
        Timer task to reset a breaker that's been had a failure.

        This does not fully clear the breaker, but resets it to the state
        of being one failure away from tripping.  This helps prevent
        thundering herd issues by keeping the number of attempts against
        a failing service/tasks minimal until it starts responding
        properly.
        """
        gevent.sleep(self.reset)
        self.tripped = False
        self.fails = self.threshold - 1
        self.timer_task = None
        self.event.set()


def DefaultBreaker():
    return CircuitBreaker(reset=60.0, threshold=5)

_defaultbreakerbox = defaultdict(DefaultBreaker)


@contextmanager
def circuit_breaker(breaker_name, block=False, breakerbox=_defaultbreakerbox):
    breaker = breakerbox[breaker_name]
    try:
        if breaker.tripped:
            if block:
                breaker.wait()
            else:
                raise CircuitBroken()
        yield breaker
        breaker.clear()
    except Exception as e:
        breaker.fault()
        raise e
