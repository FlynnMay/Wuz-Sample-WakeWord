import threading

class Event:
    def __init__(self):
        self._subscribers = []
        self._lock = threading.Lock()

    def __iadd__(self, handler):
        with self._lock:
            # if not (handler in self._subscribers):
                self._subscribers.append(handler)
        return self
    
    def __isub__(self, handler):
        with self._lock:
            # if handler in self._subscribers:
                self._subscribers.remove(handler)
        return self
    
    def __call__(self, *args, **kwds):
        with self._lock:
            for subscriber in self._subscribers:
                subscriber(*args, **kwds)

if __name__ == "__main__":
    def debug_print():
        print("debug")

    event = Event()

    event += debug_print

    event()

    print(len(event._subscribers))

    event -= debug_print

    event()

    print(len(event._subscribers))

    event += debug_print

    event()

    print(len(event._subscribers))


    