import librosa
import numpy as np
import io
import librosa.display
import matplotlib.pyplot as plt
import os


def blob_list_to_np_array(blob_list):
    # 모든 blob의 크기를 확인하고 가장 작은 형태를 선택
    res = []
    for blob in blob_list:
        arr = np.frombuffer(blob, dtype=np.int16)
        arr = arr[~np.isnan(arr)].tolist()
        for i in arr:
            res.append(i)
    return np.array(res)


def blob_list2mfcc(blob_list, sample_rate = 22050, n_mfcc = 40):
    # blob_array를 어떻게 normalize 할지 정해야함!
    
    numpy_array = blob_list_to_np_array(blob_list)
    # audio_array, _ = librosa.load(io.BytesIO(audio_combined), sr=sample_rate, mono=True)
    hop_length = len(numpy_array) // 128
    mfcc = librosa.feature.mfcc(numpy_array, sr=sample_rate, n_mfcc=n_mfcc, hop_length=hop_length)

    return mfcc


import tempfile

def blobs_to_mfcc(blob_list, sample_rate=22050, n_mfcc=40):
    # 모든 blob 데이터를 합치기 위한 빈 바이너리 데이터 생성
    combined_blob = b''
    for blob in blob_list:
        combined_blob += blob  # 각 blob을 합침
        
    # BytesIO 객체로 변환
    combined_blob_io = io.BytesIO(combined_blob)
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
        temp_file.write(combined_blob)
        temp_file_path = temp_file.name
    
    # 임시 파일을 librosa로 읽기
    audio_data, _ = librosa.load(temp_file_path, sr=sample_rate, mono=True)
    
    # MFCC 계산
    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    
    # 임시 파일 삭제
    os.unlink(temp_file_path)
    
    return mfcc

