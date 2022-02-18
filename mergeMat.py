import sys
import scipy
from scipy.io import loadmat, savemat
import numpy as np

def nzero(X):
	return X[X!=0]

if len(sys.argv) < 4:
	print("Usage: python3 "+sys.argv[0]+ " <out> <in1> <in2> ... <inN>")
else:
	outfn = sys.argv[1]
	infns = sys.argv[2:]

	datas = [loadmat(infn) for infn in infns]

	outmtxs = dict()
	outmtxs['entryNames'] = datas[0]['entryNames']
	outmtxs['modelName'] = datas[0]['modelName']
	outmtxs['Tm'] = (np.vstack([data['Tm'] for data in datas]))
	outmtxs['RTm'] = (np.vstack([data['RTm'] for data in datas]))
	outmtxs['Cli'] = (np.vstack([data['Cli'] for data in datas]))
	outmtxs['NC'] = (np.vstack([data['NC'] for data in datas]))
	#if all('Xm' in data for data in datas):
	#	outmtxs['Xm'] = nzero(np.vstack([data['Xm'] for data in datas]))
	#outmtxs['params'] = np.hstack([data['params'] for data in datas])

	savemat(outfn, outmtxs)