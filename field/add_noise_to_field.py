import pandas as pd
import numpy as np
import matplotlib.pylab as plt
from scipy.ndimage import gaussian_filter
import random
import argparse
import os

def plot_my_hist(datum):
    plotData = datum[datum['y'] == 0]
    H, xedges, yedges = np.histogram2d(plotData['x'], plotData['z'], bins=[50, 500], weights=plotData['by'])
    plt.figure(figsize=[20, 10])
    plt.imshow(H, interpolation='nearest', origin='low')
    # plt.colorbar()
    plt.show()

def generate_file(input_fileName, output, xSpace=73, ySpace=128, zSpace=1214, step=2.5, args=None):
    # (min, max, max/stepSize + 1)  in case of Z: (0, nSteps*2.5 - 2.5, nSteps)
    field = pd.read_csv(input_fileName, skiprows=1, sep ='\s+', names=['x', 'y', 'z', 'bx', 'by', 'bz'])

    field_mask = field.copy()
    field_mask[['bx', 'by', 'bz']] = field_mask[['bx', 'by', 'bz']] != 0

    field_new = field.copy()

    if args.sidesOnly:
        temp_by = np.array(field_new['by']).reshape([xSpace, ySpace, zSpace])
        temp_by = gaussian_filter(temp_by, sigma=args.sigma)
        field_new['by'] = temp_by.reshape(-1)
        field_new['by'] = field_new['by'] * field_mask['by']
        rezult = field_new
    else:
        field_new[['bx', 'by', 'bz']] = 0
        index_range = np.random.choice(field_new.index, size=args.nCores)
        field_new.loc[index_range, 'by'] = random.uniform(-args.peak, args.peak)
        temp_by = np.array(field_new['by']).reshape([xSpace, ySpace, zSpace])
        temp_by = gaussian_filter(temp_by, sigma=args.sigma)
        field_new['by'] = temp_by.reshape(-1)
        field_new['by'] = field_new['by'] / (field_new['by'].abs().max())  # *field_mask['by']
        field_new['by'] = field_new['by'] * field_mask['by']
        rezult = field.copy()
        rezult['by'] = rezult['by'] + rezult['by'] * field_new['by'] * args.fraction

    # plot_my_hist(field_mask)
    # plot_my_hist(field)
    # plot_my_hist(field_new)
    # plot_my_hist(rezult)
    rezult.to_csv(output, sep='\t', header=None, index=None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process field.')
    parser.add_argument('--input', default=os.path.expandvars("$FAIRSHIP/files/fieldMap.csv"), type=str, action='store')
    parser.add_argument('--output', default=os.path.expandvars("$FAIRSHIP/files/noisy_fieldMap.csv"), type=str, action='store')
    parser.add_argument('--sidesOnly', default=False,  action='store_true')
    parser.add_argument('--sigma', default=30, type=float, action='store')
    parser.add_argument('--nCores', default=1000, type=int, action='store')
    parser.add_argument('--peak', default=500, type=float, action='store')
    parser.add_argument('--fraction', default=0.4, type=float, action='store')
    args = parser.parse_args()

    with open(args.input) as f:
        first_line = f.readline().strip().split()

    generate_file(args.input, args.output,
                  xSpace=int(first_line[0]),
                  ySpace=int(first_line[1]),
                  zSpace=int(first_line[2]),
                  step=float(first_line[3]), args=args)