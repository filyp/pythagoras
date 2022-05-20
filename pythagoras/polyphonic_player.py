import time
import threading
import dataclasses

import numpy as np
import sounddevice


BIT_RATE = 48000


@dataclasses.dataclass
class Note:
    freq: float
    volume: float
    phase: float
    voice_num: int


class PolyphonicPlayer(threading.Thread):
    segment_duration = 0.010  # in seconds

    def __init__(self, base_freq=10, master_volume=0.05):
        threading.Thread.__init__(self)

        self.stream = sounddevice.RawOutputStream(channels=1, samplerate=BIT_RATE)
        self.stream.start()

        self.alive = True
        self.base_freq = base_freq
        self.master_volume = master_volume  # lower the volume to avoid clipping
        self.notes = list()
        self.notes_to_add = list()
        self.notes_to_delete = list()
        self.notes_to_move = list()
        self.chord_to_set = None
        self._warned_about_clipping = False

    def run(self):
        while self.alive:
            # * self.notes should only be modified in this loop
            # ! add and delete queued notes
            while self.notes_to_add:
                note = self.notes_to_add.pop()
                self.notes.append(note)
            while self.notes_to_delete:
                note = self.notes_to_delete.pop()
                if note in self.notes:
                    self.notes.remove(note)
            # ! set a chord
            if self.chord_to_set is not None:
                existing_voice_nums = set(note.voice_num for note in self.notes)
                new_voice_nums = set(self.chord_to_set.keys())
                voice_nums_to_add = new_voice_nums - existing_voice_nums
                voice_nums_to_delete = existing_voice_nums - new_voice_nums
                voice_nums_to_change = new_voice_nums & existing_voice_nums
                for voice_num in voice_nums_to_add:
                    self.notes.append(self.chord_to_set[voice_num])
                for voice_num in voice_nums_to_delete:
                    self.notes.remove(self._get_note_by_voice_num(voice_num))
                for voice_num in voice_nums_to_change:
                    note = self._get_note_by_voice_num(voice_num)
                    note.freq = self.chord_to_set[voice_num].freq
                    note.volume = self.chord_to_set[voice_num].volume
                self.chord_to_set = None
            # ! move notes
            while self.notes_to_move:
                old_freq, new_freq, volume_change = self.notes_to_move.pop()
                for note in self.notes:
                    if note.freq == old_freq:
                        # change this note
                        if new_freq is not None:
                            note.freq = new_freq
                        if volume_change is not None:
                            note.volume *= volume_change
                        break

            if len(self.notes) == 0:
                # no frequencies given so be silent
                time.sleep(self.segment_duration)
                continue

            # ! construct a sound
            final_sound = 0
            for note in self.notes:
                final_frequency = note.freq * self.base_freq
                final_sound += self.get_wave(final_frequency, note.phase) * note.volume
                # update phase
                phase_change = self.segment_duration * final_frequency * 2 * np.pi
                note.phase = (note.phase + phase_change) % (2 * np.pi)

            final_sound *= self.master_volume
            if np.max(np.abs(final_sound)) > 1 and not self._warned_about_clipping:
                print("WARNING: sound is clipping - lower the volume")
                # warn only once
                self._warned_about_clipping = True
            # clip the sound to -1..1
            final_sound = np.clip(final_sound, -1, 1)

            self.stream.write(final_sound.astype(np.float32).tobytes())

        self.stream.stop()
        self.stream.close()

    def get_wave(self, frequency, phase):
        ts = np.arange(BIT_RATE * self.segment_duration) / BIT_RATE
        wave = np.sin(2 * np.pi * frequency * ts + phase)

        # adjust volume
        human_amp = self.human_corrected_amplitude(frequency)
        # human_amp = 1
        return wave * human_amp

    def human_corrected_amplitude(self, frequency):
        low_limit = 300
        slope = -1.0
        rescaled = max(frequency / low_limit, 1)
        return rescaled**slope

    def kill(self):
        self.alive = False

    def add_note(self, freq, volume=1, phase=0):
        # randomly choose a new voice_num that is not in use
        voice_nums = [note.voice_num for note in self.notes.copy()]
        while True:
            voice_num = np.random.randint(2**32)
            if voice_num not in voice_nums:
                break
        note = Note(freq, volume, phase, voice_num)
        self.notes_to_add.append(note)

    def remove_note(self, freq_to_delete):
        for note in self.notes.copy():
            if note.freq == freq_to_delete:
                self.notes_to_delete.append(note)
                break

    def get_chord(self):
        return [(note.freq, note.volume, note.voice_num) for note in self.notes.copy()]

    def turn_off_all(self):
        for note in self.notes.copy():
            self.notes_to_delete.append(note)

    def set_chord(self, chord):
        formatted_chord = dict()
        for freq, volume, voice_num in chord:
            formatted_chord[voice_num] = Note(freq, volume, 0, voice_num)
        self.chord_to_set = formatted_chord

    def move_note(self, old_freq, new_freq=None, volume_change=None):
        self.notes_to_move.append((old_freq, new_freq, volume_change))

    def _get_note_by_voice_num(self, voice_num):
        for note in self.notes.copy():
            if note.voice_num == voice_num:
                return note
        return None
