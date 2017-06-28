
Magnetic fields for the FairShip simulation use the Geant4 VMC ("geant4_vmc") interface.
The [ShipFieldMaker](ShipFieldMaker.h) class is used to create fields, setting them to be either
global and/or local fields to specific volumes in the geometry. The VMC uses cm for 
distances and kGauss (0.1 Tesla) for magnetic fields. Here, we use the same cm unit for 
lengths, but use Tesla for magnetic fields, which the ShipFieldMaker class converts to 
kGauss units when passed to the VMC.

The script [g4Config.C](../gconfig/g4Config.C) creates a ShipFieldMaker pointer, whose makeFields 
function takes a control file that specifies what magnetic fields are required for the simulation. 
This script can also generate plots of the magnitude of the magnetic field in the z-x, z-y and/or x-y
plane using the plotField functions in [ShipFieldMaker](ShipFieldMaker.h). The location of the control 
file, and any field maps that it uses, must be specified relative to the VMCWORKDIR directory.

The structure of the control file, such as [BFieldSetup.txt](BFieldSetup.txt), uses specific 
keywords to denote what each line represents:

```
0) Comment lines start with the # symbol
1) "FieldMap" for using field maps to represent the magnetic field
2) "CopyMap" for copying a previously defined field map to another location (saving memory)
3) "Uniform" for creating a uniform magnetic field (no co-ordinate limits)
4) "Constant" for creating a uniform magnetic field with co-ordinate boundary limits
5) "Bell" for creating the Bell shaped magnetic field distribution
6) "Composite" for combining two or more field types/sources
7) "Global" for setting which (single or composite) field is the global one
8) "Region" for setting a local field to a specific volume, including the global field
9) "Local" for only setting a local field to a specific volume, ignoring the global field
```

The syntax for each of the above options are:

1) FieldMap

```
FieldMap MapLabel MapFileName x0 y0 z0
```

where MapLabel is the descriptive name of the field, MapFileName is the location of
the file containing the field map data (relative to the VMCWORKDIR directory), and 
x0,y0,z0 are the offset co-ordinates in cm for centering the field map.

The field from a map is calculated by the [ShipBFieldMap](ShipBFieldMap.h) class using trilinear 
interpolation based on the binned map data, which is essentially a 3d histogram.

The structure of the field map data file is as follows. The first line should be:

```
CLimits xMin xMax dx yMin yMax dy zMin zMax dz
```

where xMin, xMax and dx are the minimum, maximum and bin-width values (in cm) along 
the x axis, respectively, with similar values for the y and z axes.

The second line should contain the line

```
Bx(T) By(T) Bz(T)
```

which is just a label so that the user knows the following lines contain the 
field components.

The rest of the lines should contain the Bx, By and Bz components of the field
(in Tesla) for each "bin" in the order of increasing z, increasing y, then 
increasing x co-ordinates. 

The first data line corresponds to the point (xMin, yMin, zMin). The next set of 
lines correspond to the points (xMin, yMin, dz * zBin + zMin). 
After we reach z = zMax, z is reset to zMin, y is incremented using y = dy * yBin + yMin,
and the rest of the lines follow by incrementing z up to zMax as before. When y = yMax 
has been reached, x is incremented by dx, while the y and z values are reset to 
yMin and zMin, and are both incremented using the same logic as before. This is repeated 
until the very last line of the data, which will correspond to the point (xMax, yMax, zMax).

There are three field maps provided, created by Victoria Bayliss and Tom Rawlings from RAL,
which have a positional resolution of 10 cm for x,y,z. To save on disk space, they have a 
B-field precision down to 0.01 mT and are compressed. The script [convertMap.py](convertMap.py)
was used to convert the RAL field maps for FairShip use.

* [MuonFilterBFieldMap1.txt.gz](MuonFilterBFieldMap1.txt.gz) Using original co-ordinates for the steel
* [MuonFilterBFieldMap2.txt.gz](MuonFilterBFieldMap2.txt.gz) Magnet C0 inner and outer gap moved from 0 to 2 cm
* [MuonFilterBFieldMap3.txt.gz](MuonFilterBFieldMap3.txt.gz) Simplified overall magnet shape for manufacturing considerations with the 2 cm gap for magnet C0
* [MuonFilterBFieldMap4.txt.gz](MuonFilterBFieldMap4.txt.gz) As map 3, but gaps between the magnets (A0, B0, C0, C4, ...) reduced from 30 cm to 10 cm
* [MuonFilterBFieldMap5.txt.gz](MuonFilterBFieldMap5.txt.gz) As map 3, but using US1010 steel instead of grain-oriented steel

Only one of these field maps should be used as the global field map in [BFieldSetup.txt](BFieldSetup.txt). 
They need to be uncompressed before the simulation can be run; the [macro/run_simScript.py]
(../macro/run_simScript.py) run file currently does this automatically.

2) CopyMap

```
CopyMap MapLabel MapToCopy x0 y0 z0
```

where MapToCopy is the name of the (previously defined) map to be copied, with the 
new co-ordinate offset specified by the values x0,y0,z0 (cm). Note that this will
reuse the field map data already stored in memory.

3) Uniform

```
Uniform Label Bx By Bz
```

where Bx, By and Bz are the components of the uniform field (in Tesla),
valid for any x,y,z co-ordinate value.

4) Constant

```
Constant Label xMin xMax yMin yMax zMin zMax Bx By Bz
```

where xMin, xMax are the co-ordinate limits along the x axis (in cm),
similarly for the y and z axes, and Bx, By and Bz are the components
of the uniform field in Tesla.

5) [Bell](ShipBellField.h)

```
Bell Label BPeak zMiddle orientInt tubeRad
```

where BPeak is the peak of the magnetic field (in Tesla), zMiddle is
the z location of the centre of the field (cm), orientInt is an integer
to specify if the field is aligned either along the x (2) or y (1) axes
 (Bz = 0 always), and tubeRad is the radius of the tube (cm) inside the
region which specifies the extent of the field (for Bx).

6) Composite

```
Composite CompLabel Label1 ... LabelN
```

where CompLabel is the label of the composite field, comprising of the fields
named Label1 up to LabelN.

7) Global

```
Global Label1 .. LabelN
```

where Label1 to LabelN are the labels of the field(s) that are combined
to represent the global one for the whole geometry.

8) Region

```
Region VolName FieldLabel
```

where VolName is the name of the TGeo volume and FieldLabel is the
name of the local field that should be assigned to this volume. Note that this
will include the global field if it has been defined earlier in the 
configuration file, i.e. any particle inside this volume will experience
the superposition of the local field with the global one.

9) Local

```
Local VolName FieldLabel
```

where VolName is again the name of the TGeo volume and FieldLabel
is the name of the local field that should be assigned to this volume. This
will not include the global field, i.e. any particle inside this volume will
only see the local one.


Magnetic fields for local volumes are pre-enabled for the VMC with the setting 
"/mcDet/setIsLocalMagField true" in the [g4config.in](../gconfig/g4config.in) file. 
Extra options for B field tracking (stepper/chord finders..), such as those mentioned here

https://root.cern.ch/drupal/content/magnetic-field

should be added to the (end of) the g4config.in file.


Other magnetic field classes can use the above interface provided they inherit 
from [TVirtualMagField](https://root.cern.ch/root/htmldoc/TVirtualMagField.html), 
implement the TVirtualMagField::Field() virtual function, and have unique 
keyword-formatted lines assigned to them in the configuration file 
that is then understood by the ShipFieldMaker::makeFields() function, which will 
then create the fields and assign them to volumes in the geometry.
