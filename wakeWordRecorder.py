from inputAudioStreamer import InputAudioStreamer
from wakeWordHandler import WakeWordHandler
import threading

class WakeWordRecorder:
    def __init__(self, on_recording_ended = None, device_name = None): 
        self.audio_streamer = InputAudioStreamer()
        self.on_recording_ended = on_recording_ended
        self.recording_ended = threading.Event()
        self.word_detected = threading.Event()

        devices = self.audio_streamer.get_devices()

        self.device = None
        if device_name == None:
            self.print_device_table(devices)
            self.device = self.prompt_user_for_device_selction(devices)
        else:
            for d in devices:
                if d["name"] == device_name:            
                    self.device = d

        self.wakeWordHandler = WakeWordHandler(
            event=self.audio_streamer.on_frame_event,
            sample_rate=self.device["defaultSampleRate"],
            trigger_threshold=0.05, 
            on_word_used=self.on_word_used
            )
        
    def prompt_user_for_device_selction(self, devices):
        while True:
            try:
                index = int(input(f"Select Input Device (0-{len(devices)-1}): "))
                if 0 <= index < len(devices):
                    return devices[index]
                else:
                    print(f"Please enter a number between 0 and {len(devices)-1}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def print_device_table(self, devices):
        print("================================")
        print(f"Device List")
        print("================================")
        for i, d in enumerate(devices):
            print(f"({i}) {d['name']}")
        print("================================")

    def open_mic(self):
        self.audio_streamer.open(channels=self.device["maxInputChannels"], rate=self.device['defaultSampleRate'], chunk=1280, device_index=self.device["index"])
        print("Microphone is open!")
    
    def start_listening(self):
        self.wakeWordHandler.start_listening()

    def stop_listening(self):
        self.wakeWordHandler.purge()
        self.wakeWordHandler.stop_listening()

    def close_mic(self):
        self.stop_listening()
        self.audio_streamer.close()
        print("Microphone is no longer open!")

    def on_word_used(self):
        self.word_detected.set()
        print('Wuz detected')

    def start_recording(self):
        if self.audio_streamer.is_open:
            print('Recording started')
            self.audio_streamer.set_recording(True)
    
    def end_recording(self):
        if self.audio_streamer.is_open:
            print('Recording ended')
            self.audio_streamer.set_recording(False)
            frames = self.audio_streamer.get_frames()
            
            self.recording_ended.set()

            if self.on_recording_ended != None:
                self.on_recording_ended(frames)

if __name__ == "__main__":
    wwr = WakeWordRecorder(device_name="Logitech USB Microphone: Audio (hw:3,0)")
    wwr.open_mic()
    while True:
        wwr.start_listening()
        if wwr.word_detected.wait():
            wwr.stop_listening()
            wwr.start_recording()
            wwr.recording_ended.clear()
            threading.Timer(2, wwr.end_recording).start()

            if wwr.recording_ended.wait():
                wwr.word_detected.clear()