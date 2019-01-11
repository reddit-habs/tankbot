import inspect
import string


class _Formatter(string.Formatter):
    def __init__(self, f_locals, f_globals):
        self._locals = f_locals
        self._globals = f_globals

    def get_field(self, name, *args, **kwargs):
        return (eval(name, self._globals, self._locals), name)


# This is a really greasy hack, but it's neat. Probably not safe with untrusted inputs.
# https://gist.github.com/sbstp/54f1de0d01542b26da85280e8de52b00
def f(fmt, *args, **kwargs):
    if args or kwargs:
        return fmt.format(*args, **kwargs)
    frame = inspect.currentframe()
    try:
        return _Formatter(frame.f_back.f_locals, frame.f_back.f_globals).format(fmt)
    finally:
        del frame
