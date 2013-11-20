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
	
	def generate_length(self, length):
		''' Generate a sequence of particular length '''
		sequence = []
		while (len(sequence) < length):
			sequence += self.generate()
		return sequence[0:length]

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


import xml.etree.ElementTree as ET
class MusicXml:
	def _type_to_div(self, type, dotted, divisions_per_quarter):
		''' Maps from note duration names (quarter, whole, etc.) to MusicXML divisions '''
		mapping = {
			'whole':	('multiply', 4),
			'half':		('multiply', 2),
			'quarter':	('multiply', 1),
			'eighth':	('divide', 2),
			'16th':		('divide', 4),
			'32nd':		('divide', 8)
			}
		
		if (type not in mapping):
			raise RuntimeError('Unsupported note duration type "%s"' % (type))

		if (mapping[type][0] == 'divide' and divisions_per_quarter % mapping[type][1] != 0):
			raise RuntimeError('%s notes are not representable if there are %d divisions per quarter note' % (type, divisions_per_quarter))

		div = divisions_per_quarter * mapping[type][1] if mapping[type][0] == 'multiply' else divisions_per_quarter / mapping[type][1]

		if (dotted == True and div % 2 != 0):
			raise RuntimeError('Dotted %s is not representable if there are %d divisions per quarter note' % (type, divisions_per_quarter))
		
		if (dotted == True):
			div = div * 3 / 2

		return div

	def _div_to_types(self, div, divisions_per_quarter):
		''' Maps MusicXML divisions to note duration names (quarter, whole, etc.) '''
		if (div > 4 * divisions_per_quarter or div < 1):
			raise RuntimeError('Divisions argument out of range [4*divisions_per_quarter, 1]')
		
		d = divisions_per_quarter
		mapping = {
			d/8.0 :	'32nd',
			d/4.0:	'16th',
			d/2.0:	'eighth',
			d:		'quarter',
			2*d:	'half',
			4*d:	'whole'
			}

		if (div in mapping):
			return [{'type':mapping[div], 'dotted':False}]

		if (div % 3 == 0 and div*2/3 in mapping):
			return [{'type':mapping[div*2/3], 'dotted':True}]

		# "Greedy Tie" - note needs to be broken down into several tied notes
		div_i = div
		tie = []
		while(div_i > 0):
			for i in reversed(range(1, div_i + 1)):
				if (i in mapping):
					tie.append({'type':mapping[i], 'dotted':False})
					div_i -= i
					break
				if (i % 3 == 0 and i*2/3 in mapping):
					tie.append({'type':mapping[i*2/3], 'dotted':True})
					div_i -= i
					break

		return tie

	
	def _determine_divisions(self, dur_seq):
		''' Calculates optimum value for <divisions></divisions> MusicXML tag '''
		mapping = {
			'whole':	1,
			'half':		2,
			'quarter':	4,
			'eighth':	8,
			'16th':		16,
			'32nd':		32
			}

		shortest_duration_denominator = 0
		for dur in dur_seq:
			if (mapping[dur['type']] > shortest_duration_denominator):
				shortest_duration_denominator = mapping[dur['type']]

		return max(shortest_duration_denominator/4, 1)
	
	def _add_attributes(self, measure, divisions_per_quarter, beats, beat_type):
		''' Adds <attributes> tag to specified <measure> MusicXML tag '''
		addchild = ET.SubElement
		attributes = addchild(measure, 'attributes')

		addchild(attributes, 'divisions').text = str(divisions_per_quarter)
		addchild(addchild(attributes, 'key'), 'fifth').text = '0'
		time = addchild(attributes, 'time')
		addchild(time, 'beats').text = str(beats)
		addchild(time, 'beat-type').text = str(beat_type)

		clef = addchild(attributes, 'clef')
		addchild(clef, 'sign').text = 'G'
		addchild(clef, 'line').text = '2'
	

	def _add_note_xml(self, measure, pitch, div, type, dotted, tie_start, tie_end):
		''' Adds MusicXML code for one note '''
		#print 'Add note: %s div=%d type=%s dotted=%s tie_start=%s tie_end=%s' % (str(pitch), div, type, dotted, tie_start, tie_end)
		addchild = ET.SubElement

		note_tag = addchild(measure, 'note')
		pitch_tag = addchild(note_tag, 'pitch')
		addchild(pitch_tag, 'step').text = pitch.step
		addchild(pitch_tag, 'octave').text = str(pitch.octave)
		if (pitch.alter != 0): 
			addchild(pitch_tag, 'alter').text = str(pitch.alter)

		addchild(note_tag, 'duration').text = str(div)
		if (tie_end == True):
			tie = addchild(note_tag, 'tie')
			tie.set('type', 'stop')
		if (tie_start == True):
			tie = addchild(note_tag, 'tie')
			tie.set('type', 'start')
		addchild(note_tag, 'type').text = type
		if (dotted == True):
			addchild(note_tag, 'dot')

		notations_tag = None
		if (tie_start == True or tie_end == True):
			notations_tag = addchild(note_tag, 'notations')
		if (tie_end == True):
			tied = addchild(notations_tag, 'tied')
			tied.set('type', 'stop')
		if (tie_start == True):
			tied = addchild(notations_tag, 'tied')
			tied.set('type', 'start')

	def write_mxl(self, note_seq, dur_seq):
		''' Writes given note and durations sequence (in "quarter, whole, etc." form) into MusicXML file '''
		if (len(note_seq) != len(dur_seq)):
			raise RuntimeError('Notes sequence and Durations sequence must be of the same length!')

		root = ET.Element('score-partwise')
		root.set('version', '3.0')
	
		addchild = ET.SubElement

		part_list = addchild(root, 'part-list')

		score_part = addchild(part_list, 'score-part')
		score_part.set('id', 'P1')

		addchild(score_part, 'part-name').text = 'Artificial'

		part = addchild(root, 'part')
		part.set('id', 'P1')

		note_seq = list(reversed(note_seq))
		dur_seq = [{'type':T, 'dotted':False} for T in list(reversed(dur_seq))] # convert to type paired with dottedness
		BEATS = 4 # hardcoded for now
		BEAT_TYPE = 4
		DIVISIONS_PER_QUARTER = self._determine_divisions(dur_seq)
		DIVISIONS_PER_MEASURE = 4 * DIVISIONS_PER_QUARTER * BEATS / BEAT_TYPE
		running_sum = DIVISIONS_PER_MEASURE
		#print '<divisions>%d</divisions> per_measure=%d' % (DIVISIONS_PER_QUARTER, DIVISIONS_PER_MEASURE)
		tie_start_monitor = 0 # is this called a 'monitor' really?
		tie_end_monitor = 0
		measure = None
		measure_num = 1
		while(len(note_seq) > 0):
			if (running_sum == DIVISIONS_PER_MEASURE):
				# create new measure
				#print 'MEASURE'
				measure = addchild(part, 'measure')
				measure.set('number', str(measure_num))
				if (measure_num == 1):
					self._add_attributes(measure, DIVISIONS_PER_QUARTER, BEATS, BEAT_TYPE)
				measure_num += 1
				running_sum = 0

			N = note_seq.pop()
			T = dur_seq.pop()
			D = self._type_to_div(T['type'], T['dotted'], DIVISIONS_PER_QUARTER)

			if (DIVISIONS_PER_MEASURE - running_sum < D):
				D_orig = D
				D = DIVISIONS_PER_MEASURE - running_sum
				D_remainder = D_orig - D
				T_remainder = self._div_to_types(D_remainder, DIVISIONS_PER_QUARTER)
				for T_rem in reversed(T_remainder):
					note_seq.append(N)
					dur_seq.append(T_rem)
					tie_start_monitor += 1

			Ts = self._div_to_types(D, DIVISIONS_PER_QUARTER)
			T = Ts[0]
			del Ts[0]
			D = self._type_to_div(T['type'], T['dotted'], DIVISIONS_PER_QUARTER)
			for T_tied in reversed(Ts):
				note_seq.append(N)
				dur_seq.append(T_tied)
				tie_start_monitor += 1

			tie_end = False
			tie_start = False
			if (tie_end_monitor > 0):
				tie_end = True
				tie_end_monitor -= 1
			if (tie_start_monitor > 0):
				tie_start = True
				tie_start_monitor -= 1
				tie_end_monitor += 1

			self._add_note_xml(measure, N, D, T['type'], T['dotted'], tie_start, tie_end)
			running_sum += D

		filename = 'generated.xml'
		ET.ElementTree(root).write(filename)
		print 'Music written to ' + filename

