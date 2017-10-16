/*! \class ShipBFieldMap
  \brief Class that defines a (3d) magnetic field map (distances in cm, fields in tesla)

  \author John Back <J.J.Back@warwick.ac.uk>
*/

#include "ShipBFieldMap.h"

#include "TFile.h"
#include "TTree.h"

#include <fstream>
#include <iostream>

ShipBFieldMap::ShipBFieldMap(const std::string& label,
			     const std::string& mapFileName,
			     Double_t xOffset,
			     Double_t yOffset,
			     Double_t zOffset) : 
    TVirtualMagField(label.c_str()),
    fieldMap_(new std::vector<TVector3>()),
    mapFileName_(mapFileName),
    initialised_(kFALSE), 
    isCopy_(kFALSE),
    Nx_(0), Ny_(0), Nz_(0), N_(0),
    xMin_(0.0), xMax_(0.0), 
    dx_(0.0), xRange_(0.0),
    yMin_(0.0), yMax_(0.0),
    dy_(0.0), yRange_(0.0),
    zMin_(0.0), zMax_(0.0), 
    dz_(0.0), zRange_(0.0),
    xOffset_(xOffset), 
    yOffset_(yOffset),
    zOffset_(zOffset),
    Tesla_(10.0)
{
    this->initialise();
}

ShipBFieldMap::~ShipBFieldMap()
{
    // Delete the internal vector storing the field map values
    if (fieldMap_) {delete fieldMap_;}
}


ShipBFieldMap::ShipBFieldMap(const std::string& newName, const ShipBFieldMap& rhs,
			     Double_t newXOffset, Double_t newYOffset, Double_t newZOffset) :
    TVirtualMagField(newName.c_str()),
    fieldMap_(rhs.fieldMap_),
    mapFileName_(rhs.GetMapFileName()),
    initialised_(kFALSE), 
    isCopy_(kTRUE),
    Nx_(0), Ny_(0), Nz_(0), N_(0),
    xMin_(0.0), xMax_(0.0), 
    dx_(0.0), xRange_(0.0),
    yMin_(0.0), yMax_(0.0),
    dy_(0.0), yRange_(0.0),
    zMin_(0.0), zMax_(0.0), 
    dz_(0.0), zRange_(0.0),
    xOffset_(newXOffset), 
    yOffset_(newYOffset),
    zOffset_(newZOffset),
    Tesla_(10.0)
{
    // Copy constructor with new label and different global offset, which uses
    // the same field map data (pointer) and distance units as the rhs object
    this->initialise();
}

void ShipBFieldMap::Field(const Double_t* position, Double_t* B) 
{

    // Set the B field components given the position vector

    // The point (global) co-ordinates, subtracting any offsets
    Double_t x = position[0] - xOffset_;
    Double_t y = position[1] - yOffset_;
    Double_t z = position[2] - zOffset_;

    //std::cout<<"Offsets: "<<xOffset_<<", "<<yOffset_<<", "<<zOffset_<<std::endl;
    //std::cout<<"Position = "<<position[0]<<", "<<position[1]<<", "<<position[2]<<std::endl;

    // Initialise the B field components to zero
    B[0] = 0.0;
    B[1] = 0.0;
    B[2] = 0.0;

    // First check to see if we are inside the field map range
    Bool_t inside = this->insideRange(x, y, z);
    //std::cout<<"x,y,z = "<<x<<", "<<y<<", "<<z<<", Inside = "<<(int) inside<<std::endl;
    if (inside == kFALSE) {return;}

    // Find the neighbouring bins for the given point
    binPair xBinInfo = this->getBinInfo(x, ShipBFieldMap::xAxis);
    binPair yBinInfo = this->getBinInfo(y, ShipBFieldMap::yAxis);
    binPair zBinInfo = this->getBinInfo(z, ShipBFieldMap::zAxis);

    Int_t iX = xBinInfo.first;
    Int_t iY = yBinInfo.first;
    Int_t iZ = zBinInfo.first;

    // Check that the bins are valid
    if (iX == -1 || iY == -1 || iZ == -1) {return;}

    // Get the various neighbouring bin entries
    Int_t iX1(iX + 1);
    Int_t iY1(iY + 1);
    Int_t iZ1(iZ + 1);

    binA_ = this->getMapBin(iX, iY, iZ);
    binB_ = this->getMapBin(iX1, iY, iZ);
    binC_ = this->getMapBin(iX, iY1, iZ);
    binD_ = this->getMapBin(iX1, iY1, iZ);
    binE_ = this->getMapBin(iX, iY, iZ1);
    binF_ = this->getMapBin(iX1, iY, iZ1);
    binG_ = this->getMapBin(iX, iY1, iZ1);
    binH_ = this->getMapBin(iX1, iY1, iZ1);

    // Retrieve the fractional bin distances
    xFrac_ = xBinInfo.second;
    yFrac_ = yBinInfo.second;
    zFrac_ = zBinInfo.second;

    // Set the complimentary fractional bin distances
    xFrac1_ = 1.0 - xFrac_;
    yFrac1_ = 1.0 - yFrac_;
    zFrac1_ = 1.0 - zFrac_;

    // Finally get the magnetic field components using trilinear interpolation
    B[0] = this->BInterCalc(ShipBFieldMap::xAxis);
    B[1] = this->BInterCalc(ShipBFieldMap::yAxis);
    B[2] = this->BInterCalc(ShipBFieldMap::zAxis);

    //std::cout<<GetName()<<": Bins = "<<iX<<", "<<iY<<", "<<iZ
    //         <<", B = "<<B[0]<<", "<<B[1]<<", "<<B[2]<<std::endl;

}

