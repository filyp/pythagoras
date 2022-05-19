import threading
from time import sleep, time

import numpy as np
import sounddevice


BIT_RATE = 48000

sine_amps = [0.0, 1.0]
violin_amps = [0.0, 1.0, 0.286699025, 0.150079537, 0.042909002,]
            #    0.203797365, 0.229228698, 0.156931925,
            #    0.115470898, 0.0, 0.097401803, 0.087653465,]
piano_amps = [0.0, 1.0, 0.399064778, 0.229404484, 0.151836061,]
              # 0.196754229, 0.093742264, 0.060871957,]
              # 0.138605419, 0.010535002, 0.071021868,]


class PolyphonicPlayer(threading.Thread):
    segment_duration = 0.01     # in seconds

    def __init__(self, base_freq=10, amps=sine_amps, max_voices=20):
        threading.Thread.__init__(self)

        self.stream = sounddevice.RawOutputStream(
            channels=1,
            samplerate=BIT_RATE)
        self.stream.start()

        self.alive = True
        self.base_freq = base_freq
        self.ratios = []
        self.phases = []
        self.volumes = []
        self.last_time = time()
        self.amps = amps / np.sum(amps)
        self.max_voices = max_voices
        self.notes = set()

    def run(self):
        while self.alive:
            if len(self.ratios) == 0:
                # no frequencies given so be silent
                sleep(self.segment_duration)
                continue

            while len(self.phases) < len(self.ratios):
                # new ratios were added
                self.phases.append(0)
            while len(self.volumes) < len(self.ratios):
                # new ratios were added
                self.volumes.append(1)
            if  self.max_voices < len(self.ratios):
                self.max_voices = len(self.ratios)

            # construct a sound
            new_time = time()
            final_sound = 0
            for i, ratio, amplitude in zip(range(len(self.ratios)), self.ratios, self.volumes):
                frequency = ratio * self.base_freq
                final_sound += self.get_wave(frequency, self.phases[i]) * amplitude
                self.phases[i] += self.segment_duration * frequency * 2*np.pi
                self.phases[i] %= 2*np.pi

            final_sound /= self.max_voices    # adjust volume

            self.last_time = new_time
            self.stream.write(final_sound
                              .astype(np.float32)
                              .tobytes())

        self.stream.stop()
        self.stream.close()

    def get_wave(self, primary_frequency, phase):
        acc = 0
        for index, amplitude in enumerate(self.amps):
            frequency = primary_frequency * index
            wave = np.sin(2 * np.pi *
                          np.arange(BIT_RATE * self.segment_duration) *
                          frequency / BIT_RATE
                          + phase * index)
            acc += wave * amplitude
        # adjust volume
        human_amp = self.human_corrected_amplitude(primary_frequency)
        # human_amp = 1
        return acc * human_amp
    
    def human_corrected_amplitude(self, frequency):
        low_limit = 300
        slope = -1.0
        rescaled = max(frequency / low_limit, 1)
        return rescaled ** slope

    def kill(self):
        self.alive = False