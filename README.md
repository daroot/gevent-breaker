gevent-breaker
==============

[![Build Status](https://travis-ci.org/daroot/gevent-breaker.svg?branch=1.0.0)](https://travis-ci.org/daroot/gevent-breaker)

Circuit Breaker pattern for gevent apps.

Install
-------

   $ pip install gevent-breaker

Usage
-----

```python
from gevent_breaker import circuit_breaker, CircuitBroken
while True:
	try:
        # After enough errors (5 by default), raise a CircuitBroken
		with circuit_breaker("breaker1"):
			1/0
	except ZeroDivisionError:
		print("Got an exception!")
	except CircuitBroken:
        print("Too many errors!")
		break

try:
    # Don't raise a CircuitBroken, instead just wait for a period
	# of time (default 60s) before trying again.
    with circuit_breaker("breaker2", block=True):
        1/0
	except ZeroDivisionError:
        print("Got an exception")
```
