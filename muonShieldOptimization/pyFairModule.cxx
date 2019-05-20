#include "Python.h" // Needs to be included first to avoid redefinition of _POSIX_C_SOURCE 
#include "pyFairModule.h"
#include "TObject.h"

void call_python_method(PyObject* self, const char* method)
{
   // check arguments
   if ( 0 == self || 0 == method ) { throw std::runtime_error("Invalid Python object and method"); }
   // call Python
   PyObject* r = PyObject_CallMethod(self, const_cast<char*>(method), const_cast<char*>(""));
   if ( 0 == r ) { PyErr_Print(); return;}
   // release used objects
   Py_XDECREF( r ) ;
   //
   return;
}
