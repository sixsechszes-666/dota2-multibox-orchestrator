# hwnd_tracker.py
import json
import os
import time
import win32gui
import win32process
import psutil
from typing import Dict, Optional


class HWNDTracker:
    """Класс для отслеживания и сохранения HWND окон Dota 2"""

    def __init__(self, config_file="hwnd_mapping.json"):
        self.config_file = config_file
        self.hwnd_mapping = self.load_mapping()

    def load_mapping(self) -> Dict[str, int]:
        """Загрузка сохраненного маппинга PID -> HWND"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return self.validate_mapping(data)
            return {}
        except Exception as e:
            print(f"❌ Ошибка загрузки маппинга HWND: {e}")
            return {}

    def save_mapping(self):
        """Сохранение маппинга PID -> HWND"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.hwnd_mapping, f, indent=2)
            print(f"💾 Маппинг HWND сохранен: {len(self.hwnd_mapping)} записей")
        except Exception as e:
            print(f"❌ Ошибка сохранения маппинга HWND: {e}")

    def validate_mapping(self, mapping: Dict[str, int]) -> Dict[str, int]:
        """Проверка актуальности сохраненных HWND"""
        valid_mapping = {}

        for pid_str, hwnd in mapping.items():
            try:
                pid = int(pid_str)
                if psutil.pid_exists(pid) and win32gui.IsWindow(hwnd):
                    valid_mapping[pid_str] = hwnd
            except:
                continue

        return valid_mapping

    def find_dota_window_for_pid(self, target_pid: int) -> Optional[int]:
        """Поиск окна Dota 2 для конкретного PID"""
        found_windows = []

        def enum_windows_callback(hwnd, windows):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title and 'dota 2' in window_title.lower():
                        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)

                        if window_pid == target_pid or self._is_related_to_pid(window_pid, target_pid):
                            windows.append((hwnd, window_title, window_pid))
            except:
                pass
            return True

        win32gui.EnumWindows(enum_windows_callback, found_windows)

        if found_windows:
            hwnd, title, window_pid = found_windows[0]
            print(f"✅ Найдено окно Dota 2 для PID {target_pid}: {title} (HWND: {hwnd})")
            return hwnd

        return None

    def _is_related_to_pid(self, window_pid: int, target_pid: int) -> bool:
        """Проверка связи между процессами"""
        try:
            window_proc = psutil.Process(window_pid)
            target_proc = psutil.Process(target_pid)

            if window_proc.ppid() == target_pid or target_proc.ppid() == window_pid:
                return True

            children = target_proc.children(recursive=True)
            for child in children:
                if child.pid == window_pid:
                    return True

            return False
        except:
            return False

    def register_pid_hwnd(self, pid: int, max_attempts: int = 120, check_interval: int = 2) -> Optional[int]:
        """Регистрация HWND для PID с ожиданием появления окна"""
        pid_str = str(pid)

        if pid_str in self.hwnd_mapping:
            hwnd = self.hwnd_mapping[pid_str]
            if win32gui.IsWindow(hwnd):
                print(f"📋 Используется сохраненный HWND {hwnd} для PID {pid}")
                return hwnd
            else:
                del self.hwnd_mapping[pid_str]

        print(f"🔍 Поиск окна Dota 2 для PID {pid}...")

        for attempt in range(max_attempts):
            hwnd = self.find_dota_window_for_pid(pid)

            if hwnd:
                self.hwnd_mapping[pid_str] = hwnd
                self.save_mapping()
                print(f"💾 Зарегистрирован HWND {hwnd} для PID {pid}")
                return hwnd

            if attempt % 5 == 0:
                print(f"⏳ Ожидание окна для PID {pid}... (попытка {attempt + 1}/{max_attempts})")

            time.sleep(check_interval)

        print(f"⏰ Таймаут поиска окна для PID {pid}")
        return None

    def get_hwnd_for_pid(self, pid: int) -> Optional[int]:
        """Получение HWND для PID"""
        pid_str = str(pid)

        if pid_str in self.hwnd_mapping:
            hwnd = self.hwnd_mapping[pid_str]
            if win32gui.IsWindow(hwnd):
                return hwnd
            else:
                del self.hwnd_mapping[pid_str]
                self.save_mapping()

        return None

    def cleanup_invalid_entries(self):
        """Очистка недействительных записей"""
        to_remove = []

        for pid_str, hwnd in self.hwnd_mapping.items():
            try:
                pid = int(pid_str)
                if not psutil.pid_exists(pid) or not win32gui.IsWindow(hwnd):
                    to_remove.append(pid_str)
            except:
                to_remove.append(pid_str)

        for pid_str in to_remove:
            del self.hwnd_mapping[pid_str]

        if to_remove:
            self.save_mapping()
            print(f"🧹 Удалено {len(to_remove)} недействительных записей HWND")

    def get_all_registered_hwnds(self) -> Dict[int, int]:
        """Получение всех зарегистрированных PID -> HWND"""
        result = {}
        for pid_str, hwnd in self.hwnd_mapping.items():
            try:
                pid = int(pid_str)
                if psutil.pid_exists(pid) and win32gui.IsWindow(hwnd):
                    result[pid] = hwnd
            except:
                continue
        return result
