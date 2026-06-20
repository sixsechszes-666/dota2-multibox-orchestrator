# dota_manager.py
import logging
import os
import random
import time

import win32com.client
import win32gui

from core.prepare import PrepareMatchmaking

logger = logging.getLogger(__name__)


# Actions that operate on the whole system (Sandboxie, Steam, parties) instead of
# on a single Dota 2 window. They run once against a throwaway context and never
# require window activation. Any action whose name contains "sandbox" is also
# treated as a system action.
SYSTEM_ACTIONS = frozenset({
    "check_update",
    "sandbox_status",
    "launch_sandbox_instances",
    "stop_sandbox_instances",
    "wait_delay",
    "select_random_instances",
    "launch_selected_sandbox_instances",
    "collect_selected_player_ids",
    "create_party_with_selected",
    "collect_player_ids",
    "update_party_ids_from_sandboxes",
    "validate_sandbox_steam_setup",
})

# Actions that first run on every instance and then keep all instances busy with
# randomized minimap clicks. The trailing value is the default duration (seconds);
# the preceding strings are the kwargs consulted (in order) to override it.
CYCLIC_MAP_CLICK_ACTIONS = {
    "fight_on_river": ("cyclic_duration", "interval", 80),
    "jungle_farm": ("interval", 20),
}

# Minimap rectangle (relative to a window) used for cyclic "stay busy" clicks.
MINIMAP_AREA = {"min_x": 26, "min_y": 726, "max_x": 228, "max_y": 931}


def enum_windows_callback(hwnd, windows):
    """Callback for ``EnumWindows``: collect visible titled windows."""
    window_title = win32gui.GetWindowText(hwnd)
    if window_title and win32gui.IsWindowVisible(hwnd):
        windows.append((hwnd, window_title))


def get_all_windows_with_title(title):
    """Return handles of all visible windows whose title contains ``title``."""
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    return [hwnd for hwnd, window_title in windows if title in window_title]


def is_game_ended(result):
    """True if an action result signals the match has ended."""
    return (
        isinstance(result, (tuple, list))
        and len(result) > 1
        and isinstance(result[1], str)
        and "game_ended" in result[1]
    )


