Markov Chain Music Generator

== Description ==
This is a program that generates melodies after learning on some music samples.
Result is given in MusicXML music notation format (http://www.musicxml.com/).
MusicXML files can be opened in programs such as MuseScore (http://musescore.org/).

Generation algorithm uses two Markov Chains, 
one for generating note pitches and another for generating note durations.
Chains are first trained on supplied scores, then pitch and duration sequences 
are generated and combined.

== Usage ==
Python (https://www.python.org/) is needed to run the program.

Launch MCMG with:
python mcmg.py
MCMG will train on the file, hardcoded in the mcmg.py and produce
a new MusicXML file 'generated.xml' which is then to be opened in MuseScore (http://musescore.org/).