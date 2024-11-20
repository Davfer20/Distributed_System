import threading


class ReadWriteLock:
    # A lock that allows multiple readers or a single writer
    def __init__(self):
        self.readers = 0  # Number of active readers
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

    def acquire_read(self):
        # Acquire the read lock
        with self.read_lock:
            self.readers += 1
            if (
                self.readers == 1
            ):  # First reader, then acquire the write lock to block writers
                self.write_lock.acquire()

    def release_read(self):
        # Release the read lock
        with self.read_lock:
            self.readers -= 1
            if self.readers == 0:  # Last reader, then release the write lock
                self.write_lock.release()

    def acquire_write(self):
        # Acquire the write lock
        self.write_lock.acquire()

    def release_write(self):
        # Release the write lock
        self.write_lock.release()