void ShipBFieldMap::initialise()
{
 
   if (initialised_ == kFALSE) {

	this->readMapFile();
	initialised_ = kTRUE;    

    }

}

void ShipBFieldMap::readMapFile()
{

    std::cout<<"ShipBFieldMap::readMapFile() creating field "<<this->GetName()
	     <<" using file "<<mapFileName_<<std::endl;

    // Check to see if we have a ROOT file
    if (mapFileName_.find(".root") != std::string::npos) {

	this->readRootFile();

    } else {

	this->readTextFile();

    }


}

void ShipBFieldMap::readRootFile() {

    TFile* theFile = TFile::Open(mapFileName_.c_str());

    // Coordinate ranges
    TTree* rTree = dynamic_cast<TTree*>(theFile->Get("Range"));
    rTree->SetBranchAddress("xMin", &xMin_);
    rTree->SetBranchAddress("xMax", &xMax_);
    rTree->SetBranchAddress("dx", &dx_);
    rTree->SetBranchAddress("yMin", &yMin_);
    rTree->SetBranchAddress("yMax", &yMax_);
    rTree->SetBranchAddress("dy", &dy_);
    rTree->SetBranchAddress("zMin", &zMin_);
    rTree->SetBranchAddress("zMax", &zMax_);
    rTree->SetBranchAddress("dz", &dz_);

    // Fill the ranges
    rTree->GetEntry(0);

    this->setLimits();

    if (isCopy_ == kFALSE) {

	// The data is expected to contain Bx,By,Bz data values 
	// in ascending z,y,x co-ordinate order

	fieldMap_->clear();

	TTree* dTree = dynamic_cast<TTree*>(theFile->Get("Data"));
	Double_t Bx, By, Bz;
	dTree->SetBranchStatus("*", 0);
	dTree->SetBranchStatus("Bx", 1);
	dTree->SetBranchStatus("By", 1);
	dTree->SetBranchStatus("Bz", 1);

	dTree->SetBranchAddress("Bx", &Bx);
	dTree->SetBranchAddress("By", &By);
	dTree->SetBranchAddress("Bz", &Bz);

	Int_t nEntries = dTree->GetEntries();
	if (nEntries != N_) {
	    std::cout<<"Expected "<<N_<<" field map entries but found "<<nEntries<<std::endl;
	    nEntries = 0;
	}

	for (Int_t i = 0; i < nEntries; i++) {

	    dTree->GetEntry(i);

	    // B field values are in Tesla. This means these values are multiplied
	    // by a factor of ten since both FairRoot and the VMC interface use kGauss
	    Bx *= Tesla_;
	    By *= Tesla_;
	    Bz *= Tesla_;

	    // Store the B field 3-vector
	    TVector3 BVector(Bx, By, Bz);
	    fieldMap_->push_back(BVector);

	}

    }

    theFile->Close();

}

void ShipBFieldMap::readTextFile() {

    std::ifstream getData(mapFileName_.c_str());

    std::string tmpString("");

    getData >> tmpString >> xMin_ >> xMax_ >> dx_ 
	    >> yMin_ >> yMax_ >> dy_ >> zMin_ >> zMax_ >> dz_;    

    this->setLimits();

    // Check to see if this object is a "copy"
    if (isCopy_ == kFALSE) {

	// Read the field map and store the magnetic field components

	// Second line can be ignored since they are 
	// just labels for the data columns for readability
	getData >> tmpString >> tmpString >> tmpString;
	
	// The remaining lines contain Bx,By,Bz data values 
	// in ascending z,y,x co-ord order
	fieldMap_->clear();

	Double_t Bx(0.0), By(0.0), Bz(0.0);

	for (Int_t i = 0; i < N_; i++) {
	    
	    getData >> Bx >> By >> Bz;

	    // B field values are in Tesla. This means these values are multiplied
	    // by a factor of ten since both FairRoot and the VMC interface use kGauss
	    Bx *= Tesla_;
	    By *= Tesla_;
	    Bz *= Tesla_;

	    // Store the B field 3-vector
	    TVector3 BVector(Bx, By, Bz);
	    fieldMap_->push_back(BVector);
	    
	}

    }

    getData.close();

}

