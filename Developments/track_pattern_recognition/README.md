# Track Pattern Recognition
<img src="pic/tracks.jpeg" align="center">

This direcroty contains all necessary scripts to run and test track patteern recognition methods. For this run the command: 
```bash
python RunPR.py -i ship.conical.Pythia8-TGeant4.root -g geofile_full.conical.Pythia8-TGeant4.root
```
Results of track pattern recognition will appear in `hists.root` file. 

General options of `RunPR.py`:
```
-i  --input                   : Input file path
-g  --geo                     : Path to geo file
-o  --output                  : Output .root file path. Default is hists.root
-y  --dy                      : dy
-n  --n_reco                  : Number of reconstructible tracks per event is required
-t  --three                   : Is threeprong mumunu decay?
-m  --method                  : Name of a track pattern recognition method: 
                                  'Baseline' - base PR method described in 
                                               https://cds.cern.ch/record/2005715/files/main.pdf
                                  'FH' - a PR method based on Hough Transform, 
                                  'AR' - a method based on Artificial Retina, 
                                  'R' - this method recognizes tracks before and 
                                        after the magnet simultaneously
                                Default is 'Baseline'
-h  --help                    : Shows this help
```

## Code
<img src="pic/code.png" width="50%" align="center">

#### `RunPR.py`
This script runs track pattern recognition with all additional steps: input data and SHiP geometry load, hits smearing, digitization, track pattern recognition, track fit, quality metric plots.

#### `execute.py`
The script contains function which performs pure track pattern recognition without any additional steps.

#### `models` directory
The directory contains scripts of all track pattern recognition methods: Hough Transform, Artificial Retina, ...

#### `pattern_recognition.py`
The file contains functions which use models from the `models` directory to perform SHiP track pattern recognition.

#### `fit.py`
This script contains functions needed to fit recognized tracks.

#### `mctruth.py`
Functions in this script allows to get MC truth data about hits and tracks.

#### `quality.py`
The file has functions to plot quality metrics of SHiP track pattern recognition.

## Requirements
```bash
numpy >= 1.12.1
scipy >= 0.19.0
scikit-learn >= 0.17.1
```
