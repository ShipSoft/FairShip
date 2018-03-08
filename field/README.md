Magnetic fields for the FairShip simulation use the Geant4 VMC ("geant4_vmc") interface,
which associates ROOT [TVirtualMagField](https://root.cern.ch/doc/master/classTVirtualMagField.html)
objects to Geant4 
[G4MagneticField](https://www-zeuthen.desy.de/geant4/geant4.9.3.b01/classG4MagneticField.html) 
ones via the macro command

```
/mcDet/setIsLocalMagField true
```

which is called in the [g4config.in](../gconfig/g4config.in) input file.

Most of the required TVirtualMagField objects are already created in the C++ source code 
where the geometry volumes are defined. The [ShipFieldMaker](ShipFieldMaker.h) class can
be used to create new, extra fields, or replace already existing ones, using an input control 
text file, where we can set global and/or local fields for specific volumes. The VMC uses cm 
for distances and kGauss (0.1 Tesla) for magnetic fields. Here, we use the same cm unit for 
lengths, but use Tesla for magnetic fields, which the ShipFieldMaker class converts to kGauss 
units when passed to the VMC. 

The function

``` 
TVirtuaMagField::Field(const Double_t* pos, Double_t* B)
```

that is implemented in the various derived field classes finds the magnetic field components
and stores them in the array B given the global (not local) co-ordinate position pos.


The script [run_simScript.py](../macro/run_simScript.py) calls the addVMCFields() function defined
in [geomGeant4.py](../python/geomGeant4.py), which creates a ShipFieldMaker object, where its
makeFields() function takes a control file that specifies what magnetic fields are required for the 
simulation. Note that B fields (TVirtualMagFields) already defined in the geometry C++ source code
do not need to be added to this input file. This script can also generate plots of the magnitude of 
the magnetic field in the z-x, z-y and/or x-y plane using the plotField function in 
[ShipFieldMaker](ShipFieldMaker.h). The location of the control file, and any field maps that it 
uses, must be specified relative to the VMCWORKDIR directory.

The structure of the control file, such as [BFieldSetup.txt](BFieldSetup.txt), uses specific 
keywords to denote what each line represents:

```
0) Comment lines start with the # symbol
1) "FieldMap" for using field maps to represent the magnetic field
2) "SymFieldMap" for using field maps with x-y quadrant symmetry
3) "CopyMap" for copying a previously defined field map to another location (saving memory)
4) "Uniform" for creating a uniform magnetic field (no co-ordinate limits)
5) "Constant" for creating a uniform magnetic field with co-ordinate boundary limits
6) "Bell" for creating the Bell shaped magnetic field distribution
7) "Composite" for combining two or more field types/sources
8) "Global" for setting which (single or composite) field is the global one
9) "Region" for setting a local field to a specific volume, including the global field
10) "Local" for only setting a local field to a specific volume, ignoring the global field
```

The syntax for each of the above options are:

1) [FieldMap](ShipBFieldMap.h)

```
FieldMap MapLabel MapFileName [x0 y0 z0] [phi theta psi]
```

where MapLabel is the descriptive name of the field, MapFileName is the location of
the ROOT file containing the field map data (relative to the VMCWORKDIR directory),
x0, y0, z0 are the offset co-ordinates in cm, and phi, theta and psi are the Euler 
rotation angles in degrees about the z axis, the new x axis, and then the new z axis, 
in that order. The offsets and angles are optional parameters (denoted by the square
brackets); offsets still need to be provided (can be set to zero) if angles are required.

A field map that is local to a particular volume is assumed to be centred and aligned 
along the local symmetry axes. For example, if there is a collection of identical magnets 
that all use the same field map, but the magnets have different global positions and 
orientations in the geometry, then we only need to define one field map, with zero offsets 
and angles, using a binning that ensures that the map is centred and aligned along the 
local co-ordinate axes of the magnet shape. The code will then create lightweight copies 
of the field map (reusing the binning data) for each of the magnets, displaced and rotated 
to match their global positions and orientations. This occurs when the map name is used 
in either the Local or Region field-volume definitions described below. If the field map 
definition contains non-zero offsets and angles (i.e. if the original data needs 
displacement or rotation corrections) then these would be applied first before the 
individual volume transformations. A global field map will not apply local volume
transformations, only those offsets and angles that is part of its definition.

The field is calculated by the [ShipBFieldMap](ShipBFieldMap.h) class using trilinear 
interpolation based on the binned map data, which is essentially a 3d histogram.

The structure of the field map ROOT data file is as follows. It should contain two TTrees, 
one called Range which specifies the co-ordinate limits and bin sizes (in cm) using the 
following floating-point precision variables:

```
xMin, xMax, dx, yMin, yMax, dy, zMin, zMax, dz
```

and another one called Data which stores the floating-point precision B field components (T) 

```
Bx, By, Bz
```

assuming the position binning order (iX\*Ny + iY)\*Nz + iZ, where (iX,iY,iZ) is the equivalent
bin for coordinate (x,y,z), and Ny and Nz are the number of y and z bins, respectively.

All variables are stored with floating-point (not double) precision to save both 
disk space as well as memory consumption within the FairShip code.

The script [convertMisisMap.py](convertMisisMap.py) can be used to convert (ascii) field map data 
generated from MISIS engineering work to the ROOT file format for FairShip use. Alternatively, the 
script [convertRALMap.py](convertRALMap.py) can be used to convert (ascii) field map data generated 
by RAL engineers (VectorFields/Opera software output) to the ROOT file format for FairShip use. 


2) [SymFieldMap](ShipBFieldMap.h)

