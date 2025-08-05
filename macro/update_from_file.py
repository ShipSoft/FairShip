import json

def update_from_file(ship_geo, options, file):
    with open(file, 'r') as f:
        data = json.load(f)

    if 'positions' in data:
        stations = data['positions']
        ship_geo.TrackStation1.z=stations[0]
        ship_geo.TrackStation2.z=stations[1]
        ship_geo.TrackStation3.z=stations[2]
        ship_geo.TrackStation4.z=stations[3]
        print(f'Station Z-positions {stations}')
    if 'angles' in data:
        ship_geo.strawtubes.ViewAngle = data['angles']
        print(f"ship_geo.VA was set to {data['angles']}")
    # if 'magnetic_strength' in data:
    #     ship_geo.magnetic_strength = data['magnetic_strength']
    #     print(f'ship_geo.magnetic_strength was set to {data["magnetic_strength"]}')

    ship_geo.z = ship_geo.TrackStation2.z + 0.5 * (ship_geo.TrackStation3.z - ship_geo.TrackStation2.z)
    ship_geo.Bfield.z = ship_geo.z
