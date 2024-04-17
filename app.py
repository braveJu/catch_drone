from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

import os
from datetime import datetime
from time import time
import uuid
from collections import defaultdict, deque

from utils import save_file
# from OpenSSL import SSL
# from audio import blobs_to_feature_map


BASE_DIR = "./audio"
sensor_set = set()

#센서들의 현재까지 받아온 데이터를 저장하는 딕셔너리, dafaultdict를 사용하여 기본적으로 리스트 생성
sensor_data = defaultdict(deque)


app = Flask(__name__)
socketio = SocketIO(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:1234@localhost:3306/uav"
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

@socketio.on('audio')
def handle_audio(data): 
    # 변수에 데이터 저장
    recieved_data = data['data'] # Blob
    sensor_num = data['sensor_number']
    is_connected = data['is_connected']
    
    sensor_set.add(sensor_num)
     
    if is_connected == False:
        sensor_set.discard(sensor_num)
        sensor_data[sensor_num] = deque()
    
    if len(sensor_data[sensor_num]) < 1000:
        sensor_data[sensor_num].append(recieved_data)
    else:
        # save_file(f"{sensor_num}",sensor_data[sensor_num])
        sensor_data[sensor_num].popleft()
        sensor_data[sensor_num].append(recieved_data)
        
    feature_map = None
    # feature_map = blobs_to_feature_map(sensor_data[sensor_num])
    
    print(f'Received data from sensor {sensor_num}: {sensor_set}, {is_connected}')
    
    # 클라이언트로부터 받아오 데이터를 monitor로 전송하기 위한 코드
    emit('get_sensor_data', {'sensor_id': sensor_num, 'sensor_value': recieved_data, 'feature_map':feature_map}, broadcast=True)
    
    

# 홈페이지 라우트
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/monitor")
def monitor():
    return render_template('monitor.html')


# 오디오 업로드 라우트, 저장하는 부분
@app.route("/upload/audio", methods=["POST"])
def upload_audio():
    file_name = str(int(time()))
    file_dir = os.path.join(BASE_DIR, str(session["sensor_number"]))

    # 센서 번호에 해당하는 디렉토리가 없으면 생성
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # 오디오 파일 업로드
    if "audio_file" not in request.files:
        return "No file part"

    audio = request.files["audio_file"]
    audio.save(file_dir + f"/{file_name}_audio.wav")

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

# 메인 함수
if __name__ == "__main__":
    # from waitress import serve
    # serve(app, host='0.0.0.0', port=80)
    socketio.run(app,host='0.0.0.0', port = 80)
    # app.run(host='0.0.0.0', port = 80, ssl_context = context)


#waitress-serve --key=./catch_drone/key.pem --cert=./catch_drone/cert.pem app:app
