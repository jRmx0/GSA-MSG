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

		self._state_lock = threading.Lock()
		self._wait_thread = None
		self._pause_requested = False
		self._stop_requested = False

	def update_button_states(self):
		"""Adjust control buttons according to current playback state."""
		has_wave = self.wave_data is not None and self.wave_data.size > 0

		if self.is_playing:
			self.play_pause_btn.setText("Pause")
			self.play_pause_btn.setEnabled(True)
			self.stop_btn.setEnabled(True)
		elif self.is_paused:
			self.play_pause_btn.setText("Play")
			self.play_pause_btn.setEnabled(True)
			self.stop_btn.setEnabled(True)
		else:
			self.play_pause_btn.setText("Play")
			self.play_pause_btn.setEnabled(has_wave)
			self.stop_btn.setEnabled(False)

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

			with self._state_lock:
				self.wave_time = t
				self.wave_data = wave
				self.wave_int16 = wave_int16
				self.playback_pos = 0
				self.play_start_time = None
				self.is_playing = False
				self.is_paused = False

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

		elapsed = 0.0
		if self.play_start_time is not None:
			elapsed = time.monotonic() - self.play_start_time

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
		with self._state_lock:
			active_thread = self._wait_thread is not None and self._wait_thread.is_alive()
			should_stop = self.is_playing or self.is_paused or active_thread
			if should_stop:
				self._stop_requested = True

		if should_stop:
			try:
				sd.stop()
			except Exception as exc:
				print("Error stopping playback:", exc)

		with self._state_lock:
			self.playback_pos = 0
			self.is_playing = False
			self.is_paused = False
			self.play_start_time = None

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
		self.playback_pos = 0
		self.play_start_time = None
		self.is_playing = False
		self.is_paused = False
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

