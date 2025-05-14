""" DB initialization script

Stores previously hard-coded conditions from drifttubesmonitoring into the
conditions database.
"""
from ..conditionsDatabase.factory import APIFactory
from bson.json_util import loads, dumps

#Moving daniel and survey arrays in the drifttubesmonitoring.py to this script for persisting it into the conditions database
daniel = {}
survey = {}
survey['T1_MA_01']=[9.0527, 0.2443, 0.7102]
daniel['T1_MA_01']=[244.30,531.85,9052.70]
survey['T1_MA_02']=[9.0502, -0.2078, 0.7092]
daniel['T1_MA_02']=[-207.80,530.85,9050.20]
survey['T1_MA_03']=[9.0564, -0.2075, -0.6495]
daniel['T1_MA_03']=[-207.50,-570.85,9056.40]
survey['T1_MA_04']=[9.0578, 0.2436, -0.6503]
daniel['T1_MA_04']=[243.60,-571.65,9057.80]
survey['T1_MB_01']=[9.5376, -0.5044, 0.5647]
daniel['T1_MB_01']=[-504.54,564.60,9537.42]
survey['T1_MB_02']=[9.5388, -0.7293, 0.1728]
daniel['T1_MB_02']=[-729.38,172.83,9539.00]
survey['T1_MB_03']=[9.5420, 0.4446, -0.4995]
daniel['T1_MB_03']=[444.63,-499.49,9541.94]
survey['T1_MB_04']=[9.5435, 0.6693, -0.1073]
daniel['T1_MB_04']=[669.28,-107.28,9543.47]
survey['T2_MC_01']=[9.7424, 0.7588, 0.1730]
daniel['T2_MC_01']=[758.84, 173.03, 9742.35]
survey['T2_MC_02']=[9.7433, 0.5327, 0.5657]
daniel['T2_MC_02']=[532.67, 565.72, 9743.27]
survey['T2_MC_03']=[9.7381, -0.6374, -0.1104]
daniel['T2_MC_03']=[-637.45, -110.36, 9738.21]
survey['T2_MC_04']=[9.7409, -0.4121, -0.5021]
daniel['T2_MC_04']=[-412.30,-501.89, 9740.98]
survey['T2_MD_01']=[10.2314, 0.2385, 0.7078]
daniel['T2_MD_01']=[238.50, 530.50, 10231.40]
survey['T2_MD_02']=[10.2276, -0.2121, 0.7087]
daniel['T2_MD_02']=[-212.10,531.40,10227]
survey['T2_MD_03']=[10.2285, -0.2157, -0.6488]
daniel['T2_MD_03']=[-215.70, -570.35, 10228.50]
survey['T2_MD_04']=[10.2302, 0.2361, -0.6495]
daniel['T2_MD_04']=[236.10, -575.05, 10230.20]
survey['T3_B01']=[14.5712,  0.9285, -0.6818]
daniel['T3_B01']=[928.59, -681.74, 14641.10]
survey['T3_B02']=[14.5704,  0.5926, -0.6823]
daniel['T3_B02']=[592.62, -682.23, 14640.30]
survey['T3_B03']=[14.5699,  0.4245, -0.6844]
daniel['T3_B03']=[424.52, -684.35, 14639.90]
survey['T3_B04']=[14.5686,  0.0884, -0.6854]
daniel['T3_B04']=[88.46, -685.39, 14638.60]
survey['T3_B05']=[14.5685, -0.0813, -0.6836]
daniel['T3_B05']=[-81.23, -683.57, 14638.50]
survey['T3_B06']=[14.5694, -0.4172, -0.6840]
daniel['T3_B06']=[-417.09, -683.99, 14639.30]
survey['T3_B07']=[14.5696, -0.5859, -0.6864]
daniel['T3_B07']=[-585.80, -686.33, 14639.60]
survey['T3_B08']=[14.5693, -0.9216, -0.6845]
daniel['T3_B08']=[-921.58, -684.47, 14639.20]
survey['T3_T01']=[14.5733,  0.9253, 0.8931]
daniel['T3_T01']=[925.40, 893.09,14643.20]
survey['T3_T02']=[14.5741,  0.5893, 0.8914]
daniel['T3_T02']=[589.42, 891.36,14644.10]
survey['T3_T03']=[14.5746,  0.4212, 0.8907]
daniel['T3_T03']=[421.23, 890.75, 14644.60]
survey['T3_T04']=[14.5750,  0.0852, 0.8905]
daniel['T3_T04']=[85.28, 890.55, 14645.00]
survey['T3_T05']=[14.5756, -0.0839, 0.8899]
daniel['T3_T05']=[-83.89, 889.94, 14645.50]
survey['T3_T06']=[14.5769, -0.4198, 0.8888]
daniel['T3_T06']=[-419.69, 888.85, 14646.90]
survey['T3_T07']=[14.5781, -0.5896, 0.8908]
daniel['T3_T07']=[-589.56, 890.77, 14648.10]
survey['T3_T08']=[14.5812, -0.9256, 0.8896]
daniel['T3_T08']=[-925.57, 889.62, 14651.20]
survey['T4_B01']=[16.5436,  0.9184, -0.6848]
daniel['T4_B01']=[918.35,-684.86,16473.60]
survey['T4_B02']=[16.5418,  0.5824, -0.6867]
daniel['T4_B02']=[582.36, -686.73, 16471.90]
survey['T4_B03']=[16.5408,  0.4144, -0.6875]
daniel['T4_B03']=[414.37, -687.52, 16470.90]
survey['T4_B04']=[16.5389,  0.0785, -0.6883]
daniel['T4_B04']=[78.51, -688.32, 16468.90]
survey['T4_B05']=[16.5389, -0.0888, -0.6890]
daniel['T4_B05']=[-88.80, -689.05, 16468.90]
survey['T4_B06']=[16.5396, -0.4247, -0.6884]
daniel['T4_B06']=[-424.75, -688.49, 16469.60]
survey['T4_B07']=[16.5400, -0.5936, -0.6888]
daniel['T4_B07']=[-593.65, -688.85, 16470.00]
survey['T4_B08']=[16.5402, -0.9295, -0.6877]
daniel['T4_B08']=[-929.54, -687.77, 16470.20]
survey['T4_T01']=[16.5449,  0.9207, 0.8899]
daniel['T4_T01']=[920.70,889.81,16475.00]
survey['T4_T02']=[16.5456,  0.5845, 0.8884]
daniel['T4_T02']=[584.44, 888.30, 16475.70]
survey['T4_T03']=[16.5460,  0.4168, 0.8873]
daniel['T4_T03']=[416.74, 887.26, 16476.10]
survey['T4_T04']=[16.5474,  0.0804, 0.8862]
daniel['T4_T04']=[80.34, 886.14, 16477.50]
survey['T4_T05']=[16.5480, -0.0876, 0.8862]
daniel['T4_T05']=[-87.55, 886.10, 16478.00]
survey['T4_T06']=[16.5497, -0.4234, 0.8862]
daniel['T4_T06']=[-423.40, 886.18, 16479.80]
survey['T4_T07']=[16.5507, -0.5919, 0.8866]
daniel['T4_T07']=[-591.89, 886.58, 16480.80]
survey['T4_T08']=[16.5518, -0.9280, 0.8869]
daniel['T4_T08']=[-928.06, 886.85, 16481.80]

