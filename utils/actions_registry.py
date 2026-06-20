# actions_registry.py
import functools

# Реестр всех действий
ACTIONS_REGISTRY = {}

def register_action(action_name):
    """Декоратор для регистрации действий"""
    def decorator(func):
        ACTIONS_REGISTRY[action_name] = func
        return func
    return decorator

def get_action(action_name):
    """Получить действие по имени"""
    return ACTIONS_REGISTRY.get(action_name)

def get_all_actions():
    """Получить все зарегистрированные действия"""
    return list(ACTIONS_REGISTRY.keys())
