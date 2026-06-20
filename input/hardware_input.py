import ctypes
from ctypes import wintypes, windll
import time
import win32gui
import win32con
import win32com.client
import random
import math


class HardwareInputEmulator:
    """Улучшенная эмуляция аппаратного ввода с Wind Mouse алгоритмом"""

    def __init__(self):
        self.user32 = windll.user32
        self.kernel32 = windll.kernel32

        # Константы для mouse_event
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_ABSOLUTE = 0x8000

        # Коды клавиш
        self.KEY_CODES = {
            'shift': 0x10,
            'ctrl': 0x11,
            'alt': 0x12,
            'enter': 0x0D,
            'space': 0x20,
            'tab': 0x09,
            'esc': 0x1B,
            'f1': 0x70,
            'f4': 0x73,
            'a': 0x41,
            'b': 0x42,
            'c': 0x43,
            'd': 0x44,
            'e': 0x45,
            'f': 0x46,
            'g': 0x47,
            'h': 0x48,
            'i': 0x49,
            'j': 0x4A,
            'k': 0x4B,
            'l': 0x4C,
            'm': 0x4D,
            'n': 0x4E,
            'o': 0x4F,
            'p': 0x50,
            'q': 0x51,
            'r': 0x52,
            's': 0x53,
            't': 0x54,
            'u': 0x55,
            'v': 0x56,
            'w': 0x57,
            'x': 0x58,
            'y': 0x59,
            'z': 0x5A,
            '1': 0x31,
            '2': 0x32,
            '3': 0x33,
            '4': 0x34,
            '5': 0x35,
            '6': 0x36,
            '7': 0x37,
            '8': 0x38,
            '9': 0x39,
            '0': 0x30
        }

        # Получаем размеры экрана
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)

    def ultra_fast_activate(self, hwnd, max_attempts=3):
        """Ультрабыстрая активация окна с обходом ограничений Windows"""
        try:
            # Проверка активного окна
            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd == hwnd:
                return True
        except Exception as e:
            print(f"⚠️ Не удалось получить активное окно: {e}")

        # Обход ограничений Windows
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')  # Критически важная строка

        for attempt in range(max_attempts):
            try:
                # Восстановление свернутого окна
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                    time.sleep(0.03)

                # Попытка активации
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.03)

                # Проверка успеха
                if win32gui.GetForegroundWindow() == hwnd:
                    return True

            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"❌ Ошибка активации: {e}")
                time.sleep(0.05)

        return False

    def ensure_window_focus(self, window_hwnd):
        """Принудительная активация окна"""
        try:
            if win32gui.IsIconic(window_hwnd):
                win32gui.ShowWindow(window_hwnd, win32con.SW_RESTORE)
                time.sleep(0.02)

            self.user32.SetForegroundWindow(window_hwnd)
            time.sleep(0.02)
            win32gui.BringWindowToTop(window_hwnd)
            time.sleep(0.02)

            current_foreground = self.user32.GetForegroundWindow()
            return current_foreground == window_hwnd

        except Exception as e:
            print(f"Ошибка активации окна: {e}")
            return False

    def convert_to_absolute_coords(self, x, y):
        """Преобразование пиксельных координат в абсолютные для mouse_event"""
        abs_x = int((x * 65535) / self.screen_width)
        abs_y = int((y * 65535) / self.screen_height)
        return abs_x, abs_y

    def wind_mouse_movement(self, start_x, start_y, end_x, end_y, gravity=9, wind=3, min_wait=1, max_wait=4):
        """
        Wind Mouse алгоритм - естественное движение мыши

        Args:
            start_x, start_y: Начальные координаты
            end_x, end_y: Конечные координаты
            gravity: Сила притяжения к цели
            wind: Сила случайного ветра
            min_wait, max_wait: Диапазон задержек в миллисекундах
        """
        try:
            current_x, current_y = float(start_x), float(start_y)
            target_x, target_y = float(end_x), float(end_y)

            wind_x = 0.0
            wind_y = 0.0

            while True:
                # Расстояние до цели
                dist = math.sqrt((target_x - current_x) ** 2 + (target_y - current_y) ** 2)

                if dist < 1:
                    break

                # Ветер (случайная сила)
                wind_x = wind_x / math.sqrt(3) + (random.random() - 0.5) * wind * 2
                wind_y = wind_y / math.sqrt(3) + (random.random() - 0.5) * wind * 2

                # Гравитация (притяжение к цели)
                gravity_x = gravity * (target_x - current_x) / dist
                gravity_y = gravity * (target_y - current_y) / dist

                # Общая сила
                velocity_x = gravity_x + wind_x
                velocity_y = gravity_y + wind_y

                # Ограничиваем скорость
                velocity = math.sqrt(velocity_x ** 2 + velocity_y ** 2)
                if velocity > 20:
                    velocity_x = (velocity_x / velocity) * 20
                    velocity_y = (velocity_y / velocity) * 20

                # Обновляем позицию
                current_x += velocity_x
                current_y += velocity_y

                # Ограничиваем координаты
                current_x = max(0, min(self.screen_width - 1, current_x))
                current_y = max(0, min(self.screen_height - 1, current_y))

                # Двигаем мышь
                abs_x, abs_y = self.convert_to_absolute_coords(int(current_x), int(current_y))
                self.user32.mouse_event(
                    self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE,
                    abs_x, abs_y, 0, 0
                )

                # Случайная задержка
                delay = random.uniform(min_wait, max_wait) / 1000.0
                time.sleep(delay)

        except Exception as e:
            print(f"❌ Ошибка Wind Mouse: {e}")

    def send_hardware_click_improved(self, x, y, window_hwnd, button='left', humanize=True):
        """Улучшенный аппаратный клик с Wind Mouse движением"""
        try:
            # Проверяем координаты
            if x < 0 or y < 0 or x > self.screen_width or y > self.screen_height:
                print(f"❌ Координаты ({x}, {y}) вне пределов экрана ({self.screen_width}x{self.screen_height})")
                return False

            # Принудительно активируем окно
            focus_success = self.ultra_fast_activate(window_hwnd)
            if not focus_success:
                print(f"⚠️ Не удалось активировать окно, продолжаем попытку клика")

            # ✅ Wind Mouse движение или мгновенное перемещение
            if humanize:
                # Получаем текущую позицию курсора
                cursor_pos = win32gui.GetCursorPos()
                current_x, current_y = cursor_pos

                # Используем Wind Mouse алгоритм
                self.wind_mouse_movement(current_x, current_y, x, y)
            else:
                # Старый способ - мгновенное перемещение
                abs_x, abs_y = self.convert_to_absolute_coords(x, y)
                self.user32.mouse_event(
                    self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE,
                    abs_x, abs_y, 0, 0
                )

            # Небольшая пауза перед кликом
            time.sleep(random.uniform(0.05, 0.15))

            # Выполняем клик
            if button == 'left':
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.05, 0.12))  # Время удержания кнопки
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == 'right':
                self.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.05, 0.12))
                self.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

            return True

        except Exception as e:
            print(f"❌ Критическая ошибка аппаратного клика: {e}")
            return False

    def send_hardware_click(self, x, y, window_hwnd, button='left'):
        """Обёртка для обратной совместимости"""
        return self.send_hardware_click_improved(x, y, window_hwnd, button)

    # ========== МЕТОДЫ ДЛЯ КОМБИНАЦИЙ КЛАВИШ ==========

    def send_hardware_key_combination(self, window_hwnd, key_combination):
        """Отправка комбинаций клавиш"""
        try:
            # Активируем окно
            focus_success = self.ultra_fast_activate(window_hwnd)
            if not focus_success:
                print(f"⚠️ Не удалось активировать окно для комбинации {key_combination}")

            # Парсим комбинацию клавиш
            keys = key_combination.lower().split('+')

            if len(keys) == 1:
                # Одиночная клавиша
                return self._send_single_key(keys[0])
            else:
                # Комбинация клавиш
                return self._send_key_combination(keys)

        except Exception as e:
            print(f"❌ Ошибка отправки комбинации клавиш {key_combination}: {e}")
            return False

    def _send_single_key(self, key):
        """Отправка одиночной клавиши"""
        key_code = self._get_key_code(key)
        if key_code is None:
            return False

        self.user32.keybd_event(key_code, 0, 0, 0)  # Нажатие
        time.sleep(0.01)
        self.user32.keybd_event(key_code, 0, 2, 0)  # Отпускание

        print(f"✅ Отправлена клавиша: {key.upper()}")
        return True

    def _send_key_combination(self, keys):
        """Отправка комбинации клавиш"""
        key_codes = []

        # Получаем коды всех клавиш
        for key in keys:
            key_code = self._get_key_code(key)
            if key_code is None:
                print(f"❌ Неизвестная клавиша: {key}")
                return False
            key_codes.append(key_code)

        # Нажимаем все клавиши
        for key_code in key_codes:
            self.user32.keybd_event(key_code, 0, 0, 0)  # Нажатие
            time.sleep(random.uniform(0.01, 0.02))

        # Отпускаем все клавиши в обратном порядке
        for key_code in reversed(key_codes):
            self.user32.keybd_event(key_code, 0, 2, 0)  # Отпускание
            time.sleep(random.uniform(0.01, 0.02))

        combination_str = '+'.join([k.upper() for k in keys])
        return True

    def _get_key_code(self, key):
        """Получить код клавиши"""
        key = key.lower().strip()

        if key in self.KEY_CODES:
            return self.KEY_CODES[key]

        # Попытка получить код через ord для символов
        if len(key) == 1:
            return ord(key.upper())

        print(f"❌ Неизвестная клавиша: {key}")
        return None

    def send_hardware_key(self, window_hwnd, key_code_or_combination):
        """Универсальный метод для отправки клавиш"""
        if isinstance(key_code_or_combination, int):
            # Старый способ - прямой код клавиши
            try:
                focus_success = self.ultra_fast_activate(window_hwnd)
                if not focus_success:
                    print(f"⚠️ Не удалось активировать окно для клавиши")

                self.user32.keybd_event(key_code_or_combination, 0, 0, 0)  # Нажатие
                time.sleep(random.uniform(0.01, 0.03))
                self.user32.keybd_event(key_code_or_combination, 0, 2, 0)  # Отпускание
                return True
            except Exception as e:
                print(f"❌ Ошибка отправки клавиши: {e}")
                return False
        else:
            # Новый способ - строка с комбинацией
            return self.send_hardware_key_combination(window_hwnd, key_code_or_combination)

    def send_shift_right_click(self, x, y):
        """Выполнить Shift + правый клик мыши с Wind Mouse движением"""
        try:
            # Проверяем координаты
            if x < 0 or y < 0 or x > self.screen_width or y > self.screen_height:
                print(f"❌ Координаты ({x}, {y}) вне пределов экрана")
                return False

            # Нажимаем Shift
            self.user32.keybd_event(self.KEY_CODES['shift'], 0, 0, 0)  # Shift down
            time.sleep(random.uniform(0.01, 0.03))

            # Wind Mouse движение к цели
            cursor_pos = win32gui.GetCursorPos()
            current_x, current_y = cursor_pos
            self.wind_mouse_movement(current_x, current_y, x, y)

            # Небольшая пауза перед кликом
            time.sleep(random.uniform(0.02, 0.05))

            # Правый клик
            self.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.05, 0.12))
            self.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

            # Отпускаем Shift
            self.user32.keybd_event(self.KEY_CODES['shift'], 0, 2, 0)  # Shift up

            print(f"✅ Shift+ПКМ выполнен по координатам ({x}, {y})")
            return True

        except Exception as e:
            print(f"❌ Ошибка выполнения Shift+ПКМ: {e}")
            # Убеждаемся что Shift отпущен в случае ошибки
            try:
                self.user32.keybd_event(self.KEY_CODES['shift'], 0, 2, 0)
            except:
                pass
            return False

    def activate_window_safely(self, hwnd):
        """Безопасная активация окна с использованием новой функции"""
        return self.ultra_fast_activate(hwnd)