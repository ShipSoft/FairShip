import ROOT as r
import os
import argparse

parser = argparse.ArgumentParser(description='Script to collect muons hitting the SBT')
parser.add_argument('-f', '--inputfile', default='ship.conical.muonDIS-TGeant4.root')
parser.add_argument('-m', '--muonfile', default='muonDis_0.root')
args = parser.parse_args()

# Open the existing ROOT file in update mode
inputFile = r.TFile.Open(args.inputfile, "UPDATE") 
sTree = inputFile.Get("cbmsim")  

# Open the external file with additional vetoPoints
muonFile = r.TFile.Open(args.muonfile, "READ")  
muonTree = muonFile.Get('DIS') 

# Create a new file for the updated tree
outputFile = r.TFile('ship.conical.muonDIS-TGeant4_temp.root', "RECREATE")
newTree = sTree.CloneTree(0)  # Clone the structure of the existing tree, but do not copy the entries

# Access the vetoPoints branch in the original and external trees
originalVetoPoints  = r.TClonesArray("vetoPoint")
muonVetoPoints      = r.TClonesArray('vetoPoint')
combinedVetoPoints  = r.TClonesArray("vetoPoint")

sTree.SetBranchAddress("vetoPoint", originalVetoPoints)
muonTree.SetBranchAddress("muon_vetoPoints", muonVetoPoints)
newTree.SetBranchAddress("vetoPoint", combinedVetoPoints )

# Loop over all entries and combine the vetoPoints
for i in range(sTree.GetEntries()):
    
    sTree.GetEntry(i)
    muonTree.GetEntry(i)

    interaction_point = r.TVector3()  
    sTree.MCTrack[0].GetStartVertex(interaction_point)         


    # Clear and update the vetoPoints
    combinedVetoPoints.Clear()
    
    index=0

    # Copy original vetoPoints
    for hit in originalVetoPoints:
        if combinedVetoPoints.GetSize() == index:
            combinedVetoPoints.Expand(index+1)
        combinedVetoPoints[index] = hit
        index+=1
    
    for hit in muonVetoPoints:
        if hit.GetZ()<interaction_point.Z():
            if combinedVetoPoints.GetSize() == index:
                combinedVetoPoints.Expand(index+1)
            combinedVetoPoints[index] = hit
            index+=1
            
    newTree.Fill()

# Write the updated tree to the output file
newTree.Write()
outputFile.Close()
inputFile.Close()
muonFile.Close()

# Replace the old file with the new file
os.replace('ship.conical.muonDIS-TGeant4_temp.root', args.inputfile)

print(f"Updated file saved as {args.inputfile}")