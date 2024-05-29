import cv2
from datetime import datetime
import time
import os
import datetime

cap = cv2.VideoCapture(0)

# Create Object
if not cap.isOpened():
    print("Cannot open the webcam")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

try:
    while True:
        # 프레임 읽기
        ret, frame = cap.read()

        if not ret:
            print("Cannot read the frame")
            break
        # 이미지 파일명 및 경로 설정
        current_time = datetime.datetime.now()
        making_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")

        if not os.path.exists("image"):
            os.makedirs("image")

        file_name = f"image/{making_time}.jpg"

        # Save the file
        cv2.imwrite(file_name, frame)
        print(f"Image Saved: {file_name}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Capture stopped.")

finally:
    # 캡처 객체 해제
    cap.release()
    cv2.destroyAllWindows()
