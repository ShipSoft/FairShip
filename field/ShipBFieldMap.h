/*! \class ShipBFieldMap
  \brief Class that defines a (3d) magnetic field map
  \author John Back <J.J.Back@warwick.ac.uk>
*/

#ifndef ShipBFieldMap_H
#define ShipBFieldMap_H

#include "TVirtualMagField.h"
#include "TVector3.h"

#include <string>
#include <utility>
#include <vector>

class ShipBFieldMap : public TVirtualMagField
{

 public:

    //! Constructor
    /*!
      \param [in] label A descriptive name/title/label for this field
      \param [in] mapFileName The name of the field map file (distances in cm, fields in Tesla)
      \param [in] xOffset The x global co-ordinate shift to position the field map (cm)
      \param [in] yOffset The y global co-ordinate shift to position the field map (cm)
      \param [in] zOffset The z global co-ordinate shift to position the field map (cm)
    */
    ShipBFieldMap(const std::string& label, const std::string& mapFileName,
		  Double_t xOffset = 0.0, Double_t yOffset = 0.0, Double_t zOffset = 0.0);

    //! Copy constructor with a new global positioning offset. Use this if you want
    //! to reuse the same field map information elsewhere in the geometry
    /*! 
      \param [in] rhs The ShipBFieldMap object to be copied
      \param [in] newName The new description or title of the field
      \param [in] newXOffset The new global offset x co-ordinate (cm)
      \param [in] newYOffset The new global offset y co-ordinate (cm)
      \param [in] newZOffset The new global offset z co-ordinate (cm)
      \returns a copy of the field map object "rhs", keeping the same fieldMap pointer
    */
    ShipBFieldMap(const std::string& newName, const ShipBFieldMap& rhs,
		  Double_t newXOffset, Double_t newYOffset, Double_t newZOffset);

    //! Destructor
    virtual ~ShipBFieldMap();

    //! Implementation of evaluating the B field
    /*!
      \param [in] position The x,y,z global co-ordinates of the point (cm)
      \param [out] B The x,y,z components of the magnetic field (kGauss = 0.1 tesla)
    */
    virtual void Field(const Double_t* position, Double_t* B);

    //! Set the x global co-ordinate shift
    /*!
      \param [in] xValue The value of the x global co-ordinate shift (cm)
    */
    void SetXOffset(Double_t xValue) {xOffset_ = xValue;}

    //! Set the y global co-ordinate shift
    /*!
      \param [in] yValue The value of the y global co-ordinate shift (cm)
    */
    void SetYOffset(Double_t yValue) {yOffset_ = yValue;}

    //! Set the z global co-ordinate shift
    /*!
      \param [in] zValue The value of the z global co-ordinate shift (cm)
    */
    void SetZOffset(Double_t zValue) {zOffset_ = zValue;}

    //! Get the name of the map file
    /*!
      \returns the name of the map file as an STL string
    */
    std::string GetMapFileName() const {return mapFileName_;}

    //! Get the number of bins along x
    /*!
      \returns the number of bins along x
    */
    Int_t GetNx() const {return Nx_;}

    //! Get the number of bins along y
    /*!
      \returns the number of bins along y
    */
    Int_t GetNy() const {return Ny_;}

    //! Get the number of bins along z
    /*!
      \returns the number of bins along z
    */
    Int_t GetNz() const {return Nz_;}

    //! Get the total numer of bins
    /*!
      \returns the total number of bins
    */
    Int_t GetNBins() const {return N_;}

    //! Get the minimum value of x for the map
    /*!
      \returns the minimum x co-ordinate
    */
    Double_t GetXMin() const {return xMin_;}

    //! Get the maximum value of x for the map
    /*!
      \returns the maximum x co-ordinate
    */
    Double_t GetXMax() const {return xMax_;}

    //! Get the bin width along x for the map
    /*!
      \returns the bin width along x
    */
    Double_t GetdX() const {return dx_;}

     //! Get the x co-ordinate range for the map
    /*!
      \returns the x co-ordinate range
    */
    Double_t GetXRange() const {return xRange_;}

   //! Get the minimum value of y for the map
    /*!
      \returns the minimum y co-ordinate
    */
    Double_t GetYMin() const {return yMin_;}

    //! Get the maximum value of y for the map
    /*!
      \returns the maximum y co-ordinate
    */
    Double_t GetYMax() const {return yMax_;}

    //! Get the bin width along y for the map
    /*!
      \returns the bin width along y
    */
    Double_t GetdY() const {return dy_;}

     //! Get the y co-ordinate range for the map
    /*!
      \returns the y co-ordinate range
    */
    Double_t GetYRange() const {return yRange_;}

    //! Get the minimum value of z for the map
    /*!
      \returns the minimum z co-ordinate
    */
    Double_t GetZMin() const {return zMin_;}

    //! Get the maximum value of z for the map
    /*!
      \returns the maximum z co-ordinate
    */
    Double_t GetZMax() const {return zMax_;}

    //! Get the bin width along z for the map
    /*!
      \returns the bin width along z
    */
    Double_t GetdZ() const {return dz_;}

     //! Get the z co-ordinate range for the map
    /*!
      \returns the z co-ordinate range
    */
    Double_t GetZRange() const {return zRange_;}

    //! Get the x offset co-ordinate of the map for global positioning
    /*!
      \returns the map's x offset co-ordinate for global positioning
    */
    Double_t GetXOffset() const {return xOffset_;}

