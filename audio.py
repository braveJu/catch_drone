import librosa
import numpy as np
import io
import wave
from utils import load_file


def blob_list_to_np_array(data):
    li = []
    for blob in data:
        bf = np.frombuffer(blob, dtype='B')
        print(len(bf))
        li.append(bf)
    return np.array(li)


# data = load_file('./1_blob.pickle')
# # print(data)
# # feature_map = blobs_to_feature_map(data)
# print(blob_list_to_np_array(data))