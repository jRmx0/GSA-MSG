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
	
	for note, beats in HAPPY_BIRTHDAY_MELODY:
		freq = NOTE_FREQUENCIES[note]
		duration = beats * BEAT_DURATION
		
		t, wave = generate_tone(wave_type, freq, duration, amplitude, sample_rate)
		
		t_adjusted = t + current_time
		
		note_info = {
			'note': note,
			'frequency': freq,
			'duration': duration,
			'start_time': current_time,
			'end_time': current_time + duration,
			'start_sample': len(np.concatenate(all_waves)) if all_waves else 0,
			'end_sample': len(np.concatenate(all_waves + [wave])) if all_waves else len(wave),
		}
		note_info_list.append(note_info)
		
		all_times.append(t_adjusted)
		all_waves.append(wave)
		
		current_time += duration
	
	combined_time = np.concatenate(all_times)
	combined_wave = np.concatenate(all_waves)
	
	return combined_time, combined_wave, note_info_list


def get_note_at_time(note_info_list, current_time):
	for note_info in note_info_list:
		if note_info['start_time'] <= current_time < note_info['end_time']:
			return note_info
	return None


def get_melody_info():
	beat_duration = 0.5
	melody_length = (
		2.0 + 2.0 +  # First line
		2.0 + 2.0 +  # Second line  
		3.0 + 2.0 +  # Third line
		2.0 + 2.0    # Fourth line
	) * beat_duration * 2
	
	return {
		'name': 'Happy Birthday',
		'duration': melody_length,
		'note_count': 28,
		'tempo': '120 BPM (moderate)',
	}
