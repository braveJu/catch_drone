import librosa
import numpy as np
import librosa.display
import matplotlib.pyplot as plt
from scipy.io import wavfile
import time
import wave
from pydub import AudioSegment
import moviepy.editor as moviepy
import os
import subprocess
from PIL import Image

import io

def combine_blobs(blobs):
    combined_blob = b"".join(blobs)

    return combined_blob


# webm 파일로 저장해주는 함수.
def save_as_webm(blob, filename):
    with open(filename, "wb") as f:
        f.write(blob.getvalue())


def convert_webm_to_wav(input_filename, output_filename):
    subprocess.run(["ffmpeg", "-i", input_filename, output_filename])


def blobs_to_mel_spectrogram(sensor_num, blob_list, sample_rate=44100, n_mfcc=40):
    # 모든 blob 데이터를 합치기 위한 빈 바이너리 데이터 생성
    combined_blob = combine_blobs(blob_list)
    file_name = str(int(time.time()))
    webm_file = f"./temp/{sensor_num}.webm"
    wav_file = f"./audio/{sensor_num}/{file_name}.wav"

    # 저장하고 clip에서 audio 데이터 뽑아옴
    save_as_webm(combined_blob, webm_file)
    clip = moviepy.VideoFileClip(webm_file)
    clip.write_audiofile(wav_file)

    # webm파일 사용하면 필요없으니 지워!
    os.remove(webm_file)

    # save_audio_from_bytes(combined_blob, './temp/temp{}.wav'.format(sensor_num))
    # 임시 파일을 librosa로 읽기
    audio_data, _ = librosa.load(wav_file, sr=sample_rate, mono=True)
    # MFCC 계산 or Melspectrogram 계산

    mel_spectogram = librosa.feature.melspectrogram(audio_data)
    # mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    return mel_spectogram


def save_audio_from_bytes(
    byte_data, file_path, sample_width=2, channels=1, frame_rate=44100
):
    # 오디오 파일 열기
    with wave.open(file_path, "wb") as wf:
        # 오디오 파일 설정
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(frame_rate)
        # byte 데이터를 파일에 씀
        wf.writeframes(byte_data)


def wav_to_mfcc(file_name, sample_rate=44100, n_mfcc=40):
    # 임시 파일을 librosa로 읽기
    audio_data, _ = librosa.load(file_name, sr=sample_rate, mono=True)
    # MFCC 계산
    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    return mfcc


def wav_to_mel_spectogram(wav_file, file_name,sample_rate=22050):
    signal, sr = librosa.load(wav_file, sr=sample_rate, mono=True)
    signal_normalized = librosa.util.normalize(signal)

    mel = librosa.feature.melspectrogram(
        y=signal_normalized, sr=sr, n_fft=1024, hop_length=len(signal) // 128 + 1
    )
    
    S_dB = librosa.power_to_db(mel, ref=np.max)

    # dB 범위를 [0, 255]로 스케일링
    S_dB_normalized = (S_dB - S_dB.min()) / (S_dB.max() - S_dB.min()) * 255
    S_dB_normalized = S_dB_normalized.astype(np.uint8)

    # 이미지 저장
    # img = Image.fromarray(S_dB_normalized)
    # img.save(f"{file_name}.png", format='PNG')
    return S_dB_normalized
