#!/usr/bin/python

import ROOT
import numpy as np
import math
from math import exp, sqrt, log, ceil
import random
import matplotlib.pyplot as plt

from ROOT.TMath import Landau, Gaus, Poisson
from ShipGeoConfig import ConfigRegistry

#####################################################
##########  GLOBAL VALUES AND PARAMETERS ############
#####################################################

# Position of SiPMs in the detector (left/right and up/down)
sipm_hor_pos = +1 # at X = +len_vert / 2
sipm_vert_pos = -1 # at Y = -len_hor /  2

# If reversed is true the channels counted in reverse way
# (0->511 => 511<-0). It connected with how the modules are placed
is_sipm_hor_reversed = True
is_sipm_vert_reversed = True

# SiPM geometry
# hw - half width, pitch - one channel width, charr - array of 64 channels without gaps,
# edge - from left and right sides of the SiPM, gap - between two charr,
# array - 128 channels with the gap, biggap - gap between two arrays,
# ch_max_num - max channel in the SiPM (0-511),
# n_solid_sipms - number of "charr" arrays

hw = 13.06 / 2.
pitch = 0.025
charr = 1.6
edge = 0.017
gap = 0.025
array = gap + 2.*charr
biggap = 0.042
ch_max_num = 511
n_solid_sipms = 8

# SiPM geometry. If a point is in the solid part then the position will be counted.
# Else false value returns. When
sipm_map = (
	(-hw, -hw+edge, False),
	(-hw+edge, -hw+edge+charr, (-0.5, 63.5)),
	(-hw+edge+charr, -hw+edge+charr+gap, False),
	(-hw+edge+charr+gap, -hw+edge+array, (63.5, 127.5)),
	(-hw+edge+array, -hw+edge+array+biggap, False),
	(-hw+edge+array+biggap, -hw+edge+array+biggap+charr, (127.5, 191.5)),
	(-hw+edge+array+biggap+charr, -hw+edge+array+biggap+charr+gap, False),
	(-hw+edge+array+biggap+charr+gap, -hw+edge+array+biggap+array, (191.5, 255.5)),
	(-hw+edge+array+biggap+array, biggap/2., False),
	(biggap/2., biggap/2.+charr, (255.5, 319.5)),
	(biggap/2.+charr, biggap/2.+charr+gap, False),
	(biggap/2.+charr+gap, biggap/2.+array, (319.5, 383.5)),
	(biggap/2.+array, biggap/2.+array+biggap, False),
	(biggap/2.+array+biggap, biggap/2.+array+biggap+charr, (383.5, 447.5)),
	(biggap/2.+array+biggap+charr, biggap/2.+array+biggap+charr+gap, False),
	(biggap/2.+array+biggap+charr+gap, biggap/2.+array+biggap+charr+array, (447.5, 511.5)),
	(biggap/2.+array+biggap+charr+array, biggap/2.+array+biggap+charr+array+edge, False)
)

# If a point is in the dead space then the following channel value will be selected
gaps_map = {
	0.: -0.5,
	1.: 63.5,
	2.: 127.5,
	3.: 191.5,
	4.: 255.5,
	5.: 319.5,
	6.: 383.5,
	7.: 447.5,
	8.: 511.5
}

# Light yield attenuation A*exp(B*x) + C*exp(D*x)
# Sigma depends on the distance from a SiPM the also. The following parameters
ly_loss_params = 20.78, -0.26, 7.89, -3.06
ly_loss_sigma_params = 6.8482, -0.5757, 3.4458
cluster_width_mean_params = 0.6661, -0.006955, 2.163
cluster_width_sigma_params = 1.103, -0.0005751

# The random width in the range is manually set as 1% of events
# It covers cases where the width is 5-10
random_width_persent = 0.01

# Possible values of LY, channel position and cluser width
ly_min = 4.5
ly_max = 104
chpos_min = -0.5
chpos_max = 511.5
cluster_width_min = 1
cluster_width_max = 10

# Energy deposit converts in the light yield range linearly. Energy less then 0.18 MeV gives doesn't registered.
# Energy more then 0.477 MeV converts randomly with approximation distribution.
energy_range = 0.18, 0.477

# The maximum value of the CDF integral
CDF_integral = 0.0185640424

