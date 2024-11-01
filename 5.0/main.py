import time
from datetime import datetime
import pygame
import os
import logging
from logging.handlers import RotatingFileHandler

# Настройка кастомного логгера с именем 'BellScheduler'
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('logs.txt', maxBytes=1000000, backupCount=3, encoding='utf-8')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('BellScheduler')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Функция для воспроизведения стандартного звука
def play_bell():
    pygame.mixer.music.load('bell_sound.wav')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Функция для воспроизведения альтернативного звука
def play_short_bell():
    pygame.mixer.music.load('3min.wav')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Функция для загрузки расписания звонков из файла
def load_schedule(file_path):
    try:
        with open(file_path, 'r') as file:
            schedule = file.readlines()
        schedule = [line.strip() for line in schedule]
        return schedule
    except Exception as e:
        log_error_once(f"Ошибка при загрузке расписания: {e}")
        return []

# Функция для загрузки данных включения звонков по дням недели
def load_weekdays(file_path):
    weekdays = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                day, status = line.strip().split(':')
                weekdays[day.strip()] = status.strip().lower() == 'true'
        return weekdays
    except Exception as e:
        log_error_once(f"Ошибка при загрузке данных дней недели: {e}")
        return weekdays

# Функция для проверки изменений файла
def check_file_update(file_path, last_mod_time):
    mod_time = os.path.getmtime(file_path)
    if mod_time != last_mod_time:
        return True, mod_time
    return False, last_mod_time

# Функция для записи логов событий
def log_event(message):
    logger.info(message)

# Функция для записи ошибок (только один раз)
error_logged = set()  # Множество для отслеживания ошибок

def log_error_once(message):
    if message not in error_logged:
        logger.error(message)
        error_logged.add(message)

# Основная логика программы
def check_bells():
    pygame.mixer.init()

    schedule = load_schedule('schedule.txt')
    weekdays = load_weekdays('week.txt')
    last_mod_time = os.path.getmtime('schedule.txt')
    rung_bells = set()

    while True:
        current_day = datetime.now().strftime('%A')
        # Проверка включения звонков на текущий день недели
        if not weekdays.get(current_day, False):
            log_event(f"Звонки отключены сегодня ({current_day}).")
            time.sleep(86400)  # Спим сутки, чтобы не тратить ресурсы
            continue  # Переход к следующему дню

        # Если звонки включены на текущий день, продолжаем проверку
        current_time = datetime.now().strftime('%H:%M')

        # Проверка на изменение файла расписания
        file_changed, last_mod_time = check_file_update('schedule.txt', last_mod_time)
        if file_changed:
            schedule = load_schedule('schedule.txt')
            rung_bells.clear()  # Сбрасываем флаг для звонков при обновлении файла

        for line in schedule:
            if current_time in line and current_time not in rung_bells:
                try:
                    if '3min' in line:
                        play_short_bell()
                        log_event(f"Сработал короткий звонок: {current_time}")
                        print(f"Сработал короткий звонок: {current_time}")
                    else:
                        play_bell()
                        log_event(f"Сработал звонок: {current_time}")
                        print(f"Сработал звонок: {current_time}")

                    rung_bells.add(current_time)  # Запоминаем время звонка
                    time.sleep(60)  # Ждём одну минуту, чтобы избежать повторения звонка
                except Exception as e:
                    log_error_once(f"Ошибка при воспроизведении звука: {e}")
                break
        else:
            time.sleep(10)

if __name__ == "__main__":
    check_bells()
