import sys
import os
import random
from jinja2 import Template
import scipy
from scipy.io import savemat
import numpy as np
import subprocess
import multiprocess
import time
import shlex
import signal
from multiprocessing.managers import BaseManager

from auxfnc import *

class Data:
	def __init__(self, rep, log):
		self.lock = multiprocess.Lock()
		self.started = 0
		self.datas = []
		self.samples = []
		self.rep = rep
		self.log = log

	def doContinue(self, subpIdx):
		self.lock.acquire()
		try:
			cont = (self.started < self.rep)
			if cont:
				self.started += 1 
			else:
				return False
			self.logline(subpIdx, "completed "+str(len(self.datas))+"/"+str(self.rep)+", running "+str(self.started-len(self.datas)))
		finally:
			self.lock.release()
		return True

	def newData(self, subpIdx, data, sample, matname, mdlname):
		self.lock.acquire()
		try:
			self.datas.append(data)
			self.samples.append(sample)
			saveMat(self.datas, matname, mdlname, self.samples, len(self.datas))
			self.logline(subpIdx, "completed "+str(len(self.datas))+"/"+str(self.rep)+", running "+str(self.started-len(self.datas)))
		finally:
			self.lock.release()

	def logline(self, subpIdx, line):
		with open(self.log, "a") as f:
			f.write("["+str(subpIdx)+"] "+line+"\n")

if __name__ == '__main__':
	mdlname = sys.argv[1]
	bndname = sys.argv[2]
	rep = int(sys.argv[3])
	matname = sys.argv[4]
	timeout_sec = int(sys.argv[5])
	logfn = sys.argv[6]

	try:
		os.unlink(logfn)
	except:
		pass

	cmdline = 'java -jar DiffLQN_0.1/DiffLQN.jar {inp}'

	def runWatchdog(subpIdx, dt, sample, tmpmdl, tmpout, timeout_sec):
		try:
			dt.logline(subpIdx, "now trying: "+str(sample))
			cmd = cmdline.format(inp=tmpmdl, out=tmpout)
			timebeg = time.time()
			p = subprocess.Popen(cmd, start_new_session=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			p.wait(timeout=timeout_sec)
			timeend = time.time()
			dt.logline(subpIdx, "successful ("+str(timeend-timebeg)+" seconds): "+str(sample))
			return True
		except subprocess.CalledProcessError:
			dt.logline(subpIdx, "tool error: "+str(sample))
			return False
		except subprocess.TimeoutExpired:
			os.killpg(os.getpgid(p.pid), signal.SIGTERM)
			dt.logline(subpIdx, "timeout ("+str(timeout_sec)+" seconds): "+str(sample))
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
		while dt.doContinue(subpIdx):
			success = False
			while not success:
				sample = generate(bndData, rng)
				tmpmdltxt = mdlTempl.render({'inp':tmpmdl, 'out':tmpout, 'solvermode':'sim', **sample})
				with open(tmpmdl, "w") as f:
					f.write(tmpmdltxt)
				success = runWatchdog(subpIdx, dt, sample, tmpmdl, tmpout, timeout_sec)
				if success:
					try:
						data = parseOut(tmpout)
					except:
						dt.logline(subpIdx, "parser error: "+str(sample))
						success = False
			dt.newData(subpIdx, data, sample, matname, mdlname)
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
	data = manager.mydata(rep, logfn)
	cpus = os.cpu_count()
	seeds = random.sample(range(10000000), k=cpus)
	ps = [multiprocess.Process(target=createSomeSamples, args=(c, seeds[c], data)) for c in range(cpus)]
	for p in ps:
		p.start()
	for p in ps:
		p.join()