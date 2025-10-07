# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

"""Backport pythonisation for TDirectory introduced in ROOT 6.32."""
import cppyy
import ROOT


def _TDirectory_getitem(self, key):
    """Injection of TDirectory.__getitem__ that raises AttributeError on failure.

    Method that is assigned to TDirectory.__getitem__. It relies on Get to
    obtain the object from the TDirectory and adds on top:
    - Raising an AttributeError if the object does not exist
    - Caching the result of a successful get for future re-attempts.
    Once cached, the same object is retrieved every time.
    This pythonization is inherited by TDirectoryFile and TFile.

    Example:
    ```
    myfile.mydir.mysubdir.myHist.Draw()
    ```
    """
    if not hasattr(self, "_cached_items"):
        self._cached_items = dict()

    if key in self._cached_items:
        return self._cached_items[key]

    result = self.Get(key)
    if not result:
        raise KeyError(f"{repr(self)} object has no key '{key}'")

    # Caching behavior seems to be more clear to the user; can always override said
    # behavior (i.e. re-read from file) with an explicit Get() call
    self._cached_items[key] = result
    return result

def pythonize_tdirectory():
    """Apply pythonisation."""
    klass = cppyy.gbl.TDirectory
    klass.__getitem__ = _TDirectory_getitem


# FIXME Remove when support for old ROOT versions is dropped
if int(ROOT.gROOT.GetVersion().split('/')[0].split('.')[1]) < 32:
    pythonize_tdirectory()
