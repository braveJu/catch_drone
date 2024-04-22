import audioread

# 사용 가능한 백엔드 목록 확인
print(audioread.available_backends())

# 사용할 백엔드 선택
# 여기서는 ffmpeg을 백엔드로 사용하는 예시입니다.
audioread.ffdec.FFmpegAudioFile.available = True
audioread.ffdec.FFmpegAudioFile.load = lambda *args, **kwargs: audioread.ffdec.FFmpegAudioFile(*args, **kwargs)

# 만약 ffmpeg 백엔드가 사용 가능하다면 선택
if "ffmpeg" in audioread.available_backends():
    audioread.ffdec.FFmpegAudioFile.default = True