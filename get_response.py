import requests
import numpy as np
from PIL import Image

# 모델의 입력 mel-spectrogram을 받게 하는 함수

#이 함수를 0.5초마다 실행시키면 좋을듯.
def get_mel_spectrogram(url:str):
    response = requests.get(url)
    spectrogram_dict = {}
    if response.status_code == 200:
        data = response.json()
        spectrograms = data['spectrograms']

        # 각각의 spectrogram 데이터 처리
        for idx, spectrogram in enumerate(spectrograms):
            sensor_number = spectrogram['sensor_number']
            spectrogram_data = spectrogram['image']  # mel-spectrogram 데이터 리스트
            
            # 파이썬 리스트를 numpy 배열로 변환
            spectrogram_array = np.array(spectrogram_data)
            print(spectrogram_array.shape)
            spectrogram_dict[sensor_number] = spectrogram_array
            
            image_path = f"spectrogram_{sensor_number}.png"
            img = Image.fromarray(spectrogram_array.astype('uint8'))  # 넘파이 배열을 이미지로 변환
            img.save(image_path)
    else:
        print(f"Failed to get data from server. Status code: {response.status_code}")

    return spectrogram_dict
    


# url = "https://dronecatcher.info/mel-spectrog\ram"
url = 'http://127.0.0.1:5000/mel-spectrogram'
get_mel_spectrogram(url)