'''
	Markov Chain Music Generator
	
'''

import random

class MarkovChain:
	def __init__(self):
		self.transition_matrix = {}
		self.training_current_state = None
		self.creation_current_state = None

	def consume(self, state):
		prev_state = self.training_current_state
		if (prev_state == None): prev_state = '_None'

		self.training_current_state = state

		if (prev_state not in self.transition_matrix.keys()):
			self.transition_matrix[prev_state] = {'_rowsum' : 0}

		if (state not in self.transition_matrix[prev_state].keys()):
			self.transition_matrix[prev_state][state] = 0
		
		self.transition_matrix[prev_state][state] += 1
		self.transition_matrix[prev_state]['_rowsum'] += 1


	def produce(self):
		prev_state = self.creation_current_state
		if (prev_state == None): prev_state = '_None'

		roulette = random.randint(1, self.transition_matrix[prev_state]['_rowsum'])
		running_sum = 0
		produced_state = None
		for key in self.transition_matrix[prev_state]:
			if (key == '_rowsum'): 
				continue
			running_sum += self.transition_matrix[prev_state][key]
			if (running_sum >= roulette):
				produced_state = key
				break
	
		self.creation_current_state = produced_state
		return produced_state

	def reset_produce(self):
		self.creation_current_state = None

	def reset_consume(self):
		self.training_current_state = None

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
words = ['hello', 'world', 'printer', 'mate', 'tame']
for word in words:
	map(c.consume, word+'0')
	c.reset_consume()
