class Queue:
	def __init__(self, l):
		self.l = l[:]

	def pop(self):
		ans = self.l[0]
		self.l = self.l[1:]
		return ans

	def peek(self):
		return self.l[0]

	def empty(self):
		return len(self.l) == 0

def removeComments(lines):
	while not lines.empty() and (lines.peek().strip().startswith("#") or lines.peek().strip()==""):
		lines.pop()

def parseBlock(lines):
	removeComments(lines)
	if lines.empty():
		return None
	else:
		l = lines.pop().strip()
		content = []
		block = {'name':l.split()[0], 'content':content}
		while not lines.empty():
			removeComments(lines)
			if not lines.empty():
				l = lines.pop().strip()
				if l == "-1":
					break
				else:
					content.append(l.split())
		return block

class Processor:
	def __init__(self, policy, mult, isClient):
		self.policy = policy
		self.mult = mult
		self.isClient = isClient

class LQNmodel:
	def __init__(self, text):
		self.procs = dict()

		lines = Queue(text.split("\n"))
		blocks = dict()
		while (b:=parseBlock(lines)) is not None:
			blocks[b['name']] = b['content']

		if 'P' in blocks:
			bP = blocks['P']
			for ln in bP:
				if ln[0] == 'p':
					pParts = Queue(ln[1:])
					procName = pParts.pop()
					procPolicy = pParts.pop()
					multPart = pParts.pop()
					if multPart == 'i':
						procMult = float('inf')
					elif multPart == 'm':
						procMult = float(pParts.pop())
					self.procs[procName] = Processor(procPolicy, procMult, False)

		if 'T' in blocks:
			bT = blocks['T']
			for ln in bT:
				if ln[0] == 't':
					tParts = Queue(ln[1:])
					taskName = tParts.pop()
					taskType = tParts.pop()
					taskEntries = []
					while (tE := tParts.pop()) != "-1":
						taskEntries.append(tE)
					taskProc = tParts.pop()
					if taskType == 'r': #reference task = client
						self.procs[taskProc].isClient = True

	def getClientProc(self):
		clis = [p for p in self.procs.values() if p.isClient]
		if len(clis) == 0:
			return None
		else:
			return clis[0]