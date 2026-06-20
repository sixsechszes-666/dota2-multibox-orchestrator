# actions/system_actions.py
import json
import time
import os
import glob

from utils.actions_registry import register_action
import utils.dota_update_checker


@register_action("launch_sandbox_instances")
def launch_sandbox_instances_action(instance, **kwargs):
    """Запуск экземпляров Dota 2 в Sandboxie"""
    config_file = kwargs.get('config_file', 'config/sandbox_config.yaml')

    try:
        from core.sandbox_manager import SandboxManager

        instance.logger.info("📦 Создание SandboxManager...")
        manager = SandboxManager(config_file=config_file)

        instance.logger.info("🚀 Запуск экземпляров...")
        success = manager.launch_all_instances()

        if success:
            instance.logger.info("✅ Экземпляры Sandboxie запущены успешно")
            return True, "sandbox_instances_launched"
        else:
            instance.logger.error("❌ Ошибка запуска экземпляров Sandboxie")
            return False, "sandbox_launch_failed"

    except ImportError as e:
        instance.logger.error(f"❌ Модуль sandbox_manager не найден: {e}")
        return False, "sandbox_manager_not_found"
    except Exception as e:
        instance.logger.error(f"❌ Ошибка запуска Sandboxie: {e}")
        return False, str(e)


@register_action("stop_sandbox_instances")
def stop_sandbox_instances_action(instance, **kwargs):
    """Остановка экземпляров Dota 2 в Sandboxie"""

    config_file = kwargs.get('config_file', 'config/sandbox_config.yaml')

    try:
        from core.sandbox_manager import SandboxManager

        instance.logger.info("📦 Создание SandboxManager...")
        manager = SandboxManager(config_file=config_file)

        instance.logger.info("🛑 Остановка экземпляров...")
        success = manager.stop_all_instances()

        if success:
            instance.logger.info("✅ Экземпляры Sandboxie остановлены успешно")
            return True, "sandbox_instances_stopped"
        else:
            instance.logger.error("❌ Ошибка остановки экземпляров Sandboxie")
            return False, "sandbox_stop_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка остановки Sandboxie: {e}")
        return False, str(e)


@register_action("sandbox_status")
def sandbox_status_action(instance, **kwargs):
    """Проверка статуса экземпляров Sandboxie"""

    config_file = kwargs.get('config_file', 'config/sandbox_config.yaml')

    try:
        from core.sandbox_manager import SandboxManager

        instance.logger.info("📦 Создание SandboxManager...")
        manager = SandboxManager(config_file=config_file)

        instance.logger.info("📊 Получение статуса...")
        status = manager.get_status()

        if status:
            instance.logger.info(
                f"📊 Статус Sandboxie: {status['running_instances']}/{status['enabled_instances']} запущено")
            return True, f"sandbox_status_{status['running_instances']}_{status['enabled_instances']}"
        else:
            instance.logger.error("❌ Не удалось получить статус Sandboxie")
            return False, "sandbox_status_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка получения статуса Sandboxie: {e}")
        return False, str(e)


@register_action("wait_delay")
def wait_delay_action(instance, **kwargs):
    """Простое ожидание указанное количество секунд"""
    delay = kwargs.get('delay', 30)

    instance.logger.info(f"⏳ Ожидание {delay} секунд...")

    import time
    time.sleep(delay)

    instance.logger.info(f"✅ Ожидание {delay} секунд завершено")
    return True, f"waited_{delay}_seconds"


@register_action("select_random_instances")
def select_random_instances_action(instance, **kwargs):
    """Случайный выбор экземпляров для текущей игровой сессии"""

    try:
        instance.logger.info("🎲 Случайный выбор экземпляров для сессии...")

        selected_instances = select_random_sandbox_instances(**kwargs)

        if selected_instances:
            master = selected_instances['master']
            slaves = selected_instances['slaves']
            instance.logger.info(f"✅ Выбран мастер: #{master}")
            instance.logger.info(f"✅ Выбраны слейвы: {slaves}")
            instance.logger.info(f"📊 Всего экземпляров: {len(selected_instances['all_selected'])}")

            # Сохраняем выбранные экземпляры в глобальном состоянии
            _save_selected_instances(selected_instances, **kwargs)

            return True, f"selected_{len(selected_instances['all_selected'])}_instances"
        else:
            instance.logger.error("❌ Не удалось выбрать экземпляры")
            return False, "selection_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка выбора экземпляров: {e}")
        return False, str(e)


