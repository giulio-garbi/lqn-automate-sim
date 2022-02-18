import sys
import os
import random
from jinja2 import Template
import scipy
from scipy.io import savemat
import numpy as np
import subprocess
import multiprocess
from multiprocessing.managers import BaseManager

from auxfnc import *

class Data:
	def __init__(self, rep):
		self.lock = multiprocess.Lock()
		self.started = 0
		self.datas = []
		self.samples = []
		self.rep = rep

	def doContinue(self):
		self.lock.acquire()
		try:
			#print(self.started)
			cont = (self.started < self.rep)
			if cont:
				self.started += 1 
			else:
				return False
			print("completed "+str(len(self.datas))+"/"+str(self.rep)+", running "+str(self.started-len(self.datas)))
		finally:
			#print("unlock")
			self.lock.release()
		return True

	def newData(self, data, sample, matname, mdlname):
		self.lock.acquire()
		try:
			self.datas.append(data)
			self.samples.append(sample)
			saveMat(self.datas, matname, mdlname, self.samples, len(self.datas))
			print("completed "+str(len(self.datas))+"/"+str(self.rep)+", running "+str(self.started-len(self.datas)))
		finally:
			self.lock.release()

if __name__ == '__main__':
	mdlname = sys.argv[1]
	bndname = sys.argv[2]
	rep = int(sys.argv[3])
	matname = sys.argv[4]

	timeout_sec = 30*60

	cmdline = 'java -jar DiffLQN_0.1/DiffLQN.jar {inp}'

	def runWatchdog(tmpmdl, tmpout, timeout_sec):
		try:
			subprocess.run(cmdline.format(inp=tmpmdl, out=tmpout), shell=True, check=True, timeout=timeout_sec, capture_output=True)
			return True
		except subprocess.CalledProcessError:
			return False
		except subprocess.TimeoutExpired:
			return False

	bndData = readBounds(bndname)
	with open(mdlname) as f:
		mdlTempl = Template(f.read())

	pid = str(os.getpid())

	BaseManager.register("mydata",Data)

	def createSomeSamples(subpIdx, seed, dt):
		tmpmdl = "tmp"+pid+"_"+str(subpIdx)+".lqn"
		tmpout = "tmp"+pid+"_"+str(subpIdx)+".csv"
		rng = random.Random(seed)
		while dt.doContinue():
			sample = generate(bndData, rng)
			tmpmdltxt = mdlTempl.render({'inp':tmpmdl, 'out':tmpout, 'solvermode':'sim', **sample})
			with open(tmpmdl, "w") as f:
				f.write(tmpmdltxt)
			while not runWatchdog(tmpmdl, tmpout, timeout_sec):
				pass
			data = parseOut(tmpout)
			dt.newData(data, sample, matname, mdlname)
		try:
			os.unlink(tmpmdl)
		except:
			pass
		try:
			os.unlink(tmpout)
		except:
			pass

	def getManager():
		m = BaseManager()
		m.start()
		return m

	manager = getManager()
	data = manager.mydata(rep)
	cpus = os.cpu_count()
	seeds = random.sample(range(10000000), k=cpus)
	ps = [multiprocess.Process(target=createSomeSamples, args=(c, seeds[c], data)) for c in range(cpus)]
	for p in ps:
		p.start()
	for p in ps:
		p.join()