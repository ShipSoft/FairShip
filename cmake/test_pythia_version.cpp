// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "Pythia8/Pythia.h"

int main()
{
#ifdef PYTHIA_VERSION_INTEGER
    return 0;   // Success: PYTHIA_VERSION_INTEGER is defined
#else
    return 1;   // Failure: PYTHIA_VERSION_INTEGER is not defined
#endif
}