class OptimizedHardwareManager:
    """Dispatches high-level actions to one or more Dota 2 instances.

    Actions fall into three families, each with its own runner:

    * **system**   — run once, no game window required (see ``SYSTEM_ACTIONS``);
    * **cyclic**   — run on every instance, then keep them busy with minimap
      clicks for a while (see ``CYCLIC_MAP_CLICK_ACTIONS``);
    * **per-instance** — the default: activate each window in turn and run there.
    """

    def __init__(self, manager):
        self.manager = manager
        self.switch_delay = 0.1

        # Action registry, populated by ``_load_all_actions``.
        self.get_action = None
        self.get_all_actions = None
        self.available_actions = {}

        self._load_all_actions()

    # ------------------------------------------------------------------ #
    # Action registry
    # ------------------------------------------------------------------ #
    def _load_all_actions(self):
        """Import every module under ``actions/`` so its decorators register."""
        try:
            from utils.actions_registry import get_action, get_all_actions
            self.get_action = get_action
            self.get_all_actions = get_all_actions

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            actions_dir = os.path.join(project_root, "actions")

            if os.path.exists(actions_dir):
                import importlib
                for filename in os.listdir(actions_dir):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        module_name = f"actions.{filename[:-3]}"
                        try:
                            importlib.import_module(module_name)
                            logger.debug("✅ Загружен модуль действий: %s", module_name)
                        except ImportError as e:
                            logger.error("❌ Ошибка загрузки модуля %s: %s", module_name, e)

            for action_name in self.get_all_actions():
                self.available_actions[action_name] = self.get_action(action_name)

        except ImportError as e:
            logger.warning("⚠️ Реестр действий недоступен: %s", e)
            self.get_action = None
            self.get_all_actions = lambda: ["hero_pick", "team_check", "fight_on_river"]
            self.available_actions = {"hero_pick": None, "team_check": None, "fight_on_river": None}

    def get_available_actions(self):
        """Return the list of all registered action names."""
        if self.get_all_actions:
            return self.get_all_actions()
        return ["hero_pick", "team_check", "fight_on_river"]

    # ------------------------------------------------------------------ #
    # Dispatch
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_system_action(action):
        return action in SYSTEM_ACTIONS or "sandbox" in action

    def execute_hardware_sequence(self, actions, hero_image=None, **kwargs):
        """Run a list of actions, routing each to the appropriate runner."""
        all_results = []
        try:
            for action in actions:
                if self._is_system_action(action):
                    results = self._run_system_action(action, hero_image=hero_image, **kwargs)
                elif action in CYCLIC_MAP_CLICK_ACTIONS:
                    results = self._run_cyclic_action(action, hero_image=hero_image, **kwargs)
                else:
                    results = self._run_per_instance_action(action, hero_image=hero_image, **kwargs)

                # A "game ended" signal stops the whole sequence immediately.
                if len(results) == 1 and is_game_ended(results[0]):
                    return results
                all_results.extend(results)

        except Exception as e:
            logger.exception("❌ Ошибка в аппаратном выполнении: %s", e)
            all_results.append((False, str(e)))

        return all_results

    def _resolve_action(self, action):
        """Return the registered callable for ``action`` or ``None``."""
        if self.get_action and self.available_actions.get(action):
            return self.available_actions[action]
        return None

    def _ensure_instances(self, action):
        """Make sure at least one instance is discovered before acting."""
        if self.manager.instances:
            return True
        logger.info("🔍 Поиск экземпляров для действия '%s'...", action)
        if not self.manager.discover_instances():
            logger.error("❌ Экземпляры не найдены для '%s'", action)
            return False
        return True

    def _run_on_each_instance(self, action_func, action, hero_image=None, **kwargs):
        """Activate every instance window in turn and run ``action_func`` there.

        Returns ``(results, ended_result)`` where ``ended_result`` is the result
        that signalled the match ended (or ``None`` if it did not).
        """
        results = []
        for instance in self.manager.instances:
            start = time.time()

            if not self.ultra_fast_activate(instance.hwnd):
                results.append((False, "window_activation_failed"))
                continue

            try:
                result = action_func(instance, hero_image=hero_image, **kwargs)
                results.append(result)
                if is_game_ended(result):
                    logger.info("🏆 Игра завершена! Экран: %s", result[1])
                    return results, result
            except Exception as e:
                logger.error("❌ Ошибка '%s' на экземпляре #%s: %s", action, instance.instance_id, e)
                results.append((False, str(e)))
                continue

            logger.info("✅ Экземпляр #%s: '%s' за %.2fс", instance.instance_id, action, time.time() - start)
            time.sleep(self.switch_delay)

        return results, None

    # ------------------------------------------------------------------ #
    # Runners
    # ------------------------------------------------------------------ #
    def _run_system_action(self, action, hero_image=None, **kwargs):
        """Run a system action once, without touching any game window."""
        logger.info("🚀 Системное действие: '%s' (без окон Dota 2)", action)
        action_func = self._resolve_action(action)
        if not action_func:
            logger.error("❌ Действие '%s' не найдено в реестре", action)
            return [(False, f"action_not_found_{action}")]
        try:
            result = action_func(PrepareMatchmaking(), hero_image=hero_image, **kwargs)
            logger.info("✅ '%s' выполнено: %s", action, result)
            return [result]
        except Exception as e:
            logger.error("❌ Ошибка выполнения '%s': %s", action, e)
            return [(False, str(e))]

    def _run_per_instance_action(self, action, hero_image=None, **kwargs):
        """Run a registered action on every instance, one window at a time."""
        action_func = self._resolve_action(action)
        if not action_func:
            # Not in the registry — fall back to the built-in legacy handlers.
            return self._execute_standard_action(action, hero_image, **kwargs)

        if not self._ensure_instances(action):
            return [(False, "no_instances_available")]

        results, ended = self._run_on_each_instance(action_func, action, hero_image, **kwargs)
        return [ended] if ended is not None else results

    def _run_cyclic_action(self, action, hero_image=None, **kwargs):
        """Run an action on every instance, then keep them busy with map clicks."""
        action_func = self._resolve_action(action)
        if not action_func:
            logger.error("❌ Действие '%s' не найдено в реестре", action)
            return [(False, f"action_not_found_{action}")]

        if not self._ensure_instances(action):
            return [(False, "no_instances_available")]

        logger.info("⚔️ Фаза 1: '%s' на всех экземплярах", action)
        results, ended = self._run_on_each_instance(action_func, action, hero_image, **kwargs)
        if ended is not None:
            return [ended]

        *keys, default = CYCLIC_MAP_CLICK_ACTIONS[action]
        duration = next((kwargs[k] for k in keys if k in kwargs), default)
        if duration > 0:
            logger.info("🗺️ Фаза 2: циклические клики по карте (%sс)", duration)
            results.extend(self._execute_cyclic_map_clicks(duration))
        else:
            logger.info("ℹ️ Длительность = 0, пропускаем циклические клики")

        return results

    def _execute_cyclic_map_clicks(self, duration):
        """Click random minimap points across all instances, round-robin, for ``duration`` seconds."""
        if not self.manager.instances:
            logger.error("❌ Нет экземпляров для циклических кликов")
            return [(False, "no_instances_for_cyclic_clicks")]

        logger.info(
            "🎯 Карта (%d,%d)-(%d,%d), %sс, %d экземпляров",
            MINIMAP_AREA["min_x"], MINIMAP_AREA["min_y"],
            MINIMAP_AREA["max_x"], MINIMAP_AREA["max_y"],
            duration, len(self.manager.instances),
        )

        start_time = time.time()
        total_clicks = 0
        index = 0
        click_delay = 0.1  # minimum gap between clicks of different instances

        try:
            while time.time() - start_time < duration:
                instance = self.manager.instances[index]
                index = (index + 1) % len(self.manager.instances)

                try:
                    if not self.ultra_fast_activate(instance.hwnd):
                        logger.warning("⚠️ Не удалось активировать экземпляр #%s", instance.instance_id)
                        time.sleep(click_delay)
                        continue

                    window_coords = instance.get_window_coordinates()
                    if not window_coords:
                        logger.warning("⚠️ Нет координат окна экземпляра #%s", instance.instance_id)
                        time.sleep(click_delay)
                        continue

                    rx = random.randint(MINIMAP_AREA["min_x"], MINIMAP_AREA["max_x"])
                    ry = random.randint(MINIMAP_AREA["min_y"], MINIMAP_AREA["max_y"])
                    window_x, window_y, _, _ = window_coords

                    if instance.hardware_click(window_x + rx, window_y + ry, "left"):
                        total_clicks += 1
                        if total_clicks % 50 == 0:
                            remaining = duration - (time.time() - start_time)
                            logger.info(
                                "🗺️ Клик #%d: экземпляр #%s → (%d, %d), осталось %.1fс",
                                total_clicks, instance.instance_id, rx, ry, remaining,
                            )
                except Exception as e:
                    logger.error("❌ Ошибка клика экземпляра #%s: %s", instance.instance_id, e)

                time.sleep(click_delay)

            elapsed = time.time() - start_time
            rate = total_clicks / elapsed if elapsed > 0 else 0
            logger.info(
                "✅ Циклические клики завершены: %d кликов за %.1fс (%.1f кликов/с)",
                total_clicks, elapsed, rate,
            )
            return [(True, f"cyclic_clicks_completed_{total_clicks}_{elapsed:.1f}s")]

        except Exception as e:
            logger.error("❌ Ошибка циклических кликов: %s", e)
            return [(False, str(e))]

    def _execute_standard_action(self, action, hero_image=None, **kwargs):
        """Legacy fallback for built-in actions that predate the registry."""
        if not self._ensure_instances(action):
            return [(False, "no_instances_available")]

        action_results = []
        for instance in self.manager.instances:
            start_time = time.time()

            if not self.ultra_fast_activate(instance.hwnd):
                action_results.append((False, "window_activation_failed"))
                continue

            try:
                if action == "hero_pick":
                    result = instance.run_hero_pick_hardware(hero_image=hero_image, timeout=60)
                elif action == "team_check":
                    result = instance.run_team_check(timeout=90)
                elif action == "fight_on_river":
                    result = self._legacy_fight_on_river(instance, **kwargs)
                else:
                    logger.error("❌ Неизвестное действие: %s", action)
                    result = (False, f"unknown_action_{action}")

                if not isinstance(result, tuple):
                    result = (True, result) if result else (False, "no_result")

            except Exception as e:
                logger.error("❌ Ошибка выполнения %s: %s", action, e)
                result = (False, str(e))

            action_results.append(result)
            logger.info("✅ Экземпляр #%s завершён за %.2fс", instance.instance_id, time.time() - start_time)
            time.sleep(self.switch_delay)

        return action_results

    @staticmethod
    def _legacy_fight_on_river(instance, **kwargs):
        """Resolve the legacy ``fight_on_river`` implementation on an instance."""
        logger.warning("⚠️ fight_on_river выполняется legacy-способом (без циклических кликов)")
        if hasattr(instance, "gaming_actions"):
            return instance.gaming_actions.fight_on_river_hardware(
                timeout=kwargs.get("timeout", 60), iteration=kwargs.get("iteration")
            )
        if hasattr(instance, "fight_on_river_hardware"):
            return instance.fight_on_river_hardware(
                timeout=kwargs.get("timeout", 60), iteration=kwargs.get("iteration")
            )
        logger.error("❌ Метод fight_on_river_hardware не найден")
        return (False, "method_not_found")

    # ------------------------------------------------------------------ #
    # Window activation
    # ------------------------------------------------------------------ #
    def ultra_fast_activate(self, hwnd, max_attempts=3):
        """Bring ``hwnd`` to the foreground, working around Windows restrictions."""
        try:
            if win32gui.GetForegroundWindow() == hwnd:
                return True
        except Exception as e:
            logger.warning("⚠️ Не удалось получить активное окно: %s", e)

        # Sending Alt unblocks SetForegroundWindow's foreground-lock restriction.
        win32com.client.Dispatch("WScript.Shell").SendKeys("%")

        for attempt in range(max_attempts):
            try:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                    time.sleep(0.05)

                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.05)

                if win32gui.GetForegroundWindow() == hwnd:
                    return True
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error("❌ Ошибка активации: %s", e)
                time.sleep(0.1)

        # Fallback: minimize then restore to force a foreground transition.
        try:
            win32gui.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            time.sleep(0.1)
            win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
            return True
        except Exception as e:
            logger.error("❌ Альтернативный метод активации не сработал: %s", e)

        return False


