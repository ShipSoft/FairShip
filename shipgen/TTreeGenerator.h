/**
 * @file TTreeGenerator.h
 * @brief Generator class for reading particle data from ROOT TTrees
 * @author Your Name
 * @date Today's Date
 */

#ifndef SHIPGEN_TTREEGENERATOR_H_
#define SHIPGEN_TTREEGENERATOR_H_

#include "FairGenerator.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"

namespace ship
{

/**
 * @class TTreeGenerator
 * @brief A FairRoot generator that reads particle data from ROOT TTrees
 *
 * This class inherits from FairGenerator and provides functionality to read
 * particle events from ROOT TTrees containing particle momentum, position,
 * PDG ID, and weight information. It is designed for use in FairRoot-based
 * simulation frameworks.
 *
 * The expected TTree structure contains the following branches:
 * - px, py, pz: Particle momentum components (GeV/c)
 * - x, y, z: Particle position coordinates (cm)
 * - pdgid: PDG particle identification code
 * - weight: Event weight factor
 *
 * @author Your Name
 * @date Today's Date
 */
class TTreeGenerator : public FairGenerator
{
  public:
    /**
     * @brief Default constructor
     *
     * Initializes the generator with default values. The input file and tree
     * must be set using SetInput() before calling Init().
     */
    TTreeGenerator();

    /**
     * @brief Constructor with input file specification
     *
     * @param fileName Path to the ROOT file containing the TTree
     * @param treeName Name of the TTree (default: "events")
     */
    TTreeGenerator(const char* fileName, const char* treeName = "events");

    /**
     * @brief Destructor
     *
     * Properly closes the input file and cleans up resources.
     */
    virtual ~TTreeGenerator();

    /**
     * @brief Initialize the generator
     *
     * Opens the input ROOT file, retrieves the specified TTree, and sets up
     * branch addresses for reading particle data. Must be called before
     * attempting to read events.
     *
     * @return kTRUE if initialization successful, kFALSE otherwise
     */
    virtual Bool_t Init();

    /**
     * @brief Read one event and generate primary particles
     *
     * Reads the current event from the TTree and adds the particle to the
     * primary generator. Automatically advances to the next event.
     *
     * @param primGen Pointer to the FairPrimaryGenerator instance
     * @return kTRUE if event read successfully, kFALSE if end of tree reached
     */
    virtual Bool_t ReadEvent(FairPrimaryGenerator* primGen);

    /**
     * @brief Skip a specified number of events
     *
     * Advances the current event position by the specified count without
     * reading the event data.
     *
     * @param count Number of events to skip
     * @return kTRUE if successful, kFALSE if end of tree reached
     */
    virtual Bool_t SkipEvents(Int_t count);

    /**
     * @brief Rewind to the beginning of the tree
     *
     * Resets the current event position to the first event (index 0).
     *
     * @return kTRUE (always successful)
     */
    virtual Bool_t RewindEvents();

    /**
     * @brief Get the total number of events in the tree
     *
     * @return Total number of events available in the TTree
     */
    Long64_t GetNEvents() const { return fNEvents; }

    /**
     * @brief Get the current event index
     *
     * @return Current event position (0-based index)
     */
    Long64_t GetCurrentEvent() const { return fCurrentEvent; }

    /**
     * @brief Set the input file and tree name
     *
     * @param fileName Path to the ROOT file containing the TTree
     * @param treeName Name of the TTree (default: "events")
     */
    void SetInput(const char* fileName, const char* treeName = "events");

  private:
    TFile* fInputFile;   //!< Input ROOT file pointer
    TTree* fInputTree;   //!< Input TTree pointer
    TString fFileName;   //!< Path to the input ROOT file
    TString fTreeName;   //!< Name of the TTree to read

    Long64_t fNEvents;        //!< Total number of events in the tree
    Long64_t fCurrentEvent;   //!< Current event index (0-based)

    // Branch variables for particle data
    Double_t fPx;       //!< Particle momentum x-component (GeV/c)
    Double_t fPy;       //!< Particle momentum y-component (GeV/c)
    Double_t fPz;       //!< Particle momentum z-component (GeV/c)
    Double_t fX;        //!< Particle position x-coordinate (cm)
    Double_t fY;        //!< Particle position y-coordinate (cm)
    Double_t fZ;        //!< Particle position z-coordinate (cm)
    Int_t fPdgId;       //!< PDG particle identification code
    Double_t fWeight;   //!< Event weight factor

    /**
     * @brief Initialize TTree branch addresses
     *
     * Sets up the branch addresses to read particle data from the TTree.
     * Called internally by Init().
     */
    void InitBranches();

    ClassDef(TTreeGenerator, 1);
};

}   // namespace ship

#endif   // SHIPGEN_TTREEGENERATOR_H_
