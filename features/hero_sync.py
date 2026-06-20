# hero_sync.py
import time
import random
import threading
import os
import json
import socket
from core.connection_manager import GoogleSheetsManager


class HeroSynchronizer:
    """Класс для синхронизации с оптимизированным подключением"""

    def __init__(self, credentials_file="config/credentials.json", spreadsheet_name="PC_Sync_Status"):
        self.credentials_file = credentials_file
        self.spreadsheet_name = spreadsheet_name
        self.lock = threading.Lock()

        # Получаем постоянное подключение через менеджер
        self._connection = GoogleSheetsManager.get_connection(
            spreadsheet_name, credentials_file
        )

        self.client = self._connection['client']
        self.spreadsheet = self._connection['spreadsheet']
        self.worksheet = self._connection['worksheet']

        # Инициализируем заголовки только один раз
        self._initialize_headers()

        print(f"✅ Используется оптимизированное подключение к {spreadsheet_name}")

    def _initialize_headers(self):
        """Инициализация заголовков таблицы"""
        try:
            first_row = self.worksheet.row_values(1)
            if not first_row or first_row[0] != "Hero":
                headers = ["Hero", "Status", "Instance_ID", "Computer", "Timestamp", "Match_ID"]
                self.worksheet.update('A1:F1', [headers])
                print("✅ Заголовки таблицы PC_Sync_Status инициализированы")
        except Exception as e:
            print(f"❌ Ошибка инициализации заголовков: {e}")

    def _execute_with_retry(self, func, *args, **kwargs):
        """Выполнение запроса с повторными попытками и обновлением подключения"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                print(f"⚠️ Ошибка запроса (попытка {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    # Обновляем подключение при ошибке
                    print("🔄 Обновление подключения...")
                    self._connection = GoogleSheetsManager.refresh_connection(
                        self.spreadsheet_name, self.credentials_file
                    )
                    self.client = self._connection['client']
                    self.spreadsheet = self._connection['spreadsheet']
                    self.worksheet = self._connection['worksheet']

                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                else:
                    raise e

        raise RuntimeError("Неожиданное завершение retry цикла")

    def get_available_heroes_from_folder(self, heroes_folder, current_match_id):
        """Получить доступных героев для конкретного матча"""
        with self.lock:
            return self._execute_with_retry(self._get_heroes_internal, heroes_folder, current_match_id)

    def _get_heroes_internal(self, heroes_folder, current_match_id):
        """Внутренний метод получения героев с фильтрацией по матчу"""
        try:
            if not os.path.exists(heroes_folder):
                print(f"❌ Папка с героями не найдена: {heroes_folder}")
                return []

            # Получаем все PNG файлы из папки
            all_heroes = []
            for filename in os.listdir(heroes_folder):
                if filename.lower().endswith('.png'):
                    hero_name = os.path.splitext(filename)[0]
                    all_heroes.append(hero_name)

            # Получаем занятых героев ТОЛЬКО для текущего матча
            all_records = self.worksheet.get_all_records()
            taken_heroes = set()
            for record in all_records:
                if record.get('Status') == 'taken' and record.get('Match_ID') == current_match_id:
                    taken_heroes.add(record.get('Hero', ''))

            # Возвращаем доступных героев
            available_heroes = [hero for hero in all_heroes if hero not in taken_heroes]

            print(f"📁 Всего героев: {len(all_heroes)}, доступных для матча {current_match_id}: {len(available_heroes)}")
            if taken_heroes:
                print(f"🚫 Занятые герои в матче {current_match_id}: {list(taken_heroes)}")

            return available_heroes

        except Exception as e:
            print(f"❌ Ошибка получения доступных героев: {e}")
            return []

    def reserve_hero(self, hero_name, instance_id, computer_name, match_id):
        """Резервирование героя с оптимизированным подключением"""
        with self.lock:
            return self._execute_with_retry(self._reserve_hero_internal,
                                            hero_name, instance_id, computer_name, match_id)

    def _reserve_hero_internal(self, hero_name, instance_id, computer_name, match_id):
        """Внутренний метод резервирования с проверкой по матчу"""
        try:
            # Проверяем, не занят ли уже герой В ТЕКУЩЕМ МАТЧЕ
            all_records = self.worksheet.get_all_records()
            for record in all_records:
                if (record.get('Hero') == hero_name and
                        record.get('Status') == 'taken' and
                        record.get('Match_ID') == match_id):
                    print(f"❌ Герой {hero_name} уже занят в матче {match_id}")
                    return False

            # Добавляем запись о резервировании
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            new_row = [hero_name, 'taken', instance_id, computer_name, timestamp, match_id]

            self.worksheet.append_row(new_row)
            print(f"✅ Герой {hero_name} зарезервирован для экземпляра {instance_id} в матче {match_id}")
            return True

        except Exception as e:
            print(f"❌ Ошибка резервирования героя {hero_name}: {e}")
            return False

    def select_random_available_hero_from_folder(self, heroes_folder, instance_id, computer_name, match_id):
        """Выбрать случайного доступного героя из папки для конкретного матча"""
        max_attempts = 5

        for attempt in range(max_attempts):
            # Передаем match_id в метод получения героев
            available_heroes = self.get_available_heroes_from_folder(heroes_folder, match_id)

            if not available_heroes:
                print(f"❌ Нет доступных героев для матча {match_id} (попытка {attempt + 1}/{max_attempts})")
                time.sleep(random.uniform(1, 3))
                continue

            # Выбираем случайного героя
            selected_hero = random.choice(available_heroes)

            # Пытаемся зарезервировать
            if self.reserve_hero(selected_hero, instance_id, computer_name, match_id):
                print(f"🎯 Выбран герой {selected_hero} для матча {match_id}")
                return selected_hero

            print(f"⚠️ Не удалось зарезервировать {selected_hero}, повторная попытка...")
            time.sleep(random.uniform(0.5, 2))

        print(f"❌ Не удалось выбрать героя для матча {match_id} после {max_attempts} попыток")
        return None

    def clear_all_reservations(self):
        """Очистить все резервирования"""
        with self.lock:
            return self._execute_with_retry(self._clear_reservations_internal)

    def _clear_reservations_internal(self):
        """Внутренний метод очистки"""
        try:
            self.worksheet.clear()
            self._initialize_headers()
            print("✅ Все резервирования очищены")
        except Exception as e:
            print(f"❌ Ошибка очистки резервирований: {e}")

    # ========== ГИБРИДНАЯ СИНХРОНИЗАЦИЯ С ОПТИМИЗАЦИЕЙ ==========

    def get_battle_coordinates_hybrid(self, match_id, iteration, instance_id=None):
        """Гибридная синхронизация с оптимизированным подключением"""
        computer_name = socket.gethostname()

        if instance_id is None:
            instance_id = getattr(self, 'instance_id', '1')

        # Определяем роли
        is_global_master = self._is_master_instance_fixed(computer_name, instance_id)
        is_local_coordinator = str(instance_id) == "1"

        location_id = f"{match_id}_iter_{iteration}"

        print(
            f"🖥️ {computer_name}_{instance_id} - Глобальный мастер: "
            f"{is_global_master}, Локальный координатор: {is_local_coordinator}")

        if is_local_coordinator:
            if is_global_master:
                coordinates = self._execute_with_retry(self._generate_and_save_coordinates,
                                                       location_id, iteration)
            else:
                coordinates = self._execute_with_retry(self._wait_and_read_coordinates, location_id, 30)

            self._save_local_coordinates(computer_name, iteration, coordinates)
            return coordinates
        else:
            return self._read_local_coordinates(computer_name, iteration, timeout=35)

    def _save_local_coordinates(self, computer_name, iteration, coordinates):
        """Сохранить координаты в локальный файл"""
        try:
            local_file = f"battle_coords_{computer_name}.json"

            # Читаем существующие данные
            if os.path.exists(local_file):
                with open(local_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {}

            # Добавляем новые координаты
            data[f"iter_{iteration}"] = {
                "coordinates": coordinates,
                "timestamp": time.time()
            }

            # Сохраняем
            with open(local_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"💾 Координаты сохранены локально: {coordinates['name']}")

        except Exception as e:
            print(f"❌ Ошибка сохранения локальных координат: {e}")

    def _read_local_coordinates(self, computer_name, iteration, timeout=35):
        """Читать координаты из локального файла"""
        local_file = f"battle_coords_{computer_name}.json"
        start_time = time.time()

        print(f"📂 ЛОКАЛЬНЫЙ СЛЕЙВ: Ожидание координат для итерации {iteration}")

        while time.time() - start_time < timeout:
            try:
                if os.path.exists(local_file):
                    with open(local_file, 'r') as f:
                        data = json.load(f)

                    key = f"iter_{iteration}"
                    if key in data:
                        coordinates = data[key]["coordinates"]
                        print(f"📂 ЛОКАЛЬНЫЙ СЛЕЙВ: ✅ Найдены координаты - {coordinates['name']}")
                        return coordinates

                # Файл не найден или нет данных
                remaining_time = timeout - (time.time() - start_time)
                print(f"📂 ЛОКАЛЬНЫЙ СЛЕЙВ: Ожидание файла... (осталось {remaining_time:.1f}с)")
                time.sleep(2)

            except Exception as e:
                print(f"❌ ЛОКАЛЬНЫЙ СЛЕЙВ: Ошибка чтения файла: {e}")
                time.sleep(2)

        # Таймаут
        print(f"⚠️ ЛОКАЛЬНЫЙ СЛЕЙВ: Таймаут, использую fallback")
        return {"x": 130, "y": 850, "name": "Local Fallback"}

    def get_or_set_winning_side(self, match_id):
        """Определить победившую сторону с оптимизированным подключением"""
        return self._execute_with_retry(self._get_winning_side_internal, match_id)

    def _get_winning_side_internal(self, match_id, selection_mode="alternating"):
        """
        Внутренний метод определения победившей стороны

        Args:
            match_id: ID матча
            selection_mode: "random" - случайный выбор, "alternating" - по очереди
        """

        computer_name = socket.gethostname()
        is_master = self._is_master_instance_fixed(computer_name, "1")
        winning_side_id = f"{match_id}_winning_side"

        try:
            # Ищем существующий выбор
            records = self.worksheet.get_all_records()
            for record in records:
                if (record.get('Hero') == winning_side_id and
                        record.get('Status') == "=== WINNING_SIDE ==="):
                    winning_side = record.get('Match_ID', 'dire')
                    print(f"🏆 Найдена победившая сторона: {winning_side}")
                    return winning_side

            # Если мастер - выбираем
            if is_master:
                if selection_mode == "random":
                    winning_side = self._select_random_side()
                elif selection_mode == "alternating":
                    winning_side = self._select_alternating_side(records)
                else:
                    print(f"⚠️ Неизвестный режим выбора: {selection_mode}, используем случайный")
                    winning_side = self._select_random_side()

                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                self.worksheet.append_row([
                    winning_side_id,
                    "=== WINNING_SIDE ===",
                    "1",
                    computer_name,
                    current_time,
                    winning_side,
                    selection_mode
                ])

                print(f"👑 МАСТЕР выбрал победившую сторону: {winning_side} (режим: {selection_mode})")
                return winning_side
            else:
                print(f"👥 СЛЕЙВ ждет выбора победившей стороны...")
                return self._wait_for_winning_side(winning_side_id)

        except Exception as e:
            print(f"❌ Ошибка определения победившей стороны: {e}")
            return "dire"

    def _select_random_side(self):
        """Случайный выбор стороны"""
        return random.choice(["dire", "radiant"])

    def _select_alternating_side(self, records):
        """Выбор стороны по очереди"""
        try:
            # Ищем последний выбор победившей стороны
            last_winning_side = None
            winning_side_records = []

            for record in records:
                if (record.get('Status') == "=== WINNING_SIDE ===" and
                        record.get('Match_ID') in ['dire', 'radiant']):
                    winning_side_records.append({
                        'side': record.get('Match_ID'),
                        'time': record.get('Time', ''),
                        'hero': record.get('Hero', '')
                    })

            if winning_side_records:
                # Сортируем по времени, чтобы найти последний
                winning_side_records.sort(key=lambda x: x['time'], reverse=True)
                last_winning_side = winning_side_records[0]['side']
                print(f"📊 Последняя победившая сторона: {last_winning_side}")

            # Выбираем противоположную сторону
            if last_winning_side == "dire":
                next_side = "radiant"
            elif last_winning_side == "radiant":
                next_side = "dire"
            else:
                # Если нет предыдущих записей, начинаем с radiant
                next_side = "radiant"
                print("📊 Нет предыдущих записей, начинаем с radiant")

            print(f"🔄 Чередование: {last_winning_side} → {next_side}")
            return next_side

        except Exception as e:
            print(f"❌ Ошибка при чередовании сторон: {e}")
            print("🎲 Используем случайный выбор как fallback")
            return self._select_random_side()

    def _wait_for_winning_side(self, winning_side_id, timeout=30):
        """Ожидание выбора победившей стороны от мастера"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                records = self.worksheet.get_all_records()
                for record in records:
                    if (record.get('Hero') == winning_side_id and
                            record.get('Status') == "=== WINNING_SIDE ==="):
                        winning_side = record.get('Match_ID', 'dire')
                        print(f"👥 СЛЕЙВ получил победившую сторону: {winning_side}")
                        return winning_side

                time.sleep(2)
            except Exception as e:
                print(f"❌ Ошибка ожидания: {e}")
                time.sleep(2)

        print(f"⚠️ Таймаут ожидания, использую fallback: dire")
        return "dire"

    # ========== МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ==========

    def get_battle_coordinates_master_slave(self, match_id, iteration, instance_id=None):
        """УСТАРЕВШИЙ: Используйте get_battle_coordinates_hybrid"""
        print("⚠️ Используется устаревший метод get_battle_coordinates_master_slave")
        print("🔄 Переключение на гибридную синхронизацию...")
        return self.get_battle_coordinates_hybrid(match_id, iteration, instance_id)

    def _is_master_instance_fixed(self, computer_name, instance_id):
        """Только первый экземпляр на главном ПК - глобальный мастер"""
        MASTER_COMPUTER = "YOUR-PC-NAME"  # Замените на имя вашего главного ПК
        MASTER_INSTANCE = "1"

        is_master = (computer_name == MASTER_COMPUTER and str(instance_id) == MASTER_INSTANCE)

        print(f"👑 Глобальный мастер: {MASTER_COMPUTER}_{MASTER_INSTANCE}")
        print(f"🎯 {computer_name}_{instance_id}: {'ГЛОБАЛЬНЫЙ МАСТЕР' if is_master else 'НЕ МАСТЕР'}")

        return is_master

    def _generate_and_save_coordinates(self, location_id, iteration):
        """Мастер генерирует и сохраняет координаты с оптимизированным подключением"""
        print(f"👑 МАСТЕР: Генерирую координаты для {location_id}")

        battle_locations = [
            {"x": 121, "y": 833, "name": "Mid 2"},
            {"x": 130, "y": 850, "name": "Mid Original"},
            {"x": 133, "y": 839, "name": "Bot Rune"},
            {"x": 195, "y": 890, "name": "Bot Lane Left Jungle"},
            {"x": 206, "y": 893, "name": "Bot Lane"},
            {"x": 58, "y": 768, "name": "Top Lane Jungle"},
            {"x": 49, "y": 762, "name": "Top Lane"},
            {"x": 36, "y": 769, "name": "Top Lane near lotus"},
            {"x": 74, "y": 777, "name": "Top Lane deeper jungle"},
            {"x": 178, "y": 865, "name": "Bot Lane near Roshan"}
        ]

        # Проверяем существующие координаты
        try:
            records = self.worksheet.get_all_records()
            for record in records:
                if (record.get('Hero') == location_id and
                        record.get('Status') == "=== BATTLE_LOCATION ==="):
                    location_data = {
                        'name': record.get('Match_ID', 'Unknown'),
                        'x': int(record.get('Instance_ID', 130)),
                        'y': int(record.get('Computer', 850))
                    }
                    print(f"👑 МАСТЕР: Координаты уже существуют - {location_data['name']}")
                    return location_data
        except Exception as e:
            print(f"⚠️ Ошибка проверки существующих координат: {e}")

        # Генерируем новые координаты
        selected_location = random.choice(battle_locations)

        # Записываем в правильном порядке колонок
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                self.worksheet.append_row([
                    location_id,  # Hero
                    "=== BATTLE_LOCATION ===",  # Status
                    str(selected_location["x"]),  # Instance_ID (X координата)
                    str(selected_location["y"]),  # Computer (Y координата)
                    current_time,  # Timestamp
                    selected_location["name"],  # Match_ID (название локации)
                    ""  # Match_Start (пустое)
                ])

                print(f"👑 МАСТЕР: Координаты сохранены - {selected_location['name']}")
                return selected_location

            except Exception as e:
                print(f"❌ МАСТЕР: Ошибка сохранения (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)

        # Fallback
        print(f"⚠️ МАСТЕР: Использую fallback координаты")
        return {"x": 130, "y": 850, "name": "Mid Original (Fallback)"}

    def _wait_and_read_coordinates(self, location_id, timeout=30):
        """Слейвы ждут и читают координаты от мастера"""
        print(f"👥 СЛЕЙВ: Ожидание координат для {location_id}")

        start_time = time.time()
        check_interval = 2

        while time.time() - start_time < timeout:
            try:
                records = self.worksheet.get_all_records()

                for record in records:
                    hero = record.get('Hero', '')
                    status = record.get('Status', '')

                    if (hero == location_id and status == "=== BATTLE_LOCATION ==="):
                        location_data = {
                            'name': record.get('Match_ID', 'Unknown'),
                            'x': int(record.get('Instance_ID', 130)),
                            'y': int(record.get('Computer', 850))
                        }

                        print(f"👥 СЛЕЙВ: ✅ НАЙДЕНЫ координаты - {location_data['name']}")
                        return location_data

                # Координаты не найдены
                remaining_time = timeout - (time.time() - start_time)
                print(f"👥 СЛЕЙВ: ❌ Координаты для '{location_id}' не найдены")
                print(f"👥 СЛЕЙВ: Ожидание... (осталось {remaining_time:.1f}с)")
                time.sleep(check_interval)

            except Exception as e:
                print(f"❌ СЛЕЙВ: Ошибка чтения координат: {e}")
                time.sleep(check_interval)

        # Таймаут
        print(f"⚠️ СЛЕЙВ: Таймаут ожидания координат для '{location_id}'")
        return {"x": 130, "y": 850, "name": "Mid Original (Timeout Fallback)"}