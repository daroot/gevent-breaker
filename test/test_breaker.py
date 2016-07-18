import pytest
import gevent
from collections import defaultdict
from gevent_breaker import (CircuitBreaker, circuit_breaker, CircuitBroken)


@pytest.fixture
def testbreakbox():
    """
    Create a set of breakers with useful properties for testing.

    - basic [reset=10, threshold=1] (Default)
    - short [reset=0.002, threshold=1]
    - multi [reset=10, threshold=2]
    - shortmulti [reset=.002, threshold=3]
    """
    def default_test_breaker():
        return CircuitBreaker(reset=10.0, threshold=1)

    box = defaultdict(default_test_breaker)
    box["basic"]
    box["short"].reset = 0.002
    box["multi"].threshold = 2
    box["shortmulti"].threshold = 3
    box["shortmulti"].reset = 0.002
    return box


def raisefault(brk_name, breakerbox):
    """
    Deliberately raise a fault in the named breaker.

    Helper function to avoid needing to type out a full try/except block
    in every test.
    """
    try:
        with circuit_breaker(brk_name, breakerbox=breakerbox):
            1/0
    except Exception:
        pass  # Swallow, we know.


def test_new_breaker_uses_defaults(testbreakbox):
    """
    A newly instantiated CircuitBreaker should get options from
    the defaultdict's factory function, and should be untripped and have
    no outstanding timer task.
    """
    breaker = testbreakbox["basic"]
    assert breaker.reset == 10.0
    assert breaker.threshold == 1
    assert breaker.tripped is False
    assert breaker.timer_task is None


def test_breaker_trips(testbreakbox):
    """
    When a fault is raised, if the threshold is met, the breaker should trip.
    """
    breaker = testbreakbox["basic"]
    assert breaker.tripped is False
    raisefault("basic", testbreakbox)
    assert breaker.fails == 1
    assert breaker.tripped is True


def test_tripped_breaker_resets(testbreakbox):
    """
    After the reset period has elapsed, a tripped breaker should be reset
    to untripped.
    """
    breaker = testbreakbox["short"]
    assert breaker.tripped is False
    raisefault("short", testbreakbox)
    assert breaker.fails == 1
    assert breaker.tripped is True
    gevent.sleep(0.03)
    assert breaker.tripped is False


def test_breaker_will_raise(testbreakbox):
    """
    Using the circuit_breaker context should raise CircuitBroken if
    called on a CircuitBreaker that has already tripped.
    """
    breaker = testbreakbox["basic"]
    raisefault("basic", testbreakbox)
    assert breaker.tripped is True
    with pytest.raises(CircuitBroken):
        with circuit_breaker("basic", breakerbox=testbreakbox):
            1/0


def test_breaker_blocks(testbreakbox):
    """
    A circuit_breaker context with the blocks=True flag should not raise, but
    instead wait.
    """
    breaker = testbreakbox["short"]
    raisefault("short", testbreakbox)
    assert breaker.tripped is True
    with pytest.raises(gevent.Timeout), gevent.Timeout(0.001):
        with circuit_breaker("short", block=True, breakerbox=testbreakbox):
            raise Exception("Should not get here.")


def test_breaker_clears_on_success(testbreakbox):
    """
    Once a circuit_breaker context has passed, it should completely clear the
    breaker so that future uses will succeed as normal.
    """
    breaker = testbreakbox["multi"]
    raisefault("multi", testbreakbox)
    assert breaker.fails == 1
    with circuit_breaker("multi", breakerbox=testbreakbox):
        pass  # Should cause 'clear' to be run.
    assert breaker.fails == 0


def test_breaker_clear_wakes_blocking_waiters(testbreakbox):
    """
    A circuit_breaker context is waiting on a breaker reset will be
    woken and continue when the reset period has elapsed.
    """
    raisefault("short", testbreakbox)
    result = {"done": False}

    def waiting_task():
        with circuit_breaker("short", block=True):
            gevent.sleep(0.001)
            result["done"] = True

    task = gevent.spawn(waiting_task)
    gevent.idle()
    assert result["done"] is False
    task.join(timeout=0.05)
    assert task.ready() is True
    assert result["done"] is True


def test_breaker_clear_kills_timer(testbreakbox):
    """
    A cleared circuit_breaker should cancel its timer_task.
    """
    breaker = testbreakbox["basic"]

    def slow_worker():
        with circuit_breaker("basic", breakerbox=testbreakbox):
            gevent.sleep(0.01)

    task = gevent.spawn(slow_worker)
    gevent.idle()  # let slow_worker start up
    assert breaker.tripped is False
    raisefault("basic", testbreakbox)
    assert breaker.tripped is True
    assert breaker.timer_task is not None
    timer_task = breaker.timer_task

    # Wait for slow_worker to finish, which should clear breaker
    task.join(timeout=0.05)
    assert task.ready() is True
    assert breaker.tripped is False
    assert breaker.timer_task is None
    assert timer_task.ready() is True


def test_breaker_reset_fails_not_fully_reset(testbreakbox):
    """
    A circuit_breaker's reset timer task should set its failure state to
    one below the threshold, rather than  completely clear it.
    """
    breaker = testbreakbox["shortmulti"]
    for x in range(3):
        raisefault("shortmulti", testbreakbox)
    assert breaker.tripped is True
    gevent.sleep(0.02)
    # Reset should run and set us to threshold-1 for a try.
    assert breaker.tripped is False
    assert breaker.fails == 2
    # One more should be back at threshold.
    raisefault("shortmulti", testbreakbox)
    assert breaker.tripped is True
    # And clear it fully.
    with circuit_breaker("shortmulti", breakerbox=testbreakbox, block=True):
        pass
    assert breaker.tripped is False
    assert breaker.fails == 0
