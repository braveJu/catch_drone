import requests
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image


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
            spectrogram_data = spectrogram['image'][1]  # mel-spectrogram 데이터 리스트

            # 파이썬 리스트를 numpy 배열로 변환
            spectrogram_array = np.array(spectrogram_data)
            spectrogram_dict[sensor_number] = spectrogram_array
    else:
        print(f"Failed to get data from server. Status code: {response.status_code}")

    return spectrogram_dict
    

# 서버 URL
url = "http://localhost:5000/mel-spectrogram"

# 요청 보내기
response = requests.get(url)

# 응답이 성공적인지 확인
if response.status_code == 200:
    data = response.json()
    spectrograms = data['spectrograms']

    # 각각의 spectrogram 데이터 처리
    for idx, spectrogram in enumerate(spectrograms):
        sensor_number = spectrogram['sensor_number']
        spectrogram_data = spectrogram['image'][1]  # mel-spectrogram 데이터 리스트

        # 파이썬 리스트를 numpy 배열로 변환
        image_file = np.array(spectrogram_data)

        # 이미지 저장
        # image_path = f"spectrogram_{sensor_number}_{idx}.png"
        # img = Image.fromarray(image_file.astype('uint8'))  # 넘파이 배열을 이미지로 변환
        # img.save(image_path)
        # print(f"Saved spectrogram image for sensor {sensor_number} as {image_path}")

