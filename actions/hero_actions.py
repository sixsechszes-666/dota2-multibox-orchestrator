# actions/hero_actions.py
from utils.actions_registry import register_action
from features.hero_sync import HeroSynchronizer
import os
import socket
import time
import random


# actions/hero_actions.py - заменить существующую функцию
@register_action("hero_pick_sync")
def hero_pick_sync_action(instance, **kwargs):
    """Синхронизированный выбор героя с повторным пакетным поиском"""

    try:
        # Инициализируем синхронизатор
        sync = HeroSynchronizer()

        # Получаем информацию об экземпляре
        instance_id = getattr(instance, 'instance_id', 'unknown')
        computer_name = socket.gethostname()
        heroes_folder = kwargs.get('heroes_folder', instance.heroes_folder)

        # Генерируем ID матча
        current_time = int(time.time())
        match_interval = 30 * 60
        match_time_slot = current_time // match_interval
        match_id = kwargs.get('match_id', f"match_{match_time_slot}")

        instance.logger.info(f"🎮 Матч ID: {match_id}")
        instance.logger.info(f"🔄 Синхронизация для экземпляра {instance_id}")
        instance.logger.info(f"📁 Используется папка героев: {heroes_folder}")

        timeout = kwargs.get('timeout', 180)
        use_batch_mode = kwargs.get('use_batch_mode', True)
        batch_size = kwargs.get('batch_size', 15)
        max_hero_attempts = kwargs.get('max_hero_attempts', 15)
        max_batch_attempts = kwargs.get('max_batch_attempts', 5)  # Максимум попыток пакетного поиска

        # ✅ УЛУЧШЕННЫЙ ПАКЕТНЫЙ РЕЖИМ С ПОВТОРНЫМИ ПОПЫТКАМИ
        if use_batch_mode:
            instance.logger.info(f"📦 Пакетный режим: проверка до {batch_size} героев")

            # Ждем загрузки пика сначала
            instance.logger.info("⏳ Ожидание загрузки стадии пика для пакетного поиска...")
            pick_loaded = instance.wait_for_pick_loading(timeout=timeout)

            if pick_loaded:
                # Получаем список доступных героев БЕЗ резервирования
                available_heroes = sync.get_available_heroes_from_folder(heroes_folder, match_id)

                if len(available_heroes) >= batch_size:
                    # Берем случайную выборку
                    import random
                    heroes_batch = random.sample(available_heroes, min(batch_size, len(available_heroes)))
                else:
                    heroes_batch = available_heroes.copy()

                instance.logger.info(f"📋 Исходный пакет ({len(heroes_batch)}): {heroes_batch}")

                # ✅ ЦИКЛ ПАКЕТНОГО ПОИСКА С ИСКЛЮЧЕНИЕМ ЗАНЯТЫХ ГЕРОЕВ
                excluded_heroes = set()  # Герои, которые уже проверили и они заняты

                for batch_attempt in range(max_batch_attempts):
                    # Фильтруем пакет, исключая уже проверенных занятых героев
                    current_batch = [hero for hero in heroes_batch if hero not in excluded_heroes]

                    if not current_batch:
                        instance.logger.warning("❌ Все герои из пакета исключены (заняты), пакет исчерпан")
                        break

                    instance.logger.info(
                        f"🔍 Пакетная попытка {batch_attempt + 1}/{max_batch_attempts}: проверка "
                        f"{len(current_batch)} героев")
                    if excluded_heroes:
                        instance.logger.debug(f"🚫 Исключено занятых героев: {list(excluded_heroes)}")

                    # Пакетный поиск героев на экране
                    batch_result = instance.batch_find_heroes_on_screen(current_batch, heroes_folder)

                    if batch_result:
                        hero_name, hero_position, hero_image_path = batch_result
                        instance.logger.info(f"✅ Найден герой из пакета: {hero_name}")

                        # ✅ РЕЗЕРВИРУЕМ ТОЛЬКО НАЙДЕННОГО ГЕРОЯ
                        reserved = sync.reserve_hero(hero_name, instance_id, computer_name, match_id)

                        if reserved:
                            instance.logger.info(f"🔒 Герой {hero_name} успешно зарезервирован")

                            # Выбираем героя напрямую
                            success = instance.execute_hero_selection_direct(hero_name, hero_position)
                            if success:
                                instance.logger.info(
                                    f"✅ Успешно выбран герой {hero_name} "
                                    f"(пакетный режим, попытка {batch_attempt + 1})")
                                return hero_image_path, hero_position
                            else:
                                instance.logger.warning(f"⚠️ Не удалось выбрать героя "
                                                        f"{hero_name}, исключаем из пакета")
                                excluded_heroes.add(hero_name)
                                continue  # Продолжаем пакетный поиск
                        else:
                            instance.logger.warning(
                                f"⚠️ Герой {hero_name} уже занят другим экземпляром, исключаем из пакета")
                            excluded_heroes.add(hero_name)
                            continue  # ✅ ПРОДОЛЖАЕМ ПАКЕТНЫЙ ПОИСК, НЕ ПЕРЕХОДИМ К ОБЫЧНОМУ РЕЖИМУ
                    else:
                        instance.logger.warning(
                            f"❌ Пакетная попытка {batch_attempt + 1}: ни один герой не найден на экране")
                        break  # Если герои не найдены на экране, дальше искать бесполезно

                instance.logger.info(
                    f"📊 Пакетный поиск завершен: проверено попыток {batch_attempt + 1}, "
                    f"исключено героев {len(excluded_heroes)}")
            else:
                instance.logger.warning("❌ Не удалось дождаться загрузки стадии пика")

        # ✅ FALLBACK К ОБЫЧНОМУ РЕЖИМУ
        instance.logger.info("🔄 Переход к обычному режиму поиска героев...")

        for attempt in range(max_hero_attempts):
            instance.logger.info(f"🔍 Попытка {attempt + 1}/{max_hero_attempts} обычного поиска")

            selected_hero = sync.select_random_available_hero_from_folder(
                heroes_folder, instance_id, computer_name, match_id
            )

            if not selected_hero:
                instance.logger.warning(f"⚠️ Не удалось выбрать героя (попытка {attempt + 1})")
                continue

            hero_image = os.path.join(heroes_folder, f"{selected_hero}.png")
            if not os.path.exists(hero_image):
                instance.logger.warning(f"⚠️ Файл героя не найден: {hero_image}")
                continue

            instance.logger.info(f"🎯 Тестирование героя: {selected_hero}")
            result = instance.run_hero_pick_hardware(hero_image=hero_image, timeout=timeout)

            if result[0] != "undifined" and result[1] is not None:
                instance.logger.info(f"✅ Успешно выбран герой {selected_hero} (обычный режим)")
                return result
            else:
                instance.logger.warning(f"❌ Герой {selected_hero} не найден на экране")
                continue

        # Последний fallback
        instance.logger.error("❌ Все попытки исчерпаны, переход к fallback")
        return _fallback_hero_selection_until_found(instance, heroes_folder, timeout)

    except Exception as e:
        instance.logger.error(f"❌ Критическая ошибка синхронизации: {e}")
        return _fallback_hero_selection_until_found(instance, heroes_folder, kwargs.get('timeout', 180))


