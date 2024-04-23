from audio import blobs_to_mfcc
import pickle
from collections import defaultdict, deque
import numpy as np



# 센서 데이터를 관리해주는 클래스
class DataCollector:
    def __init__(self, max_sensor_num=1, max_blob=20) -> None:
        self.max_sensor_num = max_sensor_num
        self.activated_sensor = set()
        self.max_blob = max_blob
        self.sensor_data_dict = defaultdict(deque)
        self.is_stoped = set()

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

    # librosa에 데이터가 들어가야하는데, 어떻게 들어가야하지?

    # 센서들의 데이터용량이 다 차면 데이터를 mfcc로 변환해주는 함수
    def get_all_mfcc(self):
        # 모든 센서들의 블록 리스트
        mfcc_result = dict()
        for key in self.sensor_data_dict.keys():
            #deque -> list
            list_val = list(self.sensor_data_dict[key])
            mfcc = blobs_to_mfcc(key, list_val)
            mfcc_result[key] = mfcc.tolist()
        self.flush()
        return mfcc_result

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
        if len(self.activated_sensor)> 0:
            print(f"Activated : {self.get_activated_sensor_list()}")

    def flush(self):
        for key in self.sensor_data_dict.keys():
            self.sensor_data_dict[key] = deque()
        
# 데이터 저장하고, 불러오는 함수들

def save_file(file_name: str, data):
    with open(file_name, "wb") as f:
        pickle.dumps(data, f)


def load_file1(name: str):
    with open(f"{name}", "rb") as f:
        data = pickle.load(f)
    return data