def select_random_sandbox_instances(**kwargs):
    """
    Случайный выбор экземпляров песочниц

    Args:
        **kwargs: Параметры конфигурации

    Returns:
        dict: Информация о выбранных экземплярах
    """

    import random
    import time

    try:
        # Настраиваемые параметры
        total_sandboxes = kwargs.get('total_sandboxes', 9)  # Всего песочниц
        master_instance = kwargs.get('master_instance', '1')  # Мастер всегда #1
        slaves_to_select = kwargs.get('slaves_to_select', 4)  # Сколько слейвов выбрать

        print(f"🎲 КОНФИГУРАЦИЯ ВЫБОРА:")
        print(f"   📦 Всего песочниц: {total_sandboxes}")
        print(f"   👑 Мастер (фиксированный): #{master_instance}")
        print(f"   🎯 Слейвов к выбору: {slaves_to_select}")

        # Создаем список всех доступных экземпляров (исключая мастера)
        all_instances = [str(i) for i in range(1, total_sandboxes + 1)]
        available_slaves = [inst for inst in all_instances if inst != master_instance]

        print(f"   📋 Доступные слейвы: {available_slaves}")

        # Проверяем, достаточно ли экземпляров для выбора
        if len(available_slaves) < slaves_to_select:
            print(f"❌ Недостаточно экземпляров для выбора!")
            print(f"   Доступно: {len(available_slaves)}, требуется: {slaves_to_select}")
            return None

        # Случайный выбор слейвов
        selected_slaves = random.sample(available_slaves, slaves_to_select)
        selected_slaves.sort()  # Сортируем для удобства

        # Формируем полный список выбранных экземпляров
        all_selected = [master_instance] + selected_slaves
        all_selected.sort()

        selection_result = {
            'master': master_instance,
            'slaves': selected_slaves,
            'all_selected': all_selected,
            'total_selected': len(all_selected),
            'timestamp': time.time(),
            'selection_id': f"session_{int(time.time())}"
        }

        print(f"\n🎯 РЕЗУЛЬТАТ ВЫБОРА:")
        print(f"   👑 Мастер: #{master_instance}")
        print(f"   👥 Слейвы: {selected_slaves}")
        print(f"   📊 Все выбранные: {all_selected}")
        print(f"   🆔 ID сессии: {selection_result['selection_id']}")

        return selection_result

    except Exception as e:
        print(f"❌ Ошибка выбора экземпляров: {e}")
        return None


def _save_selected_instances(selection_result, **kwargs):
    """Сохранение информации о выбранных экземплярах"""

    try:
        import json
        import os

        # Сохраняем в файл для использования другими действиями
        config_dir = kwargs.get('config_dir', 'config')
        selection_file = os.path.join(config_dir, 'current_session_instances.json')

        # Создаем директорию если не существует
        os.makedirs(config_dir, exist_ok=True)

        # Добавляем дополнительную информацию
        full_config = {
            'selection_result': selection_result,
            'created_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'parameters': {
                'total_sandboxes': kwargs.get('total_sandboxes', 9),
                'master_instance': kwargs.get('master_instance', '1'),
                'slaves_to_select': kwargs.get('slaves_to_select', 4)
            }
        }

        with open(selection_file, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)

        print(f"💾 Выбранные экземпляры сохранены: {selection_file}")

        # Также сохраняем в глобальную переменную для быстрого доступа
        globals()['CURRENT_SESSION_INSTANCES'] = selection_result

    except Exception as e:
        print(f"⚠️ Не удалось сохранить выбранные экземпляры: {e}")


