from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import subprocess
import os
from datetime import datetime
from time import time
import uuid
from collections import defaultdict, deque
import json
from audio import wav_to_mfcc
from utils import save_file, DataCollector
import time
import requests
from pydub import AudioSegment
import os

import wave
# 오디오 파일이 저장되는 디렉터리
BASE_DIR = "./audio"

# 데이터를 저장해주는 클래스, in utils, 들어오는 데이터를 관리해준다.
collector = DataCollector()
temp = []
CNT = 0

app = Flask(__name__)
socketio = SocketIO(app)

# 가져가면 여기 mysql 비밀번호 바꿔야한다.
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:rootpass@localhost:3306/uav"
app.config["SECRET_KEY"] = str(uuid.uuid4())
db = SQLAlchemy(app)


# Sensor 모델 정의
class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_number = db.Column(db.Integer, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username

    def set_password(self, password):
        self.password_hash = password

    def check_password(self, password):
        return self.password_hash == password


# 데이터베이스 초기화
with app.app_context():
    db.create_all()


def send_activated_sensors():
    emit("activated_sensors", collector.get_activated_sensor_list(), broadcast=True)



@socketio.on("audio")
def handle_audio(data):
    global temp, CNT
    # 변수에 데이터 저장
    recieved_data = data["data"]  # Blob
    temp.append(recieved_data)

    # print(recieved_data)
    sensor_num = data["sensor_number"]
    is_connected = data["is_connected"]
    collector.put_sersor_data(sensor_num, recieved_data, is_connected)

#     send_activated_sensors()
    # 클라이언트로부터 받아오 데이터를 monitor로 전송하기 위한 코드
    # emit('get_sensor_data', {'sensor_id': sensor_num, 'sensor_value': recieved_data}, broadcast=True)


# 홈페이지 라우트
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/monitor")
def monitor():
    return render_template("monitor.html")


# 오디오 업로드 라우트, 저장하는 부분, for dataset
@app.route("/upload/audio", methods=["POST"])
def upload_audio():
    # 현재 시간대로 파일 이름 설정
    file_name = str(int(time.time()))
    file_dir = os.path.join(BASE_DIR, str(session["sensor_number"]))

    # 센서 번호에 해당하는 디렉토리가 없으면 생성
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # 오디오 파일 업로드
    if "audio_file" not in request.files:
        return "No file part"
    webm_file = file_dir + f"/{file_name}_audio.webm"
    audio_file = file_dir + f"/{file_name}_audio.wav"
    audio = request.files['audio_file']
    
    # audio_url_content = requests.get(audio_url)
    # with open(file_dir + f"/{file_name}_audio.wav", "wb") as f:
    #     f.write(audio_url_content.content)
    audio.save(webm_file)
    
    audio = AudioSegment.from_file(webm_file, format="webm")
    audio.export(audio_file, format="wav")
    os.remove(webm_file)

    return "Audio uploaded successfully"


# 로그인 라우트
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        sensor_number = request.form["sensor_number"]
        password = request.form["password_hash"]

        # 입력된 센서 번호와 비밀번호로 사용자 인증
        sensor = Sensor.query.filter_by(
            sensor_number=sensor_number, password_hash=password
        ).first()

        if sensor:
            # 세션에 사용자 정보 저장
            session["id"] = sensor.id
            session["sensor_number"] = sensor.sensor_number
            return redirect(url_for("client"))
        else:
            # 인증 실패 시 에러 메시지 표시
            return render_template(
                "login.html", message="Invalid username or password. Please try again."
            )

    elif request.method == "GET":
        return render_template("login.html")


# 클라이언트 라우트
@app.route("/client")
def client():
    sensor_number = session["sensor_number"]
    return render_template("client.html", sensor_number=sensor_number)


@app.route("/mfcc", methods=["GET"])
def mfcc():
    if collector.is_full():
        mfcc_result = collector.get_all_mfcc()
        json_result = jsonify(mfcc_result)
        return json_result
    else:
        return "no"

# 메인 함수
if __name__ == "__main__":

    # socketio.run(app,host='0.0.0.0', port = 80)
    socketio.run(app, port=5000)