# Parameters that are used for linear conversion of deposit energy to the range
# equal to the light yield range
ly_linear_params = 332.882, -58.7085

# The coefficient between the maximums of CDF(E) and CDF(LY), a little differs
k_cdfs_corr = 0.993076766938

# The addition of a little randomness in the converting from the energy distibution to
# the light yield distibution
sigma_in_percent = 0.01

# 4 sigma range includes 95% of events. It needs for creating a cluster
sigma_from_width = 1 / 4.

# The following parameters will be used in the converting from the energy distibution to
# the light yield distibution.
# Dictionaries format is following - (x_min, x_max) : (parameters), approximating function.

# ly_CDF_params - approximation of CDF of the light yield distribution.
# It is doesn't used already.
ly_CDF_params = {
	(4.5, 13): (
		(-13.2, 1.976),
		lambda ly, *p: exp(p[0] + p[1]*sqrt(ly))
	),
	(13, 104): (
		(0.0108183, -0.179752, -19.2, 0.00772965),
		lambda ly, *p: p[0]*(1 - exp(p[1]*(ly+p[2]))) / (1 + exp(p[1]*(ly+p[2]))) + p[3]
	)
}


# Get a CDF value from LY (actually from an energy deposit which preliminarily linearly
# converted to the range of the light yield (4.5 - 104 ph.e.)
ly_CDF_landau_params = {
	(4.5, 15): (
		(0.001038, -0.000378, 3.53e-05),
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2
	),
	(15, 40): (
		(-0.001986, -0.0003014, 7.031e-05, -2.067e-06, 1.892e-08),
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2 + p[3]*ly**3 + p[4]*ly**4
	),
	(40, 104): (
		(-0.007149, 0.001056, -1.779e-05, 1.41e-07, -4.29e-10),
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2 + p[3]*ly**3 + p[4]*ly**4
	)
}

# Get a light yild value from a CDF values
CDF_ly_params = {
	(0., 0.0006): (
		(89., 4.152, 0.0001574, -1.326e+04, 4.3),
		lambda cdf, *p: p[0] * sqrt(p[1]*(cdf+p[2])) * (1-exp(p[3]*cdf)) + p[4]
	),
	(0.0006, 0.012): (
		(158, 1.035, 0.24, 217),
		lambda cdf, *p: p[0] * log(sqrt(cdf)+p[1]) + p[2]*exp(p[3]*cdf)
	),
	(0.012, 0.018561405): (
		(9.36, 335.984, -18100, -400, 15),
		lambda cdf, *p: p[0] * log((p[1]-p[2]*cdf)/(p[1]+p[2]*cdf)) + p[3]*cdf + p[4]
	),
	(0.018561405, 0.0185640424): (
		(9.36, 335.984, -18100, -400, 15),
		lambda cdf, *p: (p[0] * log((p[1]-p[2]*0.018561405)/(p[1]+p[2]*0.018561405))
			+ p[3]*0.018561405 + p[4])
	)
}

##################################################
#####  LOAD THE TARGET TRACKER GEOMETRY  #########
##################################################

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

n_hor_planes = ship_geo.NuTauTT.n_hor_planes # 11
n_vert_planes = ship_geo.NuTauTT.n_vert_planes # 7
scifimat_hor = ship_geo.NuTauTT.scifimat_hor
scifimat_vert = ship_geo.NuTauTT.scifimat_vert
scifimat_width = ship_geo.NuTauTT.scifimat_width # 13.06 cm
scifimat_z = ship_geo.NuTauTT.scifimat_z # 0.145 cm
n_tt_stations = ship_geo.NuTauTT.n # 19

#########################################################################################
#####    FUNCTIONS FOR TTCLASS      #####################################################
#########################################################################################

