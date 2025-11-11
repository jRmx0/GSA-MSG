import threading
import time

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtWidgets import (
	QLabel,
	QComboBox,
	QHBoxLayout,
	QLineEdit,
	QPushButton,
	QVBoxLayout,
	QWidget,
)
from matplotlib.backends.backend_qt5agg import (
	FigureCanvasQTAgg as FigureCanvas,
	NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from canvas import WaveformCanvas


class ToneGenerator(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Monotone Sound Generator (16-bit)")
		self.setGeometry(300, 200, 800, 600)

		self.bit_depth = 16  # 16-bit PCM

		# --- UI Components ---
		self.wave_label = QLabel("Wave type:")
		self.wave_select = QComboBox()
		self.wave_select.addItems(["sine", "square", "triangle", "sawtooth"])

		self.freq_label = QLabel("Frequency (Hz):")
		self.freq_input = QLineEdit("440")

		self.duration_label = QLabel("Duration (s):")
		self.duration_input = QLineEdit("2")

		self.amp_label = QLabel("Amplitude (0-1):")
		self.amp_input = QLineEdit("0.5")

		self.generate_btn = QPushButton("Generate")
		self.generate_btn.clicked.connect(self.on_generate_clicked)

		self.play_pause_btn = QPushButton("Play")
		self.play_pause_btn.setEnabled(False)
		self.play_pause_btn.clicked.connect(self.on_play_pause_clicked)

		self.stop_btn = QPushButton("Stop")
		self.stop_btn.setEnabled(False)
		self.stop_btn.clicked.connect(self.on_stop_clicked)

		self.happy_bd_btn = QPushButton("Happy Birthday 🎂")
		self.happy_bd_btn.clicked.connect(self.on_happy_birthday_clicked)

		# --- Plot area ---
		self.figure = Figure(figsize=(6, 4))
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.waveform_canvas = WaveformCanvas(self.figure, self.canvas)

		# --- Layouts ---
		control_layout = QHBoxLayout()
		control_layout.addWidget(self.wave_label)
		control_layout.addWidget(self.wave_select)
		control_layout.addWidget(self.freq_label)
		control_layout.addWidget(self.freq_input)
		control_layout.addWidget(self.duration_label)
		control_layout.addWidget(self.duration_input)
		control_layout.addWidget(self.amp_label)
		control_layout.addWidget(self.amp_input)
		control_layout.addWidget(self.generate_btn)
		control_layout.addWidget(self.play_pause_btn)
		control_layout.addWidget(self.stop_btn)
		control_layout.addWidget(self.happy_bd_btn)

		main_layout = QVBoxLayout()
		main_layout.addLayout(control_layout)
		main_layout.addWidget(self.toolbar)
		main_layout.addWidget(self.canvas)

		self.setLayout(main_layout)

		# --- Playback state ---
		self.wave_time = None
		self.wave_data = None
		self.wave_int16 = None
		self.playback_pos = 0
		self.play_start_time = None
		self.is_playing = False
		self.is_paused = False

		# --- Melody playback state ---
		self.note_info_list = None
		self.current_note_index = -1
		self.melody_timer = QTimer()
		self.melody_timer.timeout.connect(self.update_melody_display)

		self._state_lock = threading.Lock()
		self._wait_thread = None
		self._pause_requested = False
		self._stop_requested = False

	def _reset_playback_state(self, wave_time=None, wave_data=None, wave_int16=None, 
	                          note_info_list=None, reset_pos=True):
		"""Reset playback state with optional new waveform data."""
		with self._state_lock:
			if wave_time is not None:
				self.wave_time = wave_time
			if wave_data is not None:
				self.wave_data = wave_data
			if wave_int16 is not None:
				self.wave_int16 = wave_int16
			if note_info_list is not None:
				self.note_info_list = note_info_list
				self.current_note_index = -1
			if reset_pos:
				self.playback_pos = 0
			self.play_start_time = None
			self.is_playing = False
			self.is_paused = False

	def update_button_states(self):
		"""Adjust control buttons according to current playback state."""
		has_wave = self.wave_data is not None and self.wave_data.size > 0
		is_active = self.is_playing or self.is_paused
		
		self.play_pause_btn.setText("Pause" if self.is_playing else "Play")
		self.play_pause_btn.setEnabled(has_wave if not is_active else True)
		self.stop_btn.setEnabled(is_active)

	def on_generate_clicked(self):
		"""Generate the waveform and update the plot."""
		try:
			wave_type = self.wave_select.currentText()
			freq = float(self.freq_input.text())
			duration = float(self.duration_input.text())
			amp = float(self.amp_input.text())

			self.sample_rate = max(int(4 * freq), 44100)
			self.stop_playback()

			from generator import generate_tone

			t, wave = generate_tone(wave_type, freq, duration, amp, self.sample_rate)
			wave = np.clip(wave, -1.0, 1.0).astype(np.float32)
			wave_int16 = np.int16(wave * 32767)

			self._reset_playback_state(t, wave, wave_int16)
			self.render_waveform(wave_type, freq)
			self.update_button_states()

		except Exception as exc:
			print("Error:", exc)

	def on_play_pause_clicked(self):
		"""Toggle between play and pause depending on current state."""
		if self.wave_data is None or self.wave_data.size == 0:
			return

		if self.is_playing:
			self.pause_playback()
		else:
			self.start_playback()

	def on_stop_clicked(self):
		"""Stop playback and reset position."""
		self.stop_playback()

	def on_happy_birthday_clicked(self):
		"""Generate and play the Happy Birthday melody."""
		try:
			self.stop_playback()
			self.melody_timer.stop()

			from happyBdExample import generate_happy_birthday

			wave_type = self.wave_select.currentText()
			amp = float(self.amp_input.text())
			self.sample_rate = 44100

			t, wave, note_info_list = generate_happy_birthday(
				sample_rate=self.sample_rate,
				wave_type=wave_type,
				amplitude=amp
			)

			wave = np.clip(wave, -1.0, 1.0).astype(np.float32)
			wave_int16 = np.int16(wave * 32767)

			self._reset_playback_state(t, wave, wave_int16, note_info_list)
			self.update_button_states()

			if note_info_list:
				self.current_note_index = 0
				self.render_single_note(0, wave_type)

			self.start_playback()
			self.melody_timer.start(50)

		except Exception as exc:
			print("Error generating Happy Birthday melody:", exc)
			import traceback
			traceback.print_exc()

	def render_single_note(self, note_index, wave_type):
		"""Render a single note from the melody."""
		if self.note_info_list is None or note_index >= len(self.note_info_list):
			return
		
		note_info = self.note_info_list[note_index]
		start_sample = note_info['start_sample']
		end_sample = note_info['end_sample']
		
		self.waveform_canvas.render_waveform(
			self.wave_time[start_sample:end_sample],
			self.wave_int16[start_sample:end_sample],
			f"Note: {note_info['note']} ({wave_type})",
			note_info['frequency'],
			self.sample_rate
		)

	def update_melody_display(self):
		"""Update the display to show the current note being played."""
		if not self.is_playing or self.note_info_list is None:
			return
		
		elapsed = time.monotonic() - self.play_start_time if self.play_start_time else 0.0
		current_time = (self.playback_pos / self.sample_rate) + elapsed
		
		for i, note_info in enumerate(self.note_info_list):
			if note_info['start_time'] <= current_time < note_info['end_time']:
				if i != self.current_note_index:
					self.current_note_index = i
					self.render_single_note(i, self.wave_select.currentText())
				break

	def start_playback(self):
		"""Start or resume playback from the current position."""
		if self.wave_data is None or self.wave_data.size == 0:
			return

		if self.playback_pos >= self.wave_data.size:
			self.playback_pos = 0

		remaining = self.wave_data[self.playback_pos:]
		if remaining.size == 0:
			return

		with self._state_lock:
			self._pause_requested = False
			self._stop_requested = False
			self.is_playing = True
			self.is_paused = False
			self.play_start_time = time.monotonic()

		try:
			sd.play(remaining, self.sample_rate, blocking=False)
		except Exception as exc:
			with self._state_lock:
				self.is_playing = False
				self.is_paused = False
				self.play_start_time = None
			print("Error starting playback:", exc)
			self.update_button_states()
			return

		self._start_wait_thread()
		self.update_button_states()

	def pause_playback(self):
		"""Pause current playback and remember the position."""
		if not self.is_playing:
			return

		self.melody_timer.stop()
		elapsed = time.monotonic() - self.play_start_time if self.play_start_time else 0.0
		samples_played = int(elapsed * self.sample_rate)

		with self._state_lock:
			self.playback_pos = min(self.playback_pos + samples_played, self.wave_data.size)
			self._pause_requested = True
			self.is_playing = False
			self.is_paused = True
			self.play_start_time = None

		try:
			sd.stop()
		except Exception as exc:
			print("Error pausing playback:", exc)

		self.update_button_states()

	def stop_playback(self):
		"""Stop playback and reset to the beginning."""
		self.melody_timer.stop()
		
		with self._state_lock:
			should_stop = (self.is_playing or self.is_paused or 
			              (self._wait_thread and self._wait_thread.is_alive()))
			if should_stop:
				self._stop_requested = True

		if should_stop:
			try:
				sd.stop()
			except Exception as exc:
				print("Error stopping playback:", exc)

		self._reset_playback_state(reset_pos=True)
		self.update_button_states()

	def _start_wait_thread(self):
		"""Start a helper thread to detect natural playback completion."""
		wait_thread = threading.Thread(target=self._monitor_playback, daemon=True)
		with self._state_lock:
			self._wait_thread = wait_thread
		wait_thread.start()

	def _monitor_playback(self):
		"""Wait for playback to finish and react if it ended naturally."""
		current_thread = threading.current_thread()
		try:
			sd.wait()
		except Exception as exc:
			print("Error waiting for playback to finish:", exc)
			return

		with self._state_lock:
			if self._wait_thread is not current_thread:
				return

			if self._pause_requested:
				self._pause_requested = False
				self._wait_thread = None
				return

			if self._stop_requested:
				self._stop_requested = False
				self._wait_thread = None
				return

			self._wait_thread = None

		QTimer.singleShot(0, self._on_playback_finished)

	@pyqtSlot()
	def _on_playback_finished(self):
		"""Handle playback completion triggered by the helper thread."""
		self.melody_timer.stop()
		self._reset_playback_state(reset_pos=True)
		self.update_button_states()

	def render_waveform(self, wave_type, freq):
		"""Render the stored waveform on the canvas."""
		self.waveform_canvas.render_waveform(
			self.wave_time, 
			self.wave_int16, 
			wave_type, 
			freq, 
			self.sample_rate
		)

