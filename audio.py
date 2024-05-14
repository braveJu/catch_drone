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
from pydub import AudioSegment
import asyncio
import moviepy.editor as moviepy



import io

def combine_blobs(blobs):
    combined_blob = io.BytesIO()
    for blob in blobs:
        combined_blob.write(blob)
    combined_blob.seek(0)
    return combined_blob

# def save_as_webm(blob, filename):
#     with open(filename, 'wb') as f:
#         f.write(blob.getvalue())

import subprocess

def convert_webm_to_wav(input_filename, output_filename):
    subprocess.run(['ffmpeg', '-i', input_filename, output_filename])


def blobs_to_mfcc(sensor_num, blob_list, sample_rate=44100, n_mfcc=40):
    # 모든 blob 데이터를 합치기 위한 빈 바이너리 데이터 생성
    combined_blob = combine_blobs(blob_list)
    # save_as_webm(combined_blob, f"./temp/{sensor_num}.webm")
    # clip = moviepy.VideoFileClip(f"./temp/{sensor_num}.webm")
    # clip.write_audiofile(f"./temp/{sensor_num}.wav")

    
    # save_audio_from_bytes(combined_blob, './temp/temp{}.wav'.format(sensor_num))
    # 임시 파일을 librosa로 읽기
    audio_data, _ = librosa.load(f'./temp/{sensor_num}.wav', sr=sample_rate, mono=True)
    # MFCC 계산
    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    return mfcc

def save_audio_from_bytes(byte_data, file_path, sample_width=2, channels=1, frame_rate=44100):
    # 오디오 파일 열기
    with wave.open(file_path, 'wb') as wf:
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