class MultiInstanceDotaManager:
    """Discovers and tracks the running Dota 2 windows to drive."""

    def __init__(self, window_title="Dota 2", confidence=0.8, debug_mode=True, log_dir="logs"):
        self.window_title = window_title
        self.confidence = confidence
        self.debug_mode = debug_mode
        self.instances = []

        self.log_dir = os.path.abspath(log_dir)
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            logger.error("❌ Ошибка при создании директории логов: %s", e)
            self.log_dir = os.path.abspath("..")

    def _build_instance(self, hwnd, index, timestamp, pid=None):
        """Create a configured :class:`PrepareMatchmaking` bound to ``hwnd``."""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, width, height = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]

        log_file = os.path.join(self.log_dir, f"dota2_instance_{index + 1}_{timestamp}.log")
        try:
            with open(log_file, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Init instance #{index + 1} (PID={pid}, HWND={hwnd})\n")
        except Exception as e:
            logger.error("❌ Ошибка при создании файла лога: %s", e)
            log_file = None

        instance = PrepareMatchmaking(
            window_title=self.window_title,
            confidence=self.confidence,
            debug_mode=self.debug_mode,
            log_file=log_file,
        )
        instance.hwnd = hwnd
        instance.window_coords = (x, y, width, height)
        instance.instance_id = str(index + 1)
        instance.process_pid = pid

        logger.info("✅ Экземпляр #%d: PID=%s, HWND=%s, %d,%d %dx%d", index + 1, pid, hwnd, x, y, width, height)
        return instance

    def discover_instances(self):
        """Discover Dota 2 windows, preferring HWNDs registered by the tracker."""
        try:
            from input.hwnd_tracker import HWNDTracker
        except ImportError:
            logger.warning("⚠️ HWND Tracker недоступен, используем поиск по заголовку окна")
            return self._discover_instances_fallback()

        hwnd_tracker = HWNDTracker()
        hwnd_tracker.cleanup_invalid_entries()
        registered_hwnds = hwnd_tracker.get_all_registered_hwnds()

        if not registered_hwnds:
            logger.error("❌ Нет зарегистрированных HWND для Dota 2")
            return False

        logger.info("✅ Найдено %d зарегистрированных окон Dota 2", len(registered_hwnds))

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.instances = []
        for i, (pid, hwnd) in enumerate(registered_hwnds.items()):
            try:
                self.instances.append(self._build_instance(hwnd, i, timestamp, pid=pid))
            except Exception as e:
                logger.error("❌ Ошибка обработки HWND %s (PID %s): %s", hwnd, pid, e)

        return len(self.instances) > 0

    def _discover_instances_fallback(self):
        """Fallback discovery: match windows purely by their title."""
        hwnd_list = get_all_windows_with_title(self.window_title)
        if not hwnd_list:
            logger.error("❌ Не найдено окон с заголовком '%s'", self.window_title)
            return False

        logger.info("✅ Найдено %d окон с заголовком '%s'", len(hwnd_list), self.window_title)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.instances = [self._build_instance(hwnd, i, timestamp) for i, hwnd in enumerate(hwnd_list)]
        return True
