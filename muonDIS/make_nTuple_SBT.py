import ROOT as r
import os
import argparse
import gc  
import shipunit as u


# ROOT setup
r.PyConfig.IgnoreCommandLineOptions = True

# Argument parser setup
parser = argparse.ArgumentParser(description='Script to collect muons hitting the SBT')
parser.add_argument("-test", dest="testing_code", help="Run Test", required=False, action="store_true")
parser.add_argument("-p", dest="path", help="path to muon background files", required=True)
parser.add_argument('-o', '--outputfile', default='muonsProduction_wsoft_SBT.root')
args = parser.parse_args()

# Histogram setup
hnumSegPermmuon = r.TH1I('hnumSegPermmuon', 'Numbers of fired segments per muon', 200, 0., 200)
hPmuon = r.TH1F('hPmuon', 'The momentum of the muons hitting the SBT', 400, 0., 400)

# Initialize variables
ev = 0
processed_events = set()

if args.testing_code: 
    print("test code, output file name overwritten as: muonsProduction_wsoft_SBT_test.root")
    args.outputfile='muonsProduction_wsoft_SBT_test.root'
    selectedmuons='SelectedMuonsSBT_test.txt'
else:
    selectedmuons='SelectedMuonsSBT.txt'

path = args.path 
fsel = open(selectedmuons, "w")

output_file = r.TFile(args.outputfile, 'recreate')
output_tree = r.TTree('MuonAndSoftInteractions', 'Muon information and soft interaction tracks')

imuondata = r.TVectorD(9)  # 9 values: pid, px, py, pz, x, y, z, weight,time_of_hit
output_tree.Branch('imuondata', imuondata)

track_array = r.TObjArray()
output_tree.Branch('tracks', track_array)

muon_vetoPoints    = r.TClonesArray("vetoPoint")
output_tree.Branch('muon_vetoPoints', muon_vetoPoints)


for inputFile in os.listdir(path):
    #print(f"Processing file: {inputFile}")    
    if args.testing_code and ev >= 100000:
        break

    f = r.TFile.Open(os.path.join(path, inputFile), 'read')

    if not f or f.IsZombie():
        print(f"Failed to open file {inputFile}")
        continue

    tree = f.Get("cbmsim")  
    if not tree:
        #print(f"Tree 'cbmsim' not found in file {inputFile}.")
        f.Close()
        continue

    for event in tree:

        ev += 1
        numHitsPermuon = 0
        
        #saving soft tracks
        track_array.Clear()
        muon_id = next((itrk for itrk in range(event.MCTrack.GetEntries()) if abs(event.MCTrack[itrk].GetPdgCode()) == 13), None)
        for track in event.MCTrack:
            if track.GetMotherId()==muon_id and (not track.GetProcName().Data() =='Muon nuclear interaction' ):
                track_array.Add(track)
        
        index=0
        muon_vetoPoints.Clear()

        #saving the incoming muon's veto response
        for hit in event.vetoPoint:
            
            detID = hit.GetDetectorID()
            pid = hit.PdgCode()
            if 1000 < detID < 999999 and abs(pid) == 13:
                if muon_vetoPoints.GetSize() == index:
                    muon_vetoPoints.Expand(index+1)
                muon_vetoPoints[index] = hit
                index+=1

        for hit in event.vetoPoint:
            
            detID = hit.GetDetectorID()
            pid = hit.PdgCode()
            trackID = hit.GetTrackID()

            if 1000 < detID < 999999 and abs(pid) == 13:
            
                if ev not in processed_events:
                    processed_events.add(ev)
                    numHitsPermuon += 1
                    P = r.TMath.Sqrt(hit.GetPx()**2 + hit.GetPy()**2 + hit.GetPz()**2)
                    weight = event.MCTrack[trackID].GetWeight()
                    hPmuon.Fill(P, weight)

                    if P > 3 / u.GeV:
                        
                        imuondata[0] = float(pid)
                        imuondata[1] = float(hit.GetPx() / u.GeV)
                        imuondata[2] = float(hit.GetPy() / u.GeV)
                        imuondata[3] = float(hit.GetPz() / u.GeV)
                        imuondata[4] = float(hit.GetX() / u.m)
                        imuondata[5] = float(hit.GetY() / u.m)
                        imuondata[6] = float(hit.GetZ() / u.m)
                        imuondata[7] = float(weight)
                        imuondata[8] = float(hit.GetTime())
                        
                        output_tree.Fill()
                
                        fsel.write(f"{pid} {hit.GetPx() / u.GeV} {hit.GetPy() / u.GeV} {hit.GetPz() / u.GeV} {hit.GetX() / u.m} {hit.GetY() / u.m} {hit.GetZ() / u.m} {weight}\n")

                else:
                    numHitsPermuon += 1
                    
        if numHitsPermuon != 0:
            hnumSegPermmuon.Fill(numHitsPermuon)

    f.Close()
    gc.collect() 

try:
    output_file.cd() 
    output_tree.Write()
    hnumSegPermmuon.Write()
    hPmuon.Write()
    output_file.Close()
except Exception as e:
    print(f"Error saving output file: {e}")

fsel.close()

print("------------------------------------------------------file saved, reading",args.outputfile, " now----------------------------------------------------------------")


file = r.TFile(args.outputfile, 'read')
if not file or file.IsZombie():
    print(f"Failed to open file ")
    exit(1)

tree = file.Get("MuonAndSoftInteractions")
if not tree:
    print(f"Tree 'MuonAndSoftInteractions' not found in file")
    file.Close()
    exit(1)

print(f"Processing tree: {tree.GetName()}")
print(f"Total number of entries: {tree.GetEntries()}")

for event in tree:

    imuondata = event.imuondata  
    pid = imuondata[0]
    px = imuondata[1]
    py = imuondata[2]
    pz = imuondata[3]
    x = imuondata[4]
    y = imuondata[5]
    z = imuondata[6]
    weight = imuondata[7]
    time_hit = imuondata[8]
    num_tracks = len(event.tracks) 

    print(f"Muon PID: {pid},  x: {x}, y: {y}, z: {z}, t_muon: {time_hit}, Number of soft tracks in this event: {num_tracks}")
    

file.Close()

#python make_nTuple_SBT.py -p <path to muonbackground files>