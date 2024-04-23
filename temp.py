import requests
import time

while True:
    data = requests.get('https://dronecatcher.info/mfcc')
    print(data.content)
    time.sleep(1)