# actions/team_actions.py
from utils.actions_registry import register_action


@register_action("team_check")
def team_check_action(instance, **kwargs):
    """Проверка команды"""
    timeout = kwargs.get('timeout', 300)
    return instance.run_team_check(timeout=timeout)


@register_action("wait_game_loading")
def wait_game_loading_action(instance, **kwargs):
    """Ожидание загрузки игры"""
    timeout = kwargs.get('timeout', 300)
    loading_image = kwargs.get('loading_image')
    return instance.wait_for_game_loading(loading_image=loading_image, timeout=timeout)
