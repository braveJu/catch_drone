from audio import blobs_to_mel_spectrogram
import pickle
from collections import defaultdict, deque
import numpy as np
from io import BytesIO
import asyncio
import os
import time
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
import librosa
from flask import jsonify
import base64

AUDIO_BASE_DIR = "./audio"
TEMP_BASE_DIR = "./temp"


MAX_SENSOR_NUM = 2
MAX_BLOB = 2


# 센서 데이터를 관리해주는 클래스
class DataCollector:
    def __init__(self, max_sensor_num=MAX_SENSOR_NUM, max_blob=MAX_BLOB) -> None:
        self.max_sensor_num = max_sensor_num
        self.activated_sensor = set()
        self.max_blob = max_blob
        self.sensor_data_dict = defaultdict(deque)
        self.is_stoped = set()
        self.header = None
        self.sensor_buffer = []
        self.spectrogram_buffer = []
        self.filename_buffer = []
        self.pair_list = []

    def setheader(self, header):
        self.header = b''.join(header[:3])

    def put_sersor_data(self, sensor_num, recieved_data, is_connected: bool):
        if is_connected and not sensor_num in self.is_stoped:
            self.activated_sensor.add(sensor_num)

            # 센서들 다 activated 되었을 때 데이터를 받아올 수 있게 한다.
            if len(self.activated_sensor) == self.max_sensor_num:
                # max_blob을 넘어가지 않게
                if len(self.sensor_data_dict[sensor_num]) > self.max_blob:
                    self.sensor_data_dict[sensor_num].popleft()
                self.sensor_data_dict[sensor_num].append(recieved_data)

        else:
            # 센서가 종료되면 activated_sensor에서 없애고, 사전도 없앤다.
            if sensor_num in self.is_stoped:
                self.is_stoped.discard(sensor_num)

            else:
                self.is_stoped.add(sensor_num)
                self.activated_sensor.discard(sensor_num)
                self.sensor_data_dict[sensor_num] = deque()

    # 오름차순으로 정리되어있는 리스트로 반환, monitoring 하기 위한
    def get_activated_sensor_list(self):
        return sorted(list(self.activated_sensor))

    # 센서들의 데이터용량이 다 차면 데이터를 mfcc로 변환해주는 함수
    def get_all_mel_spectrogram(self):
        mel_spectogram_result = dict()
        tasks = []
        for key in self.sensor_data_dict.keys():
            # deque -> list
            list_val = list(self.sensor_data_dict[key])
            tasks.append(blobs_to_mel_spectrogram(key, list_val))

        for key, result in zip(self.sensor_data_dict.keys(), tasks):
            mel_spectogram_result[key] = result.tolist()
        self.flush()
        return mel_spectogram_result

    # 모든 센서에 데이터가 다 차면?
    def is_full(self):
        if len(self.activated_sensor) == self.max_sensor_num:
            for key, val in self.sensor_data_dict.items():
                if len(val) < self.max_blob:
                    return False
            return True
        else:
            return False

    def status(self):
        if len(self.activated_sensor) > 0:
            print(f"Activated : {self.get_activated_sensor_list()}")

    def flush(self):
        for key in self.sensor_data_dict.keys():
            self.sensor_data_dict[key] = deque()
    
    
    def write_pair_info(self):
        with open("pair.txt", 'a+') as f:
            f.writelines(self.pair_list)


def save_file(file_name: str, data):
    with open(file_name, "wb") as f:
        pickle.dumps(data, f)


def load_file1(name: str):
    with open(f"{name}", "rb") as f:
        data = pickle.load(f)
    return data


def blob_save_with_wav(header, sensor_number, blobs, making_time):
    # 헤더정보를 추가하여 데이터 보존.
    webm_blob = header + b''.join(blobs)
    file_name = making_time

    wav_file_dir = os.path.join(AUDIO_BASE_DIR, str(sensor_number))
    webm_file_dir = os.path.join(TEMP_BASE_DIR, str(sensor_number))

    webm_file = os.path.join(webm_file_dir, f"{file_name}.webm")
    wav_file = os.path.join(wav_file_dir, f"{file_name}.wav")

    
    
    # 센서 번호에 해당하는 디렉토리가 없으면 생성
    if not os.path.exists(wav_file_dir):
        os.makedirs(wav_file_dir)

    if not os.path.exists(webm_file_dir):
        os.makedirs(webm_file_dir)

    
    file = open(webm_file, "wb")
    file.write(webm_blob)
    file.close()

    audio = AudioSegment.from_file(webm_file, format="webm")
    audio.export(wav_file, format="wav")
