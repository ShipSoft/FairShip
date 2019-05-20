struct _object;
typedef _object PyObject;
#include "FairModule.h"

#include <stdexcept>
void call_python_method(PyObject* self, const char* method);

 
class pyFairModule : public FairModule {
public:
   pyFairModule(PyObject* self) : fSelf(self) {}
   virtual ~pyFairModule() {}
   virtual void ConstructGeometry() { call_python_method(fSelf,"ConstructGeometry"); }
private:
   PyObject* fSelf;
ClassDef(pyFairModule, 0)
};