Bool_t ShipBFieldMap::insideRange(Double_t x, Double_t y, Double_t z)
{

    Bool_t inside(kFALSE);

    if (x >= xMin_ && x <= xMax_ && y >= yMin_ &&
	y <= yMax_ && z >= zMin_ && z <= zMax_) {inside = kTRUE;}
	

    return inside;

}

void ShipBFieldMap::setLimits() {

    // Since the default SHIP distance unit is cm, we do not need to convert
    // these map limits, i.e. cm = 1 already

    xRange_ = xMax_ - xMin_;
    yRange_ = yMax_ - yMin_;
    zRange_ = zMax_ - zMin_;

    if (dx_ > 0.0) {
	Nx_ = static_cast<Int_t>(((xMax_ - xMin_)/dx_) + 1.0);
    }
    if (dy_ > 0.0) {
	Ny_ = static_cast<Int_t>(((yMax_ - yMin_)/dy_) + 1.0);
    }
    if (dz_ > 0.0) {
	Nz_ = static_cast<Int_t>(((zMax_ - zMin_)/dz_) + 1.0);
    }

    N_ = Nx_*Ny_*Nz_;

    std::cout<<"x values: "<<xMin_<<", "<<xMax_<<", dx = "<<dx_<<std::endl;
    std::cout<<"y values: "<<yMin_<<", "<<yMax_<<", dy = "<<dy_<<std::endl;
    std::cout<<"z values: "<<zMin_<<", "<<zMax_<<", dz = "<<dz_<<std::endl;

    std::cout<<"Total number of bins = "<<N_
	     <<"; Nx = "<<Nx_<<", Ny = "<<Ny_<<", Nz = "<<Nz_<<std::endl;

}


ShipBFieldMap::binPair ShipBFieldMap::getBinInfo(Double_t u, ShipBFieldMap::CoordAxis theAxis)
{

    Double_t du(0.0), uMin(0.0), Nu(0);

    if (theAxis == ShipBFieldMap::xAxis) {
	du = dx_; uMin = xMin_; Nu = Nx_;
    } else if (theAxis == ShipBFieldMap::yAxis) {
	du = dy_; uMin = yMin_; Nu = Ny_;
    } else if (theAxis == ShipBFieldMap::zAxis) {
	du = dz_; uMin = zMin_; Nu = Nz_;
    }

    Int_t iBin(-1);
    Double_t fracL(0.0);

    if (du > 1e-10) {

	// Get the number of fractional bin widths the point is from the first volume bin
	Double_t dist = (u - uMin)/du;
	// Get the integer equivalent of this distance, which is the bin number
	iBin = static_cast<Int_t>(dist);
	// Get the actual fractional distance of the point from the leftmost bin edge
	fracL = (dist - iBin*1.0);

    }

    // Check that the bin number is valid
    if (iBin < 0 || iBin >= Nu) {
	iBin = -1; fracL = 0.0;
    }

    // Return the bin number and fractional distance of the point from the leftmost bin edge
    binPair binInfo(iBin, fracL);

    return binInfo;

}

Int_t ShipBFieldMap::getMapBin(Int_t iX, Int_t iY, Int_t iZ)
{

    // Get the index of the map entry corresponding to the x,y,z bins.
    // Remember that the map is ordered in ascending z, y, then x

    Int_t index = (iX*Ny_ + iY)*Nz_ + iZ;
    if (index < 0) {
	index = 0;
    } else if (index >= N_) {
	index = N_;
    }

    return index;

}

Double_t ShipBFieldMap::BInterCalc(CoordAxis theAxis)
{

    // Find the magnetic field component along theAxis using trilinear 
    // interpolation based on the current position and neighbouring bins
    Double_t result(0.0);

    Int_t iAxis(0);

    if (theAxis == CoordAxis::yAxis) {
	iAxis = 1;
    } else if (theAxis == CoordAxis::zAxis) {
	iAxis = 2;
    }

    if (fieldMap_) {

	// Get the field component values for the neighbouring bins
	Double_t A = (*fieldMap_)[binA_](iAxis);
	Double_t B = (*fieldMap_)[binB_](iAxis);
	Double_t C = (*fieldMap_)[binC_](iAxis);
	Double_t D = (*fieldMap_)[binD_](iAxis);
	Double_t E = (*fieldMap_)[binE_](iAxis);
	Double_t F = (*fieldMap_)[binF_](iAxis);
	Double_t G = (*fieldMap_)[binG_](iAxis);
	Double_t H = (*fieldMap_)[binH_](iAxis);

	// Perform linear interpolation along x
	Double_t F00 = A*xFrac1_ + B*xFrac_;
	Double_t F10 = C*xFrac1_ + D*xFrac_;
	Double_t F01 = E*xFrac1_ + F*xFrac_;
	Double_t F11 = G*xFrac1_ + H*xFrac_;

	// Linear interpolation along y
	Double_t F0 = F00*yFrac1_ + F10*yFrac_;
	Double_t F1 = F01*yFrac1_ + F11*yFrac_;

	// Linear interpolation along z
	result = F0*zFrac1_ + F1*zFrac_;

    }

    return result;

}
