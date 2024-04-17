import pickle
from collections import defaultdict, deque
import numpy as np

def save_file(file_name:str, data):
    with open(file_name, 'wb') as f:
        pickle.dump(data, f)
        
        
def load_file(name:str):
    with open(f'{name}', 'rb') as f:
        data = pickle.load(f)
    return data


#센서 데이터를 관리해주는 클래스
class DataCollector:
    def __init__(self, max_blob = 1000) -> None:
        self.activated_sensor = set()
        self.max_blob = max_blob
        self.sensor_data_dict = defaultdict(deque)
    
    def put_sersor_data(self, sensor_num, recieved_data, is_connected:bool):
        if is_connected:
            self.activated_sensor.add(sensor_num)
            
            # max_blob을 넘어가지 않게 1000 되면 1000개로 유지
            if len(self.sensor_data_dict[sensor_num])>self.max_blob:
                self.sensor_data_dict[sensor_num].popleft()
            self.sensor_data_dict[sensor_num].append(recieved_data)

        else:
            #센서가 종료되면 activated_sensor에서 없애고, 사전도 없앤다.
            self.activated_sensor.discard(sensor_num)
            del self.sensor_data_dict[sensor_num]
    
    # 오름차순으로 정리되어있는 리스트로 반환, monitoring 하기 위한
    def get_activated_sensor_list(self):
        return sorted(list(self.activated_sensor))
    
    
    #librosa에 데이터가 들어가야하는데, 어떻게 들어가야하지?
    def convert2numpy(self):
        if self.is_full():
            result_array = np.array([])
            for key, val in self.sensor_data_dict.items():
                pass
    
    # 모든 센서에 데이터가 다 차면?
    def is_full(self):
        for key, val in self.sensor_data_dict.items():
            if len(val) <= self.max_blob:
                return False
        return True
    
    
    