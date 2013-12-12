import random
class MarkovLine:
	def __init__(self):
		self._data = {}
		self._sum = 0
	
	def inc(self, elem):
		self._data[elem] = self._data.get(elem, 0) + 1
		self._sum += 1
	
	def roulette(self):
		r = random.randint(1, self._sum)
		running_sum = 0
		for elem in self._data:
			running_sum += self._data[elem]
			if (running_sum >= r):
				return elem
	
	def __repr__(self):
		return str(self._data)

class MarkovChainN:
	''' 
		Markov Chain stochastic model implementation.
		Degree is arbitrary.
		Markov Chain elements should implement __hash__() and __cmp__() (or rich comparisons) 
	'''
	def __init__(self, degree=2):
		if (degree < 1): raise RuntimeError('Markov Chain degree should be integer >= 1')
		if (degree != int(degree)): raise RuntimeError('Markov Chain degree must be an integer not a float')
		self._degree = degree
		self._transmat = {}
		self._reset_state()
		
	def _reset_state(self):
		self._state = ['\0'] * (self._degree - 1) # Nth degree chain depends on (N-1) previous states when choosing a new one
		
	def _consume(self, elem):
		if (tuple(self._state) not in self._transmat): self._transmat[tuple(self._state)] = MarkovLine()
		self._transmat[tuple(self._state)].inc(elem)
		if (elem != '\0'):
			self._state.append(elem)
			self._state.pop(0)
		else:
			self._reset_state()
	
	def _produce(self):
		new_elem = self._transmat[tuple(self._state)].roulette()
		if (new_elem != '\0'):
			self._state.append(new_elem)
			self._state.pop(0)
		else:
			self._reset_state()
		return new_elem
		
	def train(self, sequence):
		for elem in sequence:
			self._consume(elem)
		self._consume('\0')

	def generate(self, length_limit = None):
		sequence = []
		counter = 0
		while (length_limit == None or counter < length_limit):
			generated_state = self._produce()
			if (generated_state == '\0'):
				break
			sequence.append(generated_state)
			counter += 1

		if (length_limit != None and counter == length_limit):
			self._reset_state()

		return sequence
		
	def __repr__(self):
		result = 'Markov chain of degree %d (%d previous states matter)\n' % (self._degree, self._degree-1)
		for k in self._transmat:
			result += '%s -> %s |%d\n' % (k, self._transmat[k], self._transmat[k]._sum)
		return result
	
	# following two methods are not logically right, because they concatenate independent sequences
	def generate_at_least(self, length):
		''' Generate a sequence of length greater than or equal to some particular value '''
		sequence = []
		while (len(sequence) < length):
			sequence += self.generate()
		return sequence

	def generate_length(self, length):
		''' Generate a sequence of particular length '''
		return self.generate_at_least(length)[0:length]	



