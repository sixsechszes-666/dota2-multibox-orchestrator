# actions/communication_actions.py
from utils.actions_registry import register_action
import random
import time


@register_action("chat_game_start")
def chat_game_start_action(instance, **kwargs):
    """Отправка приветственных сообщений в начале игры"""

    all_chat_messages = [
        "gl hf",
        "good luck everyone",
        "have a good game",
        "play calm",
        "no tilt please"
    ]

    team_chat_messages = [
        "farm and push",
        "dont feed",
        "lets go team",
        "we can win",
        "lets win this",
        "hello team"
    ]

    try:
        instance.logger.info("💬 Отправка приветственных сообщений...")

        # Отправляем сообщение в All Chat
        all_msg = random.choice(all_chat_messages)
        success_all = _send_chat_message(instance, all_msg, chat_type="all")

        # Небольшая задержка между сообщениями
        time.sleep(random.uniform(0.1, 1))

        # Отправляем сообщение в Team Chat
        team_msg = random.choice(team_chat_messages)
        success_team = _send_chat_message(instance, team_msg, chat_type="team")

        if success_all and success_team:
            instance.logger.info(f"✅ Приветственные сообщения отправлены: All='{all_msg}', Team='{team_msg}'")
            return True, f"chat_start_sent"
        else:
            instance.logger.warning("⚠️ Не все сообщения отправлены успешно")
            return True, "chat_start_partial"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка отправки приветственных сообщений: {e}")
        return False, str(e)


@register_action("chat_game_end")
def chat_game_end_action(instance, **kwargs):
    """Отправка прощальных сообщений в конце игры"""

    all_chat_end_messages = [
        "close game",
        "good match",
        "gg all",
        "unlucky",
        "ez game",
        "gg wp"
    ]

    team_chat_end_messages = [
        "we tried",
        "thanks for game",
        "next game better",
        "good try team",
        "nice teamwork",
        "we did it",
        "good game"
    ]

    try:
        instance.logger.info("💬 Отправка прощальных сообщений...")

        # Отправляем сообщение в All Chat
        all_msg = random.choice(all_chat_end_messages)
        success_all = _send_chat_message(instance, all_msg, chat_type="all")

        # Небольшая задержка между сообщениями
        time.sleep(random.uniform(0.1, 1))

        # Отправляем сообщение в Team Chat
        team_msg = random.choice(team_chat_end_messages)
        success_team = _send_chat_message(instance, team_msg, chat_type="team")

        if success_all and success_team:
            instance.logger.info(f"✅ Прощальные сообщения отправлены: All='{all_msg}', Team='{team_msg}'")
            return True, f"chat_end_sent"
        else:
            instance.logger.warning("⚠️ Не все сообщения отправлены успешно")
            return True, "chat_end_partial"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка отправки прощальных сообщений: {e}")
        return False, str(e)


def _send_chat_message(instance, message, chat_type="team"):
    """
    Отправка сообщения в чат

    Args:
        instance: Экземпляр PrepareMatchmaking
        message (str): Текст сообщения
        chat_type (str): "team" для team chat, "all" для all chat

    Returns:
        bool: True если сообщение отправлено успешно
    """

    try:
        instance.logger.debug(f"📤 Отправка в {chat_type} chat: '{message}'")

        # Открываем чат
        if chat_type == "all":
            # Shift+Enter для All Chat
            instance.logger.debug("🔓 Открытие All Chat (Shift+Enter)")
            success = instance.hardware_key_press('shift+enter')
        else:
            # Enter для Team Chat
            instance.logger.debug("🔓 Открытие Team Chat (Enter)")
            success = instance.hardware_key_press('enter')

        if not success:
            instance.logger.warning(f"⚠️ Не удалось открыть {chat_type} chat")
            return False

        # Небольшая задержка после открытия чата
        time.sleep(random.uniform(0.1, 0.3))

        # Вводим сообщение по символам
        for char in message:
            if char == ' ':
                instance.hardware_key_press('space')
            elif char.isalnum():
                instance.hardware_key_press(char.lower())
            else:
                # Для специальных символов (! и т.д.)
                _input_special_char(instance, char)

            # Небольшая задержка между символами для естественности
            time.sleep(random.uniform(0.01, 0.03))

        # Отправляем сообщение
        time.sleep(random.uniform(0.1, 0.3))
        instance.hardware_key_press('enter')
        instance.logger.debug(f"✅ Сообщение '{message}' отправлено в {chat_type} chat")

        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка отправки сообщения в {chat_type} chat: {e}")
        return False

def _input_special_char(instance, char):
    """Ввод специальных символов"""
    special_chars = {
        '!': 'shift+1',
        '?': 'shift+/',
        '.': 'period',
        ',': 'comma',
        ':': 'shift+semicolon',
        ';': 'semicolon',
        "'": 'apostrophe',
        '"': 'shift+apostrophe',
        '-': 'minus',
        '_': 'shift+minus'
    }

    if char in special_chars:
        instance.hardware_key_press(special_chars[char])
    else:
        # Fallback - пытаемся отправить как есть
        instance.hardware_key_press(char)


@register_action("chat_wheel")
def chat_wheel_action(instance, **kwargs):
    """Использование колеса чата со случайным выбором фразы"""

    try:
        instance.logger.info("🎡 Активация колеса чата...")

        success = execute_chat_wheel(instance, **kwargs)

        if success:
            instance.logger.info("✅ Колесо чата использовано успешно")
            return True, "chat_wheel_used"
        else:
            instance.logger.error("❌ Ошибка использования колеса чата")
            return False, "chat_wheel_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка колеса чата: {e}")
        return False, str(e)


