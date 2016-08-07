import threading
from threading import Lock
from time import clock


slot_available = lambda thread: thread == None or thread.is_alive() == False


class ThreadPool:
    cur_count = 0

    def __init__(self, max_threads: int=1, show_time=False):
        self.MAX_THREADS = max_threads
        self.show_time = show_time

        self.thread._pool = self
        self.thread_end._pool = self
        self.lock = self.in_lock._lock = Lock()

        self.pool = [None] * self.MAX_THREADS
        self.event = threading.Event()

    def is_available_slots(self):
        return any(slot_available(thread) for thread in self.pool)

    def dispatch(self, thread):
        if not self.is_available_slots():
            # Если нет свободных слотов
            # ждем пока не завершится один из потоков
            self.event.wait()
            self.event.clear()

        # Выбираем первый свободный слот и диспетчеризуем поток
        for slot_id in range(self.MAX_THREADS):
            if slot_available(self.pool[slot_id]):
                self.cur_count += 1
                self.pool[slot_id] = thread
                thread.start()
                break

    def is_alive(self):
        return bool(self.cur_count)

    def set(self):
        self.cur_count -= 1
        self.event.set()

    def loop(self):
        while self.is_alive():
            pass
        return

    @staticmethod
    def in_lock(fun):

        def wrapper(*args, **kwargs):
            if  hasattr(ThreadPool.in_lock, '_lock'):
                lock = ThreadPool.in_lock._lock
            else:
                lock = Lock()

            lock.acquire()
            try:
                return fun(*args, **kwargs)
            except Exception as e:
                print("При выполнении {!r} возникло исключение с сообщением {!r}".format(fun.__name__, e))
            finally:
                lock.release()

        return wrapper

    @staticmethod
    def thread(func):
        """
        Декоратор для запуска метода в потоке
        """
        def wrapper(*args, **kwargs):
            self = ThreadPool.thread._pool

            t = threading.Thread(
                target=ThreadPool.thread_end(func), args=args, kwargs=kwargs)

            self.dispatch(t)

        return wrapper

    @staticmethod
    def thread_end(func):

        def wrapper(*args, **kwargs):
            self = ThreadPool.thread_end._pool

            start_time = clock()

            try:
                func(*args, **kwargs)
            except Exception as e:
                print("При выполнении {!r} возникло исключение с сообщением {!r}".format(func.__name__, e))

            end_time = clock() - start_time
            if self.show_time:
                print("Time: {}".format(end_time))

            self.set()

        return wrapper