    //! Get the y offset co-ordinate of the map for global positioning
    /*!
      \returns the map's y offset co-ordinate for global positioning
    */
    Double_t GetYOffset() const {return yOffset_;}

    //! Get the z offset co-ordinate of the map for global positioning
    /*!
      \returns the map's z offset co-ordinate for global positioning
    */
    Double_t GetZOffset() const {return zOffset_;}

    //! Get the boolean flag to specify if we are a "copy"
    /*!
      \returns the boolean copy flag status
    */
    Bool_t IsACopy() const {return isCopy_;}

    //! ClassDef for ROOT
    ClassDef(ShipBFieldMap,1);


 protected:

 private:

    //! Copy constructor not implemented
    ShipBFieldMap(const ShipBFieldMap& rhs);

    //! Copy assignment operator not implemented
    ShipBFieldMap& operator=(const ShipBFieldMap& rhs);

    //! Enumeration to specify the co-ordinate type
    enum CoordAxis {xAxis = 0, yAxis, zAxis};

    //! Initialisation
    void initialise();

    //! Read the field map data and store the information internally
    void readMapFile();

    //! Process the ROOT file containing the field map data
    void readRootFile();

    //! Process the text file containing the field map data
    void readTextFile();

    // ! Set the coordinate limits from information stored in the datafile
    void setLimits();

    //! Check to see if a point is within the map validity range
    /*!
      \param [in] x The x co-ordinate of the point (cm)
      \param [in] y The y co-ordinate of the point (cm)
      \param [in] z The z co-ordinate of the point (cm)
      \returns true/false if the point is inside the field map range
    */
    Bool_t insideRange(Double_t x, Double_t y, Double_t z);

    //! Typedef for an int-double pair
    typedef std::pair<Int_t, Double_t> binPair;

    //! Get the bin number and fractional distance from the leftmost bin edge
    /*!
      \param [in] x The co-ordinate component of the point (cm)
      \param [in] theAxis The co-ordinate axis (CoordAxis enumeration for x, y or z)
      \returns the bin number and fractional distance from the leftmost bin edge as a pair
    */
    binPair getBinInfo(Double_t x, CoordAxis theAxis);

    //! Find the vector entry of the field map data given the bins iX, iY and iZ
    /*!
      \param [in] iX The bin along the x axis
      \param [in] iY The bin along the y axis
      \param [in] iZ The bin along the z axis
      \returns the index entry for the field map data vector
    */
    Int_t getMapBin(Int_t iX, Int_t iY, Int_t iZ);

    //! Calculate the magnetic field component using trilinear interpolation.
    //! This function uses the various "binX" integers and "uFrac" variables
    /*!
      \param [in] theAxis The co-ordinate axis (CoordAxis enumeration for x, y or z)
      \returns the magnetic field component for the given axis
    */
    Double_t BInterCalc(CoordAxis theAxis);

    //! Store the field map information as a vector of 3-vectors, whose order
    //! is given by first incrementing z, then y, then x
    std::vector<TVector3>* fieldMap_;

    //! The name of the map file
    std::string mapFileName_;

    //! Initialisation boolean
    Bool_t initialised_;

    //! Flag to specify if we are a copy of the field map (just a change of global offsets)
    Bool_t isCopy_;

    //! The number of bins along x
    Int_t Nx_;
    
    //! The number of bins along y
    Int_t Ny_;

    //! The number of bins along z
    Int_t Nz_;

    //! The total number of bins
    Int_t N_;

    //! The minimum value of x for the map
    Double_t xMin_;

    //! The maximum value of x for the map
    Double_t xMax_;

    //! The bin width along x
    Double_t dx_;

    //! The co-ordinate range along x
    Double_t xRange_;

    //! The minimum value of y for the map
    Double_t yMin_;

    //! The maximum value of y for the map
    Double_t yMax_;

    //! The bin width along y
    Double_t dy_;

    //! The co-ordinate range along y
    Double_t yRange_;

    //! The minimum value of z for the map
    Double_t zMin_;

    //! The maximum value of z for the map
    Double_t zMax_;

    //! The bin width along z
    Double_t dz_;

    //! The co-ordinate range along z
    Double_t zRange_;

    //! The x value of the positional offset for the map
    Double_t xOffset_;

    //! The y value of the positional offset for the map
    Double_t yOffset_;

    //! The z value of the positional offset for the map
    Double_t zOffset_;

    //! Double converting Tesla to kiloGauss (for VMC/FairRoot B field units)
    Double_t Tesla_;

    //! Bin A for the trilinear interpolation
    Int_t binA_;

    //! Bin B for the trilinear interpolation
    Int_t binB_;

    //! Bin C for the trilinear interpolation
    Int_t binC_;

    //! Bin D for the trilinear interpolation
    Int_t binD_;

    //! Bin E for the trilinear interpolation
    Int_t binE_;

    //! Bin F for the trilinear interpolation
    Int_t binF_;

    //! Bin G for the trilinear interpolation
    Int_t binG_;

    //! Bin H for the trilinear interpolation
    Int_t binH_;

    //! Fractional bin distance along x
    Double_t xFrac_;

    //! Fractional bin distance along y
    Double_t yFrac_;

    //! Fractional bin distance along z
    Double_t zFrac_;

    //! Complimentary fractional bin distance along x
    Double_t xFrac1_;

    //! Complimentary fractional bin distance along y
    Double_t yFrac1_;

    //! Complimentary fractional bin distance along z
    Double_t zFrac1_;


};

#endif
