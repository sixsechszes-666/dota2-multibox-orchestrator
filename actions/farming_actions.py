# actions/farming_actions.py
from utils.actions_registry import register_action


@register_action("jungle_farm")
def jungle_farm_action(instance, **kwargs):
    """Фарм леса с автоматическим распределением кемпов"""
    timeout = kwargs.get('timeout', 120)
    return instance.jungle_farm_hardware(timeout=timeout)

@register_action("clear_team_cache")
def clear_team_cache_action(instance, **kwargs):
    """Очистка кэша определения команды"""
    try:
        instance.clear_team_cache()

        instance.logger.info("✅ Кэш команды успешно очищен")
        return True, "cache_cleared"
    except Exception as e:
        instance.logger.error(f"❌ Ошибка очистки кэша: {e}")
        return False, None


@register_action("clear_caches")
def clear_caches_action(instance, **kwargs):
    """Очистка всех кешей: команды и героя"""
    try:
        if hasattr(instance.gaming_actions, 'clear_team_cache'):
            instance.gaming_actions.clear_team_cache()
            instance.logger.info("✅ Кэш команды успешно очищен")
        else:
            instance.logger.debug("⚠️ Метод clear_team_cache не найден в GamingActions")

        if hasattr(instance.gaming_actions, 'clear_hero_cache'):
            instance.gaming_actions.clear_hero_cache()
            instance.logger.info("✅ Кэш героя успешно очищен")
        else:
            instance.logger.debug("⚠️ Метод clear_hero_cache не найден в GamingActions")

        instance.logger.info("🎉 Все кеши успешно очищены")
        return True, "caches_cleared"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка очистки кешей: {e}")
        return False, None

@register_action("select_neutral_item")
def select_neutral_item_action(instance, **kwargs):
    """Выбор нейтрального предмета"""
    iteration = kwargs.get('iteration', 1)
    return instance.select_neutral_item(iteration=iteration)

@register_action("observe_hero")
def observe_hero_action(instance, **kwargs):
    """Наблюдение за героем"""
    return instance.observe_hero()
