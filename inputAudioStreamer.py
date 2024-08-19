import pyaudio
import threading
import wave
from event import Event
import queue

DEFAULT_FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
DEFAULT_CHANNELS = 1              # Number of audio channels
DEFAULT_DEVICE_INDEX = 0          # Device to record from
DEFAULT_RATE = 44100              # Sampling rate (Hz)
DEFAULT_CHUNK = 1024              # Number of frames per buffer
DEFAULT_WAVE_OUTPUT_FILENAME = "recorded.wav"  # Output file name

class InputAudioStreamer: 
    def __init__(self):
        # Audio settings
        self._p = pyaudio.PyAudio()
        self._stream = None
        self._format = DEFAULT_FORMAT
        self._channels = DEFAULT_CHANNELS
        self._rate = DEFAULT_RATE
        self._chunk = DEFAULT_CHUNK
        
        # Threading
        self.is_open = False
        self._thread = None
        
        # Frames
        self._frames = []
        self._frame_lock = threading.Lock()
        self.on_frame_event = Event()
        
        # Recording
        self._recording = False
        self._recording_lock = threading.Lock()


    def open(self, format=DEFAULT_FORMAT, channels=DEFAULT_CHANNELS, rate=DEFAULT_RATE, chunk=DEFAULT_CHUNK, device_index=DEFAULT_DEVICE_INDEX):
        self._format = format
        self._channels = channels
        self._rate = rate
        self._chunk = chunk

        try:
            self._stream = self._p.open(format=format,
                                channels=channels,
                                rate=int(rate),
                                input=True,
                                frames_per_buffer=chunk,
                                input_device_index=device_index)        
            self._frames = []
            self.is_open = True
            self._thread = threading.Thread(target=self.stream_loop)
            self._thread.start()
        except Exception as e:
            self.is_open = False
            print(f"Error in recording thread: {e}")
    
    def stream_loop(self):
        try:
            while self.is_open: 
                try:
                    data = self._stream.read(self._chunk, exception_on_overflow=False)
                    with self._frame_lock:
                        with self._recording_lock:
                            if self._recording:
                                self._frames.append(data)
                        if self.on_frame_event:
                            self.on_frame_event(data)
                except IOError as e:
                    print(f"IOError in recording thread: {e}")
                except Exception as e:
                    print(f"Error in recording thread: {e}")
        except Exception as e:
            print(f"Error in recording loop: {e}")

    def close(self):
        self.is_open = False

        if self._thread and self._thread.is_alive():
            self._thread.join()
        
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()

    def set_recording(self, state: bool):
        with self._recording_lock:
            self._recording = state

    def get_frames(self):
        with self._frame_lock:
            return self._frames.copy()
        
    def clear_frames(self):
        with self._frame_lock:
            return self._frames.clear()

    def save_to_wav(self, file_name=DEFAULT_WAVE_OUTPUT_FILENAME):
        with wave.open(file_name, 'wb') as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(self._p.get_sample_size(self._format))
            wf.setframerate(self._rate)
            with self._frame_lock:
                wf.writeframes(b''.join(self._frames))

    def get_devices(self):
        input_devices = []
        for i in range(self._p.get_device_count()):
            device_info = self._p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info)
        
        return input_devices

if __name__ == "__main__":
    import time
    recorder = InputAudioStreamer()
    recorder.open()
    time.sleep(3)
    recorder.close()
    recorder.save_to_wav()
    # print(recorder.get_devices())