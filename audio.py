import librosa
import numpy as np
import io
import wave
from utils import load_file


def blob_list_to_np_array(blob_list):
    # 모든 blob의 크기를 확인하고 가장 작은 형태를 선택
    blob_shapes = [len(blob) for blob in blob_list]
    common_shape = np.min(blob_shapes, axis=0)  # 모든 blob 중 가장 작은 shape을 선택

    # 가장 작은 형태에 맞게 blob을 잘라냄
    cropped_blobs = [blob[:common_shape] for blob in blob_list]
    # 변환된 blob을 numpy 배열로 변환
    return np.array(cropped_blobs)

def darray2mfcc(audio_array:np.array):
    # 받아온 데이터로 
    return 0

data = load_file('./1_blob.pickle')
# print(data)
# feature_map = blobs_to_feature_map(data)
print(blob_list_to_np_array(data))