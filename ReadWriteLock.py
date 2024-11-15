import threading


class ReadWriteLock:
    def __init__(self):
        self.readers = 0  # Number of active readers
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

    def acquire_read(self):
        with self.read_lock:
            self.readers += 1
            if self.readers == 1:
                self.write_lock.acquire()

    def release_read(self):
        with self.read_lock:
            self.readers -= 1
            if self.readers == 0:
                self.write_lock.release()

    def acquire_write(self):
        self.write_lock.acquire()

    def release_write(self):
        self.write_lock.release()
