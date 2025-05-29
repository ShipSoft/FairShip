import pandas as pd
import numpy as np

def update_from_file(ship_geo, options, file):
    
    data = pd.read_csv(file)

    keys = data['key'].tolist()
    values = data['value'].tolist()

    for key, value in zip(keys, values):
        parts = key.split(".")

        target = locals()[parts[0]]
        for part in parts[1:-1]:
            target = getattr(target, part)

        if hasattr(target, parts[-1]):
            if parts[0] == 'options':
                value = int(value)
            setattr(target, parts[-1], value)
            print(f'{key} was set to {value}')

    # update dependent values
    ship_geo.z = ship_geo.TrackStation2.z + 0.5 * (ship_geo.TrackStation3.z - ship_geo.TrackStation2.z)
    ship_geo.Bfield.z = ship_geo.z

