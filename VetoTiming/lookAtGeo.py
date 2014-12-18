import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
from ShipGeoConfig import ConfigRegistry
from ROOT import *

# function to prepare two dictionaries: one that has the node names as key and the related intex 
# in the nodes array as value and the other one with key and value swapped. 
def prepareNodeDictionaries(nodes):
    # key: index, value: name of the node
    nodeDict_index = {}
    # key: name of the node, value: index
    nodeDict_name = {}
    for (i,n) in enumerate(nodes):
        #print i,n.GetName()
        nodeDict_index[i]=n.GetName()
        nodeDict_name[n.GetName()]=i
    return {'nodeDict_index':nodeDict_index, 'nodeDict_name':nodeDict_name}

# function to print the node names and their index. Usefull to search the name of the element you would like
# to study if you don't know it by heart. Then the name can be used with the other functions for the specific studies.
def searchForNodes(inputFile):
    r = loadGeometry(inputFile)
    fGeo = r['fGeo']
    ## Get the top volume
    fGeo = ROOT.gGeoManager
    tv = fGeo.GetTopVolume()
    nodes = tv.GetNodes()
    for (i,n) in enumerate(nodes):
        print i,n.GetName()

def searchForNodes2(inputFile):
    r = loadGeometry(inputFile)
    fGeo = r['fGeo']
    ## Get the top volume
    #fGeo = ROOT.gGeoManager
    tv = fGeo.GetTopVolume()
    nodes = tv.GetNodes()
    for (i,n) in enumerate(nodes):
        print i,n.GetName(),findPositionElement(n)['z'],findDimentionBoxElement(n)['z']

        
# basic function to be called to load the geometry from a file        
def loadGeometry(inputFile):
    dy = float( inputFile.split("/")[-1].split(".")[1])

    ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy )
    # init geometry and mag. field
    ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy )
    # -----Create geometry----------------------------------------------
    import shipDet_conf

    tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
    geofile = inputFile.replace('ship.','geofile_full.').replace('_rec.','.')
    gMan  = tgeom.Import(geofile)
    fGeo = ROOT.gGeoManager
    return {'fGeo':fGeo,'gMan':gMan}

def getNode(nodeName,fGeo=None):
    if fGeo is None:
        r = loadGeometry(inputFile)
        fGeo = r['fGeo']
    tv = fGeo.GetTopVolume()
    nodes = tv.GetNodes()
    dicts = prepareNodeDictionaries(nodes)
    return nodes[dicts['nodeDict_name'][nodeName]]
    
def findDimentionBoxElement(node):
    ## GetDZ() etc gives you half of the dimention
    sh = node.GetVolume().GetShape()
    return {'x':sh.GetDX(),
            'y':sh.GetDY(),
            'z':sh.GetDZ()}

def findPositionElement(node):
    pos = node.GetMatrix().GetTranslation()
    
    return {'x':pos[0],
            'y':pos[1],
            'z':pos[2]}
    
## inputFile: file used from which I would like to retrive the geometry used
## myNodes_name: geometrical elements I would like to analyse (find the position)
def findPositionGeoElement(inputFile, myNodes_name):
 
    r = loadGeometry(inputFile)
    fGeo = r['fGeo']
    #volumes = gMan.GetListOfVolumes()
    #for v in volumes:
    #    print v.GetName(), v.GetNumber()
    
    ## Get the top volume
    
    tv = fGeo.GetTopVolume()
    nodes = tv.GetNodes()

    tmp = prepareNodeDictionaries(nodes)
    nodeDict_name = tmp['nodeDict_name']
    res = {}
    for nd_name in myNodes_name:
        nd_index = nodeDict_name[nd_name]
        nd = nodes[nd_index]
        pos = findPositionElement(nd)
        dims = findDimentionBoxElement(nd)
        res[nd_name]={'z':pos['z'],
                      'dimZ':dims['z'],
                      'node':nd}
    return res

#inputFile = "../data/neutrino661/ship.10.0.Genie-TGeant4_D.root"
##searchForNodes(inputFile)

### nodes name to be looked at
#myNodes_name = ["volLayer2_%s"%i for i in xrange(0,12)]
#myGeoEl = findPositionGeoElement(inputFile, myNodes_name)
#print myGeoEl

##print myGeoEl["volLayer2_0"]['z'],myGeoEl["volLayer2_11"]['z']
##print myGeoEl["volLayer2_11"]['z']-myGeoEl["volLayer2_0"]['z']
