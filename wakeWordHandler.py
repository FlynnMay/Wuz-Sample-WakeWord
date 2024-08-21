import numpy as np
import time
from openwakeword.model import Model
from scipy.signal import resample
from event import Event
import threading

# Consider removing debounce and call back for a threading event instead.
class WakeWordHandler():
    
    def __init__(self, event: Event, sample_rate: int, trigger_threshold = 0.4, on_word_used = None, debounce_time = 1.0):
        self.on_word_used = on_word_used
        self.event = event
        self.model = Model(
            wakeword_model_paths=["models/whuz.onnx"]
        )
        self.n_models = len(self.model.models.keys())
        self.trigger_threshold = trigger_threshold
        self.sample_rate = sample_rate
        self.stop_event = threading.Event()
        self.last_trigger_time = 0
        self.debounce_time = debounce_time
    
    def start_listening(self):
        self.event += self.listen_for_wake_word

    def stop_listening(self):
        self.event -= self.listen_for_wake_word

    def resample_audio(self, audio_data, original_rate, target_rate=16000):
        number_of_samples = round(len(audio_data) * float(target_rate) / original_rate)
        resampled_audio = resample(audio_data, number_of_samples)
        return resampled_audio.astype(np.int16)
    
    def listen_for_wake_word(self, frame_data):
        current_time = time.time()

        # Skip if enough time hasn't passed
        if (current_time - self.last_trigger_time) < self.debounce_time:
            return
            
        # Convert frame to numpy array
        frame = np.frombuffer(frame_data, dtype=np.int16)

        # Resample the frame to 16kHz
        resampled_frame = self.resample_audio(audio_data=frame, original_rate=self.sample_rate, target_rate=16000)

        prediction = self.model.predict(resampled_frame)

        accuracy = prediction['whuz'] 
        print(accuracy)
        if accuracy >= self.trigger_threshold:
            # update trigger time to not double call the on_word_used callback.
            self.last_trigger_time = current_time
            threading.Timer(0, self.on_word_used).start()

    def purge_buffer(self):
        self.model.reset()