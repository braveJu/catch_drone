from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import uuid
import os
from pydub import AudioSegment
import numpy as np
from audio import wav_to_mel_spectrogram2, wav_to_mfcc, color_mel_spectrogram
from utils import DataCollector
from PIL import Image

# 오디오 파일이 저장되는 디렉터리 설정
AUDIO_BASE_DIR = os.path.join(os.getcwd(), "audio")
TEMP_BASE_DIR = os.path.join(os.getcwd(), "temp")
IMAGE_BASE_DIR = os.path.join(os.getcwd(), "images")

# 데이터 수집을 위한 객체 초기화
collector = DataCollector()

app = Flask(__name__)
socketio = SocketIO(app)

# SQLAlchemy 설정 - MySQL 데이터베이스 연결
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:rootpass@localhost:3306/uav"
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:1234@localhost:3306/uav"
app.config["SECRET_KEY"] = str(uuid.uuid4())
db = SQLAlchemy(app)


# Sensor 모델 정의
class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_number = db.Column(db.Integer, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<Sensor {self.sensor_number}>"

    def set_password(self, password):
        self.password_hash = password

    def check_password(self, password):
        return self.password_hash == password


# 데이터베이스 초기화
with app.app_context():
    db.create_all()


def send_activated_sensors():
    """활성화된 센서 목록을 클라이언트에게 전송"""
    emit("activated_sensors", collector.get_activated_sensor_list(), broadcast=True)


@socketio.on("temp")
def handle_temp(data):
    """임시 데이터를 처리하는 소켓 핸들러"""
    print(data["sensor_num"], "in!")
    collector.activated_sensor.add(data["sensor_num"])


@socketio.on("audio")
def handle_audio(data):
    """오디오 데이터를 처리하는 소켓 핸들러"""
    sensor_num = data["sensor_number"]
    is_connected = data["is_connected"]

    if is_connected:
        collector.activated_sensor.add(sensor_num)
    else:
        collector.activated_sensor.discard(sensor_num)
    emit("ready", len(collector.activated_sensor), broadcast=True)


@app.route("/")
def index():
    """홈페이지 라우트"""
    return render_template("index.html")


@app.route("/monitor")
def monitor():
    """모니터 페이지 라우트"""
    return render_template("monitor.html")


@app.route("/upload/audio", methods=["POST"])
def upload_audio():
    """오디오 업로드를 처리하는 라우트"""
    current_time = datetime.now()
    sensor_number = request.form.get("sensor_number")
    file_name = request.form.get("file_name")

    webm_dir = os.path.join(TEMP_BASE_DIR, sensor_number)
    file_dir = os.path.join(AUDIO_BASE_DIR, sensor_number)
    image_dir = os.path.join(IMAGE_BASE_DIR, sensor_number)

    collector.sensor_buffer.append(sensor_number)

    os.makedirs(file_dir, exist_ok=True)
    os.makedirs(webm_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    webm_file = os.path.join(webm_dir, f"{file_name}.webm")
    if len(collector.filename_buffer) == 1:
        file_name = collector.filename_buffer[0][1]

    audio_file = os.path.join(file_dir, f"{file_name}.wav")
    image_file = os.path.join(image_dir, f"{file_name}.png")

    audio = request.files["audio_file"]
    audio.save(webm_file)

    # 오디오 파일 변환 및 저장
    audio_segment = AudioSegment.from_file(webm_file, format="webm")
    audio_segment.export(audio_file, format="wav")
    os.remove(webm_file)

    # mel-spectrogram 생성
    spectrogram = wav_to_mel_spectrogram2(audio_file)

    # color mel_spectrogram 얻기
    # color_mel_spectrogram(spectrogram, image_file)

    spectrogram = spectrogram.tolist()

    if len(collector.spectrogram_buffer) == collector.max_sensor_num:
        collector.pair_list.append(
            f"{collector.filename_buffer[0]}&{collector.filename_buffer[1]}\n"
        )
        collector.pair_cnt += 1

        if collector.pair_cnt % 5 == 0:
            collector.write_pair_info()
            collector.pair_list = []

        collector.spectrogram_buffer = [[sensor_number, spectrogram]]
        collector.filename_buffer = [[sensor_number, file_name]]
        collector.image_path_buffer = [[sensor_number, image_file]]
    else:
        print(collector.filename_buffer)
        collector.spectrogram_buffer.append([sensor_number, spectrogram])
        collector.filename_buffer.append([sensor_number, file_name])
        collector.image_path_buffer.append([sensor_number, image_file])

    return "Audio uploaded successfully"


@app.route("/login", methods=["GET", "POST"])
def login():
    """로그인 라우트"""
    if request.method == "POST":
        sensor_number = request.form["sensor_number"]
        password = request.form["password_hash"]

        sensor = Sensor.query.filter_by(
            sensor_number=sensor_number, password_hash=password
        ).first()

        if sensor:
            session["id"] = sensor.id
            session["sensor_number"] = sensor.sensor_number
            return redirect(url_for("client"))
        else:
            return render_template(
                "login.html", message="Invalid username or password. Please try again."
            )

    return render_template("login.html")


@app.route("/client")
def client():
    """클라이언트 페이지 라우트"""
    sensor_number = session.get("sensor_number")
    if not sensor_number:
        return redirect(url_for("login"))
    return render_template("client.html", sensor_number=sensor_number)


@app.route("/mel-spectrogram", methods=["GET"])
def mel_spectrogram():
    """멜 스펙트로그램 데이터를 반환하는 라우트"""
    if len(collector.spectrogram_buffer) < 2:
        return "Not enough data", 400

    spectrogram1, spectrogram2 = collector.spectrogram_buffer
    file_name1, file_name2 = collector.filename_buffer
    # image_path1, image_path2 = collector.image_path_buffer

    # image1 = np.array(Image.open(image_path1))
    # image2 = np.array(Image.open(image_path2))

    # 두 스펙토그램의 입력 센서가 같으면 오류발생!
    if spectrogram1[0] == spectrogram2[0] == 0:
        return "Sync Error", 400

    response = {
        "spectrograms": [
            {
                "sensor_number": spectrogram1[0],
                "file_name": file_name1,
                "image": spectrogram1,
            },
            {
                "sensor_number": spectrogram2[0],
                "file_name": file_name2,
                "image": spectrogram2,
            },
        ]
    }
    return jsonify(response)


# 현재 처리하고있는 파일의 이름을 알려주기 위해서
@app.route("/current_filename", methods=["GET"])
def current_filename():
    file_name1, file_name2 = collector.filename_buffer

    response = {
        "filename1": file_name1,
        "filename2": file_name2,
    }
    return jsonify(response)


if __name__ == "__main__":
    # socketio.run(app, port=80, host="0.0.0.0")
    socketio.run(app)
