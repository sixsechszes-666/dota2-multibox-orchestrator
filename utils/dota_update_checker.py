import subprocess
import re
import os
import yaml
import time
import psutil
from utils.actions_registry import register_action


def check_sandbox_processes(sandbox_name):
    """Проверяет, есть ли активные процессы в песочнице БЕЗ использования WINDOWTITLE"""

    try:
        print(f"🔍 Проверка процессов в песочнице '{sandbox_name}' (без WINDOWTITLE)")

        # ✅ МЕТОД 1: Прямой поиск окон через win32gui
        found_windows = _find_sandbox_windows_direct(sandbox_name)
        if found_windows:
            return True

        # ✅ МЕТОД 2: Анализ процессов через WMIC
        found_processes = _find_sandbox_processes_wmic(sandbox_name)
        if found_processes:
            return True

        # ✅ МЕТОД 3: Поиск через Sandboxie Start.exe
        found_via_sandboxie = _check_sandbox_via_start_exe(sandbox_name)
        if found_via_sandboxie:
            return True

        print(f"✅ Песочница {sandbox_name} пуста (нет активных процессов)")
        return False

    except Exception as e:
        print(f"❌ Ошибка проверки процессов: {e}")
        return False


def _find_sandbox_windows_direct(sandbox_name):
    """Прямой поиск окон песочницы через win32gui"""

    try:
        import win32gui
        import win32process
        import psutil

        print(f"   📋 Метод 1: Прямой поиск окон песочницы #{sandbox_name}")

        def enum_windows_callback(hwnd, windows):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and 'dota' in title.lower():

                        # Получаем PID процесса окна
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)

                        # Получаем информацию о процессе
                        try:
                            process = psutil.Process(pid)
                            cmdline = ' '.join(process.cmdline()).lower()
                            exe_path = process.exe().lower()

                            windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'pid': pid,
                                'cmdline': cmdline,
                                'exe_path': exe_path
                            })

                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass  # Процесс недоступен

            except Exception:
                pass  # Пропускаем проблемные окна
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        print(f"   🔍 Найдено {len(windows)} окон Dota 2")

        # Ищем признаки песочницы в заголовках и процессах
        sandbox_windows = []
        sandbox_patterns = [
            f"[#{sandbox_name}]",
            f"[{sandbox_name}]",
            f"sandbox_{sandbox_name}",
            f"sandbox {sandbox_name}",
            f"box_{sandbox_name}",
            f"box {sandbox_name}",
            f"#{sandbox_name}"
        ]

        for window in windows:
            title_lower = window['title'].lower()
            cmdline_lower = window['cmdline']
            exe_path_lower = window['exe_path']

            # Проверяем заголовок окна
            for pattern in sandbox_patterns:
                if pattern in title_lower:
                    sandbox_windows.append(window)
                    print(f"   ✅ Найдено по заголовку: {window['title']} (PID: {window['pid']})")
                    break
            else:
                # Проверяем командную строку процесса
                for pattern in sandbox_patterns:
                    if pattern in cmdline_lower:
                        sandbox_windows.append(window)
                        print(f"   ✅ Найдено по cmdline: {window['title']} (PID: {window['pid']})")
                        break
                else:
                    # Проверяем путь к исполняемому файлу
                    sandbox_path_patterns = [
                        f"sandbox\\{sandbox_name}\\",
                        f"sandbox_{sandbox_name}\\",
                        f"box_{sandbox_name}\\",
                        f"#{sandbox_name}\\"
                    ]

                    for pattern in sandbox_path_patterns:
                        if pattern in exe_path_lower:
                            sandbox_windows.append(window)
                            print(f"   ✅ Найдено по пути: {window['title']} (PID: {window['pid']})")
                            break

        return len(sandbox_windows) > 0

    except ImportError:
        print(f"   ⚠️ win32gui/psutil недоступен")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка поиска окон: {e}")
        return False