def execute_chat_wheel(instance, **kwargs):
    """
    Выполнение колеса чата (может вызываться из любого места)

    Args:
        instance: Экземпляр PrepareMatchmaking
        **kwargs: Параметры конфигурации

    Returns:
        bool: True если колесо чата использовано успешно
    """

    try:
        # Координаты колеса чата (8 позиций)
        wheel_coords = [
            (798, 359),  # Позиция 1 (верх-право)
            (683, 380),  # Позиция 2 (лево-верх)
            (640, 493),  # Позиция 3 (лево)
            (674, 597),  # Позиция 4 (лево-низ)
            (828, 666),  # Позиция 5 (низ)
            (936, 611),  # Позиция 6 (право-низ)
            (982, 495),  # Позиция 7 (право)
            (934, 376)  # Позиция 8 (право-верх)
        ]

        # Настраиваемые параметры
        hold_delay = kwargs.get('hold_delay', random.uniform(0.03, 0.1))  # Задержка после зажатия Y
        click_delay = kwargs.get('click_delay', random.uniform(0.03, 0.1))  # Задержка после клика
        release_delay = kwargs.get('release_delay', random.uniform(0.03, 0.1))  # Задержка после отпускания Y

        # Получаем координаты окна
        window_coords = instance.get_window_coordinates()
        if not window_coords:
            instance.logger.error("❌ Не удалось получить координаты окна")
            return False

        window_x, window_y, _, _ = window_coords

        # Выбираем случайную позицию на колесе
        selected_coord = random.choice(wheel_coords)
        coord_index = wheel_coords.index(selected_coord) + 1

        instance.logger.info(
            f"🎯 Выбрана позиция #{coord_index} колеса чата: ({selected_coord[0]}, {selected_coord[1]})")

        # ШАГ 1: Зажимаем кнопку Y
        instance.logger.debug("🔽 Зажатие кнопки Y...")
        success = _hold_key_down(instance, 'y')
        if not success:
            instance.logger.error("❌ Не удалось зажать кнопку Y")
            return False

        time.sleep(hold_delay)

        # ШАГ 2: Кликаем по выбранной позиции
        click_x = window_x + selected_coord[0]
        click_y = window_y + selected_coord[1]

        instance.logger.debug(f"🖱️ Клик по позиции колеса: ({click_x}, {click_y})")
        success = instance.hardware_click(click_x, click_y, 'left')
        if not success:
            instance.logger.warning("⚠️ Не удалось кликнуть по колесу чата")

        time.sleep(click_delay)

        # ШАГ 3: Отпускаем кнопку Y
        instance.logger.debug("🔼 Отпускание кнопки Y...")
        success = _release_key(instance, 'y')
        if not success:
            instance.logger.warning("⚠️ Не удалось отпустить кнопку Y")

        time.sleep(release_delay)

        instance.logger.info(f"✅ Колесо чата использовано: позиция #{coord_index}")
        return True

    except Exception as e:
        instance.logger.error(f"❌ Ошибка выполнения колеса чата: {e}")
        # Попытка экстренного отпускания Y
        try:
            _release_key(instance, 'y')
        except:
            pass
        return False


def _hold_key_down(instance, key):
    """Зажатие клавиши (без отпускания)"""
    try:
        # Определяем hwnd
        if hasattr(instance, 'hwnd'):
            hwnd = instance.hwnd
        else:
            hwnd = instance._find_window_by_partial_title(instance.window_title)

        if not hwnd:
            instance.logger.error("❌ Не удалось найти окно для зажатия клавиши")
            return False

        # Используем hardware_input для зажатия клавиши
        if hasattr(instance.hardware_input, 'key_down'):
            # Если есть специальный метод
            success = instance.hardware_input.key_down(_get_key_code(key))
        else:
            # Fallback через ctypes
            import ctypes
            key_code = _get_key_code(key)
            ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)  # Key down
            success = True

        return success

    except Exception as e:
        instance.logger.error(f"❌ Ошибка зажатия клавиши {key}: {e}")
        return False


def _release_key(instance, key):
    """Отпускание клавиши"""
    try:
        # Используем hardware_input для отпускания клавиши
        if hasattr(instance.hardware_input, 'key_up'):
            # Если есть специальный метод
            success = instance.hardware_input.key_up(_get_key_code(key))
        else:
            # Fallback через ctypes
            import ctypes
            key_code = _get_key_code(key)
            ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)  # Key up (KEYEVENTF_KEYUP = 2)
            success = True

        return success

    except Exception as e:
        instance.logger.error(f"❌ Ошибка отпускания клавиши {key}: {e}")
        return False


def _get_key_code(key):
    """Получение кода клавиши"""
    key_codes = {
        'y': 0x59,  # Y key
        'enter': 0x0D,
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12
    }

    return key_codes.get(key.lower(), ord(key.upper()) if len(key) == 1 else 0x59)


@register_action("random_chat_wheel")
def random_chat_wheel_action(instance, **kwargs):
    """Колесо чата с настраиваемым шансом активации"""

    chance = kwargs.get('chance', 0.25)  # 25% по умолчанию

    # Проверяем, должно ли активироваться колесо
    if random.random() < chance:
        instance.logger.info(f"🎲 Колесо чата активировано (шанс: {chance * 100:.0f}%)")
        return execute_chat_wheel(instance, **kwargs)
    else:
        instance.logger.debug(f"🎲 Колесо чата пропущено (шанс: {chance * 100:.0f}%)")
        return True  # Не ошибка, просто не активировалось
