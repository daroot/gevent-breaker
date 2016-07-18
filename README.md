gevent-breker
=============

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
		with circuit_breaker("my breaker"):
			1/0
	except ZeroDivisionError:
		print("Got an exception!")
	except CircuitBroken:
        print("Too many errors!")
		break
```
