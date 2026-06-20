# prepare.py
import pyautogui
import time
import sys
import os
import numpy as np
from PIL import Image
import logging
import colorlog
import random
import cv2
import win32gui

from input.hardware_input import HardwareInputEmulator
from features.gaming_actions import GamingActions
from core.party_manager import PartyManager


class PrepareMatchmaking:
    """Class for automating Dota 2 matchmaking preparation tasks with hardware input emulation"""

    def __init__(self, window_title="Dota 2", confidence=0.8, debug_mode=True, log_file=None):
        """Initialize the PrepareMatchmaking class"""
        self.window_title = window_title
        self.confidence = confidence
        self.debug_mode = debug_mode
        self.log_file = log_file
        self.logger = self.setup_logger()

        # Инициализируем аппаратный эмулятор
        self.hardware_input = HardwareInputEmulator()
        self.party_manager = PartyManager(self)

        # Default image paths
        self.imgs_folder = "imgs"
        self.heroes_folder = os.path.join(self.imgs_folder, "heroes")
        self.loading_image = os.path.join(self.imgs_folder, "ingame_loading_check.png")
        self.pick_loading_image = os.path.join(self.imgs_folder, "pick_loading_check.png")
        self.radiant_image = os.path.join(self.imgs_folder, "radiant.png")
        self.dire_image = os.path.join(self.imgs_folder, "dire.png")
        self.pick_button_image = os.path.join(self.imgs_folder, "btn_pick.png")

        self.gaming_actions = GamingActions(self)

        # Check required packages
        self.check_required_packages()

    def setup_logger(self, log_file=None):
        """Configure and return a colorful logger with optional file output"""
        logger_name = f'dota2_assistant_{id(self)}'
        logger = logging.getLogger(logger_name)

        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)

        console_handler = logging.StreamHandler()
        if self.debug_mode:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)

        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s %(message_log_color)s%(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={
                'message': {
                    'DEBUG': 'cyan',
                    'INFO': 'white',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red',
                }
            }
        )
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

        if log_file:
            try:
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
                if self.debug_mode:
                    file_handler.setLevel(logging.DEBUG)
                else:
                    file_handler.setLevel(logging.INFO)

                file_formatter = logging.Formatter(
                    '[%(asctime)s] %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

                logger.info(f"Логирование в файл настроено: {log_file}")
            except Exception as e:
                print(f"❌ Ошибка при настройке логирования в файл {log_file}: {str(e)}")

        logger.propagate = False
        return logger

    def check_required_packages(self):
        """Check if all required packages are installed"""
        try:
            import PIL
            self.logger.debug("✅ PIL/Pillow установлен.")
        except ImportError:
            self.logger.critical("❌ PIL/Pillow не установлен. Установите: pip install pillow")
            sys.exit(1)

        try:
            import cv2
            self.logger.debug(f"✅ OpenCV установлен (версия {cv2.__version__}).")
        except ImportError:
            self.logger.critical("❌ OpenCV не установлен. Установите: pip install opencv-python")
            sys.exit(1)

        try:
            import win32gui
            self.logger.debug("✅ Win32GUI установлен.")
        except ImportError:
            self.logger.critical("❌ Win32GUI не установлен. Установите: pip install pywin32")
            sys.exit(1)

        try:
            import colorlog
            self.logger.debug("✅ ColorLog установлен.")
        except ImportError:
            print("❌ ColorLog не установлен. Установите: pip install colorlog")
            sys.exit(1)

    def get_window_coordinates(self, window_title=None):
        """Get coordinates of the specified window"""
        if hasattr(self, 'window_coords'):
            return self.window_coords

        if window_title is None:
            window_title = self.window_title

        hwnd = self._find_window_by_partial_title(window_title)

        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            x, y, width, height = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
            actual_title = win32gui.GetWindowText(hwnd)
            self.logger.info(f"Окно '{actual_title}' найдено: {x}, {y}, {width}x{height}")
            return x, y, width, height

        self.logger.error(f"Окно с названием '{window_title}' не найдено")
        return None

    def _find_window_by_partial_title(self, partial_title):
        """Find window by partial title match"""

        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if partial_title.lower() in window_text.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None

    def check_image_on_screen(self, image_path, confidence_threshold=None, window_title=None):
        """Check if an image is present on screen or in a specific window"""
        if confidence_threshold is None:
            confidence_threshold = self.confidence

        if window_title is None:
            window_title = self.window_title

        window_coords = None
        if window_title:
            window_coords = self.get_window_coordinates(window_title)
            if not window_coords:
                self.logger.error(f"Окно '{window_title}' не найдено.")
                return False, None

        if not os.path.isfile(image_path):
            self.logger.error(f"Файл изображения '{image_path}' не найден.")
            return False, None

        try:
            img = Image.open(image_path)
            img_width, img_height = img.size
            self.logger.debug(f"Изображение {image_path} успешно загружено: {img_width}x{img_height} пикселей")
        except Exception as e:
            self.logger.error(f"Файл '{image_path}' не является допустимым изображением: {str(e)}")
            return False, None

        try:
            if window_coords:
                x, y, width, height = window_coords
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                screenshot = pyautogui.screenshot()

            needle_img = cv2.imread(image_path)
            haystack_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            if needle_img.shape[0] > haystack_img.shape[0] or needle_img.shape[1] > haystack_img.shape[1]:
                self.logger.error(
                    f"Шаблон ({needle_img.shape[1]}x{needle_img.shape[0]}) больше чем скриншот ({haystack_img.shape[1]}x{haystack_img.shape[0]})")
                return False, None

            result = cv2.matchTemplate(haystack_img, needle_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence_threshold:
                button_x = max_loc[0] + needle_img.shape[1] // 2
                button_y = max_loc[1] + needle_img.shape[0] // 2

                if window_coords:
                    click_x = window_coords[0] + button_x
                    click_y = window_coords[1] + button_y
                else:
                    click_x, click_y = button_x, button_y

                self.logger.info(
                    f"Изображение найдено с уверенностью {max_val * 100:.2f}% в позиции {click_x}, {click_y}")
                return True, (click_x, click_y)
            else:
                self.logger.warning(
                    f"Изображение не найдено. Лучшее совпадение: {max_val * 100:.2f}% (ниже порога {confidence_threshold * 100:.2f}%)")
                return False, None

        except Exception as e:
            self.logger.error(f"Ошибка при поиске изображения: {str(e)}")
            return False, None

    def hardware_click(self, x, y, button='left'):
        """Улучшенный аппаратный клик с проверками"""
        if hasattr(self, 'hwnd'):
            hwnd = self.hwnd
        else:
            hwnd = self._find_window_by_partial_title(self.window_title)

        if not hwnd:
            self.logger.error("❌ Не удалось найти окно для аппаратного клика")
            return False

        # Получаем информацию об окне
        try:
            window_rect = win32gui.GetWindowRect(hwnd)
            window_x, window_y, window_right, window_bottom = window_rect
            window_width = window_right - window_x
            window_height = window_bottom - window_y

            self.logger.debug(f"Окно: {window_x}, {window_y}, размер: {window_width}x{window_height}")
            self.logger.debug(f"Клик по координатам: {x}, {y}")

            # Проверяем, что координаты в разумных пределах
            if x > 5000 or y > 3000:  # Подозрительно большие координаты
                self.logger.warning(f"⚠️ Подозрительно большие координаты клика: ({x}, {y})")

                # Если координаты слишком большие, возможно это относительные координаты
                # Попробуем преобразовать их в координаты окна
                if hasattr(self, 'window_coords'):
                    win_x, win_y, win_w, win_h = self.window_coords
                    # Проверяем, может быть это абсолютные координаты, которые нужно сделать относительными
                    if x > win_x and y > win_y:
                        # Преобразуем в относительные координаты
                        rel_x = min(x - win_x, win_w - 10)  # Ограничиваем границами окна
                        rel_y = min(y - win_y, win_h - 10)
                        abs_x = win_x + rel_x
                        abs_y = win_y + rel_y
                        self.logger.info(f"🔄 Преобразование координат: ({x}, {y}) -> ({abs_x}, {abs_y})")
                        x, y = abs_x, abs_y

        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось получить информацию об окне: {e}")

        # Выполняем клик с повторными попытками
        for attempt in range(3):
            self.logger.debug(f"Попытка клика #{attempt + 1}")
            success = self.hardware_input.send_hardware_click(x, y, hwnd, button)

            if success:
                return True
            else:
                self.logger.warning(f"⚠️ Попытка #{attempt + 1} не удалась")
                time.sleep(0.2)  # Пауза между попытками

        self.logger.error(f"❌ Все попытки аппаратного клика не удались для координат ({x}, {y})")
        return False

    def hardware_key_press(self, key):
        """Улучшенный метод нажатия клавиш с поддержкой комбинаций"""
        try:
            # Определяем hwnd
            if hasattr(self, 'hwnd'):
                hwnd = self.hwnd
            else:
                hwnd = self._find_window_by_partial_title(self.window_title)

            if not hwnd:
                self.logger.error("❌ Не удалось найти окно для аппаратного ввода")
                return False

            # Используем новую систему для строк, старую для чисел
            if isinstance(key, str):
                # Новая система - поддерживает комбинации
                success = self.hardware_input.send_hardware_key(hwnd, key)
            else:
                # Старая система - прямые коды клавиш
                success = self.hardware_input.send_hardware_key(hwnd, key)

            if success:
                pass
            else:
                self.logger.error(f"❌ Ошибка нажатия {key}")

            return success

        except Exception as e:
            self.logger.error(f"❌ Ошибка нажатия клавиши {key}: {e}")
            return False

    def find_all_image_matches(self, image_path, confidence_threshold=None, window_title=None):
        """Найти все совпадения изображения на экране"""
        if confidence_threshold is None:
            confidence_threshold = self.confidence
        if window_title is None:
            window_title = self.window_title

        window_coords = None
        if window_title:
            window_coords = self.get_window_coordinates(window_title)
            if not window_coords:
                return []

        if not os.path.isfile(image_path):
            return []

        try:
            img = Image.open(image_path)
        except Exception as e:
            return []

        try:
            if window_coords:
                x, y, width, height = window_coords
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                screenshot = pyautogui.screenshot()

            needle_img = cv2.imread(image_path)
            haystack_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            if needle_img.shape[0] > haystack_img.shape[0] or needle_img.shape[1] > haystack_img.shape[1]:
                return []

            result = cv2.matchTemplate(haystack_img, needle_img, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence_threshold)
            matches = []

            for pt_y, pt_x in zip(locations[0], locations[1]):
                confidence = result[pt_y, pt_x]
                center_x = pt_x + needle_img.shape[1] // 2
                center_y = pt_y + needle_img.shape[0] // 2

                if window_coords:
                    abs_x = window_coords[0] + center_x
                    abs_y = window_coords[1] + center_y
                else:
                    abs_x, abs_y = center_x, center_y

                matches.append({
                    'position': (abs_x, abs_y),
                    'confidence': confidence * 100,
                })

            # Убираем дублирующиеся совпадения
            filtered_matches = self.filter_duplicate_matches(matches, needle_img.shape[1], needle_img.shape[0])
            return filtered_matches

        except Exception as e:
            return []

    def filter_duplicate_matches(self, matches, template_width, template_height, overlap_threshold=0.5):
        """Фильтрует дублирующиеся совпадения"""
        if not matches:
            return []

        sorted_matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
        filtered_matches = []

        for current_match in sorted_matches:
            is_duplicate = False
            current_pos = current_match['position']

            for existing_match in filtered_matches:
                existing_pos = existing_match['position']
                distance_x = abs(current_pos[0] - existing_pos[0])
                distance_y = abs(current_pos[1] - existing_pos[1])

                threshold_x = template_width * overlap_threshold
                threshold_y = template_height * overlap_threshold

                if distance_x < threshold_x and distance_y < threshold_y:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered_matches.append(current_match)

        return filtered_matches

    def skill_upgrade(self, skill_image=None, confidence=None, window_title=None):
        """
        Прокачка навыков через хоткеи (Ctrl + Q/W/E/R/D/F)

        Args:
            skill_image (str): Не используется (для обратной совместимости)
            confidence (float): Не используется (для обратной совместимости)
            window_title (str): Заголовок окна

        Returns:
            tuple: (True, skills_upgraded) если навыки прокачаны, иначе (False, None)
        """
        self.logger.info("🔍 Прокачка навыков через хоткеи...")

        try:
            # Список кнопок навыков
            skill_keys = ['q', 'w', 'e', 'r', 'd', 'f', 'f1', 'z']

            # Перемешиваем порядок нажатия
            random.shuffle(skill_keys)

            self.logger.info(f"🎲 Порядок прокачки навыков: {' → '.join(skill_keys).upper()}")

            upgraded_skills = []

            for skill_key in skill_keys:
                try:
                    # Нажимаем Ctrl + клавиша навыка
                    combination = f"ctrl+{skill_key}"

                    success = self.hardware_key_press(combination)

                    if success:
                        upgraded_skills.append(skill_key.upper())
                    else:
                        self.logger.warning(f"⚠️ Ошибка прокачки навыка {skill_key.upper()}")

                    # Небольшая задержка между навыками
                    time.sleep(0.1)

                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка при прокачке навыка {skill_key}: {e}")

            if upgraded_skills:
                skills_str = ', '.join(upgraded_skills)
                return True, skills_str
            else:
                self.logger.debug("💡 Навыки не были прокачаны")
                return False, None

        except Exception as e:
            self.logger.error(f"❌ Ошибка прокачки навыков через хоткеи: {e}")
            return False, None

    def wait_for_game_loading(self, loading_image=None, confidence=None, window_title=None, timeout=300,
                              check_interval=5):
        """Wait for game to load by checking for a loading indicator"""
        if loading_image is None:
            loading_image = self.loading_image
        if confidence is None:
            confidence = self.confidence
        if window_title is None:
            window_title = self.window_title
        self.logger.info(f"Ожидание загрузки игры (проверка наличия {loading_image})...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            found, position = self.check_image_on_screen(loading_image, confidence, window_title)
            if found:
                self.logger.info(f"✅ Игра загружена! Индикатор загрузки найден.")
                return True

            elapsed = time.time() - start_time
            self.logger.debug(f"⏳ Игра еще не загружена. Прошло {elapsed:.1f} секунд из {timeout}.")
            time.sleep(check_interval)

        self.logger.error(f"⏱️ Время ожидания ({timeout} сек) истекло. Игра не загрузилась.")
        return False

    def wait_for_pick_loading(self, loading_image=None, confidence=None, window_title=None, timeout=180,
                              check_interval=2):
        """Wait for hero pick phase to load"""
        if loading_image is None:
            loading_image = self.pick_loading_image
        if confidence is None:
            confidence = self.confidence
        if window_title is None:
            window_title = self.window_title

        self.logger.info(f"Ожидание загрузки стадии пика (проверка наличия {loading_image})...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            found, position = self.check_image_on_screen(loading_image, confidence, window_title)
            if found:
                self.logger.info(f"✅ Стадия пика загружена! Индикатор загрузки найден.")
                return True

            elapsed = time.time() - start_time
            self.logger.debug(f"⏳ Стадия пика еще не загружена. Прошло {elapsed:.1f} секунд из {timeout}.")
            time.sleep(check_interval)

        self.logger.error(f"⏱️ Время ожидания ({timeout} сек) истекло. Стадия пика не загрузилась.")
        return False

    def check_team(self, radiant_image=None, dire_image=None, confidence=None, window_title=None):
        """Check which team is selected (Radiant or Dire)"""
        if radiant_image is None:
            radiant_image = self.radiant_image
        if dire_image is None:
            dire_image = self.dire_image
        if confidence is None:
            confidence = self.confidence
        if window_title is None:
            window_title = self.window_title

        self.logger.info(f"Проверка выбранной команды...")

        found_radiant, radiant_pos = self.check_image_on_screen(radiant_image, confidence, window_title)
        if found_radiant:
            self.logger.info(f"🌞 Выбрана команда RADIANT!")
            return "radiant", radiant_pos

        found_dire, dire_pos = self.check_image_on_screen(dire_image, confidence, window_title)
        if found_dire:
            self.logger.info(f"🌑 Выбрана команда DIRE!")
            return "dire", dire_pos

        self.logger.warning("❓ Не удалось определить выбранную команду")
        return "unknown", None

    def get_random_hero_image(self, heroes_folder=None):
        """Parse all PNG images from specified folder and select a random one"""
        if heroes_folder is None:
            heroes_folder = self.heroes_folder

        try:
            if not os.path.isdir(heroes_folder):
                self.logger.error(f"❌ Папка с героями '{heroes_folder}' не существует")
                return None

            hero_images = [
                os.path.join(heroes_folder, filename)
                for filename in os.listdir(heroes_folder)
                if filename.lower().endswith('.png')
            ]

            if not hero_images:
                self.logger.warning(f"⚠️ В папке '{heroes_folder}' не найдено PNG изображений")
                return None

            random_hero = random.choice(hero_images)
            hero_name = os.path.basename(random_hero).replace('.png', '')
            self.logger.info(f"🎲 Случайно выбран герой: {hero_name}")
            return random_hero

        except Exception as e:
            self.logger.error(f"❌ Ошибка при выборе случайного героя: {str(e)}")
            return None

    def pick_hero_hardware(self, hero_image=None, confidence=0.99, window_title=None):
        """Pick a hero using hardware input emulation"""
        if confidence is None:
            confidence = 0.99
        if window_title is None:
            window_title = self.window_title

        if hero_image is None:
            hero_image = self.get_random_hero_image()
            if hero_image is None:
                self.logger.error("❌ Не удалось выбрать случайного героя")
                return 'undifined', None

        self.logger.info(f"🔍 Поиск героя {os.path.basename(hero_image)}...")

        found_hero, hero_pos = self.check_image_on_screen(hero_image, confidence, window_title)

        if found_hero:
            self.logger.info(f"🎯 Герой {os.path.basename(hero_image)} найден!")

            if self.hardware_click(hero_pos[0], hero_pos[1], 'left'):
                time.sleep(0.2)
                found_btn, btn_pos = self.check_image_on_screen(self.pick_button_image, confidence, window_title)
                if found_btn:
                    self.logger.info(f"✅ Кнопка выбора героя найдена!")
                    self.hardware_click(btn_pos[0], btn_pos[1], 'left')
                else:
                    self.logger.warning(f"❌ Кнопка выбора героя не найдена")

                return hero_image, hero_pos
            else:
                self.logger.error("❌ Не удалось выполнить аппаратный клик по герою")
                return 'undifined', None
        else:
            self.logger.warning(f"❌ Герой {os.path.basename(hero_image)} не найден на экране")
            return 'undifined', None

    def buy_boots_hardware(self, boots_image='imgs/boots.png', confidence=None, window_title=None):
        """Buy boots using hardware input emulation"""
        if confidence is None:
            confidence = self.confidence
        if window_title is None:
            window_title = self.window_title

        self.logger.info(f"🔍 Поиск итема {os.path.basename(boots_image)}...")

        found_boots, boots_pos = self.check_image_on_screen(boots_image, confidence, window_title)

        if found_boots:
            self.logger.info(f"🎯 Итем {os.path.basename(boots_image)} найден!")
            if self.hardware_click(boots_pos[0], boots_pos[1], 'right'):
                return boots_image, boots_pos
            else:
                self.logger.error("❌ Не удалось выполнить аппаратный клик по ботинкам")
                return False, None
        else:
            self.logger.warning(f"❌ Итем {os.path.basename(boots_image)} не найден на экране")
            return False, None

    def run_team_check(self, timeout=300):
        """Run the team check workflow"""
        self.logger.info("=" * 60)
        self.logger.info("🎮 DOTA 2 TEAM CHECKER - ЗАПУСК")
        self.logger.info("=" * 60)

        game_loaded = self.wait_for_game_loading(timeout=timeout)
        if game_loaded:
            team, position = self.check_team()

            self.logger.info("-" * 60)
            if team != "unknown" and position:
                self.logger.info(f"🏆 РЕЗУЛЬТАТ: Выбрана команда {team.upper()} в позиции {position}")
            else:
                self.logger.error("❌ РЕЗУЛЬТАТ: Не удалось определить команду")

            self.logger.info("=" * 60)
            self.logger.info("🎮 DOTA 2 TEAM CHECKER - ЗАВЕРШЕНИЕ")
            self.logger.info("=" * 60)

            return team, position
        else:
            self.logger.error("❌ Не удалось дождаться загрузки игры. Проверка команды не выполнена.")
            return "unknown", None

    def run_hero_pick_hardware(self, hero_image=None, timeout=180):
        """Run the hero pick workflow using hardware input"""
        self.logger.info("=" * 60)
        self.logger.info("🎮 DOTA 2 HERO PICKER - ЗАПУСК (АППАРАТНЫЙ ВВОД)")
        self.logger.info("=" * 60)

        pick_loaded = self.wait_for_pick_loading(timeout=timeout)

        if pick_loaded:
            hero, position = self.pick_hero_hardware(hero_image)

            self.logger.info("-" * 60)
            if hero != "undifined" and position:
                hero_name = os.path.basename(hero).replace('.png', '')
                self.logger.info(f"🏆 РЕЗУЛЬТАТ: Выбран герой {hero_name} в позиции {position}")
            else:
                self.logger.error("❌ РЕЗУЛЬТАТ: Не удалось выбрать героя")

            confidence = self.confidence
            window_title = self.window_title
            time.sleep(2)
            for i in range(20):
                found_btn, btn_pos = self.check_image_on_screen(self.pick_button_image, confidence, window_title)

                if found_btn:
                    self.logger.info(f"❌ Кнопка выбора героя все еще видна на позиции {btn_pos}")
                    time.sleep(0.25)
                    self.hardware_click(btn_pos[0], btn_pos[1], 'left')
                else:
                    self.logger.info("✅ Кнопка выбора героя не найдена, пик выполнен, продолжаем")
                    break

            self.logger.info("=" * 60)
            self.logger.info("🎮 DOTA 2 HERO PICKER - ЗАВЕРШЕНИЕ")
            self.logger.info("=" * 60)

            return hero, position
        else:
            self.logger.error("❌ Не удалось дождаться загрузки стадии пика")
            return "undifined", None

    def _get_all_hero_images(self, heroes_folder=None):
        """Получить все PNG изображения героев из папки"""
        if heroes_folder is None:
            heroes_folder = self.heroes_folder

        try:
            if not os.path.exists(heroes_folder):
                self.logger.warning(f"⚠️ Папка с героями не найдена: {heroes_folder}")
                return []

            hero_images = []
            for filename in os.listdir(heroes_folder):
                if filename.lower().endswith('.png'):
                    full_path = os.path.join(heroes_folder, filename)
                    hero_images.append(full_path)

            self.logger.debug(f"📁 Найдено {len(hero_images)} изображений героев в {heroes_folder}")
            return hero_images

        except Exception as e:
            self.logger.error(f"❌ Ошибка чтения папки с героями: {e}")
            return []

    def buy_items_sequence(self, items_list):
        """Покупка последовательности предметов"""

        window_coords = self.get_window_coordinates()
        if not window_coords:
            self.logger.error("❌ Не удалось получить координаты окна")
            return False, None

        window_x, window_y, _, _ = window_coords

        for item in items_list:
            try:
                self.logger.info(f"🛒 Покупка предмета: {item['name']}")

                # Открываем магазин (F4)
                self.hardware_key_press(115)  # F4
                time.sleep(0.3)

                # Клик по предмету в магазине
                shop_x = window_x + item['shop_coords'][0]
                shop_y = window_y + item['shop_coords'][1]
                self.hardware_click(shop_x, shop_y, 'left')
                time.sleep(0.2)

                # Shift + клик в инвентарь (используем новый метод из hardware_input.py)
                inv_x = window_x + item['inventory_coords'][0]
                inv_y = window_y + item['inventory_coords'][1]
                self.hardware_click_with_shift(inv_x, inv_y)
                time.sleep(0.2)

                # Закрываем магазин (F4)
                self.hardware_key_press(115)  # F4
                time.sleep(0.5)

                self.logger.info(f"✅ Предмет {item['name']} куплен")

            except Exception as e:
                self.logger.error(f"❌ Ошибка покупки {item['name']}: {e}")
                continue

        return True, "items_purchased"

    def hardware_click_with_shift(self, x, y):
        """Ctrl + Shift + клик используя hardware_input"""
        try:
            # Нажимаем Ctrl
            if hasattr(self.hardware_input, 'key_down'):
                self.hardware_input.key_down(17)  # Ctrl down
            else:
                import ctypes
                ctypes.windll.user32.keybd_event(17, 0, 0, 0)

            time.sleep(0.05)

            # Нажимаем Shift
            if hasattr(self.hardware_input, 'key_down'):
                self.hardware_input.key_down(16)  # Shift down
            else:
                import ctypes
                ctypes.windll.user32.keybd_event(16, 0, 0, 0)

            time.sleep(0.05)

            # Делаем клик
            self.hardware_click(x, y, 'left')
            time.sleep(0.05)

            # Отпускаем клавиши в обратном порядке
            # Shift up
            if hasattr(self.hardware_input, 'key_up'):
                self.hardware_input.key_up(16)
            else:
                import ctypes
                ctypes.windll.user32.keybd_event(16, 0, 2, 0)

            time.sleep(0.05)

            # Ctrl up
            if hasattr(self.hardware_input, 'key_up'):
                self.hardware_input.key_up(17)
            else:
                import ctypes
                ctypes.windll.user32.keybd_event(17, 0, 2, 0)

            self.logger.debug(f"🖱️ Ctrl+Shift+клик выполнен по ({x}, {y})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка Ctrl+Shift+клик: {e}")
            return False

    def check_game_end(self):
        """Проверка завершения игры по экранам победы"""
        try:
            self.logger.info("🔍 Проверка конца игры...")

            # Список изображений для поиска
            victory_images = [
                ("imgs/win_dire.png", "dire_victory"),
                ("imgs/win_radiant.png", "radiant_victory"),
                ("imgs/play.png", "radiant_victory")
            ]

            for image_path, victory_type in victory_images:
                self.logger.info(f"🔎 Поиск изображения: {image_path}")

                if not os.path.exists(image_path):
                    self.logger.warning(f"📁 Файл не существует: {image_path}")
                    continue

                try:
                    found, position = self.check_image_on_screen(
                        image_path,
                        confidence_threshold=0.8,
                        window_title=self.window_title
                    )

                    if found and position:  # Если изображение найдено
                        self.logger.info(f"🏆 Обнаружен экран победы: {victory_type}")

                        if "play.png" not in image_path:
                            click_success = self.hardware_click(position[0], position[1], 'left')

                            if click_success:
                                self.logger.info(f"✅ Нажата кнопка победы: {victory_type}")
                            else:
                                self.logger.warning(f"⚠️ Не удалось нажать кнопку победы: {victory_type}")
                        else:
                            self.logger.info(f"🎮 Найдена кнопка play.png, клик пропущен")

                        return victory_type

                except Exception as e:
                    self.logger.debug(f"❌ Ошибка поиска {image_path}: {e}")
                    continue

            self.logger.debug("🔍 Проверка конца игры завершена - экраны победы не найдены")
            return None

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки конца игры: {e}")
            return None

    def check_game_end_with_stop(self):
        """Проверка конца игры с принудительной остановкой стратегии"""
        game_ended = self.check_game_end()

        if game_ended:
            # Устанавливаем флаг остановки стратегии
            self.stop_strategy = True
            self.logger.info(f"🛑 Стратегия остановлена из-за завершения игры: {game_ended}")
            return True, game_ended

        return False, None

    def is_hero_banned(self, hero_image_path, ban_threshold=0.15):
        """
        Определить, забанен ли герой по цветности/насыщенности изображения

        Args:
            hero_image_path (str): Путь к изображению героя
            ban_threshold (float): Порог насыщенности для определения бана (0.0-1.0)

        Returns:
            bool: True если герой забанен (серый), False если доступен (цветной)
        """
        try:
            # Получаем координаты окна
            window_coords = self.get_window_coordinates()
            if not window_coords:
                self.logger.warning("⚠️ Не удалось получить координаты окна")
                return True  # При ошибке считаем забаненным

            # Ищем героя на экране
            found_hero, hero_pos = self.check_image_on_screen(
                hero_image_path,
                confidence_threshold=0.6,  # Снижаем порог для серых героев
                window_title=self.window_title
            )

            if not found_hero:
                self.logger.debug(f"❌ Герой не найден на экране: {os.path.basename(hero_image_path)}")
                return True  # Если не найден - считаем забаненным

            # Получаем область вокруг найденного героя
            x, y, width, height = window_coords
            hero_region_size = 100  # Размер области для анализа

            # Вычисляем координаты области для анализа
            relative_x = hero_pos[0] - x
            relative_y = hero_pos[1] - y

            region_x = max(0, relative_x - hero_region_size // 2)
            region_y = max(0, relative_y - hero_region_size // 2)

            # Делаем скриншот области героя
            screenshot = pyautogui.screenshot(region=(
                x + region_x,
                y + region_y,
                hero_region_size,
                hero_region_size
            ))

            # Анализируем цветность
            ban_status = self._analyze_hero_color_saturation(screenshot, ban_threshold)

            hero_name = os.path.basename(hero_image_path).replace('.png', '')

            if ban_status:
                self.logger.info(f"🚫 Герой {hero_name} ЗАБАНЕН (серый)")
            else:
                self.logger.info(f"✅ Герой {hero_name} ДОСТУПЕН (цветной)")

            return ban_status

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки бана для {hero_image_path}: {e}")
            return True  # При ошибке считаем забаненным

    def _analyze_hero_color_saturation(self, screenshot, ban_threshold=0.15):
        """
        Анализирует насыщенность цветов в изображении героя

        Args:
            screenshot: PIL изображение области героя
            ban_threshold (float): Порог насыщенности

        Returns:
            bool: True если герой забанен (низкая насыщенность)
        """
        try:
            # Конвертируем в numpy array
            img_array = np.array(screenshot)

            # Конвертируем RGB в HSV для анализа насыщенности
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

            # Получаем канал насыщенности (S)
            saturation = hsv[:, :, 1]

            # Вычисляем среднюю насыщенность
            mean_saturation = np.mean(saturation) / 255.0

            # Дополнительно анализируем стандартное отклонение
            std_saturation = np.std(saturation) / 255.0

            # Комбинированный анализ: низкая насыщенность И низкое отклонение = серый герой
            is_banned = (mean_saturation < ban_threshold) and (std_saturation < 0.1)

            self.logger.debug(
                f"📊 Анализ цветности: насыщенность={mean_saturation:.3f}, отклонение={std_saturation:.3f}")

            return is_banned

        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа цветности: {e}")
            return True

    def batch_find_heroes_on_screen(self, heroes_list, heroes_folder, batch_confidence=None):
        """Пакетный поиск героев на экране с индивидуальным confidence"""
        try:
            self.logger.info(f"🔍 Пакетный поиск {len(heroes_list)} героев на экране...")

            hero_confidence_overrides = {
                'beast': 0.95,
                'axe': 0.97,
                'juggernaut': 0.96,
                'lifestealer': 0.96,
                'luna': 0.96,
                # Можно добавить больше героев по необходимости
            }

            default_confidence = batch_confidence if batch_confidence is not None else 0.99

            # Подготавливаем данные для поиска
            heroes_data = []
            for hero_name in heroes_list:
                hero_image_path = os.path.join(heroes_folder, f"{hero_name}.png")
                if os.path.exists(hero_image_path):
                    hero_confidence = hero_confidence_overrides.get(hero_name.lower(), default_confidence)
                    heroes_data.append((hero_name, hero_image_path, hero_confidence))

            if not heroes_data:
                self.logger.warning("❌ Не найдено файлов изображений для героев из пакета")
                return None

            # Последовательный поиск героев с индивидуальным confidence
            for hero_name, hero_image_path, hero_confidence in heroes_data:
                self.logger.debug(f"🔎 Проверка {hero_name} (confidence: {hero_confidence})")

                found, position = self.check_image_on_screen(
                    hero_image_path,
                    confidence_threshold=hero_confidence,  # ✅ Используем индивидуальный confidence
                    window_title=self.window_title
                )

                if found:
                    self.logger.info(
                        f"✅ Найден герой {hero_name} на позиции {position} (confidence: {hero_confidence})")
                    return (hero_name, position, hero_image_path)
                else:
                    self.logger.debug(f"❌ Герой {hero_name} не найден (confidence: {hero_confidence})")

            self.logger.info("❌ Ни один герой из пакета не найден на экране")
            return None

        except Exception as e:
            self.logger.error(f"❌ Ошибка пакетного поиска: {e}")
            return None

    def execute_hero_selection_direct(self, hero_name, hero_position):
        """Прямое выполнение выбора героя с кешированием"""
        try:
            self.logger.info(f"🎯 Прямой выбор героя {hero_name}")

            # Клик по герою
            if not self.hardware_click(hero_position[0], hero_position[1], 'left'):
                self.logger.error("❌ Не удалось кликнуть по герою")
                return False

            time.sleep(0.3)

            # Поиск и клик по кнопке выбора
            found_btn, btn_pos = self.check_image_on_screen(
                self.pick_button_image,
                confidence_threshold=0.75,
                window_title=self.window_title
            )

            if found_btn:
                self.logger.info("🎯 Кнопка выбора найдена")
                self.gaming_actions.cache_selected_hero(hero_name)

                time.sleep(2)  # Пауза перед кликом

                if self.hardware_click(btn_pos[0], btn_pos[1], 'left'):
                    self.logger.info(f"✅ Герой {hero_name} выбран!")

                    # Дополнительная проверка кнопки выбора
                    confidence = 0.75
                    window_title = self.window_title
                    time.sleep(1)

                    for i in range(20):
                        found_btn, btn_pos = self.check_image_on_screen(
                            self.pick_button_image, confidence, window_title
                        )
                        if found_btn:
                            self.logger.debug(f"🔄 Повторный клик по кнопке выбора #{i + 1}/20")
                            time.sleep(0.25)
                            self.hardware_click(btn_pos[0], btn_pos[1], 'left')
                        else:
                            self.logger.info(f"✅ Кнопка выбора исчезла после {i + 1} попыток")
                            break
                    else:
                        self.logger.warning("⚠️ Достигнут лимит попыток (20), но кнопка все еще видна")

                    return True

                else:
                    self.logger.error("❌ Не удалось нажать кнопку выбора")
                    return False

            self.logger.warning("⚠️ Кнопка выбора не найдена")
            return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка прямого выбора героя: {e}")
            return False

    def check_reconnect_button(self, confidence=None, window_title=None):
        """
        Простая проверка наличия кнопки Reconnect на экране

        Returns:
            tuple: (found, position) где found - bool, position - координаты или None
        """
        try:
            reconnect_image = "imgs/reconnect.png"

            if not os.path.exists(reconnect_image):
                self.logger.debug(f"📁 Файл {reconnect_image} не найден, пропускаю проверку")
                return False, None

            if confidence is None:
                confidence = self.confidence

            if window_title is None:
                window_title = self.window_title

            # Проверяем наличие кнопки на экране
            found, position = self.check_image_on_screen(
                reconnect_image,
                confidence_threshold=confidence,
                window_title=window_title
            )

            if found:
                self.logger.info(f"⚠️ Кнопка Reconnect обнаружена на позиции {position}")
                return True, position
            else:
                self.logger.debug("✅ Кнопка Reconnect не найдена - соединение стабильно")
                return False, None

        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка проверки кнопки Reconnect: {e}")
            return False, None

    # Wrapper методы для совместимости
    def run_hero_pick(self, hero_image=None, timeout=180):
        """Wrapper for hardware hero pick"""
        return self.run_hero_pick_hardware(hero_image, timeout)

    def fight_on_river_hardware(self, *args, **kwargs):
        """Универсальный wrapper для вызова метода из gaming_actions"""
        return self.gaming_actions.fight_on_river_hardware(*args, **kwargs)

    def jungle_farm_hardware(self, *args, **kwargs):
        """Wrapper для вызова метода из gaming_actions"""
        return self.gaming_actions.jungle_farm_hardware(*args, **kwargs)

    def select_neutral_item(self, *args, **kwargs):
        """Wrapper для выбора нейтрального предмета"""
        return self.gaming_actions.select_neutral_item(*args, **kwargs)

    def observe_hero(self, *args, **kwargs):
        """Wrapper для наблюдения за героем"""
        return self.gaming_actions.observe_hero(*args, **kwargs)

    def upgrade_talents(self, *args, **kwargs):
        """Wrapper для прокачки талантов"""
        return self.gaming_actions.upgrade_talents(*args, **kwargs)

    def execute_winning_strategy(self, *args, **kwargs):
        """Wrapper для стратегии победы"""
        return self.gaming_actions.execute_winning_strategy(*args, **kwargs)

    def create_party_with_multiple_invites(self, *args, **kwargs):
        """Wrapper для создания пати с множественными приглашениями"""
        return self.party_manager.create_party_with_multiple_invites(*args, **kwargs)

    def create_party(self, *args, **kwargs):
        """Wrapper для создания пати"""
        return self.party_manager.create_party(*args, **kwargs)

    def join_party(self, *args, **kwargs):
        """Wrapper для присоединения к пати"""
        return self.party_manager.join_party(*args, **kwargs)

    def leave_party(self, *args, **kwargs):
        """Wrapper для покидания пати"""
        return self.party_manager.leave_party(*args, **kwargs)

