# actions/party_actions.py
from utils.actions_registry import register_action


@register_action("create_party_multi")
def create_party_multi_action(instance, **kwargs):
    """Создание пати с множественными приглашениями (только локальный мастер)"""
    party_ids = kwargs.get('party_ids', [])
    timeout = kwargs.get('timeout', 30)

    return instance.create_party_with_multiple_invites(party_ids_list=party_ids, timeout=timeout)


@register_action("create_party")
def create_party_action(instance, **kwargs):
    """Создание пати с одним ID (обратная совместимость)"""
    party_id = kwargs.get('party_id', 'default_party')
    timeout = kwargs.get('timeout', 30)

    return instance.create_party_with_multiple_invites(party_ids_list=[party_id], timeout=timeout)


@register_action("join_party")
def join_party_action(instance, **kwargs):
    """Присоединение к пати (только локальный мастер)"""
    party_id = kwargs.get('party_id', 'default_party')

    return instance.join_party(party_id=party_id)


@register_action("leave_party")
def leave_party_action(instance, **kwargs):
    """Покинуть пати (только локальный мастер)"""
    return instance.leave_party()


@register_action("wait_parties_ready")
def wait_parties_ready_action(instance, **kwargs):
    """Ожидание готовности всех пати на всех ПК"""
    timeout = kwargs.get('timeout', 300)
    check_interval = kwargs.get('check_interval', 5)

    return instance.party_manager.wait_for_all_parties_ready(
        timeout=timeout,
        check_interval=check_interval
    )


@register_action("setup_region_play")
def setup_region_play_action(instance, **kwargs):
    """Настройка региона и запуск поиска игры"""
    region = kwargs.get('region', 'DUBAI')
    timeout = kwargs.get('timeout', 30)

    return instance.party_manager.setup_region_and_play(
        region=region,
        timeout=timeout
    )


@register_action("synchronized_accept")
def synchronized_accept_action(instance, **kwargs):
    """Синхронизированное принятие игры с повторными попытками"""
    timeout = kwargs.get('timeout', 300)
    check_interval = kwargs.get('check_interval', 1)
    max_checks = kwargs.get('max_checks', 20)
    max_attempts = kwargs.get('max_attempts', 10)

    return instance.party_manager.synchronized_accept_game(
        timeout=timeout,
        check_interval=check_interval,
        max_checks=max_checks,
        max_attempts=max_attempts
    )


@register_action("check_reconnect")
def check_reconnect_action(instance, **kwargs):
    """Проверка наличия кнопки Reconnect с автоматическим нажатием и ожиданием"""
    try:
        confidence = kwargs.get('confidence', 0.8)
        auto_click = kwargs.get('auto_click', True)
        click_delay = kwargs.get('click_delay', 1.0)
        wait_after_click = kwargs.get('wait_after_click', 5.0)  # Ожидание после клика
        verify_click = kwargs.get('verify_click', True)  # Проверяем исчезла ли кнопка

        # Проверяем наличие кнопки
        found, position = instance.check_reconnect_button(confidence=confidence)

        if found:
            instance.logger.info("⚠️ Обнаружена кнопка Reconnect")

            if auto_click:
                instance.logger.info(f"🖱️ Выполняю автоматический клик по кнопке Reconnect")

                # Задержка перед кликом
                import time
                time.sleep(click_delay)

                # Выполняем клик
                click_success = instance.hardware_click(position[0], position[1], 'left')

                if click_success:
                    instance.logger.info("✅ Кнопка Reconnect нажата")

                    # Ожидание после клика
                    instance.logger.info(f"⏳ Ожидание {wait_after_click}с после клика...")
                    time.sleep(wait_after_click)

                    # Проверяем, исчезла ли кнопка
                    if verify_click:
                        found_after, _ = instance.check_reconnect_button(confidence=confidence)

                        if not found_after:
                            instance.logger.info("✅ Кнопка Reconnect исчезла - переподключение инициировано")
                            return True, "reconnect_successful"
                        else:
                            instance.logger.warning("⚠️ Кнопка Reconnect все еще видна после клика")
                            return True, "reconnect_clicked_but_visible"
                    else:
                        return True, "reconnect_clicked"
                else:
                    instance.logger.error("❌ Не удалось кликнуть по кнопке Reconnect")
                    return True, "reconnect_click_failed"
            else:
                instance.logger.info("📋 Кнопка Reconnect найдена, но автоклик отключен")
                return True, "reconnect_found_no_click"
        else:
            instance.logger.debug("✅ Кнопка Reconnect отсутствует - соединение стабильно")
            return True, "no_reconnect_button"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка проверки Reconnect: {e}")
        return True, "reconnect_check_error"