def cm_to_channel(locpos, sipm_map=sipm_map, gaps_map=gaps_map, pitch=pitch, charr=charr,
				  reverse=False, ch_max_num=ch_max_num, n_solid_sipms=n_solid_sipms):

	"""
	It converts a particle position (an event) measured in cm to a position measured
	in channels. The SiPM map is used. The position is in the scifi modul frame.
	"""

	if reverse is True:
		for left, right, ch_range in sipm_map:
			if left <= locpos <= right:
				if not ch_range is False:
					ch_start = ch_range[0]
					return ch_max_num - ((locpos-left) / pitch + ch_start)
				else:
					return gaps_map.get((n_solid_sipms - (locpos + hw) // charr), False)
	elif reverse is False:
		for left, right, ch_range in sipm_map:
			if left <= locpos <= right:
				if not ch_range is False:
					ch_start = ch_range[0]
					return (locpos-left) / pitch + ch_start
				else:
					return gaps_map.get((locpos + hw) // charr, False)

def channel_to_cm(channelpos, sipm_map=sipm_map, reverse=False, pitch=pitch):

	"""
	It converts a particle position measured channels to a position measured
	in cm. The SiPM map is used. The position is in the scifi modul frame.
	"""

	if reverse is True:
		for left, _, ch_range in sipm_map:
			if not ch_range is False:
				ch_start, ch_end = ch_range
				if ch_start <= channelpos <= ch_end:
					return -(left + (channelpos - ch_start) * pitch)
	if reverse is False:
		for left, _, ch_range in sipm_map:
			if not ch_range is False:
				ch_start, ch_end = ch_range
				if ch_start <= channelpos <= ch_end:
					return left + (channelpos - ch_start) * pitch

def GetMatType(DetID):

	"""
	It returns a type of a scifi module.
	1 - vertical scifi assembly
	0 - horizontal scifi assembly
	"""

	if DetID < 1000: return False
	return (DetID % 1000) // 100.


def GetMatNum(DetID):

	"""
	It returns an id (number) of a scifi module. In current version one plane have 7 vertical
	and 11 horisontal scifi assemblies.
	"""

	return int(DetID % 1000 % 100)

def GetMatLength(DetID):

	"""
	It returns a length of a scifi mat. The values 'scifimat_vert', 'scifimat_hor' are set
	in the FairShip geometry file.
	"""

	global scifimat_vert, scifimat_hor

	if GetMatType(DetID) == 1:
		return scifimat_vert
	elif GetMatType(DetID) == 0:
		return scifimat_hor

def GetMatQty(DetID):

	"""
	It returns a number of scifi mats in a plane. In current version it is 7 for vertical
	and 11 for horisontal scifi assemblies.
	"""

	global n_vert_planes, n_hor_planes

	if GetMatType(DetID) == 1:
		return n_vert_planes
	elif GetMatType(DetID) == 0:
		return n_hor_planes

def GetStationNum(DetID):

	"""
	It returns an id of a plane. In current the detector have 19 TT stations and 5 HPT stations.
	"""

	return int(hit.GetDetectorID() // 1000.)

def global_to_local(DetID, globalpos):

	"""
	It returns the local coordinates in one scifi assembly frame from global coordinates.
	"""

	global scifimat_width

	matnum = GetMatNum(DetID)
	nmats = GetMatQty(DetID)
	return globalpos + ((nmats-1)/2. - matnum + 1) * scifimat_width

def local_to_global(DetID, localpos):

	"""
	It returns the global coordinates from the local coordinates in one scifi assembly frame.
	"""

	global scifimat_width

	matnum = GetMatNum(DetID)
	nmats = GetMatQty(DetID)
	return localpos + (-nmats/2. + matnum - 1/2.) * scifimat_width

def ly_loss_mean(distance, params=ly_loss_params):

	"""
	It return the light yield depending on the distance to SiPMs
	"""

	A1, k1, A2, k2 = params
	return A1 * exp(k1 * distance / 100.) + A2 * exp(k2 * distance / 100.)

def ly_attenuation(distance):

	"""
	It return the light yield losses in percent depending on the distance to SiPMs
	"""

	res_ly_loss = ly_loss_mean(distance) / ly_loss_mean(0.)
	return res_ly_loss

def cluster_width_mean(distance, params=cluster_width_mean_params):

	"""
	It return a mean cluster width depending on the distance to SiPMs
	"""

	A, B, C = params
	return exp(A + B*distance) + C

def cluster_width_sigma(distance, params=cluster_width_sigma_params):

	"""
	It return a standard deviation of the mean cluster width depending on the distance to SiPMs
	"""

	A, B = params
	return A + B*distance

def cluster_width_random(distance, ly, persent=random_width_persent,
						 cluster_width_min=cluster_width_min, cluster_width_max=cluster_width_max):

	"""
	It generates a cluster. The cluster have 'ly' photoelectrons.
	The cluster width depends on the distance to SiPM
	"""

	mean = cluster_width_mean(distance)
	sigma = cluster_width_sigma(distance)
	if random.random() <= persent:
		return random.randint(cluster_width_min, cluster_width_max)
	random_width = int(round(random.gauss(mean - 1, sigma))) + 1

	# Generate again if the width < minimal width and the light yield < the width
	while random_width < 1 or ly < random_width:
		random_width = int(round(random.gauss(mean - 1, sigma))) + 1

	return random_width

def approx_function(var, approx_data):

	"""
	This universal function substitutes the parameters to the function.
	The parameters and the function are in the dictionary
	"""

	for (left, right), (params, func) in approx_data.items():
		if left <= var <= right:
			return func(var, *params)
	return False

def edep_to_ly(energy, CDF_integral=CDF_integral, energy_range=energy_range,
	ly_linear_params=ly_linear_params, k_cdfs_corr=k_cdfs_corr, sigma_in_percent=sigma_in_percent,
	ly_CDF_params=ly_CDF_params, CDF_ly_params=CDF_ly_params, ly_CDF_landau_params=ly_CDF_landau_params):

	"""
	It returns the light yield calculated from the energy deposit. The calculations are based
	on the equality of the cumulative distribution functions (CDF) :
	energy => CDF(energy) => CDF(light yield) => ly

	The linear converting range 0.18 MeV < dE < 0.477 MeV corresponds 4.5 < LY < 104 ph.e.

	If energy more then 0.477 MeV the light yield calculated randomly (uniformly in the range)
	according to the distribution

	Also a little randomness is added to the CDF value with a normal distribution and
	standard deviation with 'sigma_in_percent' (in percent of the whole range 0 - max CDF)
	"""

	e_min, e_max = energy_range
	A, C = ly_linear_params
	if e_min < energy < e_max:
		ly_lin = A * energy + C
		cdf_raw = approx_function(ly_lin, ly_CDF_landau_params) * k_cdfs_corr
	elif e_max <= energy:
		cdf_raw = CDF_integral * np.random.uniform(0., 1.0)
	else:
		return 0.
	cdf_random = random.gauss(cdf_raw, sigma_in_percent * CDF_integral)

	# Generate again while the CDF value is not in the range
	while cdf_random < 0 or cdf_random > CDF_integral:
		cdf_random = random.gauss(cdf_raw, sigma_in_percent * CDF_integral)

	return approx_function(cdf_random, CDF_ly_params)

def cluster_generator(amplitude, width, wmp, cluster_width_max=cluster_width_max,
	chpos_min=chpos_min, chpos_max=chpos_max):

	"""
	It generates an event cluster with given weighted mean position in channels, width and
	amplitude.

	If right side of the cluster can be out of range, the maximum of the right side will be
	right channel.

	At first an array [0, 0, 0, ... ] is generated which corresponds to the channels.
	Next the cluster generated in the array.
	Final array will be like [0, 0, ..., 1, 2, 5, 1, 0, ...],
	[0, 17, 0, ...] or etc.
	"""

	if int(ceil(wmp + 0.5 + cluster_width_max)) < chpos_max:
		max_fired_ch = int(ceil(wmp + 0.5 + cluster_width_max))
	else:
		max_fired_ch = int(ceil(chpos_max))
	cluster = [0 for _ in range(max_fired_ch)]
	mean = wmp
	if width == 1:
		if wmp == chpos_min:
			fired_channel = 0
		elif wmp == chpos_max:
			fired_channel = int(chpos_max)
		else:
			fired_channel = int(wmp + 0.5)
		cluster[fired_channel] += amplitude
	else:
		sigma = width * sigma_from_width
		for _ in range(amplitude):
			fired_channel = int(round(random.gauss(mean, sigma)))
			while not 0 <= fired_channel < len(cluster):
				fired_channel = int(round(random.gauss(mean, sigma)))
			cluster[fired_channel] += 1
	return cluster

def is_realistic(cluster, width):

	"""
	It returns TRUE if cluster is realistic: it doesn't have a gap between numders, like
	[..., 0, 1, 2, 0, 0, 5, 6, ...], and it doens't have the light yield less then width.
	"""

	cluster_only_values = [(channel, value) for channel, value in enumerate(cluster) if value > 0]
	first_channel, _ = cluster_only_values[0]
	last_channel, _ = cluster_only_values[-1]
	if len(cluster_only_values) != width or (last_channel - first_channel + 1) != width:
		return False
	else:
		return True

def create_cluster(amplitude, width, wmp):

	"""
	The final function for creating a signal cluster

	"""
	if not chpos_min < wmp < chpos_max: return False
	if wmp is False: return False
	if not ly_min <= amplitude >= width: return False
	shifted_wmp = wmp + 0.5 # For right counting
	cluster = cluster_generator(amplitude, width, shifted_wmp)

	# Generate again if it doesn't look like real cluster
	while is_realistic(cluster, width) is False:
		cluster = cluster_generator(amplitude, width, shifted_wmp)

	return cluster

def weigthed_mean_pos(cluster):

	"""
	Calculate the weighted mean position of the cluster
	"""

	if cluster is False:
		return False
	sumup = 0.
	sumdown = 0.
	wmp = 0.
	for channel, value in enumerate(cluster):
		if value > 0:
			sumup += value * channel
			sumdown += value
	if sumdown != 0:
		wmp = sumup / sumdown - 0.5
	return wmp

#########################################################################################
#####  CLASS OF TT AND HPT EVENTS  ######################################################
#########################################################################################

class TTCluster:
	# Constructor
	def __init__(self, DetID, Xraw, Yraw, Edep):
		self.DetID = DetID
		self.Xraw = Xraw
		self.Yraw = Yraw
		self.Edep = Edep * 1000 # to MeV
		self.ly = 0.
		self.cluster = []
		self.station = 0
		self.matnum = 0
		self.Xrec = 0.
		self.Yrec = 0.
		self.is_created = False
		# Only to check the edge events
		self.recovery_globalpos = 0
		self.delta = -13
		# The default values should be set
		self.sipm_hor_pos = +1 # +1 at X = +len_vert / 2
		self.sipm_vert_pos = +1 #-1 at Y = -len_hor /  2
		self.is_sipm_hor_reversed = False # Channels and axis are co-directional or not
		self.is_sipm_vert_reversed = False
		self.ly_min = 4.5
		self.ly_max = 104

	def SetLYRange(self, ly_min, ly_max):
		self.ly_min = ly_min
		self.ly_max = ly_max

	def SetSipmPosition(self, sipm_hor_pos, sipm_vert_pos):
		self.sipm_hor_pos = sipm_hor_pos
		self.sipm_vert_pos = sipm_vert_pos

	def SetSipmIsReversed(self, is_sipm_hor_reversed, is_sipm_vert_reversed):
		self.is_sipm_hor_reversed = is_sipm_hor_reversed
		self.is_sipm_vert_reversed = is_sipm_vert_reversed

	# Cluster generator from the raw data. It returns False if it fails.
	def ClusterGen(self):
		if GetMatType(self.DetID) is False:
			return False
		elif GetMatType(self.DetID) == 1: # vert
			first_coord = self.Xraw
			second_coord = self.Yraw
			sipm_pos = self.sipm_vert_pos
			is_sipm_reversed = self.is_sipm_hor_reversed
		elif GetMatType(self.DetID) == 0: # hor
			first_coord = self.Yraw
			second_coord = self.Xraw
			sipm_pos = self.sipm_hor_pos
			is_sipm_reversed = self.is_sipm_vert_reversed
		self.matnum = GetMatNum(self.DetID)
		nmats = GetMatQty(self.DetID)
		matlen = GetMatLength(self.DetID)
		self.station = GetStationNum(self.DetID)
		localpos = global_to_local(self.DetID, first_coord)

		if sipm_pos == +1:
			distance = GetMatLength(self.DetID)/2. - second_coord
		elif sipm_pos == -1:
			distance = GetMatLength(self.DetID)/2. + second_coord

		channelpos = cm_to_channel(localpos, reverse=is_sipm_reversed)
		self.ly = int(round(
						edep_to_ly(self.Edep) * ly_attenuation(distance)
					  ))

		if not self.ly_min < self.ly < self.ly_max:
			return False

		cluster_width = int(round(cluster_width_random(distance, ly=self.ly)))
		cluster = create_cluster(self.ly, cluster_width, channelpos)
		wmp_of_cluster = weigthed_mean_pos(cluster)
		recovery_localpos = channel_to_cm(wmp_of_cluster, reverse=is_sipm_reversed)

		self.recovery_globalpos = local_to_global(self.DetID, recovery_localpos)
		self.delta = first_coord - self.recovery_globalpos

		# Some edge events may be reconstructed incorrectly
		if abs(self.delta) > 1:
			return False

		if GetMatType(self.DetID) == 1: # vert
			self.Xrec = self.recovery_globalpos
		elif GetMatType(self.DetID) == 0: # hor
			self.Yrec = self.recovery_globalpos
		self.is_created = True
		return cluster

	def GetXYZ(self):
		if self.is_created:
			return self.Xrec, self.Yrec, self.station
		else:
			return 0, 0, 0
######################################################################################



if __name__ == '__main__':

	###############################################
	##########  EXAMPLE OF USING THE CLASS  #######
	###############################################

	tt_points = []
	hpt_points = []
	tt_raw = []
	hpt_raw = []

	# Set the path to the file
	muonfile = ROOT.TFile("$PWD/ship.conical.PG_13-TGeant4.root")
	tree = muonfile.Get("cbmsim")

	for index, event in enumerate(tree):
		for hit in event.TTPoint:

			pnt = TTCluster(hit.GetDetectorID(), hit.GetX(), hit.GetY(), hit.GetEnergyLoss())
			pnt.SetLYRange(ly_min, ly_max)
			pnt.SetSipmPosition(sipm_hor_pos, sipm_vert_pos)
			pnt.SetSipmIsReversed(is_sipm_hor_reversed, is_sipm_vert_reversed)
			pnt.ClusterGen()
			if pnt.is_created is False: continue

			tt_points.append([
				hit.GetTime(), # 0; ns
				pnt.station, # 1
				pnt.matnum, # 2 ;~100-vert, ~0-hor
				False, # 3 ; in one mat
				pnt.ly, #ly signal, # 4
				False, # 5
				pnt.recovery_globalpos, # 6
				GetMatType(pnt.DetID), # 7 # 0-vert (X), 1-hor (Y)
				pnt.delta, # 8
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
			pnt = TTCluster(hit.GetDetectorID(), hit.GetX(), hit.GetY(), hit.GetEnergyLoss())
			pnt.ClusterGen()
			if pnt.is_created is False: continue

			hpt_points.append([
				hit.GetTime(), # 0; ns
				pnt.station + n_tt_stations, # 1
				pnt.matnum, # 2 ;~100-vert, ~0-hor
				False, # 3 ; in one mat
				pnt.ly, #ly signal, # 4
				False, # 5
				pnt.recovery_globalpos, # 6
				GetMatType(pnt.DetID), # 7 # 1-vert (X), 0-hor (Y)
				pnt.delta, # 8
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


	# ---- 3. SHOW THE DATA --------------------------
	fig, axs = plt.subplots(2,2)
	plt.subplot(2, 2, 1)
	axs = plt.gca()
	ly_bins = np.linspace(4,104,100)
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
		if tt_points[index, 7] == 1: # vertical
			xz_points.append([
				tt_raw[index, 7], # Z
				tt_points[index, 6]
			])
		elif tt_points[index, 7] == 0: # horizontal
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
	axs.set_ylim(-50, +50) # +-73.2475

	plt.subplot(2, 2, 4)
	axs = plt.gca()
	axs.scatter(yz_points[:,0], yz_points[:, 1])
	axs.set_xlabel("Z, [cm]")
	axs.set_ylabel("Y, [cm]")
	axs.set_ylim(-80, +80) # +-47.1575

	plt.show()
	# ----------------------------------------------

	fig, axs = plt.subplots(1,1)
	plt.subplot(1, 1, 1)
	axs = plt.gca()
	plt.hist(tt_points[:,8], bins=100, label="delta")
	plt.show()