def _load_selected_instances(**kwargs):
    """Загрузка информации о выбранных экземплярах"""

    try:
        import json
        import os

        # Проверяем глобальную переменную сначала
        if 'CURRENT_SESSION_INSTANCES' in globals():
            return globals()['CURRENT_SESSION_INSTANCES']

        # Загружаем из файла
        config_dir = kwargs.get('config_dir', 'config')
        selection_file = os.path.join(config_dir, 'current_session_instances.json')

        if os.path.exists(selection_file):
            with open(selection_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config['selection_result']

        print("⚠️ Информация о выбранных экземплярах не найдена")
        return None

    except Exception as e:
        print(f"❌ Ошибка загрузки выбранных экземпляров: {e}")
        return None


@register_action("launch_selected_sandbox_instances")
def launch_selected_sandbox_instances_action(instance, **kwargs):
    """Запуск только выбранных экземпляров Sandboxie"""

    try:
        instance.logger.info("🚀 Запуск выбранных экземпляров Sandboxie...")

        # Загружаем информацию о выбранных экземплярах
        selected_instances = _load_selected_instances(**kwargs)

        if not selected_instances:
            instance.logger.error("❌ Не найдена информация о выбранных экземплярах")
            instance.logger.info("💡 Выполните сначала действие 'select_random_instances'")
            return False, "no_selected_instances"

        instance.logger.info(f"📋 Запуск экземпляров: {selected_instances['all_selected']}")

        # Модифицируем конфигурацию для запуска только выбранных экземпляров
        success = _launch_specific_sandbox_instances(
            selected_instances['all_selected'],
            instance,
            **kwargs
        )

        if success:
            instance.logger.info("✅ Выбранные экземпляры Sandboxie запущены успешно")
            return True, f"selected_instances_launched_{len(selected_instances['all_selected'])}"
        else:
            instance.logger.error("❌ Ошибка запуска выбранных экземпляров")
            return False, "selected_launch_failed"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка запуска выбранных экземпляров: {e}")
        return False, str(e)


def _launch_specific_sandbox_instances(instance_names, instance, **kwargs):
    """Запуск конкретных экземпляров Sandboxie"""

    try:
        config_file = kwargs.get('config_file', 'config/sandbox_config.yaml')

        from core.sandbox_manager import SandboxManager

        print(f"📦 Создание SandboxManager для выбранных экземпляров...")
        manager = SandboxManager(config_file=config_file)

        # Модифицируем конфигурацию: включаем только выбранные экземпляры
        original_instances = manager.config['instances'].copy()

        for inst_config in manager.config['instances']:
            if inst_config['sandbox_name'] in instance_names:
                inst_config['enabled'] = True
                print(f"✅ Экземпляр #{inst_config['sandbox_name']}: включен")
            else:
                inst_config['enabled'] = False
                print(f"❌ Экземпляр #{inst_config['sandbox_name']}: отключен")

        print(f"🚀 Запуск {len(instance_names)} выбранных экземпляров...")
        success = manager.launch_all_instances()

        # Восстанавливаем оригинальную конфигурацию
        manager.config['instances'] = original_instances

        return success

    except Exception as e:
        print(f"❌ Ошибка запуска конкретных экземпляров: {e}")
        return False


@register_action("collect_selected_player_ids")
def collect_selected_player_ids_action(instance, **kwargs):
    """Сбор Steam ID только из выбранных экземпляров"""

    try:
        instance.logger.info("🆔 Сбор Steam ID из выбранных экземпляров...")

        # Загружаем информацию о выбранных экземплярах
        selected_instances = _load_selected_instances(**kwargs)

        if not selected_instances:
            instance.logger.error("❌ Не найдена информация о выбранных экземплярах")
            return False, "no_selected_instances"

        instance.logger.info(f"📋 Сбор Steam ID из экземпляров: {selected_instances['all_selected']}")
        instance.logger.info(f"👑 Мастер песочница: #{selected_instances['master']}")

        steam_id_mapping = collect_steam_ids_with_sandbox_mapping(
            sandbox_names=selected_instances['all_selected'],
            **kwargs
        )

        if steam_id_mapping:
            master_sandbox = selected_instances['master']
            master_id = steam_id_mapping.get(master_sandbox)

            # Собираем Steam ID слейвов
            slave_ids = []
            for sandbox_name in selected_instances['slaves']:
                slave_steam_id = steam_id_mapping.get(sandbox_name)
                if slave_steam_id:
                    slave_ids.append(slave_steam_id)

            # Все Steam ID
            all_ids = list(steam_id_mapping.values())

            instance.logger.info(f"✅ Собрано Steam ID:")
            instance.logger.info(f"   👑 Мастер (песочница #{master_sandbox}): {master_id}")
            instance.logger.info(f"   👥 Слейвы: {slave_ids}")
            instance.logger.info(f"   🗺️ Полное сопоставление: {steam_id_mapping}")

            # Сохраняем информацию для создания пати
            _save_collected_ids_with_mapping(master_id, slave_ids, all_ids, steam_id_mapping, selected_instances,
                                             **kwargs)

            return True, f"collected_selected_ids_{len(all_ids)}"
        else:
            instance.logger.error("❌ Не найдено Steam ID в выбранных экземплярах")
            return False, "no_ids_in_selected"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка сбора Steam ID из выбранных экземпляров: {e}")
        return False, str(e)


def find_steam_userdata_folder(sandbox_base, sandbox_name, sandbox_user=""):
    """
    Ищет папку userdata Steam в песочнице, проверяя все возможные пути
    """

    possible_paths = []

    # Вариант 1: С пользователем (C:\Sandbox\{user}\{sandbox}\...)
    if sandbox_user:
        # Основной компьютер (user): C:\Sandbox\user\1\drive\C\steam\userdata
        path1 = os.path.join(sandbox_base, sandbox_user, sandbox_name, "drive", "C", "steam", "userdata")
        possible_paths.append(("Основной (с пользователем)", path1))

        # Второй компьютер (Dom): C:\Sandbox\user\1\drive\C\Program Files (x86)\Steam\userdata
        path2 = os.path.join(sandbox_base, sandbox_user, sandbox_name, "drive", "C", "Program Files (x86)", "Steam",
                             "userdata")
        possible_paths.append(("Второй (с пользователем)", path2))

    # Вариант 2: Без пользователя (C:\Dom\{sandbox}\...)
    # Основной путь: C:\Dom\1\drive\C\steam\userdata
    path3 = os.path.join(sandbox_base, sandbox_name, "drive", "C", "steam", "userdata")
    possible_paths.append(("Основной (без пользователя)", path3))

    path4 = os.path.join(sandbox_base, sandbox_name, "drive", "C", "Program Files (x86)", "Steam", "userdata")
    possible_paths.append(("Второй (без пользователя)", path4))

    print(f"🔍 Поиск userdata для песочницы '{sandbox_name}' по {len(possible_paths)} путям:")

    for description, userdata_path in possible_paths:
        print(f"   📁 {description}: {userdata_path}")
        if os.path.exists(userdata_path):
            print(f"   ✅ Найден userdata: {userdata_path}")
            return userdata_path
        else:
            print(f"   ❌ userdata не найден")

    print(f"❌ userdata не найден в песочнице {sandbox_name} ни по одному пути")
    return None


def collect_steam_ids_with_sandbox_mapping(sandbox_names, **kwargs):
    """
    Сбор Steam ID с привязкой к конкретным песочницам

    Returns:
        dict: {sandbox_name: steam_id}
    """

    try:
        # Настраиваемые параметры
        sandbox_base_path = kwargs.get('sandbox_base_path', 'C:\\user')
        sandbox_user = kwargs.get('sandbox_user', '')

        print(f"🔍 Сбор Steam ID с привязкой к песочницам:")
        print(f"   📁 Базовый путь: {sandbox_base_path}")
        print(f"   👤 Пользователь: '{sandbox_user}'")
        print(f"   📦 Песочницы: {sandbox_names}")

        steam_id_mapping = {}

        for sandbox_name in sandbox_names:
            try:
                print(f"\n🔍 Обработка песочницы '{sandbox_name}':")

                # ✅ ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ ПОИСКА ВМЕСТО ЖЕСТКО ЗАДАННОГО ПУТИ
                userdata_path = find_steam_userdata_folder(sandbox_base_path, sandbox_name, sandbox_user)

                if not userdata_path:
                    print(f"   ❌ userdata не найден для песочницы '{sandbox_name}'")
                    continue

                # Ищем папки с цифровыми именами (Steam ID)
                steam_ids = []
                try:
                    for item in os.listdir(userdata_path):
                        item_path = os.path.join(userdata_path, item)

                        if os.path.isdir(item_path) and item.isdigit() and len(item) >= 8:
                            steam_ids.append(item)
                except Exception as e:
                    print(f"   ❌ Ошибка чтения userdata: {e}")
                    continue

                if steam_ids:
                    # Берем первый найденный Steam ID для этой песочницы
                    selected_steam_id = steam_ids[0]
                    steam_id_mapping[sandbox_name] = selected_steam_id
                    print(f"   ✅ Песочница '{sandbox_name}': Steam ID {selected_steam_id}")

                    if len(steam_ids) > 1:
                        print(f"   ℹ️ Найдено несколько ID, выбран первый: {steam_ids}")
                else:
                    print(f"   ⚠️ Песочница '{sandbox_name}': Steam ID не найден в userdata")

            except Exception as e:
                print(f"   ❌ Ошибка обработки песочницы '{sandbox_name}': {e}")

        print(f"\n🎯 ИТОГОВОЕ СОПОСТАВЛЕНИЕ:")
        for sandbox, steam_id in steam_id_mapping.items():
            print(f"   📦 #{sandbox} → {steam_id}")

        return steam_id_mapping

    except Exception as e:
        print(f"❌ Критическая ошибка сбора Steam ID с сопоставлением: {e}")
        return {}

def _save_collected_ids(master_id, slave_ids, all_ids, **kwargs):
    """Сохранение собранных Steam ID"""

    try:
        import json
        import os

        config_dir = kwargs.get('config_dir', 'config')
        ids_file = os.path.join(config_dir, 'current_session_steam_ids.json')

        ids_config = {
            'master_steam_id': master_id,
            'slave_steam_ids': slave_ids,
            'all_steam_ids': all_ids,
            'party_ids_for_invites': slave_ids,  # Мастер приглашает слейвов
            'created_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_ids': len(all_ids)
        }

        with open(ids_file, 'w', encoding='utf-8') as f:
            json.dump(ids_config, f, indent=2, ensure_ascii=False)

        print(f"💾 Steam ID сохранены: {ids_file}")

        # Также сохраняем в глобальную переменную
        globals()['CURRENT_SESSION_STEAM_IDS'] = ids_config

    except Exception as e:
        print(f"⚠️ Не удалось сохранить Steam ID: {e}")

def _save_collected_ids_with_mapping(master_id, slave_ids, all_ids, steam_id_mapping, selected_instances, **kwargs):
    """Сохранение собранных Steam ID с дополнительной информацией"""

    try:
        import json
        import os

        config_dir = kwargs.get('config_dir', 'config')
        ids_file = os.path.join(config_dir, 'current_session_steam_ids.json')

        ids_config = {
            'master_steam_id': master_id,
            'master_sandbox': selected_instances['master'],  # номер песочницы мастера
            'slave_steam_ids': slave_ids,
            'slave_sandboxes': selected_instances['slaves'],  # номера песочниц слейвов
            'all_steam_ids': all_ids,
            'steam_id_mapping': steam_id_mapping,  # полное сопоставление
            'party_ids_for_invites': slave_ids,
            'selected_instances': selected_instances,  # вся информация о выборе
            'created_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_ids': len(all_ids)
        }

        with open(ids_file, 'w', encoding='utf-8') as f:
            json.dump(ids_config, f, indent=2, ensure_ascii=False)

        print(f"💾 Steam ID с сопоставлением сохранены: {ids_file}")

        # Также сохраняем в глобальную переменную
        globals()['CURRENT_SESSION_STEAM_IDS'] = ids_config

    except Exception as e:
        print(f"⚠️ Не удалось сохранить Steam ID: {e}")

@register_action("create_party_with_selected")
def create_party_with_selected_action(instance, **kwargs):
    """Создание пати с приглашениями только выбранных экземпляров"""

    try:
        instance.logger.info("👥 Создание пати с выбранными экземплярами...")

        # Загружаем сохраненные Steam ID
        if 'CURRENT_SESSION_STEAM_IDS' in globals():
            ids_config = globals()['CURRENT_SESSION_STEAM_IDS']
        else:
            # Загружаем из файла
            config_dir = kwargs.get('config_dir', 'config')
            ids_file = os.path.join(config_dir, 'current_session_steam_ids.json')

            if os.path.exists(ids_file):
                with open(ids_file, 'r', encoding='utf-8') as f:
                    ids_config = json.load(f)
            else:
                instance.logger.error("❌ Не найдены Steam ID для создания пати")
                return False, "no_steam_ids"

        # Получаем информацию о мастере
        master_steam_id = ids_config['master_steam_id']
        master_sandbox = ids_config.get('master_sandbox', '1')
        party_ids = ids_config['party_ids_for_invites']

        instance.logger.info(f"👑 Мастер: Steam ID {master_steam_id} (песочница #{master_sandbox})")
        instance.logger.info(f"📨 Приглашаем {len(party_ids)} слейвов: {party_ids}")

        master_hwnd = _find_master_window(master_sandbox, instance)

        if master_hwnd:
            instance.logger.info(f"🎯 Найдено окно мастера (песочница #{master_sandbox})")

            # Активируем окно мастера
            success = _activate_master_window(master_hwnd, instance)
            if success:
                instance.logger.info("✅ Окно мастера активировано успешно")

                # Небольшая пауза для стабилизации
                time.sleep(1)

                # Создаем пати с найденными ID
                result = instance.create_party_with_multiple_invites(
                    party_ids_list=party_ids,
                    timeout=kwargs.get('timeout', 30)
                )

                if result:
                    instance.logger.info("✅ Пати создана с выбранными экземплярами")
                    return True, f"party_created_with_{len(party_ids)}_selected"
                else:
                    instance.logger.error("❌ Ошибка создания пати с выбранными")
                    return False, "party_creation_failed"
            else:
                instance.logger.error("❌ Не удалось активировать окно мастера")
                return False, "master_window_activation_failed"
        else:
            instance.logger.error(f"❌ Не найдено окно мастера для песочницы #{master_sandbox}")
            return False, "master_window_not_found"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка создания пати с выбранными: {e}")
        return False, str(e)

@register_action("collect_player_ids")
def collect_player_ids_action(instance, **kwargs):
    """Сбор Steam ID игроков из всех песочниц"""

    try:
        instance.logger.info("🆔 Сбор Steam ID игроков из песочниц...")

        collected_ids = collect_steam_ids_from_sandboxes(**kwargs)

        if collected_ids:
            instance.logger.info(f"✅ Собрано {len(collected_ids)} Steam ID: {collected_ids}")
            return True, f"collected_ids_{len(collected_ids)}"
        else:
            instance.logger.warning("⚠️ Не найдено ни одного Steam ID")
            return False, "no_ids_found"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка сбора Steam ID: {e}")
        return False, str(e)


def collect_steam_ids_from_sandboxes(**kwargs):
    """
    Сбор Steam ID из папок userdata всех песочниц

    Args:
        **kwargs: Параметры конфигурации

    Returns:
        list: Список найденных Steam ID
    """

    try:
        # Настраиваемые параметры
        sandbox_base_path = kwargs.get('sandbox_base_path', 'C:\\Sandbox')
        sandbox_user = kwargs.get('sandbox_user', '')  # Из sandbox_config.yaml
        sandbox_names = kwargs.get('sandbox_names', ['1', '2', '3', '4', '5', '6'])

        print(f"🔍 Поиск Steam ID в песочницах:")
        print(f"   📁 Базовый путь: {sandbox_base_path}")
        print(f"   👤 Пользователь: {sandbox_user}")
        print(f"   📦 Песочницы: {sandbox_names}")

        collected_ids = []
        detailed_info = []

        for sandbox_name in sandbox_names:
            try:
                print(f"\n🔍 Проверка песочницы '{sandbox_name}':")

                # ✅ ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ ПОИСКА ВМЕСТО ЖЕСТКО ЗАДАННОГО ПУТИ
                userdata_path = find_steam_userdata_folder(sandbox_base_path, sandbox_name, sandbox_user)

                if not userdata_path:
                    detailed_info.append({
                        'sandbox': sandbox_name,
                        'path': 'not_found',
                        'status': 'userdata_not_found',
                        'steam_ids': []
                    })
                    continue

                # Ищем папки с цифровыми именами (Steam ID)
                steam_ids = []
                for item in os.listdir(userdata_path):
                    item_path = os.path.join(userdata_path, item)

                    # Проверяем, что это папка и имя состоит только из цифр
                    if os.path.isdir(item_path) and item.isdigit():
                        # Дополнительная проверка - минимальная длина Steam ID
                        if len(item) >= 8:  # Steam ID обычно 8+ цифр
                            steam_ids.append(item)
                            print(f"   ✅ Найден Steam ID: {item}")

                if steam_ids:
                    collected_ids.extend(steam_ids)
                    print(f"   📊 Песочница '{sandbox_name}': найдено {len(steam_ids)} ID")
                else:
                    print(f"   ⚠️ Песочница '{sandbox_name}': Steam ID не найдены")

                detailed_info.append({
                    'sandbox': sandbox_name,
                    'path': userdata_path,
                    'status': 'success' if steam_ids else 'no_ids_found',
                    'steam_ids': steam_ids
                })

            except Exception as e:
                print(f"   ❌ Ошибка обработки песочницы '{sandbox_name}': {e}")
                detailed_info.append({
                    'sandbox': sandbox_name,
                    'path': 'error',
                    'status': 'error',
                    'error': str(e),
                    'steam_ids': []
                })

        # Убираем дубликаты и сортируем
        unique_ids = list(set(collected_ids))
        unique_ids.sort()

        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   🆔 Всего найдено Steam ID: {len(unique_ids)}")
        print(f"   📦 Песочниц обработано: {len(detailed_info)}")
        print(f"   ✅ Успешных: {sum(1 for info in detailed_info if info['status'] == 'success')}")
        print(f"   ❌ С ошибками: {sum(1 for info in detailed_info if info['status'] == 'error')}")

        if unique_ids:
            print(f"\n🎯 НАЙДЕННЫЕ STEAM ID:")
            for i, steam_id in enumerate(unique_ids, 1):
                print(f"   {i}. {steam_id}")

        # Сохраняем детальную информацию для отладки
        _save_collection_report(detailed_info, unique_ids, **kwargs)

        return unique_ids

    except Exception as e:
        print(f"❌ Критическая ошибка сбора Steam ID: {e}")
        return []


def _save_collection_report(detailed_info, collected_ids, **kwargs):
    """Сохранение отчета о сборе Steam ID"""

    try:
        import json
        import time

        report_dir = kwargs.get('report_dir', 'logs')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_dir, f"steam_ids_collection_{timestamp}.json")

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'collected_ids': collected_ids,
            'total_ids': len(collected_ids),
            'detailed_info': detailed_info,
            'parameters': {
                'sandbox_base_path': kwargs.get('sandbox_base_path', 'C:\\Sandbox'),
                'sandbox_user': kwargs.get('sandbox_user', ''),
                'sandbox_names': kwargs.get('sandbox_names', ['1', '2', '3', '4', '5', '6'])
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Отчет сохранен: {report_file}")

    except Exception as e:
        print(f"⚠️ Не удалось сохранить отчет: {e}")


@register_action("update_party_ids_from_sandboxes")
def update_party_ids_from_sandboxes_action(instance, **kwargs):
    """Обновление party_ids в конфигурации на основе найденных Steam ID"""

    try:
        instance.logger.info("🔄 Обновление party_ids из песочниц...")

        # Собираем Steam ID
        collected_ids = collect_steam_ids_from_sandboxes(**kwargs)

        if not collected_ids:
            instance.logger.error("❌ Не найдено Steam ID для обновления")
            return False, "no_ids_to_update"

        # Обновляем party_ids в kwargs для использования в scenarios
        kwargs['party_ids'] = collected_ids

        instance.logger.info(f"✅ Party IDs обновлены: {collected_ids}")

        # Можно также сохранить в файл для scenarios.yaml
        _save_party_ids_config(collected_ids, **kwargs)

        return True, f"party_ids_updated_{len(collected_ids)}"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка обновления party_ids: {e}")
        return False, str(e)


def _save_party_ids_config(party_ids, **kwargs):
    """Сохранение party_ids в конфигурационный файл"""

    try:
        import yaml

        config_file = kwargs.get('output_config_file', 'config/auto_party_ids.yaml')

        config = {
            'auto_generated': True,
            'generated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'party_ids': party_ids,
            'scenarios_usage': {
                'startup': {
                    'create_party_multi': {
                        'party_ids': party_ids
                    }
                }
            }
        }

        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print(f"💾 Конфигурация party_ids сохранена: {config_file}")

    except Exception as e:
        print(f"⚠️ Не удалось сохранить конфигурацию party_ids: {e}")


@register_action("validate_sandbox_steam_setup")
def validate_sandbox_steam_setup_action(instance, **kwargs):
    """Валидация настройки Steam в песочницах"""

    try:
        instance.logger.info("🔍 Валидация настройки Steam в песочницах...")

        collected_ids = collect_steam_ids_from_sandboxes(**kwargs)

        # Дополнительные проверки
        validation_results = _perform_steam_validation(collected_ids, **kwargs)

        if validation_results['is_valid']:
            instance.logger.info(f"✅ Валидация пройдена: {validation_results['summary']}")
            return True, "validation_passed"
        else:
            instance.logger.warning(f"⚠️ Проблемы с валидацией: {validation_results['issues']}")
            return False, "validation_issues"

    except Exception as e:
        instance.logger.error(f"❌ Ошибка валидации: {e}")
        return False, str(e)


def _perform_steam_validation(steam_ids, **kwargs):
    """Выполнение дополнительных проверок Steam настройки"""

    try:
        issues = []

        # Проверка количества ID
        expected_count = len(kwargs.get('sandbox_names', ['1', '2', '3', '4', '5', '6']))
        if len(steam_ids) < expected_count:
            issues.append(f"Найдено {len(steam_ids)} Steam ID, ожидалось {expected_count}")

        # Проверка формата Steam ID
        invalid_ids = []
        for steam_id in steam_ids:
            if not steam_id.isdigit() or len(steam_id) < 8:
                invalid_ids.append(steam_id)

        if invalid_ids:
            issues.append(f"Некорректные Steam ID: {invalid_ids}")

        # Проверка дубликатов
        if len(steam_ids) != len(set(steam_ids)):
            issues.append("Найдены дублирующиеся Steam ID")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'summary': f"{len(steam_ids)} уникальных Steam ID найдено",
            'steam_ids': steam_ids
        }

    except Exception as e:
        return {
            'is_valid': False,
            'issues': [f"Ошибка валидации: {e}"],
            'summary': "Валидация не завершена",
            'steam_ids': []
        }


