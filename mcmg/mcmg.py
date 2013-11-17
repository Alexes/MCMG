'''
	Markov Chain Music Generator
	
'''

import random

class MarkovChain:
	def __init__(self):
		self.transmat = {}
		self.rowsums = {}
		self.start_vector = {}
		self.start_vector_rowsum = 0
		self.training_state = None
		self.production_state = None

	def _consume(self, state):
		prev_state = self.training_state
		if (prev_state == None): 
			if (state not in self.start_vector.keys()):
				self.start_vector[state] = 0
			self.start_vector[state] += 1
			#self.start_vector[state] = self.start_vector.get(state, 0) + 1
			self.start_vector_rowsum += 1
		else:
			if (prev_state not in self.transmat.keys()):
				self.transmat[prev_state] = {}
				self.rowsums[prev_state] = 0

			if (state not in self.transmat[prev_state].keys()):
				self.transmat[prev_state][state] = 0
		
			self.transmat[prev_state][state] += 1
			self.rowsums[prev_state] += 1

		if (state == '\0'):
			self._reset_training()
		else:
			self.training_state = state


	def _produce(self):
		prev_state = self.production_state
		generated_state = None
		if (prev_state == None): 
			roulette = random.randint(1, self.start_vector_rowsum)
			running_sum = 0

			for next_state in self.start_vector:
				running_sum += self.start_vector[next_state]
				if (running_sum >= roulette):
					generated_state = next_state
					break
		else:
			roulette = random.randint(1, self.rowsums[prev_state])
			running_sum = 0
		
			for next_state in self.transmat[prev_state]:
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
	
	def __str__(self):
		s = ''
		def _escape_zero(v): 
			if (v == '\0'): return '\\0' 
			else: return v

		for prev_state in self.transmat.keys():
			tm = str(prev_state) + ': ['
			for next_state in self.transmat[prev_state].keys():
				tm += '%s:%d, ' % (_escape_zero(str(next_state)), self.transmat[prev_state][next_state])
			tm += '] rowsum: %d' % (self.rowsums[prev_state])
			s += tm + '\n'

		tm = 'First: ['
		for next_state in self.start_vector.keys():
			tm += '%s:%d, ' % (_escape_zero(str(next_state)), self.start_vector[next_state]) 
		tm += '] rowsum: %d' % (self.start_vector_rowsum)
		s += tm

		return s

class Note:
	def __init__(self, step, octave, alter = 0):
		self.step = step
		self.octave = int(octave)
		self.alter = int(alter) # but could be decimal

	def __str__(self):
		accidental = None
		if (self.alter >= 0):
			accidental = '#' * self.alter
		else:
			accidental = 'b' * (-1 * self.alter)

		return self.step + accidental + str(self.octave)

	def midi(self): # ...note number
		offsets = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
		num = (self.octave + 1) * 12 
		num += offsets[self.step] 
		num += self.alter
		return num

	def __hash__(self):
		return self.midi() # hash(int) returns just integer itself
	
	def __cmp__(self, other): 
		'''self > other if 'self' note is of higher frequency than 'other' note'''
		if (not isinstance(other, Note)):
			return 1 # TODO wtf?
		return self.midi() - other.midi()


if (__name__ == '__main__'):
	import sys
	music_xml_filename = 'D:\Projects\MCMG\MusicXML\The_dance_of_victory-Eluveitie\lg-155582393382959147.xml'

	import xml.etree.ElementTree as ET
	tree = ET.parse(music_xml_filename)
	root = tree.getroot()


	part = root.find('part')
	part_id = part.get('id')
	part_name = root.find("./part-list/score-part[@id='%s']" % part_id).find('part-name').text


	PRINT_NOTES = 35
	note_sequence = []
	durations_sequence = []
	print 'First %d notes of part "%s":' % (PRINT_NOTES, part_name)
	for note in part.iter('note'):
		step = note.find('pitch').find('step').text
		octave = note.find('pitch').find('octave').text
		
		alter = note.find('pitch').find('alter')
		if (alter == None): alter = 0
		else: alter = int(alter.text)
		
		n = Note(step, octave, alter)
		note_sequence.append(n)

		type = note.find('type').text
		durations_sequence.append(type)

		print n, '\t', type
	
		PRINT_NOTES -= 1
		if (PRINT_NOTES == 0): 
			break


	noteChain = MarkovChain()
	noteChain.train(note_sequence)
	print noteChain

	durChain = MarkovChain()
	durChain.train(durations_sequence)
	print durChain

	for note in noteChain.generate():
		duration = durChain._produce()
		print note, '\t', duration if duration != '\0' else durChain._produce()


# TODO improve MarkovChain: get rid of 'something in dict.keys()'. Change for self.start_vector[state] = self.start_vector.get(state, 0) + 1