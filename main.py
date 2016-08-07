#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import listdir, mkdir, path
from urllib import request
from progressbar import ProgressBar

from threadpool import ThreadPool

th_pool = ThreadPool(max_threads=3)


class TaskManager:
    tasks_dir = 'tasks'
    download_file = None
    files = [] # list()

    def get_all_tasks(self):
        self.files = listdir(self.tasks_dir)

    def __iter__(self):
        return self.get_url()

    def get_url(self):
        for i, file in enumerate(self.files, 1):
            print('\nОбрабатываем файл {} из {}'.format(i, len(self.files)))
            with open('{}/{}'.format(self.tasks_dir, file), 'r') as f:
                links = f.read().split('\n')

            for j, link in enumerate(links, 1):
                print('\nОбрабатываем урл {} из {}'.format(i, len(links)))
                filename, url = link.split('|')
                try:
                    mkdir(file)
                except IOError:
                    pass
                self.download_file = '{}/{}'.format(file, filename)
                yield url


class Downloader:
    file_path = ''
    file_total_size = 0
    file_size = 0

    @th_pool.thread
    def download(self, file_path: str, url: str):
        self.file_path = file_path

        messages = {False: '\nЗагрузка файла {} завершена', True: '\nПри загрузке файла {} возникло исключение с сообщением: {}'}
        error = None

        print('\nЗагрузка файла {} начата'.format(self.file_path))
        try:
            request.urlretrieve(url=url, filename=self.file_path)
        except Exception as e:
            error = e
        finally:
            print(messages[bool(error)].format(self.file_path, error))
            return


class ProgressManager(ProgressBar):
    downloads = {}
    enabled = False

    def re_init(self):
        super().__init__(max_value=self.max_size, min_value=0)

    max_size = 0
    cur_size = 0

    def get_url_size(self, url):
        try:
            file = request.urlopen(url)
            return file.length
        except Exception:
            return 0

    def get_file_size(self, filename):
        try:
            if path.exists(filename):
                return path.getsize(filename)
        except Exception:
            return 0

    @th_pool.thread
    def view_progress(self):
        while self.enabled:
            try:
                max_size = 0
                cur_size = 0
                for thread in th_pool.pool:
                    try:
                        file_path = thread._kwargs['file_path']
                        url = thread._kwargs['url']
                    except Exception as e:
                        continue
                    max_size += self.get_url_size(url)
                    cur_size += self.get_file_size(file_path)

                if max_size != self.max_value:
                    self.re_init()
                if cur_size != self.cur_size:
                    self.update(self.cur_size)

                self.cur_size, self.max_size = cur_size, max_size

            except Exception as e:
                continue
        return


tm = TaskManager()
dm = Downloader()
pb = ProgressManager()

tm.get_all_tasks()
pb.enabled = True
pb.view_progress()

for url in tm:
    dm.download(file_path=tm.download_file, url=url)

while True:
    if th_pool.cur_count == 1:
        break

pb.enabled = False