def _fallback_hero_selection_until_found(instance, heroes_folder, timeout):
    """
    Fallback функция для поиска любого героя без синхронизации
    Перебирает всех героев из папки до тех пор, пока не найдет подходящего
    """
    try:
        instance.logger.info("🔄 Fallback: поиск любого доступного героя")

        # Получаем список всех героев из папки
        if not os.path.exists(heroes_folder):
            instance.logger.error(f"❌ Папка героев не найдена: {heroes_folder}")
            return "undifined", None

        hero_files = [f for f in os.listdir(heroes_folder) if f.lower().endswith('.png')]

        if not hero_files:
            instance.logger.error("❌ Не найдено файлов героев")
            return "undifined", None

        # Перемешиваем список героев для случайного порядка
        random.shuffle(hero_files)

        # Пытаемся найти любого героя, который есть на экране
        for hero_file in hero_files:
            hero_image_path = os.path.join(heroes_folder, hero_file)
            hero_name = hero_file.replace('.png', '')

            instance.logger.info(f"🔍 Fallback попытка выбора героя: {hero_name}")

            try:
                result = instance.run_hero_pick_hardware(hero_image=hero_image_path, timeout=timeout)

                if result[0] != "undifined" and result[1] is not None:
                    instance.logger.info(f"✅ Fallback: успешно выбран герой {hero_name}")
                    return result
                else:
                    instance.logger.debug(f"❌ Fallback: герой {hero_name} не найден на экране")
                    continue

            except Exception as e:
                instance.logger.warning(f"⚠️ Ошибка при попытке выбора героя {hero_name}: {e}")
                continue

        # Если не найден ни один герой из папки
        instance.logger.error("❌ Не удалось найти ни одного героя из папки на экране")
        return "undifined", None

    except Exception as e:
        instance.logger.error(f"❌ Ошибка fallback поиска героя: {e}")
        return "undifined", None


@register_action("skill_upgrade")
def skill_upgrade_action(instance, **kwargs):
    """Прокачка навыков"""
    skill_image = kwargs.get('skill_image', 'imgs/skill_upgrade.png')
    confidence = kwargs.get('confidence')
    return instance.skill_upgrade(skill_image=skill_image, confidence=confidence)

