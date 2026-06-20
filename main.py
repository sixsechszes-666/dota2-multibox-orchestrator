"""Command-line entry point for the Dota 2 multibox orchestrator.

Usage:
    python main.py --scenario standard_game      # run a named scenario
    python main.py --scenario game_loop          # run the endless launch→play loop
    python main.py --actions hero_pick team_check [--hero invoker]
"""
import argparse
import logging
import time

import yaml

from core.dota_manager import (
    MultiInstanceDotaManager,
    OptimizedHardwareManager,
    SYSTEM_ACTIONS,
    is_game_ended,
)
from utils.logging_setup import configure_logging

logger = logging.getLogger(__name__)

SCENARIOS_FILE = "config/scenarios.yaml"

# One "big loop" = a fresh launch followed by this many game cycles, then restart.
GAME_CYCLES_PER_LOOP = 1
PAUSE_BETWEEN_CYCLES = 10   # seconds between game cycles
RESTART_DELAY = 60          # seconds between big loops
STARTUP_RETRY_DELAY = 30    # seconds to wait after a failed startup
CRASH_RESTART_DELAY = 120   # seconds to wait after an unexpected crash


def _needs_game_window(action_name):
    """True if running ``action_name`` requires a live Dota 2 window."""
    return action_name not in SYSTEM_ACTIONS and "sandbox" not in action_name


def execute_scenario(scenario_name, hardware_manager, manager):
    """Run a scenario from the YAML file; stop early if a match ends."""
    try:
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error("❌ Не удалось прочитать %s: %s", SCENARIOS_FILE, e)
        return False

    scenario = config.get("scenarios", {}).get(scenario_name)
    if scenario is None:
        logger.error("❌ Сценарий '%s' не найден", scenario_name)
        return False

    logger.info("🎯 Выполнение сценария: %s", scenario_name)

    has_sandbox_actions = any("sandbox" in step.get("action", "") for step in scenario)
    has_window_actions = any(_needs_game_window(step.get("action", "")) for step in scenario)

    # Pure game scenarios need instances up front; sandbox scenarios launch their
    # own and discover instances lazily once Sandboxie has started them.
    if has_window_actions and not has_sandbox_actions:
        if not manager.discover_instances():
            logger.error("❌ Не удалось найти экземпляры Dota 2")
            return False

    for step in scenario:
        action_name = step["action"]
        repeat = step.get("repeat", 1)
        interval = step.get("interval", 0)
        iteration_start = step.get("iteration_start", 1)
        kwargs = {k: v for k, v in step.items()
                  if k not in ("action", "repeat", "interval", "iteration_start")}

        # In mixed scenarios, instances may not exist until Sandboxie has launched.
        if _needs_game_window(action_name) and has_sandbox_actions and not manager.instances:
            logger.info("🔍 Поиск экземпляров после запуска Sandboxie...")
            if not manager.discover_instances():
                logger.warning("⚠️ Экземпляры ещё не готовы, пропускаем '%s'", action_name)
                continue

        for i in range(repeat):
            logger.info("🎯 %s (итерация %d/%d)", action_name, i + 1, repeat)

            if action_name == "fight_on_river":
                kwargs["iteration"] = iteration_start + i

            try:
                results = hardware_manager.execute_hardware_sequence([action_name], **kwargs)
                if any(is_game_ended(r) for r in results):
                    logger.info("🏆 Игра завершена — сценарий '%s' успешно завершён", scenario_name)
                    return True
            except Exception as e:
                logger.warning("⚠️ Ошибка выполнения '%s': %s", action_name, e)

            if i < repeat - 1 and interval > 0:
                logger.info("⏳ Ожидание %d секунд...", interval)
                time.sleep(interval)

    logger.info("✅ Сценарий '%s' завершён полностью", scenario_name)
    return True


def execute_infinite_loop(hardware_manager, manager):
    """Endless loop: startup → GAME_CYCLES_PER_LOOP game cycles → restart."""
    loop_count = 0
    while True:
        loop_count += 1
        logger.info("%s", "=" * 60)
        logger.info("🔄 НАЧАЛО БОЛЬШОГО ЦИКЛА #%d", loop_count)
        logger.info("%s", "=" * 60)

        try:
            logger.info("🚀 Этап 1: ЗАПУСК (цикл #%d)", loop_count)
            if not execute_scenario("startup", hardware_manager, manager):
                logger.error("❌ Ошибка запуска, повтор через %d с...", STARTUP_RETRY_DELAY)
                time.sleep(STARTUP_RETRY_DELAY)
                continue

            successful_cycles = 0
            for cycle in range(GAME_CYCLES_PER_LOOP):
                logger.info("🎮 Этап 2: ИГРОВОЙ ЦИКЛ %d/%d (большой цикл #%d)",
                            cycle + 1, GAME_CYCLES_PER_LOOP, loop_count)

                if execute_scenario("game_cycle", hardware_manager, manager):
                    successful_cycles += 1
                    logger.info("✅ Игровой цикл %d/%d успешен", cycle + 1, GAME_CYCLES_PER_LOOP)
                else:
                    logger.warning("⚠️ Игровой цикл %d/%d с ошибками", cycle + 1, GAME_CYCLES_PER_LOOP)

                if cycle < GAME_CYCLES_PER_LOOP - 1:
                    time.sleep(PAUSE_BETWEEN_CYCLES)

            logger.info("📊 Большой цикл #%d: %d/%d игровых циклов успешно",
                        loop_count, successful_cycles, GAME_CYCLES_PER_LOOP)
            logger.info("🔄 Перезапуск через %d с...", RESTART_DELAY)
            time.sleep(RESTART_DELAY)

        except KeyboardInterrupt:
            logger.warning("⚠️ Получен сигнал остановки. Завершение работы...")
            break
        except Exception as e:
            logger.exception("❌ Критическая ошибка в большом цикле #%d: %s", loop_count, e)
            time.sleep(CRASH_RESTART_DELAY)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Dota 2 multibox orchestrator")
    parser.add_argument("--scenario", nargs="?", const="standard_game", metavar="NAME",
                        help="run a named scenario from config/scenarios.yaml "
                             "(use 'game_loop' for the endless loop)")
    parser.add_argument("--actions", nargs="+", metavar="ACTION",
                        help="run one or more actions ad-hoc")
    parser.add_argument("--hero", metavar="IMAGE", help="hero template for --actions")
    return parser.parse_args(argv)


def main(argv=None):
    configure_logging()
    args = parse_args(argv)

    manager = MultiInstanceDotaManager(window_title="Dota 2", confidence=0.8,
                                       debug_mode=False, log_dir="logs")
    hardware_manager = OptimizedHardwareManager(manager)
    logger.info("📋 Доступные действия: %s", hardware_manager.get_available_actions())

    if args.scenario:
        if args.scenario == "game_loop":
            execute_infinite_loop(hardware_manager, manager)
        else:
            execute_scenario(args.scenario, hardware_manager, manager)

    elif args.actions:
        if any(_needs_game_window(a) for a in args.actions) and not manager.discover_instances():
            logger.error("❌ Не удалось найти экземпляры Dota 2")
            return 1
        hardware_manager.execute_hardware_sequence(args.actions, hero_image=args.hero)

    else:
        if not manager.discover_instances():
            logger.error("❌ Не удалось найти экземпляры Dota 2")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
