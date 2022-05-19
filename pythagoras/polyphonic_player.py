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
    segment_duration = 0.010     # in seconds

    def __init__(self, base_freq=10, amps=sine_amps, max_voices=20):
        threading.Thread.__init__(self)

        self.stream = sounddevice.RawOutputStream(
            channels=1,
            samplerate=BIT_RATE)
        self.stream.start()

        self.alive = True
        self.base_freq = base_freq
        self.last_time = time()
        self.amps = amps / np.sum(amps)
        self.max_voices = max_voices
        self.notes = dict()   # voice_num: [freq, amplitude, phase]
        self.next_voice_num = 0
        self.notes_to_add = []
        self.notes_to_delete = []

    def run(self):
        while self.alive:
            # ! add and delete queued notes
            for voice_num, note in self.notes_to_add:
                self.notes[voice_num] = note
            for voice_num in self.notes_to_delete:
                del self.notes[voice_num]
            self.notes_to_add = []
            self.notes_to_delete = []

            if len(self.notes) == 0:
                # no frequencies given so be silent
                sleep(self.segment_duration)
                continue
            if  self.max_voices < len(self.notes):
                self.max_voices = len(self.notes)

            # construct a sound
            new_time = time()
            final_sound = 0
            
            for note in self.notes.values():
                ratio, amplitude, phase = note
                frequency = ratio * self.base_freq
                final_sound += self.get_wave(frequency, phase) * amplitude
                # update phase
                note[2] = (phase + self.segment_duration * frequency * 2*np.pi) % (2*np.pi)

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
    
    def add_note(self, freq, volume=1, phase=0):
        self.notes_to_add.append((self.next_voice_num, [freq, volume, phase]))
        self.next_voice_num += 1
    
    def remove_note(self, freq):
        for voice_num, note in self.notes.items():
            if note[0] == freq:
                self.notes_to_delete.append(voice_num)
                break
    
    def get_chord(self):
        return [[freq, volume, voice_num] for voice_num, [freq, volume, phase] in self.notes.items()
                if freq != 0]
    
    def turn_off_all(self):
        self.notes = dict()
        # self.next_voice_num = 0
    
    def set_chord(self, chord):
        for freq, volume, voice_num in chord:
            if voice_num in self.notes:
                # ! update existing note
                self.notes[voice_num][0] = freq
                self.notes[voice_num][1] = volume
            else:
                # ! add new note
                self.add_note(freq, volume)
        # ! remove notes that are not in the chord
        new_voice_nums = [voice_num for freq, volume, voice_num in chord]
        for voice_num, [freq, _, _] in self.notes.items():
            if voice_num not in new_voice_nums:
                self.remove_note(freq)
    
    def move_note(self, old_freq, new_freq=None, volume_change=None):
        # ! assumes that the voice_num exists
        for freq, _, voice_num in self.get_chord():
            if freq == old_freq:
                if new_freq is not None:
                    self.notes[voice_num][0] = new_freq
                if volume_change is not None:
                    self.notes[voice_num][1] *= volume_change
                break
