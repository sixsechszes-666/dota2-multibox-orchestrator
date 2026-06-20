# actions/combat_actions.py
from utils.actions_registry import register_action


@register_action("fight_on_river")
def fight_on_river_action(instance, **kwargs):
    """Бой на реке с синхронизированными координатами по итерациям"""
    timeout = kwargs.get('timeout', 180)
    iteration = kwargs.get('iteration')  # Получаем номер итерации
    return instance.fight_on_river_hardware(timeout=timeout, iteration=iteration)


@register_action("winning_strategy")
def winning_strategy_action(instance, **kwargs):
    """Выполнение стратегии победы с проверкой конца игры"""
    timeout = kwargs.get('timeout', 180)
    iteration = kwargs.get('iteration')

    # Проверяем конец игры перед выполнением стратегии
    game_ended = instance.check_game_end()
    if game_ended:
        instance.logger.info(f"🏆 Игра завершена! Обнаружен экран: {game_ended}")
        return True, f"game_ended_{game_ended}"

    # Если игра не завершена, выполняем стратегию
    result = instance.execute_winning_strategy(timeout=timeout, iteration=iteration)

    # Проверяем конец игры после выполнения стратегии
    game_ended = instance.check_game_end()
    if game_ended:
        instance.logger.info(f"🏆 Игра завершена во время стратегии! Обнаружен экран: {game_ended}")
        return True, f"game_ended_{game_ended}"

    return result