if (__name__ == '__main__'):
	import sys
	music_xml_filename = 'D:\Projects\MCMG\MusicXML\The_dance_of_victory-Eluveitie\lg-155582393382959147.xml'

	import xml.etree.ElementTree as ET
	tree = ET.parse(music_xml_filename)
	root = tree.getroot()

	# TODO a "choose part" dialog
	# Choose a part to train on:
	# [1] (P1) Piano
	# [2] (P2) Violin
	part = root.find('part')
	part_id = part.get('id')
	part_name = root.find("./part-list/score-part[@id='%s']" % part_id).find('part-name').text


	PRINT_NOTES = 35
	note_sequence = []
	durations_sequence = []
	print 'Training on first %d notes of part "%s":' % (PRINT_NOTES, part_name)
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

	#note_seq = noteChain.generate()
	note_seq = noteChain.generate_length(200)
	dur_seq = durChain.generate_length(len(note_seq))
	#dur_seq = []
	#for note in note_seq:
	#	duration = durChain._produce()
	#	if (duration == '\0'): duration = durChain._produce()
	#	dur_seq.append(duration)
	#	print note, '\t', duration
	

	mx = MusicXml()		

	#note_seq = [Note('C', 4)] * 5
	#dur_seq = ['quarter']*3 + ['eighth'] + ['quarter']
	
	#note_seq = [Note('C', 4)] * 4
	#dur_seq = ['quarter']*4

	#note_seq = [Note('C', 4)] * 1
	#dur_seq = ['whole']*1


	#note_seq = [Note('C', 4)] * 5
	#dur_seq = ['quarter']*3 + ['16th'] + ['quarter']

	print '==========================='
	mx.write_mxl(note_seq, dur_seq)






# TODO improve MarkovChain: get rid of 'something in dict.keys()'. Change for self.start_vector[state] = self.start_vector.get(state, 0) + 1