survey['RPC1_L']= [17.6823, 1.1611, 1.1909]
survey['RPC1_R']= [17.6864, -1.2679, 1.2145]
survey['RPC2_L']= [18.6319, 1.1640, 1.1926]
survey['RPC2_R']= [18.6360, -1.2650, 1.2065]
survey['RPC3_L']= [19.1856, 1.1644, 1.1933]
survey['RPC3_R']= [19.1902, -1.2646, 1.2021]
survey['RPC4_L']= [19.7371, 1.1610, 1.1938]
survey['RPC4_R']= [19.7410, -1.2670, 1.1979]
survey['RPC5_L']= [20.2852, 1.1677, 1.1945]
survey['RPC5_R']= [20.2891, -1.2614, 1.1943]

#Moving alignCorrection array in the drifttubesmonitoring.py to this script for persisting it into the conditions database
alignCorrection = {}
alignCorrection[0]=[0, 0, 0]
alignCorrection[1]=[0, 0, 0]
alignCorrection[2]=[0, 0, 0]
alignCorrection[3]=[0, 0, 0]
# u layers
alignCorrection[4]=[0.0, 0, 0]
alignCorrection[5]=[0.0, 0, 0]
alignCorrection[6]=[0.0, 0, 0]
alignCorrection[7]=[0.0, 0, 0]
# v layers
alignCorrection[8]= [0.035, 0, 0]
alignCorrection[9]= [0.007, 0, 0]
alignCorrection[10]=[-0.009, 0, 0]
alignCorrection[11]=[-0.03, 0, 0]
# x layers
alignCorrection[12]=[0.18, 0, 0]
alignCorrection[13]=[0.16, 0, 0]
alignCorrection[14]=[0.136, 0, 0]
alignCorrection[15]=[0.12, 0, 0]
# T 3
alignCorrection[16]=[0.008, 0, 0]
alignCorrection[17]=[0.04, 0, 0]
alignCorrection[18]=[0.018, 0, 0]
alignCorrection[19]=[0.07, 0, 0]
alignCorrection[20]=[-0.078, 0, 0]
alignCorrection[21]=[-0.09, 0, 0]
alignCorrection[22]=[-0.08, 0, 0]
alignCorrection[23]=[-0.09, 0, 0]
# T 4
alignCorrection[24]=[0, 0, 0]
alignCorrection[25]=[0, 0, 0]
alignCorrection[26]=[0.0, 0, 0]
alignCorrection[27]=[0.0, 0, 0]
alignCorrection[28]=[0.0, 0, 0]
alignCorrection[29]=[0.0, 0, 0]
alignCorrection[30]=[0.0, 0, 0]
alignCorrection[31]=[0.0, 0, 0]

#[Creating] database and getting an instance of the MongoDBAdapter
api_factory = APIFactory()
conditionsDB = api_factory.construct_DB_API("../conditionsDatabase/config.yml")

#Adding detector "muflux" and subdector "driftTubes"
conditionsDB.add_detector("muflux")
conditionsDB.add_detector("driftTubes", "muflux")

#Adding "daniel" condition to the database
conditionsDB.add_condition("muflux/driftTubes", "strawPositions", "muflux/driftTubes_daniel_2020-03-23 18:14", daniel,
                           "alignment", "2020-03-23", "2020-03-23 18:12", "2020-05-20")

#Adding "survey" condition to the database
conditionsDB.add_condition("muflux/driftTubes", "strawPositions", "muflux/driftTubes_survey_2020-03-23 18:14", survey,
                           "alignment", "2020-03-23", "2020-03-23 18:12", "2020-05-20")

#Adding "alignCorrection" condition to the database
conditionsDB.add_condition("muflux/driftTubes", "alignCorrection", "muflux/driftTubes_align_2020-03-23",
loads(dumps(alignCorrection)), "alignment", "2020-03-23", "2020-03-23", "2020-05-20")
