import sys
import os
import random
from jinja2 import Template
import scipy
from scipy.io import savemat
import numpy as np

def split(l):
	return [s for s in l.split() if s != ""]

def notEmpty(l):
	return l is not None and l != ""

def printMatrix(name, data):
	return name+" = ["+"; \n".join(" ".join(str(s) for s in ln) for ln in data)+"]"

def comment(s):
	return "# "+s

class Scan:
	def __init__(self, cont):
		self.cont = cont
		self.i = 0

	def pop(self):
		if self.i >= len(self.cont):
			return None
		else:
			ans = self.cont[self.i]
			self.i += 1
			return ans

def parseOut(fname):
	data = dict()
	rts = dict()
	thrs = dict()
	data['responseTimes'] = rts
	data['throughput'] = thrs
	with open(fname) as f:
		for line in f:
			tokens = [s.strip() for s in line.strip().split(',')]
			measure = tokens[0]
			entryOrProc = tokens[1]
			name = tokens[2]
			value = tokens[3]
			if entryOrProc == 'entry':
				if measure == 'throughput':
					thrs[name] = value
				elif measure == 'response time':
					rts[name] = value
	return data

def saveMat(datas, matFname, modelName, samples, sz):
	entriesNames = list(datas[0]['throughput'].keys())
	entriesNames.sort()
	RTm = [[0.0] * len(entriesNames) for i in range(sz)] #full response time, with nested calls, waiting for cpu and cpu time
	Tm = [[0.0] * len(entriesNames) for i in range(sz)] #entry throughput
	Cli = [[0.0] for i in range(sz)]
	NC = [[0.0] * len(entriesNames) for i in range(sz)]
	outsamples = [dict()] * sz
	for d in range(sz):
		data = datas[d]
		sample = samples[d]
		if data is not None:
			outsamples[d] = sample

			for i in range(len(entriesNames)):
				ent = entriesNames[i]
				RTm[d][i] = float(data['responseTimes'][ent])
				Tm[d][i] = float(data['throughput'][ent])
				Cli[d][0] = float(sample['cli'])
				NC[d][0] = float('inf')
				NC[d][1] = float(sample['cpu1'])
				NC[d][2] = float(sample['cpu2'])
				NC[d][3] = float(sample['cpu3'])

	savemat(matFname, {'Tm':np.array(Tm), 'RTm':np.array(RTm), 'entryNames': np.asarray(entriesNames, dtype='object'), \
		'modelName':modelName, 'params':np.array(outsamples), 'Cli':np.array(Cli, dtype='float'), 'NC':np.array(NC, dtype='float')})

'''def makeMatrixes(datas):
	entriesNames = list(datas[0]['throughput'].keys())
	entriesNames.sort()
	RTlqn = [[""] * len(entriesNames) for i in range(len(datas))] #full response time, with nested calls, waiting for cpu and cpu time
	Tm = [[""] * len(entriesNames) for i in range(len(datas))] #entry throughput

	for d in range(len(datas)):
		data = datas[d]
		for i in range(len(entriesNames)):
			ent = entriesNames[i]
			RTlqn[d][i] = data['responseTimes'][ent]
			Tm[d][i] = data['throughput'][ent]

	return "\n\n".join([comment(", ".join(entriesNames)), printMatrix("RTlqn", RTlqn), printMatrix("Tm", Tm)])'''

def readBounds(fname):
	bndData = dict()
	with open(fname) as f:
		for line in f:
			l = line.strip()
			if not l.startswith("#") and len(l)>0:
				parts = l.split()
				name = parts[0]
				typ = parts[1]
				if typ == "int":
					bnd = (int(parts[2]), int(parts[3]))
				elif typ in ["float", "double", "real", "decimal"]:
					typ = "float"
					bnd = (float(parts[2]), float(parts[3]))
				else:
					raise Exception()
				bndData[name] = {'type':typ, 'bnd':bnd}
	return bndData

def generate(bndData, rng=None):
	if rng is None:
		rng = random
	out = dict()
	for k in bndData:
		typ = bndData[k]['type']
		bnd = bndData[k]['bnd']
		if typ == 'int':
			out[k] = rng.randint(bnd[0], bnd[1])
		elif typ == 'float':
			out[k] = rng.uniform(bnd[0], bnd[1])
	return out