@register_action("buy_boots")
def buy_boots_action(instance, **kwargs):
    """Покупка ботинок"""
    boots_image = kwargs.get('boots_image', 'imgs/boots.png')
    confidence = kwargs.get('confidence')
    return instance.buy_boots_hardware(boots_image=boots_image, confidence=confidence)

@register_action("upgrade_talents")
def upgrade_talents_action(instance, **kwargs):
    """Прокачка талантов героя"""
    return instance.upgrade_talents()


@register_action("buy_core_items")
def buy_core_items_action(instance, **kwargs):
    """Покупка основных предметов по очереди: Tarrasque, Moon shard, Desolator"""

    items_sequence = [
        {
            'name': 'Tarrasque',
            'shop_coords': (1300, 539),
            'inventory_coords': (1330, 711)
        },
        {
            'name': 'Moon shard',
            'shop_coords': (1304, 516),
            'inventory_coords': (1486, 711)
        },
        {
            'name': 'Desolator',
            'shop_coords': (1374, 401),
            'inventory_coords': (1562, 710)
        }
    ]

    return instance.buy_items_sequence(items_sequence)


@register_action("buy_random_boots")
def buy_random_boots_action(instance, **kwargs):
    """Покупка случайных ботинок из 3 вариантов"""

    boots_options = [
        {
            'name': 'Phase boots',
            'shop_coords': (1548, 348),
            'inventory_coords': (1381, 712)
        },
        {
            'name': 'Power treads',
            'shop_coords': (1548, 348),
            'inventory_coords': (1442, 713)
        }
    ]

    # Выбираем случайные ботинки
    selected_boots = random.choice(boots_options)
    instance.logger.info(f"🥾 Выбраны ботинки: {selected_boots['name']}")

    return instance.buy_items_sequence([selected_boots])


@register_action("buy_random_bracers")
def buy_random_bracers_action(instance, **kwargs):
    """Покупка 2 случайных предметов: Bracer или Wraith band + обязательная Morbid Mask"""

    bracer_options = [
        {
            'name': 'Bracer',
            'shop_coords': (1469, 211),
            'inventory_coords': (1319, 715)
        },
        {
            'name': 'Wraith band',
            'shop_coords': (1469, 211),
            'inventory_coords': (1403, 709)
        }
    ]

    # Обязательный предмет - Morbid Mask
    morbid_mask = {
        'name': 'Morbid Mask',
        'shop_coords': (1469, 372),
        'inventory_coords': (1469, 372)
    }

    # Инициализируем список сразу с Morbid Mask
    items_to_buy = [morbid_mask]

    # Добавляем 2 случайных предмета
    selected_item = random.choice(bracer_options).copy()
    selected_item['name'] = f"{selected_item['name']} #1"
    items_to_buy.append(selected_item)

    instance.logger.info(f"🔗 Покупаем: {[item['name'] for item in items_to_buy]}")

    return instance.buy_items_sequence(items_to_buy)

@register_action("check_pick_button")
def check_pick_button_action(instance, **kwargs):
    """Проверка наличия кнопки Pick и нажатие на неё"""

    try:
        pick_button_image = kwargs.get('pick_button_image', 'imgs/btn_pick.png')
        confidence_threshold = kwargs.get('confidence_threshold', 0.74)
        max_attempts = kwargs.get('max_attempts', 50)
        check_interval = kwargs.get('check_interval', 1)  # Интервал между проверками в секундах

        instance.logger.info("🔍 Проверка наличия кнопки Pick...")

        # Проверяем существование файла изображения
        if not os.path.exists(pick_button_image):
            instance.logger.warning(f"📁 Файл кнопки не найден: {pick_button_image}")
            return False, "file_not_found"

        # Первоначальная проверка наличия кнопки
        found, position = instance.check_image_on_screen(
            pick_button_image,
            confidence_threshold=confidence_threshold,
            window_title=getattr(instance, 'window_title', None)
        )

        if not found:
            instance.logger.info("ℹ️ Кнопка Pick не найдена на экране - пропуск")
            return True, "button_not_found"

        instance.logger.info(f"✅ Кнопка Pick найдена на позиции: {position}")

        # Нажимаем на кнопку
        click_success = instance.hardware_click(position[0], position[1], 'left')

        if not click_success:
            instance.logger.warning("⚠️ Не удалось нажать на кнопку Pick")
            return False, "click_failed"

        instance.logger.info("✅ Кнопка Pick нажата успешно")

        # Проверяем, что кнопка исчезла после нажатия
        for attempt in range(max_attempts):
            time.sleep(check_interval)

            instance.logger.info(f"🔍 Проверка исчезновения кнопки (попытка {attempt + 1}/{max_attempts})")

            found_after_click, _ = instance.check_image_on_screen(
                pick_button_image,
                confidence_threshold=confidence_threshold,
                window_title=getattr(instance, 'window_title', None)
            )

            if not found_after_click:
                instance.logger.info("✅ Кнопка Pick исчезла - операция завершена успешно")
                return True, "button_clicked_and_disappeared"

            instance.logger.debug(f"🔄 Кнопка все еще видна, ожидание...")

        # Если кнопка не исчезла после всех попыток
        instance.logger.warning(f"⚠️ Кнопка Pick не исчезла после {max_attempts} проверок")
        return True, "button_clicked_but_still_visible"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка при проверке кнопки Pick: {e}")
        return False, "error"


