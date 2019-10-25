# -*- coding: utf-8 -*-

import os
import ROOT
# TODO: add header to CMake
ROOT.gROOT.ProcessLine('#include "' + os.path.join(os.path.expandvars('$FAIRSHIP'), 'utils', 'logger.hxx') + '"')

for func in ('fatal', 'error', 'warn', 'info', 'debug'):
    # The double lambda is used in order to capture 'func' by value, not by reference
    # (which would always point to the last value taken in the loop)
    globals()[func] = (lambda f:
        lambda *args: ROOT.ship.__dict__[f](*map(type, args))(*args)
    )(func)
    globals()[func].__doc__ = \
        'Python wrapper around the C++ function template ship::{}(Types... args).'.format(func)
