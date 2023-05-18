from pynput import keyboard as kb
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
from TimePlayer import BMSPlayer

p = 0
b = BMSPlayer(r'E:\Unknow\BMS\energy trixxx_wav\another.bms', r'E:\Unknow\BMS\energy trixxx_wav')
a = b.zip_track


def muti_play(l: list):
    if not l:
        return
    n = len(l)
    if n == 1:
        _play_with_simpleaudio(AudioSegment.from_wav(l[0]))
    else:
        sound = AudioSegment.from_wav(l[0])
        for i in range(1, n):
            sound = sound.overlay(AudioSegment.from_wav(l[i]))
        _play_with_simpleaudio(sound)


def on_press(key):
    global p,a
    muti_play(a[p][0])
    p += 1


if __name__ == "__main__":
    with kb.Listener(on_press=on_press) as lsn:
        lsn.join()