def _find_master_window(master_sandbox, instance):
    """Поиск окна мастера по номеру песочницы"""

    try:
        # Получаем доступ к менеджеру экземпляров
        from core.dota_manager import MultiInstanceDotaManager

        # Проверяем, есть ли доступ к менеджеру через instance
        if hasattr(instance, 'manager') and hasattr(instance.manager, 'instances'):
            manager_instances = instance.manager.instances
        else:
            # Пытаемся найти через глобальный менеджер
            print("🔍 Поиск экземпляров через discover_instances...")
            temp_manager = MultiInstanceDotaManager(window_title="Dota 2")
            if temp_manager.discover_instances():
                manager_instances = temp_manager.instances
            else:
                print("❌ Не удалось найти экземпляры")
                return None

        print(f"🔍 Поиск окна мастера среди {len(manager_instances)} экземпляров")

        # Ищем экземпляр с нужным номером песочницы
        for inst in manager_instances:
            # Проверяем различные способы идентификации песочницы
            sandbox_id = None

            if hasattr(inst, 'sandbox_name'):
                sandbox_id = inst.sandbox_name
            elif hasattr(inst, 'instance_id'):
                sandbox_id = str(inst.instance_id)
            elif hasattr(inst, 'title'):
                # Извлекаем номер из заголовка окна
                import re
                match = re.search(r'\[#(\d+)\]', inst.title)
                if match:
                    sandbox_id = match.group(1)

            print(f"🔍 Экземпляр: sandbox_id={sandbox_id}, hwnd={getattr(inst, 'hwnd', 'unknown')}")

            if sandbox_id == master_sandbox:
                print(f"✅ Найден мастер: песочница #{sandbox_id}, hwnd={inst.hwnd}")
                return inst.hwnd

        print(f"❌ Не найдено окно для мастера песочницы #{master_sandbox}")
        return None

    except Exception as e:
        print(f"❌ Ошибка поиска окна мастера: {e}")
        return None