def _find_sandbox_processes_wmic(sandbox_name):
    """Поиск процессов песочницы через WMIC"""

    try:
        print(f"   📋 Метод 2: Анализ процессов через WMIC")

        cmd = ["wmic", "process", "where", "name='dota2.exe'", "get", "ProcessId,CommandLine,ExecutablePath"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            print(f"   ⚠️ WMIC недоступен")
            return False

        lines = result.stdout.split('\n')
        sandbox_processes = []

        print(f"   🔍 Анализ {len(lines)} строк из WMIC")

        for line in lines:
            if line.strip() and 'dota2.exe' in line:
                line_lower = line.lower()

                # Расширенный список признаков песочницы
                sandbox_indicators = [
                    f"sandbox_{sandbox_name}",
                    f"sandbox {sandbox_name}",
                    f"box_{sandbox_name}",
                    f"box {sandbox_name}",
                    f"#{sandbox_name}",
                    f"[#{sandbox_name}]",
                    f"[{sandbox_name}]",
                    f"\\{sandbox_name}\\",
                    f"/{sandbox_name}/",
                    f"sandbox\\{sandbox_name}\\",
                    f"box\\{sandbox_name}\\"
                ]

                for indicator in sandbox_indicators:
                    if indicator in line_lower:
                        sandbox_processes.append(line.strip())
                        print(f"   ✅ Найден процесс песочницы #{sandbox_name} по '{indicator}'")
                        print(f"     📋 {line.strip()[:150]}...")
                        break

        return len(sandbox_processes) > 0

    except Exception as e:
        print(f"   ❌ Ошибка WMIC анализа: {e}")
        return False


def _check_sandbox_via_start_exe(sandbox_name):
    """Проверка через Sandboxie Start.exe"""

    try:
        print(f"   📋 Метод 3: Проверка через Sandboxie Start.exe")

        # Находим путь к Sandboxie
        sandboxie_paths = [
            "C:\\sand\\Start.exe",
            "C:\\Program Files\\Sandboxie\\Start.exe",
            "C:\\Program Files\\Sandboxie-Plus\\Start.exe",
            "C:\\Program Files (x86)\\Sandboxie\\Start.exe",
            "C:\\Program Files (x86)\\Sandboxie-Plus\\Start.exe"
        ]

        start_exe_path = None
        for path in sandboxie_paths:
            if os.path.exists(path):
                start_exe_path = path
                break

        if not start_exe_path:
            print(f"   ⚠️ Start.exe не найден")
            return False

        # Пробуем команду получения списка процессов песочницы
        sandbox_formats = [
            sandbox_name,  # 1
            f"#{sandbox_name}",  # #1
            f"Sandbox_{sandbox_name}",  # Sandbox_1
            f"Box_{sandbox_name}"  # Box_1
        ]

        for sandbox_format in sandbox_formats:
            try:
                # Некоторые версии Sandboxie поддерживают /listpids
                cmd = [start_exe_path, f"/box:{sandbox_format}", "/listpids"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='cp866',
                    errors='replace'
                )

                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    active_pids = [pid.strip() for pid in pids if pid.strip().isdigit()]

                    if active_pids:
                        print(f"   ✅ Найдены PID в песочнице {sandbox_format}: {active_pids}")
                        return True

            except Exception:
                pass  # Пробуем следующий формат

        print(f"   ℹ️ Sandboxie не показывает активные процессы")
        return False

    except Exception as e:
        print(f"   ❌ Ошибка проверки через Start.exe: {e}")
        return False


def terminate_sandbox_processes(sandbox_name):
    """Завершает все процессы в указанной песочнице Sandboxie через Start.exe"""
    if not check_sandbox_processes(sandbox_name):
        print(f"ℹ️ В песочнице {sandbox_name} нет процессов для завершения")
        return True

    sandboxie_paths = [
        "C:\\sand\\Start.exe",
        "C:\\Program Files\\Sandboxie\\Start.exe",
        "C:\\Program Files\\Sandboxie-Plus\\Start.exe",
        "C:\\Program Files (x86)\\Sandboxie\\Start.exe",
        "C:\\Program Files (x86)\\Sandboxie-Plus\\Start.exe"
    ]

    start_exe_path = None
    for path in sandboxie_paths:
        if os.path.exists(path):
            start_exe_path = path
            break

    if not start_exe_path:
        print("❌ Start.exe не найден. Проверьте установку Sandboxie")
        return False

    try:
        cmd = [start_exe_path, f"/box:{sandbox_name}", "/terminate"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"🔍 Команда завершения: {' '.join(cmd)}")
        print(f"🔍 Код возврата: {result.returncode}")
        if result.stdout:
            print(f"🔍 Stdout: {result.stdout}")
        if result.stderr:
            print(f"🔍 Stderr: {result.stderr}")

        # Проверяем код возврата
        if result.returncode == 0:
            print("⏳ Команда terminate выполнена успешно, ждем 3 секунды...")

            # Простая проверка - если команда вернула 0, считаем успешным
            print(f"✅ Процессы в песочнице {sandbox_name} завершены (код возврата: 0)")
            return True
        else:
            print(f"❌ Команда terminate вернула ошибку: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при завершении процессов: {e}")
        return False


def find_steam_folder_in_sandbox(sandbox_base, sandbox_name):
    """Ищет папку Steam в песочнице, проверяя оба возможных пути"""
    possible_paths = [
        # Путь для второго компьютера (Dom)
        os.path.join(sandbox_base, sandbox_name, "drive", "C", "Program Files (x86)", "Steam"),
        # Путь для основного компьютера (user)
        os.path.join(sandbox_base, sandbox_name, "drive", "C", "steam")
    ]

    for steam_path in possible_paths:
        if os.path.exists(steam_path):
            print(f"✅ Найден Steam по пути: {steam_path}")
            return steam_path

    print(f"❌ Steam не найден в песочнице {sandbox_name}")
    return None


def launch_steam_for_update(sandbox_name, steam_path=None):
    """Запускает Steam в песочнице для обновления Dota 2"""
    sandboxie_paths = [
        "C:\\sand\\Start.exe",
        "C:\\Program Files\\Sandboxie\\Start.exe",
        "C:\\Program Files\\Sandboxie-Plus\\Start.exe",
        "C:\\Program Files (x86)\\Sandboxie\\Start.exe",
        "C:\\Program Files (x86)\\Sandboxie-Plus\\Start.exe"
    ]

    start_exe_path = None
    for path in sandboxie_paths:
        if os.path.exists(path):
            start_exe_path = path
            break

    if not start_exe_path:
        print("❌ Start.exe не найден")
        return False

    # Определяем путь к Steam.exe в зависимости от найденной папки Steam
    if not steam_path:
        # Пытаемся найти Steam в стандартных местах
        possible_steam_paths = [
            "C:\\Program Files (x86)\\Steam\\Steam.exe",
            "C:\\steam\\steam.exe"
        ]
        for path in possible_steam_paths:
            if os.path.exists(path):
                steam_path = path
                break

    if not steam_path:
        print("❌ Steam.exe не найден")
        return False

    try:
        cmd = [
            start_exe_path,
            f"/box:{sandbox_name}",
            steam_path,
            "-silent"
        ]
        process = subprocess.Popen(cmd)
        print(f"✅ Steam запущен в песочнице {sandbox_name} для обновления")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска Steam в {sandbox_name}: {e}")
        return False


def check_single_sandbox_update(sandbox_base, sandbox_name, latest_buildid):
    """Проверяет обновление в одной песочнице с поддержкой разных путей"""
    steam_folder = find_steam_folder_in_sandbox(sandbox_base, sandbox_name)
    if not steam_folder:
        return False

    local = get_local_buildid_multi_path(steam_folder)
    if local and local == latest_buildid:
        return True
    return False


def auto_update_sandbox(sandbox_name, sandbox_base, latest_buildid,
                        check_interval=60, max_checks=30):
    """Автоматически обновляет Dota 2 в песочнице"""
    print(f"🔄 Начинаю автообновление песочницы {sandbox_name}")

    if not terminate_sandbox_processes(sandbox_name):
        return False

    time.sleep(2)

    if not launch_steam_for_update(sandbox_name):
        return False

    print(f"⏳ Ожидание обновления Dota 2 в песочнице {sandbox_name}...")
    print(f"📅 Проверка каждые {check_interval} секунд, максимум {max_checks} попыток")

    for attempt in range(max_checks):
        time.sleep(check_interval)
        print(f"🔍 Проверка {attempt + 1}/{max_checks}: песочница {sandbox_name}")

        if check_single_sandbox_update(sandbox_base, sandbox_name, latest_buildid):
            print(f"✅ Dota 2 обновлена в песочнице {sandbox_name}!")
            terminate_sandbox_processes(sandbox_name)
            print(f"🏁 Автообновление песочницы {sandbox_name} завершено успешно")
            return True

    print(f"⚠️ Обновление не завершилось за {max_checks * check_interval // 60} минут")
    return False


def get_latest_dota_buildid(steamcmd_path):
    """Получает актуальный buildid для публичной ветки Dota 2 с помощью SteamCMD"""
    if not os.path.exists(steamcmd_path):
        print(f"Ошибка: SteamCMD не найден по пути {steamcmd_path}")
        return None

    cmd = [
        steamcmd_path,
        "+login", "anonymous",
        "+app_info_print", "570",
        "+quit"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        match = re.search(r'"public"\s*{[^}]*"buildid"\s*"(\d+)"', res.stdout, re.DOTALL)
        if match:
            return match.group(1)
        print("Не удалось найти buildid в выводе SteamCMD.")
        return None
    except subprocess.TimeoutExpired:
        print("Ошибка: Запрос к SteamCMD занял слишком много времени.")
        return None
    except Exception as e:
        print(f"Ошибка при выполнении SteamCMD: {e}")
        return None


def get_local_buildid_multi_path(steam_folder):
    """Читает локальный buildid из файла appmanifest_570.acf с поддержкой разных путей"""
    if not steam_folder:
        return None

    manifest = os.path.join(steam_folder, 'steamapps', 'appmanifest_570.acf')
    if not os.path.exists(manifest):
        print(f"⚠️ Файл manifest не найден: {manifest}")
        return None

    try:
        with open(manifest, encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'"buildid"\s*"(\d+)"', content)
        if match:
            buildid = match.group(1)
            print(f"📋 Найден buildid: {buildid} в {steam_folder}")
            return buildid
        else:
            print(f"⚠️ buildid не найден в файле {manifest}")
            return None
    except Exception as e:
        print(f"❌ Ошибка при чтении {manifest}: {e}")
        return None


@register_action("check_and_auto_update_sandboxes")
def check_and_auto_update_sandboxes_action(instance, **kwargs):
    """
    Объединённое действие: безопасно проверяет и обновляет песочницы с управлением процессами
    """
    steamcmd_path = kwargs.get('steamcmd_path')
    sandbox_base = kwargs.get('sandbox_base')
    sandboxes = kwargs.get('sandboxes', [])
    check_interval = kwargs.get('check_interval', 60)
    max_checks = kwargs.get('max_checks', 30)

    # ✅ НОВЫЕ ПАРАМЕТРЫ для управления процессами
    terminate_before_check = kwargs.get('terminate_before_check', True)  # Закрывать процессы перед проверкой
    terminate_after_update = kwargs.get('terminate_after_update', True)  # Закрывать процессы после обновления
    wait_after_terminate = kwargs.get('wait_after_terminate', 10)  # Ожидание после закрытия
    wait_after_update = kwargs.get('wait_after_update', 15)  # Ожидание после обновления

    # Автоматическое определение пути к SteamCMD
    if not steamcmd_path or not os.path.exists(steamcmd_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fallback_path = os.path.join(project_root, "steamcmd", "steamcmd.exe")
        if os.path.exists(fallback_path):
            steamcmd_path = fallback_path
        else:
            instance.logger.error("❌ SteamCMD не найден")
            return False, "steamcmd_not_found"

    instance.logger.info("🔄 НАЧАЛО БЕЗОПАСНОГО ЦИКЛА ОБНОВЛЕНИЯ ПЕСОЧНИЦ")
    instance.logger.info(f"📦 Песочницы для обработки: {sandboxes}")

    # ✅ ШАГ 1: МАССОВОЕ ЗАКРЫТИЕ ВСЕХ ПРОЦЕССОВ ПЕРЕД ПРОВЕРКОЙ
    if terminate_before_check:
        instance.logger.info("🛑 ШАГ 1: Закрытие всех процессов во всех песочницах перед проверкой")

        terminated_count = 0
        for sandbox_name in sandboxes:
            try:
                instance.logger.info(f"🛑 Закрытие процессов в песочнице '{sandbox_name}'")

                if terminate_sandbox_processes(sandbox_name):
                    terminated_count += 1
                    instance.logger.info(f"✅ Песочница '{sandbox_name}': процессы закрыты")
                else:
                    instance.logger.warning(f"⚠️ Песочница '{sandbox_name}': не удалось закрыть процессы")

            except Exception as e:
                instance.logger.error(f"❌ Ошибка закрытия процессов в '{sandbox_name}': {e}")

        instance.logger.info(f"📊 Результат закрытия: {terminated_count}/{len(sandboxes)} песочниц")

        # Ожидание стабилизации системы
        if wait_after_terminate > 0:
            instance.logger.info(f"⏳ Ожидание стабилизации системы: {wait_after_terminate} секунд")
            time.sleep(wait_after_terminate)
    else:
        instance.logger.info("ℹ️ ШАГ 1: Закрытие процессов пропущено (terminate_before_check=False)")

    # ✅ ШАГ 2: ПОЛУЧЕНИЕ АКТУАЛЬНОГО BUILDID
    instance.logger.info("🔍 ШАГ 2: Получение актуального buildid")
    latest_buildid = get_latest_dota_buildid(steamcmd_path)
    if not latest_buildid:
        instance.logger.error("❌ Не удалось получить актуальный buildid")
        return False, "no_latest_buildid"

    instance.logger.info(f"🎯 Актуальный buildid: {latest_buildid}")

    # ✅ ШАГ 3: ПРОВЕРКА И ОБНОВЛЕНИЕ ПЕСОЧНИЦ
    instance.logger.info("🔄 ШАГ 3: Проверка и обновление песочниц")
    results = {}
    updated_sandboxes = []
    failed_sandboxes = []

    for sandbox_name in sandboxes:
        try:
            instance.logger.info(f"🔍 Проверка песочницы '{sandbox_name}'")

            # Используем функцию поиска Steam папки
            steam_folder = find_steam_folder_in_sandbox(sandbox_base, sandbox_name)
            if not steam_folder:
                instance.logger.warning(f"⚠️ Steam не найден в песочнице {sandbox_name}")
                results[sandbox_name] = {"local": None, "status": "not_found", "path": "not_found"}
                continue

            local_buildid = get_local_buildid_multi_path(steam_folder)

            if not local_buildid:
                instance.logger.warning(f"⚠️ Не найден buildid в песочнице {sandbox_name}")
                results[sandbox_name] = {"local": None, "status": "not_found", "path": steam_folder}
                continue

            if local_buildid == latest_buildid:
                instance.logger.info(f"✅ Песочница {sandbox_name} уже обновлена")
                results[sandbox_name] = {"local": local_buildid, "status": "up_to_date", "path": steam_folder}
                continue

            # Песочница устарела - начинаем автообновление
            instance.logger.info(f"🔄 Песочница {sandbox_name} устарела ({local_buildid} → {latest_buildid})")
            results[sandbox_name] = {"local": local_buildid, "status": "outdated", "path": steam_folder}

            # ✅ МОДИФИЦИРОВАННОЕ ОБНОВЛЕНИЕ (без повторного закрытия процессов)
            if auto_update_sandbox_safe(sandbox_name, sandbox_base, latest_buildid,
                                        check_interval, max_checks, skip_initial_terminate=True):
                updated_sandboxes.append(sandbox_name)
                results[sandbox_name]["status"] = "updated"
                instance.logger.info(f"✅ Песочница {sandbox_name} успешно обновлена")
            else:
                failed_sandboxes.append(sandbox_name)
                results[sandbox_name]["status"] = "update_failed"
                instance.logger.error(f"❌ Не удалось обновить песочницу {sandbox_name}")

        except Exception as e:
            instance.logger.error(f"❌ Ошибка обработки песочницы '{sandbox_name}': {e}")
            failed_sandboxes.append(sandbox_name)
            results[sandbox_name] = {"local": None, "status": "error", "path": "error", "error": str(e)}

    instance.logger.info(f"📊 Результат обновления: {len(updated_sandboxes)} обновлено, {len(failed_sandboxes)} ошибок")

    # ✅ ШАГ 4: ФИНАЛЬНОЕ ЗАКРЫТИЕ ПРОЦЕССОВ (ОПЦИОНАЛЬНО)
    if terminate_after_update:
        instance.logger.info("🛑 ШАГ 4: Финальное закрытие всех процессов после обновления")

        final_terminated = 0
        for sandbox_name in sandboxes:
            try:
                instance.logger.info(f"🛑 Финальное закрытие процессов в песочнице '{sandbox_name}'")

                if terminate_sandbox_processes(sandbox_name):
                    final_terminated += 1
                    instance.logger.info(f"✅ Песочница '{sandbox_name}': процессы финально закрыты")
                else:
                    instance.logger.info(f"ℹ️ Песочница '{sandbox_name}': процессы уже закрыты")

            except Exception as e:
                instance.logger.error(f"❌ Ошибка финального закрытия в '{sandbox_name}': {e}")

        instance.logger.info(f"📊 Результат финального закрытия: {final_terminated}/{len(sandboxes)} песочниц")

        # Ожидание после финального закрытия
        if wait_after_update > 0:
            instance.logger.info(f"⏳ Ожидание после обновления: {wait_after_update} секунд")
            time.sleep(wait_after_update)
    else:
        instance.logger.info("ℹ️ ШАГ 4: Финальное закрытие процессов пропущено (terminate_after_update=False)")

    # Формируем итоговый результат
    result_info = {
        "latest_buildid": latest_buildid,
        "results": results,
        "updated": updated_sandboxes,
        "failed": failed_sandboxes,
        "total_processed": len(sandboxes),
        "terminated_before": terminate_before_check,
        "terminated_after": terminate_after_update
    }

    # Определяем успешность операции
    if failed_sandboxes:
        instance.logger.warning(
            f"⚠️ Обновление завершено с ошибками. Обновлено: {len(updated_sandboxes)}, Ошибок: {len(failed_sandboxes)}")
        return False, result_info
    else:
        instance.logger.info(f"✅ Все песочницы проверены и обновлены. Обновлено: {len(updated_sandboxes)}")
        return True, result_info


def auto_update_sandbox_safe(sandbox_name, sandbox_base, latest_buildid,
                             check_interval=60, max_checks=30, skip_initial_terminate=False):
    """
    Модифицированная версия auto_update_sandbox с опцией пропуска начального закрытия процессов
    """
    print(f"🔄 Начинаю безопасное автообновление песочницы {sandbox_name}")

    if not skip_initial_terminate:
        if not terminate_sandbox_processes(sandbox_name):
            return False
        time.sleep(2)

    if not launch_steam_for_update(sandbox_name):
        return False

    print(f"⏳ Ожидание обновления Dota 2 в песочнице {sandbox_name}...")
    print(f"📅 Проверка каждые {check_interval} секунд, максимум {max_checks} попыток")

    for attempt in range(max_checks):
        time.sleep(check_interval)
        print(f"🔍 Проверка {attempt + 1}/{max_checks}: песочница {sandbox_name}")

        if check_single_sandbox_update(sandbox_base, sandbox_name, latest_buildid):
            print(f"✅ Dota 2 обновлена в песочнице {sandbox_name}!")
            print(f"🏁 Автообновление песочницы {sandbox_name} завершено успешно")
            return True

    print(f"⚠️ Обновление не завершилось за {max_checks * check_interval // 60} минут")
    return False


@register_action("check_sandbox_builds")
def check_sandbox_builds_action(instance, **kwargs):
    """
    Действие для проверки buildid в наборе Sandboxie-папок с поддержкой разных путей
    """
    steamcmd_path = kwargs.get('steamcmd_path')
    base = kwargs.get('sandbox_base')
    names = kwargs.get('sandboxes', [])

    # Автоматическое определение пути к SteamCMD
    if not steamcmd_path or not os.path.exists(steamcmd_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fallback_path = os.path.join(project_root, "steamcmd", "steamcmd.exe")
        if os.path.exists(fallback_path):
            steamcmd_path = fallback_path
        else:
            instance.logger.error("❌ SteamCMD не найден")
            return False, "steamcmd_not_found"

    latest = get_latest_dota_buildid(steamcmd_path)
    if not latest:
        instance.logger.error("❌ Не удалось получить актуальный buildid.")
        return False, "no_latest_buildid"

    instance.logger.info(f"Актуальный buildid: {latest}")

    results = {}
    for name in names:
        # Используем новую функцию поиска Steam папки
        steam_folder = find_steam_folder_in_sandbox(base, name)
        if not steam_folder:
            results[name] = {"local": None, "status": "not_found", "path": "not_found"}
            instance.logger.info(f"Sandbox {name}: Steam не найден")
            continue

        local = get_local_buildid_multi_path(steam_folder)
        status = "not_found" if not local else ("up_to_date" if local == latest else "outdated")
        results[name] = {"local": local, "status": status, "path": steam_folder}
        instance.logger.info(f"Sandbox {name}: local={local} → {status} (путь: {steam_folder})")

    return True, results
