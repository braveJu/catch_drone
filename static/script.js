document.addEventListener("DOMContentLoaded", () => {
    // HTML 요소와 변수 초기화
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const sensorNumberElement = document.getElementById("sen_num");
    const sensorNumber = sensorNumberElement.textContent;
    const maxCNT = 2; 
    const MAX_SEN = 2; 
    const STARTVAL = 5; 
    const number_x = 20; 
    const socket = io(); 
    let mediaRecorder; 
    let audioChunks = []; 
    let tempChunk = []; 
    let isReady = false; 
    let header_list = []; 
    let header = null; 
    let cnt = 0; 

    const options = { mimeType: 'audio/webm' }; 

    // 현재 시간을 포맷팅하여 반환하는 함수
    function getCurrentFormattedTime() {
        const now = new Date();
        const year = String(now.getFullYear());
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `${year}-${month}-${day}!${hours}-${minutes}-${seconds}`;
    }

    // 녹음을 시작하는 함수
    function handleStartRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream, options);
                mediaRecorder.start(STARTVAL);

                mediaRecorder.ondataavailable = handleDataAvailable;
                mediaRecorder.onstop = handleStopRecording;
                socket.emit('temp', { 'sensor_num': sensorNumber });
                startButton.disabled = true;
                stopButton.disabled = false;
            })
            .catch(error => console.error('Error accessing microphone:', error));
    }

    // 녹음을 중지하는 함수
    function handleStopRecording() {
        mediaRecorder.stop();
        sendAudioDataToServer(new Blob(audioChunks), sensorNumber, getCurrentFormattedTime());
        resetRecordingState();
    }

    // 오디오 데이터가 준비되었을 때 호출되는 함수
    function handleDataAvailable(event) {
        if (cnt < maxCNT) {
            header_list.push(event.data);
        }
        if (cnt === maxCNT) {
            header = header_list;
        }

        socket.emit('audio', { sensor_number: sensorNumber, is_connected: true });
        socket.on('ready', data => { isReady = data === MAX_SEN; });

        if (isReady && header !== null) {
            audioChunks.push(event.data);
            tempChunk.push(event.data);

            if (tempChunk.length >= number_x) {
                sendChunkToServer();
                tempChunk = [];
            }
        }
        cnt += 1;
    }

    // 오디오 청크를 서버로 전송하는 함수
    function sendChunkToServer() {
        tempChunk = tempChunk.slice(-number_x);
        const combinedChunks = header.concat(tempChunk);
        const blob = new Blob(combinedChunks, { type: 'audio/webm' });

        const formData = new FormData();
        formData.append('audio_file', blob);
        formData.append('sensor_number', sensorNumber);
        formData.append('file_name', getCurrentFormattedTime());

        fetch('/upload/audio', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => console.log(data))
            .catch(error => console.error('Error:', error));
    }

    // 전체 오디오 데이터를 서버로 전송하는 함수
    function sendAudioDataToServer(blob, sensorNumber, fileName) {
        const formData = new FormData();
        formData.append('audio_file', blob);
        formData.append('sensor_number', sensorNumber);
        formData.append('file_name', fileName);

        fetch('/upload/audio', {
            method: 'POST',
            body: formData
        })
            .then(response => response.text())
            .then(data => console.log(data))
            .catch(error => console.error('Error:', error));
    }

    // 녹음 상태를 초기화하는 함수
    function resetRecordingState() {
        socket.emit('audio', { sensor_number: sensorNumber, is_connected: false });
        audioChunks = [];
        startButton.disabled = false;
        stopButton.disabled = true;
    }

    // 이벤트 리스너 설정
    startButton.addEventListener('click', handleStartRecording);
    stopButton.addEventListener('click', handleStopRecording);
});