def _activate_master_window(master_hwnd, instance):
    """Активация окна мастера"""

    try:
        # Используем функцию ultra_fast_activate если доступна
        if hasattr(instance, 'ultra_fast_activate'):
            print("🚀 Использование ultra_fast_activate для активации мастера")
            return instance.ultra_fast_activate(master_hwnd)
        else:
            # Fallback к стандартной активации
            print("🔄 Использование стандартной активации окна")
            import win32gui
            import win32con

            # Восстановление свернутого окна
            if win32gui.IsIconic(master_hwnd):
                win32gui.ShowWindow(master_hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)

            # Активация окна
            win32gui.SetForegroundWindow(master_hwnd)
            time.sleep(0.1)

            # Проверка успеха
            current_hwnd = win32gui.GetForegroundWindow()
            success = current_hwnd == master_hwnd

            if success:
                print("✅ Окно мастера активировано (стандартный метод)")
            else:
                print(f"⚠️ Возможно, окно не активировано: текущий hwnd={current_hwnd}, нужный={master_hwnd}")

            return success

    except Exception as e:
        print(f"❌ Ошибка активации окна мастера: {e}")
        return False

@register_action("clear_current_steam_ids")
def clear_current_steam_ids_action(instance, **kwargs):
    """Очищает файл current_session_steam_ids.json и удаляет глобальную переменную"""
    config_dir = kwargs.get('config_dir', 'config')
    ids_file = os.path.join(config_dir, 'current_session_steam_ids.json')

    try:
        if os.path.exists(ids_file):
            os.remove(ids_file)
            print(f"💾 Файл {ids_file} удалён (очищен)")
        else:
            print(f"ℹ️ Файл {ids_file} не найден, нечего очищать")

        if 'CURRENT_SESSION_STEAM_IDS' in globals():
            del globals()['CURRENT_SESSION_STEAM_IDS']
            print("💾 Глобальная переменная CURRENT_SESSION_STEAM_IDS очищена")

        instance.logger.info("✅ Очистка current_session_steam_ids.json выполнена")
        return True, "steam_ids_cleared"
    except Exception as e:
        instance.logger.error(f"❌ Ошибка при очистке файла Steam IDs: {e}")
        return False, str(e)
