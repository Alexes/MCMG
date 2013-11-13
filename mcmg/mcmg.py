'''
	Markov Chain Music Generator
	
'''

import random

class MarkovChain:
	def __init__(self):
		self.transmat = {}
		self.training_state = None
		self.production_state = None

	def _consume(self, state):
		prev_state = self.training_state
		if (prev_state == None): prev_state = '_None'

		if (prev_state not in self.transmat.keys()):
			self.transmat[prev_state] = {'_rowsum' : 0}

		if (state not in self.transmat[prev_state].keys()):
			self.transmat[prev_state][state] = 0
		
		self.transmat[prev_state][state] += 1
		self.transmat[prev_state]['_rowsum'] += 1

		if (state == '\0'):
			self._reset_training()
		else:
			self.training_state = state


	def _produce(self):
		prev_state = self.production_state
		if (prev_state == None): prev_state = '_None'

		roulette = random.randint(1, self.transmat[prev_state]['_rowsum'])
		running_sum = 0
		generated_state = None
		for next_state in self.transmat[prev_state]:
			if (next_state == '_rowsum'): 
				continue
			running_sum += self.transmat[prev_state][next_state]
			if (running_sum >= roulette):
				generated_state = next_state
				break
	
		if (generated_state == '\0'):
			self._reset_production()
		else:
			self.production_state = generated_state

		return generated_state

	def _reset_training(self):
		self.training_state = None

	def _reset_production(self):
		self.production_state = None

	def train(self, sequence):
		if (len(sequence) == 0): return
		if (self.training_state != None): raise RuntimeError('Markov chain is not in empty training state. Other training in progress or previous ended incorrectly')
		for event in sequence:
			self._consume(event)
		self._consume('\0')

	def generate(self, length_limit = 200):
		sequence = []
		counter = 0
		while (counter < length_limit):
			generated_state = self._produce()
			if (generated_state == '\0'):
				break
			sequence.append(generated_state)
			counter += 1

		if (counter == length_limit):
			self._reset_production()

		return sequence
	
	def print_transmat(self):
		def _escape_zero(v): 
			if (v == '\0'): return '\\0' 
			else: return v

		for prev_state in self.transmat.keys():
			str = prev_state + ': ['
			for next_state in self.transmat[prev_state].keys():
				str += '%s:%d, ' % (_escape_zero(next_state), self.transmat[prev_state][next_state])
			str += ']'
			print str

import sys
music_xml_filename = 'D:\Projects\MCMG\MusicXML\The_dance_of_victory-Eluveitie\lg-155582393382959147.xml'

import xml.etree.ElementTree as ET
tree = ET.parse(music_xml_filename)
root = tree.getroot()


part = root.find('part')
part_id = part.get('id')
part_name = root.find("./part-list/score-part[@id='%s']" % part_id).find('part-name').text


PRINT_NOTES = 35
print 'First %d notes of part "%s":' % (PRINT_NOTES, part_name)
for note in part.iter('note'):
	step = note.find('pitch').find('step').text
	octave = note.find('pitch').find('octave').text
	type = note.find('type').text
	alter = note.find('pitch').find('alter')

	halfsteps = 0
	if (alter != None): halfsteps = int(alter.text)

	accidental = None
	if (halfsteps >= 0):
		accidental = '#' * halfsteps
	else:
		accidental = 'b' * halfsteps
		

	print step + accidental + octave + ' ' + type
	
	PRINT_NOTES -= 1
	if (PRINT_NOTES == 0): 
		break


c = MarkovChain()
words = '''
mast tame same teams
team meat steam stem
'''.replace('\n', ' ').split(' ')
for word in words:
	c.train(word)
c.print_transmat()


print ''.join(c.generate())
print ''.join(c.generate())
print ''.join(c.generate())
print ''.join(c.generate())
print ''.join(c.generate())