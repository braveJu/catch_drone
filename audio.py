import librosa
import numpy as np
import io
import librosa.display
import matplotlib.pyplot as plt
import os
from scipy.io import wavfile
import audioread
import time
import tempfile
import wave


def blobs_to_mfcc(sensor_num, blob_list, sample_rate=22050, n_mfcc=40):
    # 모든 blob 데이터를 합치기 위한 빈 바이너리 데이터 생성
    combined_blob = b"".join(blob_list)
    save_audio_from_bytes(combined_blob, './temp/temp{}.mp3'.format(sensor_num))
    # 임시 파일을 librosa로 읽기
    audio_data, _ = librosa.load('./temp/temp{}.mp3'.format(sensor_num), sr=sample_rate, mono=True)
    # MFCC 계산
    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    # os.remove('./temp/temp{}.wav'.format(sensor_num))

    return mfcc


def save_audio_from_bytes(byte_data, file_path, sample_width=2, channels=1, frame_rate=22050):
    # 오디오 파일 열기
    with wave.open(file_path, 'wb') as wf:
        # 오디오 파일 설정
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(frame_rate)
        # byte 데이터를 파일에 씀
        wf.writeframes(byte_data)
        
