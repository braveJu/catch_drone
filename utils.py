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

# 오디오 데이터가 저장되는 디렉토리
AUDIO_BASE_DIR = os.path.join(os.getcwd(), "audio")
TEMP_BASE_DIR = os.path.join(os.getcwd(), "temp")

# 최대 센서 수와 최대 블랍 수 정의
MAX_SENSOR_NUM = 2
MAX_BLOB = 2


# 센서 데이터를 관리하는 클래스
class DataCollector:
    def __init__(self, max_sensor_num=MAX_SENSOR_NUM, max_blob=MAX_BLOB) -> None:
        self.max_sensor_num = max_sensor_num
        self.activated_sensor = set()  # 활성화된 센서 목록
        self.max_blob = max_blob
        self.sensor_data_dict = defaultdict(deque)  # 각 센서의 데이터 저장
        self.is_stoped = set()  # 정지된 센서 목록
        self.header = None
        self.sensor_buffer = []
        self.spectrogram_buffer = []
        self.filename_buffer = []
        self.image_path_buffer = []
        self.pair_list = []
        self.pair_cnt = 0

    # 헤더 설정 함수
    def setheader(self, header):
        self.header = b"".join(header[:3])

    # 센서 데이터 추가 함수
    def put_sensor_data(self, sensor_num, recieved_data, is_connected: bool):
        if is_connected and sensor_num not in self.is_stoped:
            self.activated_sensor.add(sensor_num)

            # 모든 센서가 활성화되었을 때 데이터 수집 시작
            if len(self.activated_sensor) == self.max_sensor_num:
                if len(self.sensor_data_dict[sensor_num]) > self.max_blob:
                    self.sensor_data_dict[sensor_num].popleft()
                self.sensor_data_dict[sensor_num].append(recieved_data)
        else:
            # 센서가 종료되면 데이터 초기화
            if sensor_num in self.is_stoped:
                self.is_stoped.discard(sensor_num)
            else:
                self.is_stoped.add(sensor_num)
                self.activated_sensor.discard(sensor_num)
                self.sensor_data_dict[sensor_num] = deque()

    # 활성화된 센서 목록 반환 함수
    def get_activated_sensor_list(self):
        return sorted(list(self.activated_sensor))

    # 모든 센서의 데이터가 가득 찼을 때 MFCC로 변환하는 함수
    def get_all_mel_spectrogram(self):
        mel_spectrogram_result = dict()
        tasks = []
        for key in self.sensor_data_dict.keys():
            list_val = list(self.sensor_data_dict[key])
            tasks.append(blobs_to_mel_spectrogram(key, list_val))

        for key, result in zip(self.sensor_data_dict.keys(), tasks):
            mel_spectrogram_result[key] = result.tolist()
        self.flush()
        return mel_spectrogram_result

    # 모든 센서의 데이터가 가득 찼는지 확인하는 함수
    def is_full(self):
        if len(self.activated_sensor) == self.max_sensor_num:
            for key, val in self.sensor_data_dict.items():
                if len(val) < self.max_blob:
                    return False
            return True
        return False

    # 현재 활성화된 센서 상태 출력 함수
    def status(self):
        if len(self.activated_sensor) > 0:
            print(f"Activated: {self.get_activated_sensor_list()}")

    # 데이터 초기화 함수
    def flush(self):
        for key in self.sensor_data_dict.keys():
            self.sensor_data_dict[key] = deque()

    # 페어 정보를 파일에 저장하는 함수
    def write_pair_info(self):
        with open("pair.txt", "a") as f:
            f.writelines(self.pair_list)


# 파일 저장 함수
def save_file(file_name: str, data):
    with open(file_name, "wb") as f:
        pickle.dump(data, f)


# 파일 로드 함수
def load_file1(name: str):
    with open(name, "rb") as f:
        data = pickle.load(f)
    return data


# 블랍 데이터를 WAV 파일로 저장하는 함수
def blob_save_with_wav(header, sensor_number, blobs, making_time):
    webm_blob = header + b"".join(blobs)
    file_name = making_time

    wav_file_dir = os.path.join(AUDIO_BASE_DIR, str(sensor_number))
    webm_file_dir = os.path.join(TEMP_BASE_DIR, str(sensor_number))

    webm_file = os.path.join(webm_file_dir, f"{file_name}.webm")
    wav_file = os.path.join(wav_file_dir, f"{file_name}.wav")

    # 디렉토리가 존재하지 않으면 생성
    os.makedirs(wav_file_dir, exist_ok=True)
    os.makedirs(webm_file_dir, exist_ok=True)

    # 웹엠 파일 저장
    with open(webm_file, "wb") as file:
        file.write(webm_blob)

    # 웹엠 파일을 WAV 파일로 변환하여 저장
    audio = AudioSegment.from_file(webm_file, format="webm")
    audio.export(wav_file, format="wav")
