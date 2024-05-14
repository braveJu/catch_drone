

// AudioBuffer를 WAV 형식으로 인코딩하는 함수
function encodeWAV(audioBuffer) {
    var buffer = new ArrayBuffer(44 + audioBuffer.length * 2);
    var view = new DataView(buffer);

    // WAV 헤더 생성
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + audioBuffer.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM 포맷
    view.setUint16(22, 1, true); // 채널 수
    view.setUint32(24, audioBuffer.sampleRate, true);
    view.setUint32(28, audioBuffer.sampleRate * 2, true); // 샘플링 속도
    view.setUint16(32, 2, true); // 블록 크기
    view.setUint16(34, 16, true); // 비트 수
    writeString(view, 36, 'data');
    view.setUint32(40, audioBuffer.length * 2, true);

    // PCM 데이터 작성
    var index = 44;
    var channelData = audioBuffer.getChannelData(0);
    for (var i = 0; i < channelData.length; i++) {
        view.setInt16(index, channelData[i] * 0x7FFF, true);
        index += 2;
    }

    return view;
}

// DataView에 문자열을 쓰는 헬퍼 함수
function writeString(view, offset, string) {
    for (var i = 0; i < string.length; i++) {
        view.setUint16(offset + i, string.charCodeAt(i));
    }
}

function convertWebMToWAV(webmBlob) {
    let fileReader = new FileReader();
    let audioContext; // 루프 외부에서 audioContext 변수 선언
    return new Promise((resolve, reject) => {
        fileReader.onload = function () {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log("Before webmBlob", webmBlob);
            audioContext.decodeAudioData(this.result, function (decodedData) {
                let wavBuffer = audioContext.createBuffer(1, decodedData.length, audioContext.sampleRate);
                wavBuffer.copyToChannel(decodedData.getChannelData(0), 0);
                
                let wavBlob = new Blob([encodeWAV(wavBuffer)], { type: 'audio/wav' });
                console.log("WAVE : ", wavBlob)
                // 오디오 컨텍스트 닫기
                audioContext.close();
                resolve(wavBlob);
            });
        };

        fileReader.onerror = function () {
            reject(new Error("Failed to read the WebM file."));
        };

        fileReader.readAsArrayBuffer(webmBlob);
    });
}