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
from audio import wav_to_mel_spectogram
from utils import save_file, DataCollector, blob_save_with_wav
import time
import datetime
from pydub import AudioSegment
import os


# 오디오 파일이 저장되는 디렉터리
BASE_DIR = "./audio"

# 데이터를 저장해주는 클래스, in utils, 들어오는 데이터를 관리해준다.
collector = DataCollector()
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


@socketio.on("temp")
def handle_temp(data):
    print(data["sensor_num"], "in!")
    collector.activated_sensor.add(data["sensor_num"])



@socketio.on("audio")
def handle_audio(data):
    # 변수에 데이터 저장
    # recieved_data = data["data"]  # Blob
    # header = data["header"]

    sensor_num = data["sensor_number"]
    is_connected = data["is_connected"]

    if is_connected:
        collector.activated_sensor.add(sensor_num)
    else:
        collector.activated_sensor.discard(sensor_num)
    emit("ready", len(collector.activated_sensor), broadcast=True)

    # if not collector.is_full():
    #     collector.put_sersor_data(sensor_num, recieved_data, is_connected)

    # # 받아온 헤더의 정보를 collector에 넣어준다.
    # if collector.header == None:
    #     collector.setheader(header=header)

    # # collector가 가득차면 데이터를 저장하자! 초마다. 같은 초의 파일이 생성되기 만들어야함
    # if collector.is_full():
    #     print("blob가득참")
    #     keys = list(collector.sensor_data_dict.keys())
    #     current_time = datetime.datetime.now()
    #     making_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    #     for key in collector.sensor_data_dict.keys():
    #         blob_list = collector.sensor_data_dict[key]
    #         if len(blob_list) == 0:
    #             pass
    #         blob_save_with_wav(
    #             header=collector.header,
    #             sensor_number=key,
    #             blobs=blob_list,
    #             making_time=str(making_time),
    #         )

    # for key in keys:
    #     wav_file = os.path.join(BASE_DIR, key, f"{making_time}.wav")
    # collector.flush()

    # print("가득 안참!")


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
# fetch로 데이터 받아올때 처리하는 함수입니다.
@app.route("/upload/audio", methods=["POST"])
def upload_audio():
    # 현재 시간대로 파일 이름 설정
    current_time = datetime.datetime.now()
    # file_name = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    sensor_number = request.form.get("sensor_number")
    
    file_name = request.form.get("file_name")

    webm_dir = os.path.join("./temp", sensor_number)
    file_dir = os.path.join(BASE_DIR, sensor_number)

    collector.sensor_buffer.append(sensor_number)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    if not os.path.exists(webm_dir):
        os.makedirs(webm_dir)

    # if len(collector.sensor_buffer) == collector.max_sensor_num:
    # 센서 번호에 해당하는 디렉토리가 없으면 생성

    webm_file = webm_dir + f"/{file_name}.webm"
    audio_file = file_dir + f"/{file_name}.wav"
    audio = request.files["audio_file"]
    audio.save(webm_file)

    audio = AudioSegment.from_file(webm_file, format="webm")
    audio.export(audio_file, format="wav")
    os.remove(webm_file)
    # 0 보다 크면 파일 하나가 이미 들어온거니까
        
    #mel-spectrogram 만드는 부분
    spectrogram = wav_to_mel_spectogram(wav_file=audio_file, file_name=audio_file).tolist()
    
    if len(collector.spectrogram_buffer) == collector.max_sensor_num:
        collector.spectrogram_buffer = [[sensor_number, spectrogram]]
        collector.filename_buffer= [[sensor_number,file_name]]
    else:
        collector.spectrogram_buffer.append([sensor_number, spectrogram])
        collector.filename_buffer.append([sensor_number,file_name])

        
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


@app.route("/mel-spectrogram", methods=["GET"])
def mel_spectrogram():
    # 예제: 실제로는 collector에서 데이터를 가져와야 합니다.
    if len(collector.spectrogram_buffer) < 2:
        return "Not enough data", 400

    spectrogram1, spectrogram2 = collector.spectrogram_buffer[:2]

    response = {
        'spectrograms': [
            {'sensor_number': spectrogram1[0], 'image': spectrogram1},
            {'sensor_number': spectrogram2[0], 'image': spectrogram2}
        ]
    }

    return jsonify(response)

# 메인 함수
if __name__ == "__main__":

    # socketio.run(app,host='0.0.0.0', port = 80)
    socketio.run(app, port=5000)
