import sys

import numpy as np
from PyQt5.QtWidgets import QApplication

from ui import ToneGenerator

def generate_tone(wave_type, frequency, duration, amplitude, sample_rate):
    """Generate a monotone waveform normalized to the range [-1.0, 1.0]."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    if wave_type == "sine":
        wave = np.sin(2 * np.pi * frequency * t)
    elif wave_type == "square":
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave_type == "triangle":
        wave = 2 * np.arcsin(np.sin(2 * np.pi * frequency * t)) / np.pi
    elif wave_type == "sawtooth":
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
    else:
        wave = np.zeros_like(t)

    return t, wave * amplitude


def main():
    app = QApplication(sys.argv)
    window = ToneGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
