import os
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
from timeloop import Timeloop
from BMS import BMS
import threading
from tinytag import TinyTag
import pickle
import soundfile as sf
from functools import lru_cache
import numpy as np


def s_len(fp):
    return TinyTag.get(fp).duration


@lru_cache(maxsize=128)
def read_audio(audio_path):
    audio_data, _ = sf.read(audio_path)
    return audio_data


@lru_cache(maxsize=None)
def get_l(fp, sample_rate=44100):
    return s_len(fp) * sample_rate


class BMSPlayer:
    __slots__ = ['track', 'zip_track', 'tl', 'flag', 'mspt', 't', 's_type']

    def __init__(self, bms_fp, key_fp, type='wav', cache=True, new=False):

        self.track: list
        self.zip_track: list
        self.tl = Timeloop()
        self.flag = True
        self.mspt: float
        self.t = None
        self.s_type: str

        fn = os.path.basename(bms_fp).split('.')[0]
        if self.__check_cache(fn):
            obj = BMSPlayer.load(fn)
            self.__dict__.update(obj.__dict__)
        else:
            bms = BMS(bms_fp, type)
            self.s_type = type
            key_list = [os.path.join(key_fp, key + '.' + type) for key in bms.key_dict.values()]
            wav_lens = dict(zip(key_list, [s_len(fp) for fp in key_list]))
            func = {'wav': AudioSegment.from_wav, 'ogg': AudioSegment.from_ogg}
            self.track = [sorted([os.path.join(key_fp, n) for n in notes], key=lambda fp: wav_lens[fp], reverse=True)
                          for
                          notes in bms.track]
            self.zip_track = [
                [sorted([os.path.join(key_fp, n) for n in notes[0]], key=lambda fp: wav_lens[fp], reverse=True),
                 notes[1]]
                for notes in bms.zip()]
            if not self.zip_track[0][0]:
                self.zip_track = self.zip_track[1:]
            self.mspt = 4 * 60 / (bms.m_l * bms.Bpm)
            self.__save2file(fn)

    def __check_cache(self, fn: str, fp='./'):
        if os.path.exists(os.path.join(fp, fn + '_bmsp')):
            return True
        else:
            return False

    def __save2file(self, fn: str, fp='./'):
        with open(os.path.join(fp, fn + '_bmsp'), 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, fn: str, fp='./'):
        with open(os.path.join(fp, fn + '_bmsp'), 'rb') as f:
            return pickle.load(f)

    def __get_s(self, l: list, t: str):
        func = {'wav': AudioSegment.from_wav, 'ogg': AudioSegment.from_ogg}
        n = len(l)
        if not n:
            return None
        elif n == 1:
            return func[t](l[0])
        else:
            sound = func[t](l[0])
            for i in range(1, n):
                sound = sound.overlay(func[t](l[i]))
            return sound

    def __play(self, func, n=1):
        self.t = threading.Timer(self.mspt * n, func)
        self.t.start()

    def play(self):
        self.p = iter(self.track)
        self.__play(self.__check)

    def __check(self):
        try:
            l = next(self.p)
            self.__play(self.__check)
            if l:
                self.__multi_play(l)
                # _play_with_simpleaudio(l)
        except StopIteration:
            self.t.cancel()

    def __multi_play(self, l: list):
        if not l:
            return
        func = {'wav': AudioSegment.from_wav, 'ogg': AudioSegment.from_ogg}
        n = len(l)
        if n == 1:
            _play_with_simpleaudio(func[self.s_type](l[0]))
        else:
            sound = func[self.s_type](l[0])
            for i in range(1, n):
                sound = sound.overlay(func[self.s_type](l[i]))
            _play_with_simpleaudio(sound)

    def zip_play(self):
        self.p = iter(self.zip_track)
        self.__play(self.__zip_check)

    def __zip_check(self):
        try:
            l = next(self.p)
            self.__play(self.__zip_check, n=l[1])
            if l:
                self.__multi_play(l[0])
        except StopIteration:
            self.t.cancel()

    def save_preview(self, fp='./'):
        _, sample_rate = sf.read(self.zip_track[0][0][0])
        l = len(self.zip_track)
        durations = np.zeros(l)
        durations[0] = self.zip_track[0][1]
        for i in range(1, l):
            durations[i] = durations[i - 1] + self.zip_track[i][1]
        durations = durations * self.mspt * sample_rate + np.array([get_l(self.zip_track[i][0][0], sample_rate) for i in range(l)])
        get_l.cache_clear()
        duration = np.max(durations)
        output_audio = np.zeros((int(duration) + 1, 2), dtype='float64')
        start_sample = 0.
        for audios, time in self.zip_track:
            if audios:
                for audio in audios:
                    end_sample = start_sample + get_l(audio)
                    output_audio[int(start_sample):int(end_sample)] += read_audio(audio)
            start_sample += time * self.mspt * 44100
        output_audio = output_audio / np.max(np.abs(output_audio))
        sf.write('preview.wav', output_audio, 44100, 'PCM_24')
