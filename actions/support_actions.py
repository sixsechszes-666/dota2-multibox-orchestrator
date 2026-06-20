# actions/support_actions.py
from utils.actions_registry import register_action
import random
import time


@register_action("ward_placement")
def ward_placement_action(instance, **kwargs):
    """Расстановка вардов локальными мастерами"""

    # Проверяем, является ли экземпляр локальным мастером
    if not _is_local_master(instance):
        instance.logger.info("👥 Не локальный мастер - пропускаю расстановку вардов")
        return True, "not_local_master"

    instance.logger.info("👑 ЛОКАЛЬНЫЙ МАСТЕР: Расстановка вардов")

    try:
        success = execute_ward_placement(instance, **kwargs)

        if success:
            instance.logger.info("✅ Варды успешно расставлены локальным мастером")
            return True, "wards_placed_by_master"
        else:
            instance.logger.error("❌ Ошибка расстановки вардов")
            return False, "ward_placement_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка при расстановке вардов: {e}")
        return False, str(e)


def execute_ward_placement(instance, **kwargs):
    """
    Выполнение расстановки вардов (может вызываться из любого места)

    Args:
        instance: Экземпляр PrepareMatchmaking
        **kwargs: Параметры конфигурации

    Returns:
        bool: True если варды расставлены успешно
    """

    try:
        instance.logger.info("🔍 Начало расстановки вардов...")

        # Настраиваемые параметры
        shop_delay = kwargs.get('shop_delay', random.uniform(0.2, 0.4))
        buy_delay = kwargs.get('buy_delay', random.uniform(0.05, 0.15))
        move_delay = kwargs.get('move_delay', random.uniform(0.05, 0.1))
        ward_delay = kwargs.get('ward_delay', random.uniform(0.05, 0.1))

        # Получаем координаты окна
        window_coords = instance.get_window_coordinates()
        if not window_coords:
            instance.logger.error("❌ Не удалось получить координаты окна")
            return False

        window_x, window_y, _, _ = window_coords

        # ШАГ 1: Покупка 2 вардов
        success = _buy_wards(instance, window_x, window_y, shop_delay, buy_delay)
        if not success:
            return False

        # ШАГ 2: Выбор случайной локации
        ward_location = _select_random_ward_location()
        instance.logger.info(f"🗺️ Выбрана локация варда #{ward_location['id']}")

        # ШАГ 3: Движение к локации
        success = _move_to_ward_location(instance, window_x, window_y, ward_location, move_delay)
        if not success:
            return False

        # ШАГ 4: Установка вардов
        success = _place_wards(instance, ward_delay)
        if not success:
            return False

        instance.logger.info("✅ Расстановка вардов завершена успешно")
        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка выполнения расстановки вардов: {e}")
        return False


def _buy_wards(instance, window_x, window_y, shop_delay, buy_delay):
    """Покупка 2 вардов в магазине"""

    try:
        # Открываем магазин (F4)
        instance.logger.info("🏪 Открытие магазина для покупки вардов...")
        success = instance.hardware_key_press('f4')
        if not success:
            instance.logger.error("❌ Не удалось открыть магазин")
            return False

        time.sleep(shop_delay)

        # Координаты варда: X: 1303, Y: 210
        ward_x = window_x + 1303
        ward_y = window_y + 210

        # Покупаем первый вард
        instance.logger.info("🔍 Покупка первого варда...")
        success = instance.hardware_click(ward_x, ward_y, 'right')
        if not success:
            instance.logger.warning("⚠️ Не удалось купить первый вард")
        else:
            instance.logger.info("✅ Первый вард куплен")

        time.sleep(buy_delay)

        # Покупаем второй вард
        instance.logger.info("🔍 Покупка второго варда...")
        success = instance.hardware_click(ward_x, ward_y, 'right')
        if not success:
            instance.logger.warning("⚠️ Не удалось купить второй вард")
        else:
            instance.logger.info("✅ Второй вард куплен")

        time.sleep(buy_delay)

        # Закрываем магазин (F4)
        instance.logger.info("🏪 Закрытие магазина...")
        success = instance.hardware_key_press('f4')
        if not success:
            instance.logger.warning("⚠️ Не удалось закрыть магазин")

        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка покупки вардов: {e}")
        return False