```
SymFieldMap MapLabel MapFileName [x0 y0 z0] [phi theta psi]
```

This reuses the [ShipBFieldMap](ShipBFieldMap.h) class to define a field map where we
have x-y quadrant symmetry: Bx is antisymmetric in x and y, By is symmetric in x and y, 
while no symmetry is assumed for Bz. This implies that Bx changes sign whenever x < 0 
or y < 0; note that Bx remains unchanged when we have both x < 0 and y < 0. We only need to 
store the field components for the positive x and y quadrant co-ordinates in the ROOT file
defined by the MapFileName string (relative to the VMCWORKDIR directory), requiring only
roughly 25% of the memory compared to a full field map. The parameters x0, y0, z0 are the 
offset co-ordinates in cm, and phi, theta and psi are the Euler rotation angles in degrees 
about the z axis, the new x axis, and then the new z axis, in that order. The offsets and 
angles are optional parameters (denoted by the square brackets); offsets still need to be 
provided (can be set to zero) if angles are required.


3) CopyMap

```
CopyMap MapLabel MapToCopy x0 y0 z0 [phi theta psi]
```

where MapToCopy is the name of the (previously defined) map to be copied, with the 
new co-ordinate offsets specified by the values x0, y0 and z0 (cm), as well as the 
optional Euler rotation angles phi, theta and psi (degrees), corresponding to rotations 
about the z, new x and new z axis, in that order. Note that this will reuse the field 
map data already stored in memory.

4) [Uniform](https://root.cern.ch/doc/master/classTGeoUniformMagField.html)

```
Uniform Label Bx By Bz
```

where Bx, By and Bz are the components of the uniform field (in Tesla),
valid for any x,y,z co-ordinate value.

5) [Constant](ShipConstField.h)

```
Constant Label xMin xMax yMin yMax zMin zMax Bx By Bz
```

where xMin, xMax are the global co-ordinate limits along the x axis (in cm),
similarly for the y and z axes, and Bx, By and Bz are the components
of the uniform field in Tesla.

6) [Bell](ShipBellField.h)

```
Bell Label BPeak zMiddle orientInt tubeRad
```

where BPeak is the peak of the magnetic field (in Tesla), zMiddle is
the global z location of the centre of the field (cm), orientInt is an integer
to specify if the field is aligned either along the x (2) or y (1) axes 
(Bz = 0 always), and tubeRad is the radius of the tube (cm) inside the
region which specifies the extent of the field (for Bx).

7) [Composite](ShipCompField.h)

```
Composite CompLabel Label1 ... LabelN
```

where CompLabel is the label of the composite field, comprising of the fields
named Label1 up to LabelN.

8) Global

```
Global Label1 .. LabelN
```

where Label1 to LabelN are the labels of the field(s) that are combined
to represent the global one for the whole geometry.

9) Region

```
Region VolName FieldLabel [FieldMapScaleFactor]
```

where VolName is the name of the TGeo volume, FieldLabel is the name 
of the local field that should be assigned to this volume and FieldMapScaleFactor 
is an optional scaling number that can be used to adjust the (maximum) magnitude 
of any local field map (not other field types). Note that this keyword will 
include the global field if it has been defined earlier in the configuration file, 
i.e. any particle inside this volume will experience the superposition of the 
(scaled) local field with the global one.

10) Local

```
Local VolName FieldLabel [FieldMapScaleFactor]
```

where VolName is again the name of the TGeo volume, FieldLabel is the name 
of the local field that should be assigned to this volume and FieldMapScaleFactor 
is an optional scaling number that can be used to adjust the (maximum) magnitude 
of any local field map (not other field types). This keyword will not include the 
global field, i.e. any particle inside this volume will only see the local one.


As mentioned earlier, magnetic fields for local volumes are enabled for the VMC with the setting 
"/mcDet/setIsLocalMagField true" in the [g4config.in](../gconfig/g4config.in) file. 
Extra options for B field tracking (stepper/chord finders..), such as those mentioned here

https://root.cern.ch/magnetic-field

should be added to the (end of) the g4config.in file.


Other magnetic field classes can use the above interface provided they inherit 
from [TVirtualMagField](https://root.cern.ch/doc/master/classTVirtualMagField.html),
implement the TVirtualMagField::Field() virtual function, and have unique 
keyword-formatted lines assigned to them in the configuration file 
that is then understood by the ShipFieldMaker::makeFields() function, which will 
then create the fields and assign them to volumes in the geometry.
