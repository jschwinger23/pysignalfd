# pysignalfd

A pure Python wrapper of [signalfd(2)](https://man7.org/linux/man-pages/man2/signalfd.2.html).

# Installation

```shell
pip install pysigalfd
```

# Usage

```python
import signal
import pysignalfd


sigs = [signal.SIGTERM, signal.SIGHUP]
signal.pthread_sigmask(signal.SIG_BLOCK, sigs)
fd = pysignalfd.signalfd(sigs, CLOEXEC=True, NONBLOCK=False)
for signum in pysignalfd.parse_siginfo(fd):
    print(signum)
```

# Similar Tools

1. [python-signalfd](https://pypi.org/project/python-signalfd/)
2. [signalfd](https://pypi.org/project/signalfd/)

Both module relies on "Python.h" to extend, by which there is a concern that installation might fail on the disparate Linux environments.