@register_action("buy_and_consume_consumables")
def buy_and_consume_consumables_action(instance, **kwargs):
    """Покупка и поедание Faerie Fire + Mango"""

    try:
        instance.logger.info("🧪 Покупка и поедание consumables (Faerie Fire + Mango)...")

        # Получаем координаты окна
        window_coords = instance.get_window_coordinates()
        if not window_coords:
            instance.logger.error("❌ Не удалось получить координаты окна")
            return False, "window_coordinates_failed"

        window_x, window_y, _, _ = window_coords

        # Настраиваемые параметры
        shop_delay = kwargs.get('shop_delay', random.uniform(0.3, 0.5))  # Задержка после открытия магазина
        buy_delay = kwargs.get('buy_delay', random.uniform(0.05, 0.1))  # Задержка между покупками
        consume_delay = kwargs.get('consume_delay', random.uniform(0.05, 0.15))  # Задержка между поеданием
        close_delay = kwargs.get('close_delay', random.uniform(0.05, 0.15))  # Задержка после закрытия магазина

        # ШАГ 1: Открываем магазин (F4)
        instance.logger.info("🏪 Открытие магазина (F4)...")
        success = instance.hardware_key_press('f4')
        if not success:
            instance.logger.error("❌ Не удалось открыть магазин")
            return False, "shop_open_failed"

        time.sleep(shop_delay)

        # ШАГ 2: Покупаем Faerie Fire (ПКМ по 1379, 186)
        instance.logger.info("🧚 Покупка Faerie Fire...")
        faerie_x = window_x + 1379 + random.randint(-2,2)
        faerie_y = window_y + 186 + random.randint(-2,2)

        success = instance.hardware_click(faerie_x, faerie_y, 'right')
        if not success:
            instance.logger.warning("⚠️ Не удалось купить Faerie Fire")
        else:
            pass

        time.sleep(buy_delay)

        # ШАГ 3: Покупаем Mango (ПКМ по 1379, 210)
        instance.logger.info("🥭 Покупка Mango...")
        mango_x = window_x + 1379 + random.randint(-2,2)
        mango_y = window_y + 210 + random.randint(-2,2)

        success = instance.hardware_click(mango_x, mango_y, 'right')
        if not success:
            instance.logger.warning("⚠️ Не удалось купить Mango")
        else:
            pass

        time.sleep(buy_delay)

        # ШАГ 4: Закрываем магазин (F4)
        instance.logger.info("🏪 Закрытие магазина (F4)...")
        success = instance.hardware_key_press('f4')
        if not success:
            instance.logger.warning("⚠️ Не удалось закрыть магазин")

        time.sleep(close_delay)

        # ШАГ 5: Съедаем в случайном порядке (z, x)
        consumable_keys = ['z', 'x']  # z = Faerie Fire, x = Mango (обычно)
        random.shuffle(consumable_keys)  # Случайный порядок

        instance.logger.info(f"🍽️ Поедание в порядке: {' → '.join(consumable_keys).upper()}")

        for i, key in enumerate(consumable_keys, 1):
            consumable_name = "Faerie Fire" if key == 'z' else "Mango"
            instance.logger.info(f"🍽️ Поедание {i}/2: {consumable_name} ({key.upper()})...")

            success = instance.hardware_key_press(key)
            if success:
                instance.logger.info(f"✅ {consumable_name} съеден")
            else:
                instance.logger.warning(f"⚠️ Не удалось съесть {consumable_name}")

            # Задержка между поеданием
            if i < len(consumable_keys):
                time.sleep(consume_delay)

        instance.logger.info("🎉 Покупка и поедание consumables завершены!")
        return True, "consumables_bought_and_consumed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка покупки consumables: {e}")
        return False, str(e)

@register_action("random_consumables")
def safe_consumables_action(instance, **kwargs):
    kwargs['shop_delay'] = random.uniform(0.3, 0.5)
    kwargs['buy_delay'] = random.uniform(0.05, 0.1)
    kwargs['consume_delay'] = random.uniform(0.05, 0.15)
    kwargs['close_delay'] = random.uniform(0.05, 0.15)

    return buy_and_consume_consumables_action(instance, **kwargs)
