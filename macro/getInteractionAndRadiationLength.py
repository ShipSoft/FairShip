from array import array

# get dimensions by running getGeoInformation on the geofile 
# python $FAIRSHIP/macro/getGeoInformation.py -g geofile_full.conical.Genie-TGeant4.root

# python -i $FAIRSHIP/macro/run_simScript.py --Genie -f /eos/experiment/ship/data/GenieEvents/genie-nu_mu.root
start=array('d',[0,0,3666.5])
end=array('d',[0,0,3898.700])
mparam=array('d',[0,0,0,0,0,0,0,0,0,0,0,0])
Geniegen.MeanMaterialBudget(start, end, mparam)

print mparam[8], " equivalent interaction length fraction"
print mparam[1], " equivalent rad length fraction"

