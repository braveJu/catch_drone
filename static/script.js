document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const sensorNumberElement = document.getElementById("sen_num");
    const sensorNumber = sensorNumberElement.textContent;
    const maxCNT = 2;
    const MAX_SEN = 2;
    const STARTVAL = 10;
    const number_x = 25;
    const socket = io();
    let mediaRecorder;
    let audioChunks = [];
    let tempChunk = [];
    let isReady = false;
    let flag = true;
    let header_list = [];
    let header = null;
    let cnt = 0;
    let current_date = null;

    const options = { mimeType: 'audio/webm' };

    function getCurrentFormattedTime() {
        const now = new Date();
        const year = String(now.getFullYear());
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');

        return `${year}:${month}:${day}_${hours}:${minutes}:${seconds}`;
    }

    function handleStartRecording() {


        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream, options);
                mediaRecorder.start(STARTVAL);

                mediaRecorder.ondataavailable = event => handleDataAvailable(event);
                mediaRecorder.onstop = handleStopRecording;
                socket.emit('temp', { 'sensor_num': sensorNumber });
                startButton.disabled = true;
                stopButton.disabled = false;
            })
            .catch(error => console.error('Error accessing microphone:', error));
    }

    function handleStopRecording() {
        mediaRecorder.stop();
        sendAudioDataToServer(new Blob(audioChunks), sensorNumber, getCurrentFormattedTime());
        resetRecordingState();
    }

    function handleDataAvailable(event) {

        if (cnt < maxCNT) {
            header_list.push(event.data);
        }
        if (cnt == maxCNT) {
            header = header_list;
        }

        socket.emit('audio', { sensor_number: sensorNumber, is_connected: true });
        socket.on('ready', data => { isReady = data == MAX_SEN; });
        if (isReady && header != null) {
            audioChunks.push(event.data);
            tempChunk.push(event.data);

            if (tempChunk.length >= number_x) {
                sendChunkToServer();
                tempChunk = [];
                setTimeout(100);
            }
        }
        cnt += 1;
    }

    function extractWebMHeader(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function () {
                const buffer = reader.result;
                const dataView = new DataView(buffer);

                // Extract WebM header info
                const headerInfo = new Uint8Array(buffer); // Adjust the slice to read more if needed
                console.log(headerInfo);
                // Resolve the promise with the header info
                resolve(headerInfo);
            };

            reader.onerror = function () {
                // Reject the promise if there is an error reading the blob
                reject(new Error("Failed to read blob"));
            };

            reader.readAsArrayBuffer(blob);
        });
    }

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
            .then(response => console.log(response.text))
            .then(data => console.log(data))
            .catch(error => console.error('Error:', error));
    }

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

    function resetRecordingState() {
        socket.emit('audio', { sensor_number: sensorNumber, is_connected: false });
        audioChunks = [];
        startButton.disabled = false;
        stopButton.disabled = true;
    }

    startButton.addEventListener('click', handleStartRecording);
    stopButton.addEventListener('click', handleStopRecording);
});
