import time
import random
import os
import yaml
import win32api
import json

class GamingActions:
    """Класс для игровых действий в Dota 2"""

    def __init__(self, prepare_instance):
        """
        Инициализация с экземпляром PrepareMatchmaking

        Args:
            prepare_instance: Экземпляр класса PrepareMatchmaking
        """
        self.prepare = prepare_instance
        self.logger = prepare_instance.logger
        self.cached_winning_side = None
        self.cached_match_id = None

        self.hero_spell_config = self._load_hero_spell_config()

        self._current_hero_name = None

    def _load_hero_spell_config(self):
        """Загрузить конфигурацию исключений способностей для героев"""
        config_path = "config/hero_spell_config.json"

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(
                    f"✅ Загружена конфигурация способностей для {len(config.get('spell_exclusions', {}))} героев")
                return config
            else:
                self.logger.warning(f"⚠️ Файл конфигурации {config_path} не найден, исключения не будут применяться")
                return {"spell_exclusions": {}}
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки конфигурации способностей: {e}")
            return {"spell_exclusions": {}}

    def select_neutral_item(self, iteration=None):
        """Выбор нейтрального предмета каждые 5 итераций"""
        try:

            self.logger.info(f"🎁 Выбор нейтрального предмета (итерация {iteration})")

            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна для выбора предмета")
                return False

            window_x, window_y, _, _ = window_coords

            # 1. Клик по фиксированной координате (открытие меню)
            menu_coords = (1141, 835)
            click_x = window_x + menu_coords[0]
            click_y = window_y + menu_coords[1]
            self.logger.info(f"🖱️ Открытие меню нейтральных предметов: {menu_coords}")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.4)

            # 2. Клик по случайной из первых 4 координат (выбор слота)
            slot_coords = [
                (1031, 593),
                (1024, 638),
                (1035, 691),
                (1027, 735)
            ]
            selected_slot = random.choice(slot_coords)
            click_x = window_x + selected_slot[0]
            click_y = window_y + selected_slot[1]
            self.logger.info(f"🎯 Выбор слота предмета: {selected_slot}")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.2)

            # 3. Клик по случайной из вторых 4 координат (подтверждение)
            confirm_coords = [
                (1218, 586),
                (1220, 635),
                (1225, 686),
                (1226, 738)
            ]
            selected_confirm = random.choice(confirm_coords)
            click_x = window_x + selected_confirm[0]
            click_y = window_y + selected_confirm[1]
            self.logger.info(f"✅ Подтверждение выбора: {selected_confirm}")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.3)

            self.logger.info("🎁 Нейтральный предмет успешно выбран")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка выбора нейтрального предмета: {e}")
            return False

    def observe_hero(self):
        """Наблюдение за героем (клики для фокуса камеры)"""
        try:
            self.logger.info("👁️ Наблюдение за героем")

            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна для наблюдения")
                return False

            window_x, window_y, _, _ = window_coords

            # Два клика по координате (519, 882) - фокус на герое
            focus_coords = (519, 882)
            for click_num in range(2):
                click_x = window_x + focus_coords[0]
                click_y = window_y + focus_coords[1]
                self.logger.info(f"🖱️ Фокус на герое {click_num + 1}/2 по coordinate {focus_coords}")
                self.prepare.hardware_click(click_x, click_y, 'left')
                time.sleep(0.1)

            # Финальный клик по координате (807, 485) - центрирование камеры
            center_coords = (807, 485)
            click_x = window_x + center_coords[0] + random.randint(-80, 80)
            click_y = window_y + center_coords[1] + random.randint(-80, 80)
            self.logger.info(f"🎯 Центрирование камеры по координате {center_coords}")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.2)

            self.logger.info("👁️ Наблюдение за героем завершено")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка наблюдения за героем: {e}")
            return False

    def upgrade_talents(self):
        """Прокачка талантов героя"""
        try:
            self.logger.info("🌟 Прокачка талантов - начало")

            # Нажимаем кнопку U (открытие меню талантов)
            self.prepare.hardware_key_press('u')
            time.sleep(0.2)

            # Случайный выбор между талантами 1 и 2
            talent_key = random.choice(['1', '2'])
            self.logger.info(f"🎲 Выбран талант: кнопка {talent_key}")
            self.prepare.hardware_key_press(talent_key)
            time.sleep(0.2)

            self.logger.info("🌟 Прокачка талантов завершена")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка прокачки талантов: {e}")
            return False

    def fight_on_river_hardware(self, timeout=180, iteration=None):
        """Fight on river with team-based alternating attacks"""
        self.logger.info("=" * 60)
        self.logger.info(f"🎮 DOTA 2 ДРАКА НА РЕКЕ - ИТЕРАЦИЯ {iteration if iteration else 'N/A'}")
        self.logger.info("=" * 60)

        from features.hero_sync import HeroSynchronizer

        game_loaded = self.prepare.wait_for_game_loading(timeout=timeout)

        if game_loaded:
            try:
                instance_id = getattr(self.prepare, 'instance_id', '1')

                if iteration is None:
                    iteration = 1

                # Определяем команду текущего экземпляра
                my_team, _ = self._get_cached_or_detect_team()

                # Определяем какая команда атакует в этой итерации
                if iteration % 2 == 1:
                    attacking_team = "radiant"  # Нечетные итерации - атакует Radiant
                    team_description = "СВЕТ атакует, ТЬМА движется"
                else:
                    attacking_team = "dire"  # Четные итерации - атакует Dire
                    team_description = "ТЬМА атакует, СВЕТ движется"

                # Определяем мое действие
                should_attack = (my_team == attacking_team)

                self.logger.info(f"👤 Моя команда: {my_team.upper()}")
                self.logger.info(f"🎯 Итерация {iteration}: {team_description}")

                if should_attack:
                    self.logger.info("🗡️ МОЕ ДЕЙСТВИЕ: АТАКА (Shift+ПКМ → Shift+A)")
                else:
                    self.logger.info("🏃 МОЕ ДЕЙСТВИЕ: ДВИЖЕНИЕ (Shift+ПКМ)")

                # Получаем координаты боя
                sync = HeroSynchronizer()

                current_time = int(time.time())
                match_interval = 30 * 60
                match_time_slot = current_time // match_interval
                base_match_id = f"match_{match_time_slot}"

                battle_location = sync.get_battle_coordinates_hybrid(
                    base_match_id,
                    iteration,
                    instance_id=instance_id
                )

                self.logger.info(f"🎯 Позиция боя: {battle_location['name']}")

                # Выполняем боевые действия
                self._execute_team_battle_actions(battle_location, should_attack, my_team, attacking_team, iteration)

            except Exception as e:
                self.logger.error(f"❌ Ошибка выполнения боя на реке: {e}")

            return "unknown", 'unknown'
        else:
            self.logger.error("❌ Не удалось дождаться загрузки игры")
            return "unknown", None

    def _execute_team_battle_actions(self, battle_location, should_attack, my_team, attacking_team, iteration):
        """Выполнить боевые действия на основе команды"""
        try:
            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна")
                return False

            window_x, window_y, _, _ = window_coords

            # Дополнительные клики (скан и глиф) - только для атакующей команды
            if should_attack:
                self._execute_special_clicks(window_x, window_y, battle_location, iteration)

            # Основные боевые координаты с рандомизацией
            click_x = window_x + battle_location["x"] + random.randint(-1, 1)
            click_y = window_y + battle_location["y"] + random.randint(-1, 1)


            if should_attack:
                # Атакующая команда: позиция + атака
                self.logger.info(f"🗡️ КОМАНДА {my_team.upper()} АТАКУЕТ в {battle_location['name']}")

                # Телепорт к зоне файта
                tp_x = click_x + random.randint(-10, 10)
                tp_y = click_y + random.randint(-10, 10)

                self.prepare.hardware_key_press('shift+t')
                self.prepare.hardware_click(tp_x, tp_y, 'left')

                # Перемещение камеры к зоне файта
                self.prepare.hardware_click(click_x, click_y, 'left')
                time.sleep(random.uniform(0.05, 0.1))

                for _ in range(random.randint(1, 2)):
                    # Дополнительный клик по координатам 800, 450 с рандомизацией ±10
                    target_x = window_x + 801 + random.randint(-30, 30)
                    target_y = window_y + 479 + random.randint(-30, 30)
                    self.prepare.hardware_input.send_shift_right_click(target_x, target_y)
                    time.sleep(random.uniform(0.05, 0.1))

                self._activate_random_abilities()
                # Shift+A для атаки
                for _ in range(random.randint(2, 3)):
                    self.prepare.hardware_key_press('shift+a')
                self.logger.info("✅ Команда атаки: Shift+A")
                chat_wheel_success = self.chat_wheel_support(chance=0.15)
                if chat_wheel_success:
                    self.logger.debug("✅ Колесо чата обработано во время river fight")

            else:
                # Не атакующая команда: только движение
                self.logger.info(f"🏃 КОМАНДА {my_team.upper()} ДВИЖЕТСЯ к {battle_location['name']}")

                self.prepare.hardware_click(click_x, click_y, 'left')
                time.sleep(random.uniform(0.05, 0.1))

                for _ in range(random.randint(2, 4)):
                    # Дополнительный клик по координатам 800, 450 с рандомизацией ±10
                    target_x = window_x + 801 + random.randint(-30, 30)
                    target_y = window_y + 479 + random.randint(-30, 30)
                    self.prepare.hardware_input.send_shift_right_click(target_x, target_y)
                    time.sleep(random.uniform(0.05, 0.1))

                chat_wheel_success = self.chat_wheel_support(chance=0.10)
                if chat_wheel_success:
                    self.logger.debug("✅ Колесо чата обработано во время river fight")

                self.logger.info("✅ Команда движения: Shift+ПКМ")

            # Наблюдение за героем
            self._press_shift_combinations()
            self._perform_post_farming_actions()



            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка выполнения боевых действий: {e}")
            return False

    def _execute_special_clicks(self, window_x, window_y, battle_location, iteration):
        """Выполнить дополнительные клики (скан и глиф) для атакующей команды"""
        try:

            # Клик скан (каждые 3-5 итераций)
            if iteration and iteration % random.randint(3, 5) == 0:
                scan_x = window_x + 267
                scan_y = window_y + 880
                self.logger.info(f"🔧 Дополнительный клик скан (итерация {iteration}): ({267}, {880})")
                self.prepare.hardware_click(scan_x, scan_y, 'left')
                time.sleep(random.uniform(0.05, 0.1))
                click_x = window_x + battle_location["x"] + random.randint(-10, 10)
                click_y = window_y + battle_location["y"] + random.randint(-10, 10)
                self.prepare.hardware_click(click_x, click_y, 'left')
                time.sleep(random.uniform(0.05, 0.1))


            # Клик глиф (каждые 3-5 итераций)
            if iteration and iteration % random.randint(3, 5) == 0:
                glyph_x = window_x + 267
                glyph_y = window_y + 920
                self.logger.info(f"🔧 Дополнительный клик глиф (итерация {iteration}): ({267}, {920})")
                self.prepare.hardware_click(glyph_x, glyph_y, 'left')
                time.sleep(random.uniform(0.05, 0.1))

        except Exception as e:
            self.logger.debug(f"⚠️ Ошибка дополнительных кликов: {e}")

    def jungle_farm_hardware(self, timeout=120, iteration=None):
        """Jungle farming with skill upgrade and neutral item selection"""
        self.logger.info("=" * 60)
        self.logger.info("🌲 DOTA 2 ФАРМ ЛЕСА - ЗАПУСК")
        self.logger.info("=" * 60)

        game_loaded = self.prepare.wait_for_game_loading(timeout=timeout)

        if game_loaded:
            # Проверяем кэшированную команду
            team, position = self._get_cached_or_detect_team()

            if team in ["radiant", "dire"]:

                instance_id = getattr(self.prepare, 'instance_id', '1')
                self.logger.info(f"🆔 Instance ID: {instance_id}")

                camps_list = self._get_jungle_camp_coordinates(team, instance_id)

                if camps_list:

                    success_count = 0
                    for i, camp_data in enumerate(camps_list, 1):

                        success = self._execute_jungle_farming(camp_data)

                        if success:
                            success_count += 1
                            self.logger.info(f"✅ Кемп {camp_data['name']} выполнен ({success_count}/{len(camps_list)})")
                        else:
                            self.logger.warning(f"⚠️ Проблемы при фарме кемпа {camp_data['name']}")

                        # Небольшая задержка между кемпами
                        if i < len(camps_list):
                            time.sleep(random.uniform(0.5, 1))

                    # После фарма всех кемпов - дополнительные действия
                    self._perform_post_farming_actions(len(camps_list))

                    # Выбор нейтрального предмета
                    self.select_neutral_item(iteration)

                    self._press_shift_combinations()

                    self.logger.info(f"🏁 Фарм завершен: {success_count}/{len(camps_list)} кемпов успешно")
                else:
                    self.logger.error(f"❌ Не удалось определить кемпы для экземпляра {instance_id}")

                return team, position
            else:
                self.logger.warning(f"Неизвестная команда: {team}")
                return team, position
        else:
            self.logger.error("❌ Не удалось дождаться загрузки игры")
            return "unknown", None

    def _get_cached_or_detect_team(self):
        """
        Получить команду из кэша или определить новую
        """
        # Проверяем кэшированное значение
        if hasattr(self, '_cached_team') and hasattr(self, '_cached_position'):
            team = self._cached_team
            position = self._cached_position
            self.logger.info(f"📋 Используется кэшированная команда: {team.upper()}")
            return team, position

        # Если кэша нет - определяем команду
        self.logger.info("🔍 Первое определение команды...")
        team, position = self.prepare.check_team()

        # Сохраняем в кэш
        if team in ["radiant", "dire"]:
            self._cached_team = team
            self._cached_position = position
            self.logger.info(f"💾 Команда {team.upper()} сохранена в кэш")

        return team, position

    def clear_team_cache(self):
        """
        Очистить кэш команды (для принудительного переопределения)
        """
        if hasattr(self, '_cached_team'):
            delattr(self, '_cached_team')
        if hasattr(self, '_cached_position'):
            delattr(self, '_cached_position')
        self.logger.info("🗑️ Кэш команды очищен")

    def _perform_post_farming_actions(self, camps_count=3):
        """Выполнить действия после фарма (наблюдение, таланты и прокачка)"""
        if camps_count < 3:
            return

        self.logger.info("🔧 Выполнение действий после фарма")

        # Прокачка талантов (перед скиллами)
        self.upgrade_talents()

        # Прокачка навыков (после талантов)
        self.logger.info("🆙 Прокачка навыков...")
        try:
            skill_result = self.prepare.skill_upgrade()
            if skill_result[0]:
                self.logger.info(f"🆙 Навык успешно прокачан в позиции {skill_result[1]}")
            else:
                self.logger.debug("💡 Индикаторы прокачки навыков не найдены")
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка при прокачке навыков: {e}")

        # Наблюдение за героем
        self.observe_hero()

    def _get_jungle_camp_coordinates(self, team, instance_id, total_instances=None):
        """Получить случайные батчи кемпов из общего пула"""
        try:
            config_file = "config/jungle_camps.yaml"

            if not os.path.exists(config_file):
                self.logger.error(f"❌ Файл конфигурации кемпов не найден: {config_file}")
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                camps_config = yaml.safe_load(f)

            team_camps = camps_config.get(f"{team}_camps", {})

            if not team_camps:
                self.logger.error(f"❌ Нет конфигурации для команды {team}")
                return None

            # Получаем все доступные батчи (группы кемпов)
            available_batches = list(team_camps.keys())  # ["1", "2", "3", "4", "5", "6"]

            if not available_batches:
                self.logger.error(f"❌ Нет доступных батчей для команды {team}")
                return None

            # Определяем количество батчей для экземпляра
            if total_instances:
                batches_per_instance = max(1, len(available_batches) // total_instances)
            else:
                batches_per_instance = max(1, len(available_batches) // 6)  # По умолчанию на 6 экземпляров

            # Случайно выбираем батчи для этого экземпляра
            selected_batches = random.sample(available_batches,
                                             min(batches_per_instance, len(available_batches)))

            # Собираем все кемпы из выбранных батчей
            selected_camps = []
            for batch_id in selected_batches:
                batch_camps = team_camps[batch_id]
                selected_camps.extend(batch_camps)

            # Преобразуем координаты
            for camp in selected_camps:
                if camp.get("click"):
                    camp["click"] = tuple(camp["click"])
                if camp.get("farm"):
                    camp["farm"] = tuple(camp["farm"])

            self.logger.info(
                f"🎯 Экземпляр {instance_id} получил батчи {selected_batches} ({len(selected_camps)} кемпов)")

            return selected_camps

        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки конфигурации кемпов: {e}")
            return None

    def _activate_random_abilities(self):
        """Активация случайных способностей с учетом исключений"""
        try:
            # Получаем кешированного героя из PrepareMatchmaking
            current_hero = self._current_hero_name

            # Базовые способности
            all_abilities = ['q', 'w', 'e', 'r']

            # Загружаем конфигурацию исключений
            spell_exclusions = self.hero_spell_config.get('spell_exclusions', {})

            # Фильтруем способности
            if current_hero and current_hero in spell_exclusions:
                excluded_spells = spell_exclusions[current_hero]
                available_abilities = [ability for ability in all_abilities if ability not in excluded_spells]
                self.logger.info(
                    f"🚫 Для героя {current_hero.upper()} исключены способности: "
                    f"{[spell.upper() for spell in excluded_spells]}")
            else:
                available_abilities = all_abilities
                if current_hero:
                    self.logger.debug(f"🎯 Для героя {current_hero.upper()} используются все способности")
                else:
                    self.logger.warning("⚠️ Герой не кеширован, используются все способности")

            if not available_abilities:
                self.logger.warning("⚠️ Нет доступных способностей для активации")
                return

            # Случайное количество способностей для активации
            max_abilities_to_use = min(len(available_abilities), 4)
            min_abilities_to_use = min(2, max_abilities_to_use)

            num_abilities = random.randint(min_abilities_to_use, max_abilities_to_use)

            # Выбираем случайные способности
            selected_abilities = random.sample(available_abilities, num_abilities)
            random.shuffle(selected_abilities)

            abilities_str = [f'Shift+{ability.upper()}' for ability in selected_abilities]
            self.logger.info(f"⚡ Активация способностей: {' → '.join(abilities_str)}")

            for i, ability in enumerate(selected_abilities):
                combination = f"shift+{ability}"

                try:
                    success = self.prepare.hardware_key_press(combination)
                    if success:
                        self.logger.debug(f"✅ {combination.upper()} активировано")
                    else:
                        self.logger.warning(f"⚠️ Ошибка активации {combination.upper()}")

                    if i < len(selected_abilities) - 1:
                        time.sleep(random.uniform(0.05, 0.1))

                except Exception as e:
                    self.logger.warning(f"⚠️ Исключение при активации {combination.upper()}: {e}")

            time.sleep(random.uniform(0.05, 0.1))
            self.logger.info("💫 Активация способностей завершена")

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка активации способностей: {e}")

    def _execute_jungle_farming(self, camp_data):
        """Выполнить фарм конкретного кемпа"""
        try:
            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("Не удалось получить координаты окна")
                return False

            window_x, window_y, _, _ = window_coords

            # Проверяем специальные случаи
            if camp_data.get("special"):
                self.logger.info("🔧 Специальный кемп - выполняется только A")
                # Для Radiant Camp 1.3 - только A без координат
                self.prepare.hardware_key_press('a')
                time.sleep(0.1)
                return True

            # Обычный кемп - выполняем клик
            if camp_data.get("click"):
                click_x = window_x + camp_data["click"][0]
                click_y = window_y + camp_data["click"][1]

                self.logger.info(f"🖱️ Клик для движения: ({camp_data['click'][0]}, {camp_data['click'][1]})")
                self.prepare.hardware_click(click_x, click_y, 'left')
                time.sleep(0.1)

            # Выполняем фарм (move_mouse + shift+A)
            if camp_data.get("farm"):
                # Получаем базовую позицию для фарма
                base_farm_x = window_x + camp_data["farm"][0]
                base_farm_y = window_y + camp_data["farm"][1]

                # Случайное смещение для фарма
                farm_x = base_farm_x + random.randint(-10, 10)
                farm_y = base_farm_y + random.randint(-10, 10)

                self.logger.info(f"⚔️ Фарм позиция: ({camp_data['farm'][0]}, {camp_data['farm'][1]})")

                # Случайное количество предварительных Shift+ПКМ (1-2 раза)
                shift_right_clicks = random.randint(1, 2)

                for i in range(shift_right_clicks):
                    try:
                        # Используем новый метод для Shift+ПКМ
                        success = self.prepare.hardware_input.send_shift_right_click(farm_x, farm_y)

                        if success:
                            pass
                        else:
                            self.logger.warning(f"⚠️ Ошибка выполнения Shift+ПКМ #{i + 1}")

                        # Случайная задержка между нажатиями
                        time.sleep(random.uniform(0.05, 0.15))

                    except Exception as e:
                        self.logger.warning(f"⚠️ Исключение при Shift+ПКМ #{i + 1}: {e}")

                if camp_data.get("is_skill", False):
                    self.logger.info("💫 Кемп с активацией способностей")
                    self._activate_random_abilities()
                else:
                    self.logger.debug("🗡️ Обычный кемп без способностей")

                # Небольшая пауза перед основным действием
                time.sleep(random.uniform(0.05, 0.15))

                # Нажимаем Shift+A через улучшенную систему
                self.prepare.hardware_key_press('shift+a')
                time.sleep(random.uniform(0.05, 0.1))

            # Дополнительная информация о типе кемпа
            camp_types = []
            if camp_data.get("is_line"):
                camp_types.append("🛡️ линейный")
            if camp_data.get("is_rune"):
                camp_types.append("💎 с руной")
            if camp_data.get("is_skill"):
                camp_types.append("💫 с способностями")
            if not camp_types:
                camp_types.append("🌲 лесной")

            self.logger.info(f"📋 Тип кемпа: {', '.join(camp_types)}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка выполнения фарма: {e}")
            return False

    def execute_winning_strategy(self, timeout=180, iteration=None):
        """Выполнение стратегии в зависимости от победившей стороны с проверкой конца игры"""
        self.logger.info("=" * 60)
        self.logger.info(f"🏆 ВЫПОЛНЕНИЕ СТРАТЕГИИ ПОБЕДЫ - ИТЕРАЦИЯ {iteration if iteration else 'N/A'}")
        self.logger.info("=" * 60)

        # ЕДИНСТВЕННАЯ НАЧАЛЬНАЯ ПРОВЕРКА
        game_ended = self.prepare.check_game_end()
        if game_ended:
            self.logger.info(f"🏆 Игра уже завершена! Выходим из стратегии: {game_ended}")
            return True, f"game_ended_{game_ended}"

        from features.hero_sync import HeroSynchronizer

        # Используем кэшированное определение команды
        team, position = self._get_cached_or_detect_team()

        if team in ["radiant", "dire"]:
            self.logger.info(f"🎮 Моя команда: {team.upper()}")

            # Получаем победившую сторону (проверяем только на первой итерации)
            try:
                current_time = int(time.time())
                match_interval = 30 * 60
                match_time_slot = current_time // match_interval
                base_match_id = f"match_{match_time_slot}"

                # Проверяем, нужно ли обновить кеш
                if (self.cached_winning_side is None or
                        self.cached_match_id != base_match_id or
                        iteration == 1):

                    self.logger.info("🔄 Определение победившей стороны...")
                    sync = HeroSynchronizer()
                    winning_side = sync.get_or_set_winning_side(base_match_id)

                    # Обновляем кеш
                    self.cached_winning_side = winning_side
                    self.cached_match_id = base_match_id

                    self.logger.info(f"💾 Кеширована победившая сторона: {winning_side.upper()}")
                else:
                    # Используем кешированное значение
                    winning_side = self.cached_winning_side
                    self.logger.info(f"📋 Используется кешированная сторона: {winning_side.upper()}")

                if team == winning_side:
                    # Моя команда побеждает - выполняем атакующую стратегию
                    self.logger.info("⚔️ Выполняю атакующую стратегию (моя команда побеждает)")
                    self._execute_winning_team_strategy(winning_side)
                else:
                    # Моя команда проигрывает - фармим лес
                    self.logger.info("🌲 Выполняю оборонительную стратегию (фарм леса)")
                    self._execute_losing_team_strategy(team)

                # ЕДИНСТВЕННАЯ ФИНАЛЬНАЯ ПРОВЕРКА
                final_game_ended = self.prepare.check_game_end()
                if final_game_ended:
                    self.logger.info(f"🏆 Игра завершена после выполнения стратегии: {final_game_ended}")
                    return True, f"game_ended_{final_game_ended}"

            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка определения стратегии: {e}")

                # ПРОВЕРКА ТОЛЬКО ПРИ ОШИБКЕ
                game_ended = self.prepare.check_game_end()
                if game_ended:
                    self.logger.info(f"🏆 Игра завершена во время ошибки: {game_ended}")
                    return True, f"game_ended_{game_ended}"

                # Fallback - фарм леса БЕЗ дополнительных проверок
                self.logger.info("🔄 Fallback: выполняю оборонительную стратегию")
                self._execute_losing_team_strategy()

            return team, position

        else:
            self.logger.error("❌ Не удалось дождаться загрузки игры")

            # ✅ ПРОВЕРКА ТОЛЬКО ПРИ ОШИБКЕ ЗАГРУЗКИ
            game_ended = self.prepare.check_game_end()
            if game_ended:
                self.logger.info(f"🏆 Игра завершена (ошибка загрузки): {game_ended}")
                return True, f"game_ended_{game_ended}"

            return "unknown", None

    def _execute_winning_team_strategy_with_checks(self, winning_side):
        """Стратегия для победившей команды с проверками конца игры"""
        # Выполняем существующую стратегию
        self._execute_winning_team_strategy(winning_side)
        return False

    def _execute_losing_team_strategy_with_checks(self):
        """Стратегия для проигравшей команды с проверками конца игры"""
        # Выполняем существующую стратегию
        self._execute_losing_team_strategy()
        return False

    def _execute_winning_team_strategy(self, winning_side):
        """Стратегия для победившей команды"""
        window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
        if not window_coords:
            self.logger.error("❌ Не удалось получить координаты окна")
            return

        window_x, window_y, _, _ = window_coords

        if winning_side == "dire":
            self.logger.info("⚫ Стратегия победы для DIRE")

            # 1. Клик левой кнопкой на (121, 829)
            click_x = window_x + 121
            click_y = window_y + 829
            self.logger.info("🖱️ Клик 1: (121, 829) левой кнопкой")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.3)

            # 2. Клик правой кнопкой на (818, 637)
            click_x = window_x + 818
            click_y = window_y + 637
            self.logger.info("🎯 Перемещение на (818, 637) и Shift+A")
            win32api.SetCursorPos((click_x, click_y))
            time.sleep(0.2)
            self.prepare.hardware_key_press('shift+a')

            # 3. Клик левой кнопкой на (50, 898)
            click_x = window_x + 50
            click_y = window_y + 898
            self.logger.info("🖱️ Клик 3: (50, 898) левой кнопкой")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.3)

            # 4. Перемещение мыши на (643, 654) и Shift+A
            mouse_x = window_x + 643
            mouse_y = window_y + 654
            self.logger.info("🎯 Перемещение на (643, 654) и Shift+A")
            win32api.SetCursorPos((mouse_x, mouse_y))
            time.sleep(0.2)
            self.prepare.hardware_key_press('shift+a')
            self.observe_hero()

        elif winning_side == "radiant":
            self.logger.info("⚪ Стратегия победы для RADIANT")

            # 1. Сбор на миду - клик левой кнопкой на (121, 829)
            click_x = window_x + 121
            click_y = window_y + 829
            self.logger.info("🖱️ Сбор на миду: (121, 829) левой кнопкой")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.3)

            # 2. Клик правой кнопкой на (818, 637)
            click_x = window_x + 818
            click_y = window_y + 637
            self.logger.info("🎯 Перемещение на (818, 637) и Shift+A")
            win32api.SetCursorPos((click_x, click_y))
            time.sleep(0.2)
            self.prepare.hardware_key_press('shift+a')

            # 3. Клик левой кнопкой на (199, 763)
            click_x = window_x + 199
            click_y = window_y + 763
            self.logger.info("🖱️ Клик 3: (199, 763) левой кнопкой")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.3)

            # 4. Перемещение мыши на (679, 664) и Shift+A
            mouse_x = window_x + 679
            mouse_y = window_y + 664
            self.logger.info("🎯 Перемещение на (679, 664) и Shift+A")
            win32api.SetCursorPos((mouse_x, mouse_y))
            time.sleep(0.2)
            self.prepare.hardware_key_press('shift+a')
            self.observe_hero()

    def _execute_losing_team_strategy(self, cached_team=None):
        """Стратегия для проигравшей команды - фарм леса с использованием кэшированной команды"""
        self.logger.info("🌲 Выполняю фарм леса (проигравшая команда)")

        # Используем кэшированное значение вместо повторной проверки
        if cached_team and cached_team in ["radiant", "dire"]:
            team = cached_team
            self.logger.info(f"📋 Используется кэшированная команда для фарма: {team.upper()}")
        else:
            # Только если кэша нет - проверяем заново
            self.logger.info("🔍 Определение команды для фарма (кэш недоступен)...")
            team, _ = self.prepare.check_team()

        if team in ["radiant", "dire"]:
            # Получаем instance_id и продолжаем с известной командой
            instance_id = getattr(self.prepare, 'instance_id', '1')
            camps_list = self._get_jungle_camp_coordinates(team, instance_id)

            if camps_list:
                jungle_camps = [camp for camp in camps_list if not camp.get('is_line', False)]

                # Логируем информацию о фильтрации
                total_camps = len(camps_list)
                jungle_camps_count = len(jungle_camps)
                line_camps_count = total_camps - jungle_camps_count

                if line_camps_count > 0:
                    self.logger.info(f"🚫 Исключено {line_camps_count} линейных кемпов из {total_camps}")

                self.logger.info(f"🌲 Выбрано {jungle_camps_count} лесных кемпов для фарма")

                if jungle_camps:
                    success_count = 0
                    for i, camp_data in enumerate(jungle_camps, 1):
                        self.logger.info(f"🔄 Фарм кемпа {i}/{len(jungle_camps)}: {camp_data['name']}")

                        success = self._execute_jungle_farming(camp_data)

                        if success:
                            success_count += 1

                        if i < len(jungle_camps):
                            time.sleep(1)

                    self.observe_hero()
                    self.logger.info(f"🏁 Фарм завершен: {success_count}/{len(jungle_camps)} лесных кемпов")
                else:
                    self.logger.warning("⚠️ Нет доступных лесных кемпов (все кемпы помечены как линейные)")
            else:
                self.logger.error(f"❌ Не удалось получить список кемпов для команды {team.upper()}")
        else:
            self.logger.error(f"❌ Неизвестная команда для фарма: {team}")

    def _press_shift_combinations(self):
        """Нажимает Shift+Z и затем Shift+случайное из (X,C,V)"""
        try:
            success_z = self.prepare.hardware_key_press('z')

            if success_z:
                pass
            else:
                self.logger.warning("⚠️ Ошибка выполнения Shift+Z")

            # Небольшая задержка между нажатиями
            time.sleep(random.uniform(0.03, 0.05))

            # Выбираем случайную клавишу из X, C, V
            random_keys = ['x', 'c', 'v']
            selected_key = random.choice(random_keys)

            shift_combination = f"{selected_key}"

            success_random = self.prepare.hardware_key_press(shift_combination)

            if success_random:
                pass
            else:
                self.logger.warning(f"⚠️ Ошибка выполнения {shift_combination.upper()}")

            if success_z and success_random:
                pass
            else:
                self.logger.warning("⚠️ Не все комбинации клавиш выполнены успешно")

        except Exception as e:
            self.logger.error(f"❌ Ошибка выполнения комбинаций клавиш: {e}")

    def cache_selected_hero(self, hero_name):
        """
        Сохранить имя выбранного героя в кеш

        Args:
            hero_name (str): Имя героя для кеширования
        """
        try:
            if hero_name and isinstance(hero_name, str):
                # Упрощенное кеширование без timestamp
                self._current_hero_name = hero_name.lower().strip()
                self.logger.info(f"💾 Герой кеширован: {hero_name}")
                return True
            else:
                self.logger.warning(f"⚠️ Некорректное имя героя для кеширования: {hero_name}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка кеширования героя: {e}")
            return False

    def get_cached_hero(self):
        """
        Получить имя кешированного героя

        Returns:
            str: Имя героя или None если кеш пуст
        """
        try:
            # Упрощенное получение из атрибута
            return getattr(self, '_current_hero_name', None)

        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка получения кешированного героя: {e}")
            return None

    def clear_hero_cache(self):
        """Очистить кеш героя"""
        try:
            # Упрощенная очистка без timestamp
            old_hero = self._current_hero_name
            self._current_hero_name = None

            if old_hero:
                self.logger.info(f"🗑️ Кеш героя очищен (был: {old_hero})")
            else:
                self.logger.debug("🗑️ Кеш героя уже был пуст")

        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка очистки кеша героя: {e}")

    def is_hero_cached(self):
        """
        Проверить, есть ли кешированный герой

        Returns:
            bool: True если герой кеширован
        """
        return hasattr(self, '_current_hero_name') and self._current_hero_name is not None

    def ward_placement_support(self, **kwargs):
        """Поддержка расстановки вардов для интеграции в другие функции"""

        try:
            # Импортируем функцию выполнения
            from actions.support_actions import execute_ward_placement, _is_local_master

            # Проверяем, является ли экземпляр локальным мастером
            if not _is_local_master(self.prepare):
                self.logger.debug("👥 Не локальный мастер - пропускаю расстановку вардов")
                return True

            # Выполняем расстановку вардов
            success = execute_ward_placement(self.prepare, **kwargs)

            if success:
                pass
            else:
                self.logger.warning("⚠️ Не удалось расставить варды во время боя")

            return success

        except Exception as e:
            self.logger.error(f"❌ Ошибка интеграции расстановки вардов: {e}")
            return False

    def chat_wheel_support(self, **kwargs):
        """Поддержка колеса чата для интеграции в боевые действия"""

        try:
            # Импортируем функцию выполнения
            from actions.communication_actions import execute_chat_wheel

            chance = kwargs.get('chance', 0.25)  # 25% шанс по умолчанию

            # Проверяем шанс активации
            if random.random() < chance:
                self.logger.info(f"🎡 Активация колеса чата во время боя (шанс: {chance * 100:.0f}%)")

                # Выполняем колесо чата с быстрыми настройками для боя
                success = execute_chat_wheel(self.prepare,
                                             hold_delay=0.05,
                                             click_delay=0.1,
                                             release_delay=0.05)

                if success:
                    self.logger.info("✅ Колесо чата использовано во время боя")
                else:
                    self.logger.warning("⚠️ Не удалось использовать колесо чата во время боя")

                return success
            else:
                self.logger.debug(f"🎲 Колесо чата пропущено во время боя (шанс: {chance * 100:.0f}%)")
                return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка интеграции колеса чата: {e}")
            return False
