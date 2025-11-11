"""
Happy Birthday Melody Generator

This module generates the "Happy Birthday" melody using the tone generator.
"""

import numpy as np
from generator import generate_tone

# Musical note frequencies (in Hz) for the 4th octave
NOTE_FREQUENCIES = {
	'C4': 261.63,
	'D4': 293.66,
	'E4': 329.63,
	'F4': 349.23,
	'G4': 392.00,
	'A4': 440.00,
	'B4': 493.88,
	'C5': 523.25,
}

BEAT_DURATION = 0.5

HAPPY_BIRTHDAY_MELODY = [
	('G4', 0.75), ('G4', 0.25), ('A4', 1.0), ('G4', 1.0), ('C5', 1.0), ('B4', 2.0),
	('G4', 0.75), ('G4', 0.25), ('A4', 1.0), ('G4', 1.0), ('D4', 1.0), ('C5', 2.0),
	('G4', 0.75), ('G4', 0.25), ('G4', 1.0), ('E4', 1.0), ('C5', 1.0), ('B4', 1.0), ('A4', 2.0),
	('F4', 0.75), ('F4', 0.25), ('E4', 1.0), ('C5', 1.0), ('D4', 1.0), ('C5', 2.0),
]


def generate_happy_birthday(sample_rate=44100, wave_type="sine", amplitude=0.5):	
	all_waves = []
	all_times = []
	note_info_list = []
	current_time = 0.0
	current_sample = 0
	
	for note, beats in HAPPY_BIRTHDAY_MELODY:
		freq = NOTE_FREQUENCIES[note]
		duration = beats * BEAT_DURATION
		
		t, wave = generate_tone(wave_type, freq, duration, amplitude, sample_rate)
		
		note_info_list.append({
			'note': note,
			'frequency': freq,
			'duration': duration,
			'start_time': current_time,
			'end_time': current_time + duration,
			'start_sample': current_sample,
			'end_sample': current_sample + len(wave),
		})
		
		all_times.append(t + current_time)
		all_waves.append(wave)
		
		current_time += duration
		current_sample += len(wave)
	
	return np.concatenate(all_times), np.concatenate(all_waves), note_info_list


def get_note_at_time(note_info_list, current_time):
	for note_info in note_info_list:
		if note_info['start_time'] <= current_time < note_info['end_time']:
			return note_info
	return None


def get_melody_info():
	total_beats = sum(beats for _, beats in HAPPY_BIRTHDAY_MELODY)
	melody_length = total_beats * BEAT_DURATION
	
	return {
		'name': 'Happy Birthday',
		'duration': melody_length,
		'note_count': len(HAPPY_BIRTHDAY_MELODY),
		'tempo': '120 BPM (moderate)',
	}
