import threading
import numpy as np
import asyncio
import websockets
from wakeWordRecorder import WakeWordRecorder        
import argparse

def chunkFrames(frames: list, chunkSize: int):
    all_chunks = []
    chunks = []
    for i, frame in enumerate(frames):
        if i % chunkSize == 0:
            all_chunks.append(chunks.copy())
            chunks.clear()
        
        chunks.append(frame)
    
    return all_chunks

async def connect(wwr: WakeWordRecorder, uri, record_time = 5):
    wwr.open_mic()

    async for websocket in websockets.connect(uri):
        wwr.start_listening()
        
        if wwr.word_detected.wait():
            wwr.stop_listening()
            wwr.start_recording()
            wwr.recording_ended.clear()
            
            threading.Timer(record_time, wwr.end_recording).start()
            print("Recording started")

            if wwr.recording_ended.wait():
                print("Recording ended")
                wwr.word_detected.clear()

                await websocket.send("start")

                frames = wwr.audio_streamer.get_frames()

                for frame in frames:
                    await websocket.send(frame)

                await websocket.send('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hot word triggered microphone recorder for Wuz')
    parser.add_argument("-t", "--time", type=float, help="The length of time after the hot word is detected that the system records from the microphone", default=10)
    parser.add_argument("-d", "--device", type=str, help="The input device to listen and record from", default=None)
    parser.add_argument("-u", "--uri", type=str, help="The uri to connect the websocket into", default="ws://localhost:3001")
    args = parser.parse_args()
    wwr = WakeWordRecorder(device_name=args.device)
    asyncio.run(connect(wwr=wwr, uri=args.uri, record_time=args.time))