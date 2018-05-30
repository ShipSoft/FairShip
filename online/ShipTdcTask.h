#ifndef ONLINE_SHIPTDCTASK_H
#define ONLINE_SHIPTDCTASK_H

#include "FairTask.h"

class TClonesArray;
class TH1I;
class TCanvas;

/**
 * An example analysis task for demonstartion of THttpServer usage.
 * Loops over detector raw items in an event and fills the histogram.
 */
class ShipTdcTask : public FairTask {
public:
   /** Standard Constructor. */
   ShipTdcTask(const char *name, Int_t iVerbose);

   /** Destructor. */
   virtual ~ShipTdcTask();

   /** Initialization of the task. */
   virtual InitStatus Init();

   /** Process an event. */
   virtual void Exec(Option_t *);

   /** Called at the end of each event. */
   virtual void FinishEvent();

   /** Called at the end of task. */
   virtual void FinishTask();

private:
   TClonesArray *fRawData; /**< Array with input data. */
   TH1I *fhChannel;        /**< Histogram object which is registered on http server. */
   TH1I *fhTime;

   ShipTdcTask(const ShipTdcTask &);
   ShipTdcTask &operator=(const ShipTdcTask &);

public:
   ClassDef(ShipTdcTask, 1)
};

#endif
