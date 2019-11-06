# -*- coding: utf-8 -*-

import os
import ROOT
# TODO: add header to CMake
ROOT.gROOT.ProcessLine('#include "' + os.path.join(os.path.expandvars('$FAIRSHIP'), 'utils', 'logger.hxx') + '"')

def _make_wrapper(funcname):
    def function(*args, **kwargs):
        delim = kwargs.get('delim', ' ')
        # Interleaves arguments with delimiters. No delimiter at the end.
        args_with_delim = [val for pair in zip(args, len(args)*[delim]) for val in pair][:-1]
        return ROOT.ship.__dict__[funcname](*map(type, args_with_delim))(*args_with_delim)
    docstring = '''\
    Python wrapper around the C++ function template ship::{}(Types... args).

    Keyword arguments:
    delim -- delimiter to be inserted between each argument (default \' \')
    '''.format(funcname)
    return function, docstring

def _add_wrappers():
    # This function is used to avoid polluting the global namespace
    for funcname in ('fatal', 'error', 'warn', 'info', 'debug'):
        function, docstring = _make_wrapper(funcname)
        globals()[funcname] = function
        globals()[funcname].__doc__ = docstring

_add_wrappers()
