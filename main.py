#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys
from os import listdir, mkdir, path
from time import sleep
from urllib import request
from progressbar import ProgressBar

from threadpool import ThreadPool

th_pool = ThreadPool(max_threads=sys.argv[1] if len(sys.argv) > 1 else 2)


class TaskManager:
    tasks_dir = 'tasks'
    files = []

    def get_all_tasks(self):
        self.files = listdir(self.tasks_dir)

    def __iter__(self):
        return self.get_url()

    @staticmethod
    def get_name(line):
        query_string = request.unquote(line).split('?')[1].split('&')
        query_parameters = {key.split('=')[0]: key.split('=')[1] for key in query_string}
        try:
            ext = query_parameters['mime'].split('/').pop()
            name = re.sub(r'\s+', '_', query_parameters['title'])
        except KeyError:
            return line.split('?')[0].split('/').pop()
        else:
            return '{}.{}'.format(name, ext)

    def get_url(self):
        for i, file in enumerate(self.files, 1):
            print('\nОбрабатываем файл {} из {}'.format(i, len(self.files)))
            with open('{}/{}'.format(self.tasks_dir, file), 'r') as f:
                links = f.read().split('\n')
            download_dir = re.sub(r'\s+', '_', file)
            for j, link in enumerate(links, 1):
                print('\nОбрабатываем урл {} из {}'.format(j, len(links)))

                if link:
                    filename = self.get_name(link)
                else:
                    continue

                url = link

                try:
                    mkdir(download_dir)
                except IOError:
                    pass
                file_path = '{}/{}'.format(download_dir, filename)
                yield url, file_path


class Downloader:
    file_size = 0
    _error_cache = 'error_cache'

    def up(self, size):
        self.file_size += size

    def down(self, size):
        self.file_size -= size

    @staticmethod
    def get_url_size(self, url):
        try:
            file = request.urlopen(url)
            return file.length
        except Exception as e:
            print(e)
            return 0

    @th_pool.thread
    def download(self, file_path: str, url: str):
        th_pool.lock.acquire()
        file_size = self.get_url_size(url=url)
        self.up(file_size)
        th_pool.lock.release()

        messages = {False: '\nЗагрузка файла {} завершена', True: '\nПри загрузке файла {} возникло исключение с сообщением: {}'}
        error = None

        print('\nЗагрузка файла {} начата'.format(file_path))
        try:
            if file_size == 0:
                raise Exception('Не удалось получить размер файла!')
            request.urlretrieve(url=url, filename=file_path)
        except Exception as e:
            error = e
            with open(self._error_cache, 'a') as f:
                f.write('{}\n'.format(url))
        finally:
            print(messages[bool(error)].format(file_path, error))
            th_pool.lock.acquire()
            self.down(file_size)
            th_pool.lock.release()
            return


class ProgressManager(ProgressBar):
    downloads = {}
    enabled = False

    def re_init(self, max_size):
        super().__init__(max_value=max_size, min_value=0)

    cur_size = 0

    @staticmethod
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
                max_size = downloader.file_size
                cur_size = 0
                for thread in th_pool.pool:
                    try:
                        file_path = thread._kwargs['file_path']
                    except Exception:
                        continue
                    cur_size += self.get_file_size(file_path)

                if max_size != self.max_value:
                    self.re_init(max_size)
                if cur_size != self.cur_size:
                    self.update(cur_size)

                self.cur_size = cur_size
            except Exception:
                continue
        return


tasks = TaskManager()
downloader = Downloader()
progress = ProgressManager()

tasks.get_all_tasks()
progress.enabled = True
progress.view_progress()

for url, filename in tasks:
    downloader.download(file_path=filename, url=url)

    if th_pool.cur_count == th_pool.MAX_THREADS:
        while th_pool.cur_count != 1:
            sleep(1)

while th_pool.cur_count != 1:
    sleep(1)

progress.enabled = False