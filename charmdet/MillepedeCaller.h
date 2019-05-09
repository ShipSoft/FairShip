#ifndef CHARMDET_MILLEPEDECALLER_H_
#define CHARMDET_MILLEPEDECALLER_H_

#include "TObject.h"
#include "Mille.h"

/**
 * A class for wrapping the millepede function call such that it can be called from
 * within a python script
 *
 * @author Stefan Bieschke
 * @date Apr. 9, 2019
 */
class MillepedeCaller: public TObject
{
public:
	MillepedeCaller(const char *outFileName, bool asBinary = true, bool writeZero = false);
	~MillepedeCaller();

	void call_mille(int n_local_derivatives,
					const float *local_derivatives,
					int n_global_derivatives,
					const float *global_derivatives,
					const int *label,
					float measured_residual,
					float sigma);

	ClassDef(MillepedeCaller,1);

private:
	Mille mille;
};

#endif /* CHARMDET_MILLEPEDECALLER_H_ */
