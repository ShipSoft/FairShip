# -*- coding: utf-8 -*-

from __future__ import print_function
from functools import wraps
import sys
import six # For compatibility with both Python 2 and 3

class MethodLogger(object):
    """
    This class wraps a instance of an arbitrary class, intercepts all its
    method calls and logs them to a file (default: `sys.stdout`).

    >>> import method_logger as ml
    >>> from StringIO import StringIO
    >>> class TestClass(object):
    ...     def __init__(self):
    ...         pass
    ...     def func(*args, **kwargs):
    ...         pass
    ...
    >>> cl = TestClass()
    >>> sink = StringIO()
    >>> lg = ml.MethodLogger(cl, sink=sink)
    >>> lg.func(3, y=8, foo='bar')
    >>> sink.getvalue()
    "TestClass.func(3, y=8, foo='bar')\\n"
    >>> sink.close()
    """
    def __init__(self, wrapped_instance, sink=sys.stdout):
        self._class = wrapped_instance
        self._sink = sink
        self._prefix = type(wrapped_instance).__name__ + '.'

    def method_logger(self, met):
        qualified_name = self._prefix + str(met.__name__)
        @wraps(met)
        def _logger(*args, **kwargs):
            args_str = ', '.join(repr(arg) for arg in args)
            kwargs_str = ', '.join(str(k) + '=' + repr(v) for (k,v) in six.iteritems(kwargs))
            all_args_str = args_str + (', ' if len(kwargs_str) > 0 else '') + kwargs_str
            print('{0}({1})'.format(qualified_name, all_args_str), file=self._sink)
            return met.__call__(*args, **kwargs)
        return _logger

    def __getattr__(self, attr):
        return self.method_logger(getattr(self._class, attr))