def _select_random_ward_location():
    """Выбор случайной локации для установки варда"""

    ward_locations = [
        {
            'id': 1,
            'move_coords': (130, 842),
            'place_coords': (498, 509),
            'description': 'River rune spot'
        },
        {
            'id': 2,
            'move_coords': (130, 842),
            'place_coords': (807, 640),
            'description': 'Dire jungle entrance'
        },
        {
            'id': 3,
            'move_coords': (130, 842),
            'place_coords': (209, 341),
            'description': 'Radiant jungle high ground'
        },
        {
            'id': 4,
            'move_coords': (130, 842),
            'place_coords': (1003, 166),
            'description': 'Dire high ground'
        },
        {
            'id': 5,
            'move_coords': (130, 842),
            'place_coords': (695, 121),
            'description': 'Top river'
        },
        {
            'id': 6,
            'move_coords': (114, 826),
            'place_coords': (510, 628),
            'description': 'Bottom river'
        },
        {
            'id': 7,
            'move_coords': (114, 826),
            'place_coords': (1192, 371),
            'description': 'Dire side ward'
        },
        {
            'id': 8,
            'move_coords': (114, 826),
            'place_coords': (1421, 526),
            'description': 'Dire deep ward'
        },
        {
            'id': 9,
            'move_coords': (114, 826),
            'place_coords': (923, 105),
            'description': 'Top lane ward'
        },
        {
            'id': 10,
            'move_coords': (114, 826),
            'place_coords': (326, 457),
            'description': 'Radiant side ward'
        }
    ]

    return random.choice(ward_locations)


def _move_to_ward_location(instance, window_x, window_y, ward_location, move_delay):
    """Движение к локации установки варда"""

    try:
        move_coords = ward_location['move_coords']
        place_coords = ward_location['place_coords']

        # Первый клик - движение к общей области
        move_x = window_x + move_coords[0]
        move_y = window_y + move_coords[1]

        instance.logger.info(f"🚶 Движение к области варда: ({move_coords[0]}, {move_coords[1]})")
        success = instance.hardware_click(move_x, move_y, 'left')
        if not success:
            instance.logger.warning("⚠️ Не удалось выполнить движение к области")
            return False

        time.sleep(move_delay)

        # Второй клик - точная позиция установки
        place_x = window_x + place_coords[0] + random.randint(-3, 3)
        place_y = window_y + place_coords[1] + random.randint(-3, 3)

        instance.logger.info(f"🎯 Движение к точке установки: ({place_coords[0]}, {place_coords[1]})")
        success = instance.hardware_click(place_x, place_y, 'left')
        if not success:
            instance.logger.warning("⚠️ Не удалось выполнить движение к точке установки")
            return False

        time.sleep(move_delay)
        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка движения к локации варда: {e}")
        return False


def _place_wards(instance, ward_delay):
    """Установка вардов (нажатие X, C в случайном порядке)"""

    try:
        ward_keys = ['z', 'x', 'c']
        random.shuffle(ward_keys)  # Случайный порядок

        instance.logger.info(f"🔍 Установка вардов в порядке: {' → '.join(ward_keys).upper()}")

        for i, key in enumerate(ward_keys, 1):
            instance.logger.info(f"🔍 Установка варда {i}/2: {key.upper()}...")

            success = instance.hardware_key_press(key)
            if success:
                instance.logger.info(f"✅ Вард {key.upper()} установлен")
            else:
                instance.logger.warning(f"⚠️ Не удалось установить вард {key.upper()}")

            # Задержка между установкой вардов
            if i < len(ward_keys):
                time.sleep(ward_delay)

        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка установки вардов: {e}")
        return False


def _is_local_master(instance):
    """Проверка, является ли экземпляр локальным мастером"""
    try:
        import socket
        computer_name = socket.gethostname()
        instance_id = getattr(instance, 'instance_id', '1')

        # Локальный мастер = первый экземпляр на каждом ПК
        is_master = str(instance_id) == "1"

        instance.logger.debug(f"🖥️ {computer_name}_{instance_id}: {'МАСТЕР' if is_master else 'СЛЕЙВ'}")
        return is_master

    except Exception as e:
        instance.logger.error(f"❌ Ошибка определения локального мастера: {e}")
        return False
