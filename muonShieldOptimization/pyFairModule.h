#include "TObject.h"
#include "Python.h"
#include <stdexcept>
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

class FairModule;

class pyFairModule : public FairModule {
 public:
   pyFairModule(PyObject* self) : fSelf(self) {}
   virtual ~pyFairModule() {}
   virtual void ConstructGeometry() { call_python_method(fSelf,"ConstructGeometry"); }
 private:
   PyObject* fSelf;
ClassDef(pyFairModule, 0)
};
