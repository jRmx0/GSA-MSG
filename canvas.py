import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter


class WaveformCanvas:
	"""Handles waveform rendering on a matplotlib canvas."""
	
	def __init__(self, figure, canvas):
		"""
		Initialize the waveform canvas renderer.
		
		Args:
			figure: matplotlib Figure object
			canvas: FigureCanvas object
		"""
		self.figure = figure
		self.canvas = canvas
	
	def render_waveform(self, wave_time, wave_int16, wave_type, freq, sample_rate):
		"""
		Render the waveform on the canvas.
		
		Args:
			wave_time: Time array for x-axis
			wave_int16: Waveform data as 16-bit integers
			wave_type: Type of wave (sine, square, triangle, sawtooth)
			freq: Frequency in Hz
			sample_rate: Sample rate in Hz
		"""
		if wave_time is None or wave_int16 is None:
			return
		
		self.figure.clear()
		ax = self.figure.add_subplot(111)
		ax.plot(wave_time, wave_int16, linewidth=0.8)
		
		# Handle special case for melodies (freq=0 or wave_type contains "Melody")
		if freq == 0 or "Melody" in wave_type or "Birthday" in wave_type:
			ax.set_title(
				f"{wave_type} ({sample_rate/1000:.1f} kHz, 16-bit)"
			)
		else:
			ax.set_title(
				f"{wave_type.capitalize()} Wave – {freq} Hz ({sample_rate/1000:.1f} kHz, 16-bit)"
			)
		
		ax.set_xlabel("Time (s)")
		ax.set_ylabel("Amplitude (16-bit integer)")
		ax.grid(True)
		
		ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
		max_val = np.max(np.abs(wave_int16)) if wave_int16.size else 0
		if max_val == 0:
			max_val = 32767
		ax.set_ylim(-max_val * 1.1, max_val * 1.1)
		
		if wave_time.size > 0:
			ax.set_xlim(wave_time[0], wave_time[-1])
		
		self.canvas.draw()
