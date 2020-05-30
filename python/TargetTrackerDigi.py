#!/usr/bin/python

import ROOT
import numpy as np
import math
import random
import matplotlib.pyplot as plt

from ROOT.TMath import Landau, Gaus, Poisson
from ShipGeoConfig import ConfigRegistry

__author__ = 'Petrov Aleksandr'

def cm_to_chan(locpos):
	'''
	Connection between local geo position [cm] and channel number [ch].
	'locpos' is local geo position and has range [-13.06/2, +13.06/2]
	hw - halfwidth four packages in setup, 512 channels
	pitch - width of a channel
	charr - width of the die (64 channel assembly without gap)
	edge - distance from package edge to sensitive area of array
	gap - gap between two 64-channel dies in the array (128 channels)
	array - width of the array, 3.259 cm
	gaparr - additional gap between two arrays 
	biggap - edge+edge+gaparr = 0.042 [cm] between two arrays
	'''
	hw = 13.06 / 2.
	pitch = 0.025
	charr = 1.6
	edge = 0.017
	gap = 0.025
	array = gap + 2.*charr
	gaparr = 0.008
	biggap = 2.*edge + gaparr
	interval = (
		(-hw, -hw+edge, False), # 1 gap
		(-hw+edge, -hw+edge+charr, 0), # I sipm
		(-hw+edge+charr, -hw+edge+charr+gap, False), # 2 gap
		(-hw+edge+charr+gap, -hw+edge+array, 1), # II sipm
		(-hw+edge+array, -hw+edge+array+biggap, False), # 3 gap
		(-hw+edge+array+biggap, -hw+edge+array+biggap+charr, 2), # III sipm
		(-hw+edge+array+biggap+charr, -hw+edge+array+biggap+charr+gap, False), # 4 gap
		(-hw+edge+array+biggap+charr+gap, -hw+edge+array+biggap+array, 3), # IV sipm
		(-hw+edge+array+biggap+array, biggap/2., False), # 5 gap
		(biggap/2., biggap/2.+charr, 4), # V sipm
		(biggap/2.+charr, biggap/2.+charr+gap, False), # 6 gap
		(biggap/2.+charr+gap, biggap/2.+array, 5), # VI sipm
		(biggap/2.+array, biggap/2.+array+biggap, False), # 7 gap
		(biggap/2.+array+biggap, biggap/2.+array+biggap+charr, 6), # VII sipm
		(biggap/2.+array+biggap+charr, biggap/2.+array+biggap+charr+gap, False), # 8 gap
		(biggap/2.+array+biggap+charr+gap, biggap/2.+array+biggap+charr+array, 7), # VIII sipm
		(biggap/2.+array+biggap+charr+array, biggap/2.+array+biggap+charr+array+edge, False) # 9 gap
	)
	channel_for_gaps = {
	# If the event is in a dead space the channel is selected
		0.: 0.5, 
		1.: 64.5,
		2.: 128.5, 
		3.: 192.5,
		4.: 256.5, 
		5.: 320.5,
		6.: 384.5,
		7.: 448.5, 
		8.: 512.5
	}
	for left, right, sipmnum in interval:
		if left < locpos < right:
			if not sipmnum is False:
				# return (locpos - left + charr*sipmnum) / pitch - 0.5
				return 512 - ((locpos - left + charr*sipmnum) / pitch - 0.5)
			else:
				# return channel_for_gaps.get((locpos + hw) // charr, False)
				# print 'GAP: ch={} ; lpos={} '.format(channel_for_gaps.get(
				# 	(8 - (locpos + hw) // charr), False), locpos)
				return channel_for_gaps.get(
					(8 - (locpos + hw) // charr), False)
	return False  

def chan_to_cm (channelpos):
	'''
	Connection between channel number [ch] and geometrical position [cm]
	Here channelpos is the cluster weighted mean position [ch]
	sipm - sipm array of 128 channels; for one scifi mat the sipm_array has number 0, 1, 2 or 3 
	die - which die (first or second 64 ch. part) of the sipm array; to count gap between dies => 0 or 1
	channel_die - which channel in the die (stamp?) pitch => 0, 1, ..., or 63
	pos_in_channel - local position [channel]

	SiPMs are placed for Y: +(length of vert. mat)/2 and for X: -(length of hor. mat)/2. 
	Position range for one mat: [-len/2, +len/2], where len = 13.06 [cm].
	Channel numbering is the opposite of the X and Y axes
	'''
	channelpos_ = 512 - channelpos
	sipm_array = int(channelpos / 128) 
	die = (int(channelpos) / 64) % 2
	channel_die = int(channelpos) % 64
	pos_in_channel = channelpos - int(channelpos)
	locpos = (sipm_array * (3.259 - 2*0.017 + 0.042) + die * (1.6 + 0.025) + 
			 (channel_die + pos_in_channel) * 0.025 + (-13.06/2 + 0.017 + 0.025/2))
	return -locpos

def get_mat_info(det_id):
	'''
	Return: horizontal or vertical plane, num of TT station, 
	mat num, total num of mats in the plane, len of mats
	'''
	station = int(hit.GetDetectorID() // 1000.)
	if (det_id % 1000) // 100. == 1: # vertical scifi plane
		way = 'vertical'
		matnum = int(det_id % 1000 % 100) # number vertical scifi plane
		n_planes = ship_geo.NuTauTT.n_vert_planes # 7
		matlen = len_vert / 2.
	elif det_id % 10000 > 0: # horizontal scifi plane
		way = 'horizontal'
		matnum = int(det_id % 1000) # number horizontal scifi plane
		n_planes = ship_geo.NuTauTT.n_hor_planes # 11
		matlen = len_hor / 2.
	return way, station, matnum, n_planes, matlen

def global_to_mat(det_id, globalpos):
	way, tt, matnum, n, matlen = get_mat_info(det_id)
	location = globalpos + ((n - 1)/2. - matnum + 1) * scifimat_width
	return location

def mat_to_global(det_id, localpos):
	way, tt, matnum, n, matlen = get_mat_info(det_id)
	location = localpos + (-n/2. + matnum)*scifimat_width - scifimat_width/2
	return location

def ly_loss_mean(distance):
	return 20.78 * math.exp(-0.26 * distance / 100.) + 7.89 * math.exp(-3.06 * distance / 100.)
def ly_loss_sigma(distance):
	return 6.8482 * math.exp(-0.5757 * distance / 100.) + 3.4458
def ly_loss_random(distance):
	# Here '/ 100.' - [cm] converted in [m] 
	mean = ly_loss_mean(distance / 100.)
	sigma = ly_loss_sigma(distance / 100.)
	res = random.gauss(mean, sigma)
	# RECURSION
	if res < 4.5:
		res = ly_loss_random(distance)
	return res

def cluster_width_mean(distance):
	return math.exp(0.6661 - 0.006955*distance) + 2.163
def cluster_width_sigma(distance):
	return 1.103 - 0.0005751*distance
def cluster_width_random(distance, ly=104):
	mean = cluster_width_mean(distance)
	sigma = cluster_width_sigma(distance)
	# The random width is manually set as 1% of events
	# It covers cases where the width is 5-10 
	if random.random() <= 0.01:
		return random.randint(1, 10)
	random_width = int(round(random.gauss(mean - 1, sigma))) + 1
	# Cluster width >= 1
	# Recursion
	if random_width < 1 or ly < random_width:
		random_width = cluster_width_random(distance, ly=ly)
	return random_width

def ly_to_CDF(ly):
    '''
    Approximation of function: X = Light Yield distribution, Y = Cumulative Distribution Function
    '''
    if ly < 4.5 or ly > 104:
        # Incorrect LY value in the CDF
        return False 
    if ly < 13:
        p = (-13.2, 1.976)
        cdf = math.exp(p[0] + p[1]*math.sqrt(ly))
    else:
        p = (0.0108183, -0.179752, -19.2, 0.00772965)
        cdf = p[0] * (1 - math.exp(p[1]*(ly+p[2]))) / (1 + math.exp(p[1]*(ly+p[2]))) + p[3]
    return cdf

def CDF_to_ly(cdf):
    '''
    Approximation of function: X = Cumulative Distribution Function, Y = Light Yield distribution
    '''
    if 0.0 < cdf < 0.0006:
        p = (89., 4.152, 0.0001574, -1.326e+04, 4.3)
        ly = p[0]*math.sqrt(p[1]*(cdf+p[2]))*(1-math.exp(p[3]*cdf)) + p[4]
    elif 0.0006 <= cdf < 0.012:
        p = (158, 1.035, 0.24, 217)
        ly = p[0]*math.log(math.sqrt(cdf)+p[1]) + p[2]*math.exp(p[3]*cdf)
    elif 0.012 <= cdf < 0.018561406:
        p = (9.36, 335.984, -18100, -400, 15)
        ly = p[0]*math.log((p[1]-p[2]*cdf)/(p[1]+p[2]*cdf)) + p[3]*cdf + p[4]
    else:
        return CDF_to_ly(0.018561405)
    return ly

def ly_to_CDF_landau(ly):
    '''
    Approximation of function: X = Light Yield distribution, Y = Landau CDF
    '''
    if 4.5 <= ly < 15:
        p = (0.001038, -0.000378, 3.53e-05)
        cdf = p[0] + p[1]*ly + p[2]*ly*ly
    elif 15 <= ly < 40:
        p = (-0.001986, -0.0003014, 7.031e-05, -2.067e-06, 1.892e-08)
        cdf = p[0] + p[1]*ly + p[2]*ly*ly + p[3]*ly*ly*ly + p[4]*ly*ly*ly*ly
    elif 40 <= ly < 105:
        p = (-0.007149, 0.001056, -1.779e-05, 1.41e-07, -4.29e-10)
        cdf = p[0] + p[1]*ly + p[2]*ly*ly + p[3]*ly*ly*ly + p[4]*ly*ly*ly*ly
    else:
        # Incorrect LY value in the CDF
        return False
    return cdf

def edep_to_ly(energy):
    '''
    Approximation of the conversion of the energy Deposit distribution to the ly distribution. 
    Some events are linear, events outside the range are random.
    The energy is in MeV.
    '''
    integral = 0.0185640424
    if 0.18 < energy < 0.477:
        ly_lin = 332.882 * energy - 58.7085 
        cdf_raw = ly_to_CDF_landau(ly_lin) * 0.993076766938
    elif 0.477 <= energy:
        cdf_raw = integral * np.random.uniform(0., 1.0) 
    else:
        # LY threshold is 4.5 ph.e. It is equally energy treshold 0.18 MeV
        return 0     
    cdf_random = random.gauss(cdf_raw, 0.01*integral)
    if cdf_random < 0 or cdf_random > integral:
        cdf_random = edep_to_ly(energy)
    # Should be 0 < CDF < integral.
    while cdf_random < 0 or cdf_random > integral:
        cdf_random = random.gauss(cdf_raw, 0.01*integral)
    return CDF_to_ly(cdf_random)
    

def create_cluster_array(amplitude, width, wmp):
	if not 0.5 <= wmp <= 512.5:
		# print 'WARNING: WMP is out of the SiPM range', wmp
		return False
	if wmp is False or amplitude < 4.5 or amplitude < width:
		# print 'WARNING: LY < 4.5 [ph.e.] or LY < cluster width'
		return False
	# The maximum cluster width is set based on experience
	max_width = 10
	if wmp + max_width < 512:
		max_wmp = int(math.ceil(wmp + max_width))
	else:
		max_wmp = 512
	cluster_array = [0 for i_ in range(int(math.ceil(wmp + max_width)))]
	mean = wmp 
	# The 4 sigma range includes 95% of events, so sigma is set manually
	sigma = width / 4
	for i_ in range(amplitude):
		is_in_range = False
		while is_in_range is False:
			fired_channel = int(round(random.gauss(mean, sigma)))
			if fired_channel < len(cluster_array):
				is_in_range = True
		cluster_array[fired_channel] += 1
	return cluster_array

def create_cluster(amplitude, width, wmp):
	cluster_is_realistic = False
	# For right counting 
	shifted_wmp = wmp + 0.5
	while cluster_is_realistic is False:
		cluster_array = create_cluster_array(amplitude, width, shifted_wmp)
		if cluster_array is False:
			break
		array_only_values = [x for x in cluster_array[:] if x > 0]
		if len(array_only_values) != width:
			cluster_is_realistic = False
			break
		cluster_is_realistic = True
		for index, value in enumerate(cluster_array[:], 1):
			# For example ...0230700... is not realistic for simulation
			if index + 1 < len(cluster_array) and index - 1 >= 0:
				if cluster_array[index] == 0 and cluster_array[index-1] != 0 and cluster_array[index+1] != 0:
					cluster_is_realistic = False
					break
	return cluster_array

def weigthed_mean_pos(cluster):
	if cluster is False:
		return False
	sumup = 0.
	sumdown = 0.
	wmp = 0.
	for index, amplitude in enumerate(cluster[:]):
		if amplitude > 0:
			sumup += amplitude * index
			sumdown += amplitude
	if sumdown != 0:
		wmp = sumup / sumdown - 0.5
	return wmp
# ---------------------------------------------------------------------------


design2018 = {'dy': 10.,'dv': 6,'ds': 9,'nud': 3,'caloDesign': 3,'strawDesign': 10}
dy = design2018['dy']
dv = design2018['dv']
ds = design2018['ds'] 
nud = design2018['nud'] 
caloDesign = design2018['caloDesign'] 
strawDesign = design2018['strawDesign']
geofile = None

ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight=dy, 
	tankDesign=dv, muShieldDesign=ds, nuTauTargetDesign=nud, CaloDesign=caloDesign, 
	strawDesign=strawDesign, muShieldGeo=geofile)

input_file = ROOT.TFile("$PWD/ship.conical.PG_13-TGeant4.root")
# input_file = ROOT.TFile("$PWD/ship.conical.Pythia8-TGeant4.root") 
tree = input_file.Get("cbmsim")

tt_points = []
tt_raw = []
hpt_points = []
hpt_raw = []

n_hor_planes = ship_geo.NuTauTT.n_hor_planes # 11
n_vert_planes = ship_geo.NuTauTT.n_vert_planes # 7
len_hor = ship_geo.NuTauTT.scifimat_hor
len_vert = ship_geo.NuTauTT.scifimat_vert 
scifimat_width = ship_geo.NuTauTT.scifimat_width # 13.06 cm
scifimat_z = ship_geo.NuTauTT.scifimat_z # 0.145 cm
n_tt_stations = ship_geo.NuTauTT.n # 19

#---- 1. EXTRACT DATA ----------------
# TT
for index, event in enumerate(tree):
	for hit in event.TTPoint:

		if get_mat_info(hit.GetDetectorID()) is False: continue

		way, tt_num_plane, matnum, n_mats, matlen = get_mat_info(hit.GetDetectorID())
		if way == 'vertical':
			first_coord = hit.GetX()
			second_coord = hit.GetY()
			way_bin = 0
		elif way == 'horizontal':
			first_coord = hit.GetY()
			second_coord = hit.GetX()
			way_bin = 1
		localpos = global_to_mat(hit.GetDetectorID(), first_coord)
		distance = matlen + (-1, +1)[way_bin] * second_coord
		channelpos = cm_to_chan(localpos)
		ly_amplitude = int(round(ly_loss_random(distance)))
		cluster_width = int(round(cluster_width_random(distance, ly=ly_amplitude)))
		cluster = create_cluster(ly_amplitude, cluster_width, channelpos)
		wmp_of_cluster = weigthed_mean_pos(cluster)
		recovery_localpos = chan_to_cm (wmp_of_cluster)
		recovery_globalpos = mat_to_global(hit.GetDetectorID(), recovery_localpos)
		delta = first_coord - recovery_globalpos

		if abs(delta) > 1: continue
		if wmp_of_cluster is False: continue

		tt_points.append([
			hit.GetTime(), # 0; ns
			tt_num_plane, # 1
			matnum, # 2 ;~100-vert, ~0-hor
			channelpos, # 3 ; in one mat
			edep_to_ly(hit.GetEnergyLoss()*1.0e03), #ly signal, # 4
			cluster_width, # 5
			recovery_globalpos, # 6
			way_bin, # 7 # 0-vert (X), 1-hor (Y)
			delta, # 8
		])

		tt_raw.append([
			hit.GetTrackID(), # 0
			hit.GetTime(), # 1 ; ns
			hit.PdgCode(), # 2 
			hit.GetEventID(), # 3
			hit.GetDetectorID(), # 4
			hit.GetX(), # 5 ; cm
			hit.GetY(), # 6 ; cm
			hit.GetZ(), # 7 ; cm
			hit.GetEnergyLoss() * 1.0e03, # 8 ; MeV
			hit.GetPx(), # 9
			hit.GetPy(), # 10
			hit.GetPz(), # 11
			hit.GetLength() # 12
		])
# Convert to numpy array
tt_raw = np.array(tt_raw)
tt_points = np.array(tt_points)

# HPT 
for index, event in enumerate(tree):
	for hit in event.HptPoint:

		if get_mat_info(hit.GetDetectorID()) is False: continue

		way, hpt_num_plane, matnum, n_mats, matlen = get_mat_info(hit.GetDetectorID())
		if way == 'vertical':
			first_coord = hit.GetX()
			second_coord = hit.GetY()
			way_bin = 0
		elif way == 'horizontal':
			first_coord = hit.GetY()
			second_coord = hit.GetX()
			way_bin = 1
		localpos = global_to_mat(hit.GetDetectorID(), first_coord)
		distance = matlen + (-1, +1)[way_bin] * second_coord
		channelpos = cm_to_chan(localpos)
		ly_amplitude = int(round(ly_loss_random(distance)))
		cluster_width = int(round(cluster_width_random(distance, ly=ly_amplitude)))
		cluster = create_cluster(ly_amplitude, cluster_width, channelpos)
		wmp_of_cluster = weigthed_mean_pos(cluster)
		recovery_localpos = chan_to_cm (wmp_of_cluster)
		recovery_globalpos = mat_to_global(hit.GetDetectorID(), recovery_localpos)
		delta = first_coord - recovery_globalpos

		if abs(delta) > 1: continue
		if wmp_of_cluster is False: continue

		hpt_points.append([
			hit.GetTime(), # 0; ns
			hpt_num_plane + n_tt_stations, # 1
			matnum, # 2 ;~100-vert, ~0-hor
			channelpos, # 3 ; in one mat
			edep_to_ly( hit.GetEnergyLoss()*1.0e03 ), # 4
			cluster_width, # 5
			recovery_globalpos, # 6
			way_bin, # 7
			delta # 8
		])

		hpt_raw.append([
			hit.GetTrackID(), # 0
			hit.GetTime(), # 1 ; ns
			hit.PdgCode(), # 2 
			hit.GetEventID(), # 3
			hit.GetDetectorID(), # 4
			hit.GetX(), # 5 ; cm
			hit.GetY(), # 6 ; cm
			hit.GetZ(), # 7 ; cm
			hit.GetEnergyLoss() * 1.0e03, # 8 ; MeV
			hit.GetPx(), # 9
			hit.GetPy(), # 10
			hit.GetPz(), # 11
			hit.GetLength() # 12
		])
# Convert to numpy array
hpt_raw = np.array(hpt_raw)
hpt_points = np.array(hpt_points)

# Merge the arrays
tt_raw = np.vstack((tt_raw, hpt_raw))
tt_points = np.vstack((tt_points, hpt_points))
# ----------------------------------------------


# ---- 2. WRITE THE DATA --------------------------
if not tt_points.any():
	print 'WARNING: TTPoint is empty!'

if tt_points.any():
	with open("TToutput.txt","w") as ttout:
		ttout.write("TT station; Detector ID; Position [channel];" 
						"Amplitude [ph.e.]; Cluster Width; Coordinate [cm]; X or Y \n")
		for index, event in enumerate(tt_points):
			ttout.write('{:2.0f}; '.format(tt_points[index,1]))
			ttout.write("{:2.0f}; ".format(tt_points[index,2]))
			ttout.write("{}; ".format(tt_points[index,3]))
			ttout.write("{}; ".format(tt_points[index,4]))
			ttout.write("{:2.0f}; ".format(tt_points[index,5]))
			ttout.write("{}; ".format(tt_points[index,6]))
			if tt_points[index,7] == 0: # vertical scifi mat gives X coordinate
				ttout.write("X")
			elif tt_points[index,7] == 1: # horizontal scifi mat gives Y coordinate
				ttout.write("Y")
			ttout.write("\n")
# ----------------------------------------------


# ---- 3. SHOW THE DATA --------------------------
if tt_points.any():
	fig, axs = plt.subplots(2,2)
	plt.subplot(2, 2, 1) 
	axs = plt.gca()
	ly_bins = np.linspace(4.5,100,200)
	plt.hist(tt_points[:,4], bins=ly_bins, label="Light yield")
	axs.set_xlabel("LY, [ph.e.]")
	axs.set_ylabel("Events")
	plt.legend(loc="upper right")

	plt.subplot(2, 2, 2) 
	axs = plt.gca()
	nbins = 24
	plt.hist(tt_points[:,1], bins=nbins, label="TT station")
	axs.set_xlabel("Station number")
	axs.set_ylabel("Events")
	plt.legend(loc="upper right")

	# Print 'X-Z' and 'Y-Z' as output data.
	# 'X-Y-Z' graphics need additional analysis (linking by time).
	xz_points = []
	yz_points = []
	for index, event in enumerate(tt_points):
		if tt_points[index, 7] == 0: # vertical
			xz_points.append([
				tt_raw[index, 7], # Z
				tt_points[index, 6]
			])
		elif tt_points[index, 7] == 1: # horizontal
			yz_points.append([
				tt_raw[index, 7], # Z
				tt_points[index, 6]
			])
	xz_points = np.array(xz_points)
	yz_points = np.array(yz_points)

	plt.subplot(2, 2, 3) 
	axs = plt.gca()
	axs.scatter(xz_points[:,0], xz_points[:, 1])
	axs.set_xlabel("Z, [cm]")
	axs.set_ylabel("X, [cm]")
	axs.set_ylim(-50, +50) # +-47.1575 

	plt.subplot(2, 2, 4)
	axs = plt.gca()
	axs.scatter(yz_points[:,0], yz_points[:, 1])
	axs.set_xlabel("Z, [cm]")
	axs.set_ylabel("Y, [cm]")
	axs.set_ylim(-80, +80) # +-73.2475

	plt.show()
# ----------------------------------------------


