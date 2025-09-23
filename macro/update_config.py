import json
from ShipGeoConfig import AttrDict

def update_config(global_config, my_config, name):
    with open(my_config, 'r') as f:
        data = json.load(f)
    new_values = AttrDict(data[name])
    if name == 'geometry':
        stations = new_values.positions
        global_config.TrackStation1.z=stations[0]
        global_config.TrackStation2.z=stations[1]
        global_config.TrackStation3.z=stations[2]
        global_config.TrackStation4.z=stations[3]
        print(f'Station Z-positions {stations}')
        #global_config.strawtubes.ViewAngle = new_values.angles
        #print(f"ship_geo.VA was set to {data['angles']}")
    # if 'magnetic_strength' in data:
    #     ship_geo.magnetic_strength = data['magnetic_strength']
    #     print(f'ship_geo.magnetic_strength was set to {data["magnetic_strength"]}')

        global_config.z = global_config.TrackStation2.z + 0.5 * (global_config.TrackStation3.z - global_config.TrackStation2.z)
        global_config.Bfield.z = global_config.z
    if name == 'options':
        global_config.theSeed = new_values.theSeed
        global_config.nEvents = new_values.nEvents
