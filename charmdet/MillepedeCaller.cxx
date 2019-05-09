#include "MillepedeCaller.h"
#include <iostream>

MillepedeCaller::MillepedeCaller(const char *outFileName, bool asBinary, bool writeZero)
: mille(outFileName, asBinary, writeZero)
{

}

MillepedeCaller::~MillepedeCaller()
{
	// TODO Auto-generated destructor stub
}

