# party_manager.py
import time
import socket


class PartyManager:
    """Класс для управления пати в Dota 2"""

    def __init__(self, prepare_instance):
        self.prepare = prepare_instance
        self.logger = prepare_instance.logger

    def create_party_with_multiple_invites(self, party_ids_list, timeout=30):
        """
        Создание пати и приглашение нескольких игроков (только для локального мастера)

        Args:
            party_ids_list (list): Список ID для приглашения
            timeout (int): Таймаут операции в секундах

        Returns:
            tuple: (success, data) - success: bool, data: str с информацией о результате
        """
        # Проверяем, является ли текущий экземпляр локальным мастером
        if not self._is_local_master():
            self.logger.info("👥 Не локальный мастер - пропускаю создание пати")
            return True, "not_local_master"

        self.logger.info("=" * 60)
        self.logger.info("👑 ЛОКАЛЬНЫЙ МАСТЕР: СОЗДАНИЕ ПАТИ И ПРИГЛАШЕНИЯ")
        self.logger.info("=" * 60)

        if not party_ids_list:
            self.logger.warning("⚠️ Список ID для приглашения пуст")
            return False, "empty_party_list"

        self.logger.info(f"📋 Планируется пригласить {len(party_ids_list)} игроков: {party_ids_list}")

        try:
            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна")
                return False, "window_coordinates_failed"

            window_x, window_y, _, _ = window_coords

            # Приглашаем каждого игрока из списка
            successful_invites = 0
            for i, party_id in enumerate(party_ids_list, 1):
                self.logger.info(f"👤 Приглашение {i}/{len(party_ids_list)}: {party_id}")

                if self._invite_single_player(window_x, window_y, party_id):
                    successful_invites += 1
                    self.logger.info(f"✅ Игрок {party_id} приглашен ({successful_invites}/{len(party_ids_list)})")
                else:
                    self.logger.warning(f"⚠️ Не удалось пригласить {party_id}")

                # Задержка между приглашениями
                if i < len(party_ids_list):
                    time.sleep(2)

            self.logger.info(f"🏁 Приглашения завершены: {successful_invites}/{len(party_ids_list)} успешно")

            if successful_invites > 0:
                return True, f"party_created_invites_{successful_invites}_{len(party_ids_list)}"
            else:
                return False, "no_successful_invites"

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания пати с приглашениями: {e}")
            return False, str(e)

    def _is_local_master(self):
        """Проверка, является ли текущий экземпляр локальным мастером"""
        try:
            computer_name = socket.gethostname()
            instance_id = getattr(self.prepare, 'instance_id', '1')

            # Локальный мастер = первый экземпляр на каждом ПК
            is_master = str(instance_id) == "1"

            self.logger.info(
                f"🖥️ {computer_name}_{instance_id}: {'ЛОКАЛЬНЫЙ МАСТЕР' if is_master else 'ЛОКАЛЬНЫЙ СЛЕЙВ'}")
            return is_master

        except Exception as e:
            self.logger.error(f"❌ Ошибка определения локального мастера: {e}")
            return False

    def _invite_single_player(self, window_x, window_y, party_id):
        """
        Приглашение одного игрока в пати

        Args:
            window_x, window_y: Координаты окна
            party_id: ID игрока для приглашения

        Returns:
            bool: True если приглашение отправлено успешно
        """
        try:
            # Шаг 0: Нажатие на (249, 70) - начальное действие
            self.logger.info(f"🖱️ Нчальное действие для {party_id}")
            click_x = window_x + 249
            click_y = window_y + 70
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Шаг 1: Нажатие на (295, 410) - открытие меню пати
            self.logger.info(f"🖱️ Открытие меню пати для {party_id}")
            click_x = window_x + 295
            click_y = window_y + 410
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Шаг 2: Нажатие на (808, 451) - кнопка приглашения
            self.logger.info(f"🖱️ Кнопка приглашения для {party_id}")
            click_x = window_x + 808
            click_y = window_y + 451
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Шаг 3: Ввод ID пати
            self.logger.info(f"⌨️ Ввод ID: {party_id}")
            if not self._input_party_id(party_id):
                return False

            # Шаг 4: Нажатие на (724, 558) - подтверждение
            self.logger.info(f"🖱️ Подтверждение приглашения для {party_id}")
            click_x = window_x + 724
            click_y = window_y + 558
            self.prepare.hardware_click(click_x, click_y, 'left')

            # Шаг 5: Ожидание 3 секунды
            self.logger.info("⏳ Ожидание 3 секунды...")
            time.sleep(3)

            # Шаг 6: Нажатие на (665, 208)
            click_x = window_x + 665
            click_y = window_y + 208
            self.prepare.hardware_click(click_x, click_y, 'left')

            # Шаг 7: Нажатие на (249, 70)
            click_x = window_x + 957
            click_y = window_y + 207
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Шаг 7: Нажатие на (249, 70)
            click_x = window_x + 944
            click_y = window_y + 207
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Шаг 8: Нажатие на (249, 70) - финальное действие
            self.logger.info(f"🖱️ Финальное действие для {party_id}")
            click_x = window_x + 249
            click_y = window_y + 70
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка приглашения {party_id}: {e}")
            return False

    def _input_party_id(self, party_id):
        """Ввод ID пати через клавиатуру"""
        try:
            # Очищаем поле
            self.prepare.hardware_key_press('ctrl+a')
            time.sleep(0.1)

            # Вводим каждый символ ID
            for char in str(party_id):
                if char.isdigit():
                    self.prepare.hardware_key_press(char)
                elif char.isalpha():
                    self.prepare.hardware_key_press(char.lower())
                else:
                    self._input_special_char(char)

                time.sleep(0.02)

            self.logger.info(f"✅ ID '{party_id}' введен успешно")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка ввода ID: {e}")
            return False

    def _input_special_char(self, char):
        """Ввод специальных символов"""
        special_chars = {
            '-': 'minus',
            '_': 'shift+minus',
            '.': 'period',
            '@': 'shift+2',
            '#': 'shift+3',
            ' ': 'space'
        }

        if char in special_chars:
            self.prepare.hardware_key_press(special_chars[char])
        else:
            self.prepare.hardware_key_press(char)

    def create_party(self, party_id, timeout=30):
        """Создание пати с одним ID"""
        return self.create_party_with_multiple_invites([party_id], timeout)

    def join_party(self, party_id):
        """Присоединение к пати (только для НЕ локальных мастеров)"""

        # ✅ ИЗМЕНЕНО: теперь выполняется только для НЕ мастеров
        if self._is_local_master():
            self.logger.info("👑 Локальный мастер - пропускаю присоединение к пати")
            return True, "local_master_skip"

        try:
            self.logger.info("👥 Присоединение к пати (НЕ локальный мастер)")

            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна")
                return False, "window_coordinates_failed"

            window_x, window_y, _, _ = window_coords

            # ДЕЙСТВИЕ: клик по координатам (713, 610)
            click_x = window_x + 713
            click_y = window_y + 610

            self.logger.info(f"🖱️ Клик для присоединения к пати: ({713}, {610})")
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            self.logger.info(f"✅ Присоединение к пати {party_id} выполнено")
            return True, f"joined_party_{party_id}"

        except Exception as e:
            self.logger.error(f"❌ Ошибка присоединения к пати: {e}")
            return False, str(e)

    def leave_party(self):
        """Покинуть пати"""
        if not self._is_local_master():
            self.logger.info("👥 Не локальный мастер - пропускаю покидание пати")
            return True, "not_local_master"

        try:
            self.logger.info("👋 Покидание пати...")

            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                return False, "window_coordinates_failed"

            window_x, window_y, _, _ = window_coords

            # Открываем меню пати
            click_x = window_x + 295
            click_y = window_y + 410
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            # Кнопка покинуть пати
            click_x = window_x + 800
            click_y = window_y + 500
            self.prepare.hardware_click(click_x, click_y, 'left')
            time.sleep(0.5)

            self.logger.info("✅ Пати покинута")
            return True, "party_left_successfully"

        except Exception as e:
            self.logger.error(f"❌ Ошибка покидания пати: {e}")
            return False, str(e)

    def wait_for_all_parties_ready(self, timeout=300, check_interval=5):
        """Ожидание готовности всех ПК"""
        try:
            from features.hero_sync import HeroSynchronizer
            import time

            self.logger.info("⏳ Ожидание готовности всех ПК...")

            sync = HeroSynchronizer()
            computer_name = socket.gethostname()

            # Генерируем ID сессии
            current_time = int(time.time())
            session_interval = 60 * 60
            session_slot = current_time // session_interval
            party_session_id = f"party_session_{session_slot}"

            # Если это локальный мастер - отмечаем готовность
            if self._is_local_master():
                self.logger.info("👑 Локальный мастер - отмечаю пати как готовую")
                self._mark_party_ready(sync, party_session_id, computer_name)

            # Ждем готовности всех ПК
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                ready_status = self._check_all_parties_status(sync, party_session_id)

                if ready_status['all_ready']:
                    self.logger.info(f"✅ Все ПК готовы! Готовых пати: {ready_status['ready_count']}")
                    return True, f"all_parties_ready_{ready_status['ready_count']}"
                else:
                    elapsed = time.time() - start_time
                    self.logger.info(
                        f"⏳ Ожидание... Готово {ready_status['ready_count']}/{ready_status['min_required']} ПК. Прошло {elapsed:.1f}с")

                time.sleep(check_interval)

            # Таймаут
            self.logger.warning(f"⏰ Таймаут ожидания ({timeout}с)")
            final_status = self._check_all_parties_status(sync, party_session_id)
            return False, f"timeout_ready_{final_status['ready_count']}"

        except Exception as e:
            self.logger.error(f"❌ Ошибка ожидания готовности пати: {e}")
            return False, str(e)

    def _mark_party_ready(self, sync, party_session_id, computer_name):
        """Отметить что пати на данном ПК готова"""
        try:
            worksheet = sync.worksheet

            # Hero | Status | Instance_ID | Computer | Timestamp | Match_ID | Match_Start
            new_record = [
                party_session_id,  # Hero
                'party_ready',  # Status
                f"{computer_name}_master",  # Instance_ID
                computer_name,  # Computer
                int(time.time()),  # Timestamp
                party_session_id,  # Match_ID
                ''  # Match_Start
            ]

            worksheet.append_row(new_record)
            self.logger.info(f"✅ ПК {computer_name} отмечен как готовый")

        except Exception as e:
            self.logger.error(f"❌ Ошибка отметки готовности: {e}")

    def _check_all_parties_status(self, sync, party_session_id):
        """Проверить статус готовности всех ПК"""
        try:
            worksheet = sync.worksheet
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                return {'all_ready': False, 'ready_count': 0, 'pc_status': {}, 'min_required': 2}

            headers = all_values[0]

            # Определяем индексы колонок
            try:
                match_id_idx = headers.index('Match_ID') if 'Match_ID' in headers else 5
                instance_id_idx = headers.index('Instance_ID') if 'Instance_ID' in headers else 2
                computer_idx = headers.index('Computer') if 'Computer' in headers else 3
                status_idx = headers.index('Status') if 'Status' in headers else 1
            except ValueError:
                return {'all_ready': False, 'ready_count': 0, 'pc_status': {}, 'min_required': 2}

            pc_status = {}
            ready_count = 0

            # Проверяем каждую строку данных
            for row in all_values[1:]:
                if len(row) > max(match_id_idx, instance_id_idx, computer_idx, status_idx):
                    match_id = row[match_id_idx] if len(row) > match_id_idx else ''
                    instance_id = row[instance_id_idx] if len(row) > instance_id_idx else ''
                    computer = row[computer_idx] if len(row) > computer_idx else ''
                    status = row[status_idx] if len(row) > status_idx else ''

                    # Проверяем условия
                    if (match_id == party_session_id and
                            status == 'party_ready' and
                            computer and
                            '_master' in str(instance_id)):
                        pc_status[computer] = True
                        ready_count += 1

            # Определяем минимальное количество ПК
            min_required_pcs = 2
            all_ready = ready_count >= min_required_pcs

            return {
                'all_ready': all_ready,
                'ready_count': ready_count,
                'pc_status': pc_status,
                'min_required': min_required_pcs
            }

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки статуса: {e}")
            return {
                'all_ready': False,
                'ready_count': 0,
                'pc_status': {},
                'min_required': 2
            }

    def setup_region_and_play(self, region="DUBAI", timeout=30):
        """
        Настройка региона и запуск поиска игры (только для локального мастера)

        Args:
            region (str): Выбранный регион (DUBAI, INDIA, SE_ASIA, BRAZIL, PERU, ARGENTINA)
            timeout (int): Таймаут операции в секундах

        Returns:
            tuple: (success, data) - результат операции
        """

        # ✅ ПРОВЕРКА: только локальный мастер выполняет настройку
        if not self._is_local_master():
            self.logger.info("👥 Не локальный мастер - пропускаю настройку региона")
            return True, "not_local_master"

        try:
            self.logger.info("👑 ЛОКАЛЬНЫЙ МАСТЕР: Настройка региона и запуск поиска игры")
            self.logger.info(f"🌍 Выбранный регион: {region}")

            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                self.logger.error("❌ Не удалось получить координаты окна")
                return False, "window_coordinates_failed"

            window_x, window_y, _, _ = window_coords

            # Координаты регионов
            region_coords = {
                "DUBAI": (527, 389),
                "INDIA": (731, 389),
                "SE_ASIA": (728, 445),
                "BRAZIL": (732, 608),
                "PERU": (933, 610),
                "ARGENTINA": (528, 663),
                "EAST_EUROPE": (731, 336),
                "WEST_EUROPE": (932, 333)
            }

            if region not in region_coords:
                self.logger.error(f"❌ Неизвестный регион: {region}")
                return False, f"unknown_region_{region}"

            # Шаг 1: Нажимаем кнопку PLAY
            self.logger.info("🖱️ Шаг 1: Нажимаем кнопку PLAY")
            play_x = window_x + 1426
            play_y = window_y + 901
            self.prepare.hardware_click(play_x, play_y, 'left')
            time.sleep(1)

            # Шаг 2: Нажимаем кнопку REGIONS
            self.logger.info("🖱️ Шаг 2: Нажимаем кнопку REGIONS")
            regions_x = window_x + 1522
            regions_y = window_y + 865
            self.prepare.hardware_click(regions_x, regions_y, 'left')
            time.sleep(1)

            # Шаг 3: Нажимаем кнопку AUTO 2 раза
            self.logger.info("🖱️ Шаг 3: Нажимаем кнопку AUTO (2 раза)")
            auto_x = window_x + 509
            auto_y = window_y + 181

            for i in range(2):
                self.logger.info(f"  🖱️ AUTO клик {i + 1}/2")
                self.prepare.hardware_click(auto_x, auto_y, 'left')
                time.sleep(0.5)

            # Шаг 4: Выбираем регион
            self.logger.info(f"🖱️ Шаг 4: Выбираем регион {region}")
            region_x = window_x + region_coords[region][0]
            region_y = window_y + region_coords[region][1]
            self.prepare.hardware_click(region_x, region_y, 'left')
            time.sleep(1)

            # Шаг 5: Нажимаем кнопку CONTINUE
            self.logger.info("🖱️ Шаг 5: Нажимаем кнопку CONTINUE")
            continue_x = window_x + 742
            continue_y = window_y + 792
            self.prepare.hardware_click(continue_x, continue_y, 'left')
            time.sleep(1)

            # ✅ НОВЫЕ ШАГИ: Дополнительные действия после настройки региона

            # Шаг 6: Нажимаем кнопку PLAY еще раз (1-й раз)
            self.logger.info("🖱️ Шаг 6: Нажимаем кнопку PLAY (1-й дополнительный раз)")
            self.prepare.hardware_click(play_x, play_y, 'left')
            time.sleep(1)

            # Шаг 7: Нажимаем кнопку PLAY еще раз (2-й раз)
            self.logger.info("🖱️ Шаг 7: Нажимаем кнопку PLAY (2-й дополнительный раз)")
            self.prepare.hardware_click(play_x, play_y, 'left')
            time.sleep(1)

            # Шаг 8: Финальное нажатие CONTINUE
            self.logger.info("🖱️ Шаг 8: Финальное нажатие кнопки CONTINUE")
            self.prepare.hardware_click(continue_x, continue_y, 'left')
            time.sleep(1)

            self.logger.info(f"✅ Полная настройка региона {region} и запуск игры завершены")
            return True, f"region_setup_and_play_complete_{region}"

        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки региона и запуска: {e}")
            return False, str(e)

    def synchronized_accept_game(self, timeout=300, check_interval=1, max_checks=20, max_attempts=10):
        """
        Синхронизированное принятие игры между всеми ПК (с повторными попытками)

        Args:
            timeout (int): Таймаут ожидания кнопки accept для каждой попытки
            check_interval (int): Интервал проверки синхронизации (секунды)
            max_checks (int): Максимальное количество проверок синхронизации
            max_attempts (int): Максимальное количество попыток принятия игры

        Returns:
            tuple: (success, data) - результат операции
        """
        try:
            self.logger.info("🎮 Запуск цикла принятия игры...")

            for attempt in range(max_attempts):
                self.logger.info(f"🔄 Попытка принятия игры {attempt + 1}/{max_attempts}")

                # Выполняем одну попытку принятия игры
                result = self._single_accept_attempt(timeout, check_interval, max_checks)

                if result[0] and "accept_clicked" in result[1]:
                    self.logger.info(f"✅ Игра успешно принята на попытке {attempt + 1}!")
                    return True, f"game_accepted_attempt_{attempt + 1}"

                elif result[0] and "decline_clicked" in result[1]:
                    self.logger.info(f"❌ Игра отклонена на попытке {attempt + 1}, ожидаем следующую...")
                    # Продолжаем цикл для следующей попытки
                    continue

                elif "timeout" in result[1]:
                    self.logger.warning(f"⏰ Таймаут на попытке {attempt + 1}, ожидаем следующую...")
                    # Продолжаем цикл для следующей попытки
                    continue

                else:
                    self.logger.warning(f"⚠️ Неопределенный результат на попытке {attempt + 1}: {result[1]}")
                    # Продолжаем цикл для следующей попытки
                    continue

            # Если дошли сюда, значит превышено максимальное количество попыток
            self.logger.error(f"❌ Превышено максимальное количество попыток ({max_attempts})")
            return False, f"max_attempts_exceeded_{max_attempts}"

        except Exception as e:
            self.logger.error(f"❌ Ошибка цикла принятия игры: {e}")
            return False, str(e)

    def _click_decline_master_only(self):
        """Нажать decline (только мастер)"""
        try:
            self.logger.info("👑 МАСТЕР: Нажимаем DECLINE")

            # Ищем и нажимаем кнопку decline
            found, position = self.prepare.check_image_on_screen(
                "imgs/decline.png",
                confidence_threshold=0.8,
                window_title=self.prepare.window_title
            )

            if found and position:
                self.prepare.hardware_click(position[0], position[1], 'left')
                self.logger.info(f"❌ МАСТЕР: Кнопка DECLINE нажата в позиции: {position}")
                return True, "decline_clicked_by_master"
            else:
                self.logger.warning("⚠️ МАСТЕР: Кнопка decline не найдена")
                return False, "decline_button_not_found"

        except Exception as e:
            self.logger.error(f"❌ Ошибка нажатия decline мастером: {e}")
            return False, str(e)

    def _wait_for_master_decision(self):
        """Ожидание решения мастера (для не-мастеров)"""
        try:
            self.logger.info("👥 Не-мастер: Ожидаю решения мастера...")

            # Ждем решения мастера
            max_wait_time = 30  # 30 секунд ожидания
            start_time = time.time()

            while (time.time() - start_time) < max_wait_time:
                # Проверяем, есть ли кнопка accept
                found, position = self.prepare.check_image_on_screen(
                    "imgs/accept.png",
                    confidence_threshold=0.8,
                    window_title=self.prepare.window_title
                )

                if found and position:
                    # Кнопка найдена, нажимаем
                    self.logger.info("✅ Не-мастер: Нажимаю кнопку accept")
                    self.prepare.hardware_click(position[0], position[1], 'left')
                    return True, "accept_clicked_non_master"

                time.sleep(1)

            # Если дошли сюда, кнопка исчезла или время истекло
            self.logger.info("👥 Не-мастер: Кнопка accept исчезла или время истекло")
            return True, "master_decision_processed"

        except Exception as e:
            self.logger.error(f"❌ Ошибка ожидания решения мастера: {e}")
            return False, str(e)

    def _wait_for_accept_button(self, timeout):
        """Ожидание появления кнопки accept"""
        try:
            start_time = time.time()

            while (time.time() - start_time) < timeout:
                # Ищем кнопку accept
                found, position = self.prepare.check_image_on_screen(
                    "imgs/accept.png",
                    confidence_threshold=0.8,
                    window_title=self.prepare.window_title
                )

                if found:
                    self.logger.info(f"✅ Кнопка accept найдена в позиции: {position}")
                    return True

                time.sleep(1)  # Проверяем каждую секунду

            return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка ожидания кнопки accept: {e}")
            return False

    def _synchronize_accept_with_other_pcs(self, max_checks, check_interval):
        """Синхронизация готовности accept между ПК (только для мастеров)"""
        try:
            from features.hero_sync import HeroSynchronizer

            sync = HeroSynchronizer()
            computer_name = socket.gethostname()

            # Генерируем ID сессии для accept
            current_time = int(time.time())
            session_interval = 20  # 20 секунд
            session_slot = current_time // session_interval
            accept_session_id = f"accept_session_{session_slot}"

            self.logger.info(f"🆔 Accept сессия: {accept_session_id}")

            # Отмечаем что наш ПК готов к accept
            self._mark_accept_ready(sync, accept_session_id, computer_name)

            # Проверяем готовность других ПК
            for check_num in range(max_checks):
                self.logger.info(f"🔍 Проверка синхронизации {check_num + 1}/{max_checks}")

                ready_status = self._check_all_accept_status(sync, accept_session_id)

                if ready_status['all_ready']:
                    self.logger.info(f"✅ Все ПК готовы к accept! Готовых: {ready_status['ready_count']}")
                    return "all_ready"
                else:
                    self.logger.info(f"⏳ Готово {ready_status['ready_count']}/{ready_status['min_required']} ПК")

                    # Показываем статус каждого ПК
                    for pc_name, status in ready_status['pc_status'].items():
                        status_icon = "✅" if status else "⏳"
                        self.logger.info(f"  {status_icon} {pc_name}: {'готов' if status else 'ожидание'}")

                time.sleep(check_interval)

            # Превышено максимальное количество проверок
            self.logger.warning(f"⏰ Превышено максимальное количество проверок ({max_checks})")
            return "timeout"

        except Exception as e:
            self.logger.error(f"❌ Ошибка синхронизации accept: {e}")
            return str(e)

    def _mark_accept_ready(self, sync, accept_session_id, computer_name):
        """Отметить что ПК готов к accept (с проверкой дублей)"""
        try:
            worksheet = sync.worksheet

            current_time = int(time.time())
            time_threshold = 30  # 30 секунд - считаем записи свежими

            all_values = worksheet.get_all_values()
            if len(all_values) > 1:
                headers = all_values[0]

                try:
                    match_id_idx = headers.index('Match_ID') if 'Match_ID' in headers else 5
                    computer_idx = headers.index('Computer') if 'Computer' in headers else 3
                    status_idx = headers.index('Status') if 'Status' in headers else 1
                    timestamp_idx = headers.index('Timestamp') if 'Timestamp' in headers else 4

                    # Проверяем существующие записи
                    for row in all_values[1:]:
                        if len(row) > max(match_id_idx, computer_idx, status_idx, timestamp_idx):
                            match_id = row[match_id_idx] if len(row) > match_id_idx else ''
                            computer = row[computer_idx] if len(row) > computer_idx else ''
                            status = row[status_idx] if len(row) > status_idx else ''
                            timestamp = row[timestamp_idx] if len(row) > timestamp_idx else '0'

                            if (match_id == accept_session_id and
                                    computer == computer_name and
                                    status == 'accept_ready'):

                                try:
                                    record_time = int(timestamp)
                                    if current_time - record_time < time_threshold:
                                        self.logger.info(f"⏭️ Свежая запись уже существует для {computer_name}")
                                        return
                                except (ValueError, TypeError):
                                    pass

                except ValueError:
                    pass  # Если не удалось определить индексы, продолжаем добавление

            # Hero | Status | Instance_ID | Computer | Timestamp | Match_ID | Match_Start
            new_record = [
                accept_session_id,  # Hero
                'accept_ready',  # Status
                f"{computer_name}_master",  # Instance_ID
                computer_name,  # Computer
                current_time,  # Timestamp
                accept_session_id,  # Match_ID
                ''  # Match_Start
            ]

            worksheet.append_row(new_record)
            self.logger.info(f"✅ ПК {computer_name} отмечен как готовый к accept")

        except Exception as e:
            self.logger.error(f"❌ Ошибка отметки готовности accept: {e}")

    def _check_all_accept_status(self, sync, accept_session_id):
        """Проверить статус готовности accept всех ПК (исключая текущий ПК)"""
        try:
            worksheet = sync.worksheet
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                return {'all_ready': False, 'ready_count': 0, 'pc_status': {}, 'min_required': 2}

            headers = all_values[0]

            # Определяем индексы колонок
            try:
                match_id_idx = headers.index('Match_ID') if 'Match_ID' in headers else 5
                instance_id_idx = headers.index('Instance_ID') if 'Instance_ID' in headers else 2
                computer_idx = headers.index('Computer') if 'Computer' in headers else 3
                status_idx = headers.index('Status') if 'Status' in headers else 1
                timestamp_idx = headers.index('Timestamp') if 'Timestamp' in headers else 4
            except ValueError:
                return {'all_ready': False, 'ready_count': 0, 'pc_status': {}, 'min_required': 2}

            current_computer = socket.gethostname()
            self.logger.debug(f"🖥️ Текущий ПК: {current_computer}")

            # Собираем все записи для данной сессии
            session_records = []
            for row in all_values[1:]:
                if len(row) > max(match_id_idx, instance_id_idx, computer_idx, status_idx, timestamp_idx):
                    match_id = row[match_id_idx] if len(row) > match_id_idx else ''
                    instance_id = row[instance_id_idx] if len(row) > instance_id_idx else ''
                    computer = row[computer_idx] if len(row) > computer_idx else ''
                    status = row[status_idx] if len(row) > status_idx else ''
                    timestamp = row[timestamp_idx] if len(row) > timestamp_idx else '0'

                    if (match_id == accept_session_id and
                            status == 'accept_ready' and
                            computer and
                            '_master' in str(instance_id)):

                        try:
                            timestamp_int = int(timestamp)
                        except (ValueError, TypeError):
                            timestamp_int = 0

                        session_records.append({
                            'computer': computer,
                            'timestamp': timestamp_int,
                            'instance_id': instance_id
                        })

            unique_pcs = {}
            for record in session_records:
                pc = record['computer']
                timestamp = record['timestamp']

                if pc == current_computer:
                    self.logger.debug(f"🚫 Пропускаем запись от текущего ПК: {pc}")
                    continue

                # Берем только последнюю запись от каждого ПК
                if pc not in unique_pcs or timestamp > unique_pcs[pc]['timestamp']:
                    unique_pcs[pc] = record
                    self.logger.debug(f"✅ Учитываем ПК: {pc} (timestamp: {timestamp})")

            ready_count = len(unique_pcs)

            self.logger.info(f"📊 Найдено готовых ПК (исключая текущий): {ready_count}")
            for pc_name in unique_pcs.keys():
                self.logger.info(f"  ✅ {pc_name}: готов к accept")

            # Определяем минимальное количество ДРУГИХ ПК
            min_required_pcs = 1  # требуется минимум 1 другой ПК
            all_ready = ready_count >= min_required_pcs

            return {
                'all_ready': all_ready,
                'ready_count': ready_count,
                'pc_status': {pc: True for pc in unique_pcs.keys()},
                'min_required': min_required_pcs
            }

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки статуса accept: {e}")
            return {'all_ready': False, 'ready_count': 0, 'pc_status': {}, 'min_required': 1}

    def _click_accept_all_instances(self):
        """Нажать accept на всех экземплярах"""
        try:
            self.logger.info("✅ Нажимаем ACCEPT на всех экземплярах")

            # Получаем координаты окна
            window_coords = self.prepare.get_window_coordinates(self.prepare.window_title)
            if not window_coords:
                return False, "window_coordinates_failed"

            # Ищем и нажимаем кнопку accept
            found, position = self.prepare.check_image_on_screen(
                "imgs/accept.png",
                confidence_threshold=0.8,
                window_title=self.prepare.window_title
            )

            if found and position:
                self.prepare.hardware_click(position[0], position[1], 'left')
                self.logger.info(f"✅ Кнопка ACCEPT нажата в позиции: {position}")
                return True, "accept_clicked"
            else:
                self.logger.warning("⚠️ Кнопка accept не найдена для нажатия")
                return False, "accept_button_not_found"

        except Exception as e:
            self.logger.error(f"❌ Ошибка нажатия accept: {e}")
            return False, str(e)

    def _single_accept_attempt(self, timeout, check_interval, max_checks):
        """Одна попытка принятия игры"""
        try:
            from features.hero_sync import HeroSynchronizer
            import time

            self.logger.info("🔍 Ожидание кнопки accept...")

            # Ждем появления кнопки accept на нашем экране
            accept_found = self._wait_for_accept_button(timeout)

            if not accept_found:
                self.logger.warning("⏰ Кнопка accept не появилась в течение таймаута")
                return False, "accept_button_timeout"

            self.logger.info("✅ Кнопка accept найдена на нашем экране!")

            # Если это локальный мастер - выполняем синхронизацию
            if self._is_local_master():
                self.logger.info("👑 Локальный мастер - выполняю синхронизацию accept")

                sync_result = self._synchronize_accept_with_other_pcs(max_checks, check_interval)

                if sync_result == "all_ready":
                    self.logger.info("✅ Все ПК готовы! Принимаем игру на всех экземплярах")
                    return self._click_accept_all_instances()

                elif sync_result == "timeout":
                    self.logger.warning("⏰ Не все ПК готовы - МАСТЕР отклоняет игру")
                    return self._click_decline_master_only()
                else:
                    self.logger.error(f"❌ Ошибка синхронизации: {sync_result}")
                    return False, sync_result
            else:
                # Не мастер - ждет решения мастера
                self.logger.info("👥 Не мастер - ожидаю решения мастера")
                return self._wait_for_master_decision()

        except Exception as e:
            self.logger.error(f"❌ Ошибка попытки принятия игры: {e}")
            return False, str(e)