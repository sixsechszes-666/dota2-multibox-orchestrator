# sandbox_manager.py
import subprocess
import time
import os
import yaml
import logging
import psutil
import win32gui


class SandboxManager:
    """Класс для управления экземплярами Dota 2 в Sandboxie"""

    def __init__(self, config_file=os.path.join("config", "sandbox_config.yaml"), debug_mode=False):
        self.config_file = config_file
        self.debug_mode = debug_mode
        self.logger = self.setup_logger()
        self.config = self.load_config()
        self.launched_pids = set()

    def setup_logger(self):
        """Настройка логгера"""
        logger = logging.getLogger('SandboxManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)-8s %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def load_config(self):
        """Загрузка конфигурации из YAML файла"""
        try:
            if not os.path.exists(self.config_file):
                self.logger.warning(f"⚠️ Файл конфигурации {self.config_file} не найден, создаю по умолчанию")
                self.create_default_config()

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self.logger.info(f"✅ Конфигурация загружена из {self.config_file}")
            return config

        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            return self.get_default_config()

    def create_default_config(self):
        """Создание конфигурации по умолчанию"""
        default_config = self.get_default_config()

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)

            self.logger.info(f"✅ Создан файл конфигурации по умолчанию: {self.config_file}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания конфигурации: {e}")

    def get_default_config(self):
        """Конфигурация по умолчанию"""
        return {
            'sandboxie': {
                'path': 'C:\\Program Files\\Sandboxie\\Start.exe',
                'default_box': 'DefaultBox'
            },
            'dota2': {
                'steam_path': 'C:\\steam\\steam.exe',
                'dota_app_id': '570',
                'launch_options': ['-novid', '-high', '-window', '-w', '1600', '-h', '900', '-map', 'dota', '-prewarm',
                                   '-map_reduce_memory', '-nojoy', '-novr', '-nohltv', '-softparticledefaultoff',
                                   '-noaafonts'],
                'startup_delay': 40,
                'window_check_timeout': 120
            },
            'instances': [
                {
                    'name': 'Dota2_Instance_1',
                    'sandbox_name': '1',
                    'enabled': True,
                    'priority': 1
                },
                {
                    'name': 'Dota2_Instance_2',
                    'sandbox_name': '2',
                    'enabled': True,
                    'priority': 2
                }
            ]
        }

    def launch_all_instances(self):
        """Запуск всех включенных экземпляров с отслеживанием уникальных PID"""
        try:
            self.logger.info("🚀 Запуск всех экземпляров Dota 2 в Sandboxie")

            self.launched_pids = set()
            enabled_instances = [inst for inst in self.config['instances'] if inst.get('enabled', True)]

            if not enabled_instances:
                self.logger.warning("⚠️ Нет включенных экземпляров для запуска")
                return False

            enabled_instances.sort(key=lambda x: x.get('priority', 999))
            self.logger.info(f"📋 Найдено {len(enabled_instances)} экземпляров для запуска")

            launched_count = 0
            for instance in enabled_instances:
                if self.launch_single_instance(instance):
                    launched_count += 1

                    startup_delay = self.config['dota2'].get('startup_delay', 40)
                    if instance != enabled_instances[-1]:
                        self.logger.info(f"⏳ Ожидание {startup_delay} секунд перед следующим запуском...")
                        time.sleep(startup_delay)

            self.logger.info(f"✅ Успешно запущено {launched_count}/{len(enabled_instances)} экземпляров")
            return launched_count > 0

        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска экземпляров: {e}")
            return False

    def launch_single_instance(self, instance_config):
        """Запуск одного экземпляра Dota 2 с регистрацией HWND"""
        try:
            instance_name = instance_config['name']
            sandbox_name = str(instance_config['sandbox_name'])

            self.logger.info(f"🎮 Запуск экземпляра: {instance_name} в песочнице: {sandbox_name}")

            known_pids = self.launched_pids.copy()
            for inst_config in self.config['instances']:
                current_sandbox = str(inst_config['sandbox_name'])
                current_pids = self._get_current_pids_for_sandbox(current_sandbox)
                known_pids.update(current_pids)

            # Формируем команду запуска
            sandboxie_path = self.config['sandboxie']['path']
            steam_path = self.config['dota2']['steam_path']
            app_id = self.config['dota2']['dota_app_id']
            launch_options = ' '.join(self.config['dota2'].get('launch_options', []))

            command = [
                sandboxie_path,
                f'/box:{sandbox_name}',
                steam_path,
                "-silent",
                f'-applaunch',
                app_id
            ]

            if launch_options:
                command.extend(launch_options.split())

            self.logger.info(f"🔧 Команда запуска: {' '.join(command)}")

            # Запускаем процесс
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.logger.info(f"✅ Процесс запущен для {instance_name} (PID запуска: {process.pid})")

            # Ожидаем появления нового уникального PID
            new_pid = self.wait_for_new_unique_pid(known_pids, sandbox_name, timeout=120)

            if new_pid is None:
                self.logger.warning(f"⏰ Таймаут ожидания нового уникального PID для {instance_name}")
                return False

            self.launched_pids.add(new_pid)
            self.logger.info(f"💾 Новый уникальный PID {new_pid} сохранен для {instance_name}")

            from input.hwnd_tracker import HWNDTracker

            hwnd_tracker = HWNDTracker()
            hwnd = hwnd_tracker.register_pid_hwnd(new_pid, max_attempts=120, check_interval=2)

            if hwnd:
                self.logger.info(f"🎯 Экземпляр {instance_name} успешно запущен (PID: {new_pid}, HWND: {hwnd})")
                return True
            else:
                self.logger.info(
                    f"✅ Экземпляр {instance_name} запущен (PID: {new_pid}) - HWND будет зарегистрирован позже")
                return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска экземпляра {instance_config.get('name', 'Unknown')}: {e}")
            return False

    def _get_current_pids_for_sandbox(self, sandbox_name):
        """Получить текущие PID для указанной песочницы"""
        current_pids = set()

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                is_dota_process = ('dota' in proc_name or 'steam.exe' in proc_name or 'gameoverlayui' in proc_name)

                if is_dota_process:
                    try:
                        proc_obj = psutil.Process(proc.info['pid'])
                        create_time = proc_obj.create_time()
                        current_time = time.time()

                        if (current_time - create_time) < 300:
                            current_pids.add(proc.info['pid'])
                    except:
                        continue

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return current_pids

    def wait_for_new_unique_pid(self, known_pids, sandbox_name, timeout=120, check_interval=2):
        """Ожидание появления нового уникального PID процесса Dota 2"""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            current_pids = set()

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                    is_dota_process = ('dota' in proc_name or 'steam.exe' in proc_name or 'gameoverlayui' in proc_name)

                    if is_dota_process:
                        try:
                            proc_obj = psutil.Process(proc.info['pid'])
                            create_time = proc_obj.create_time()
                            current_time = time.time()

                            if (current_time - create_time) < (timeout + 10):
                                current_pids.add(proc.info['pid'])
                        except:
                            continue

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            new_pids = current_pids - set(known_pids)

            if new_pids:
                new_pid = max(new_pids)
                self.logger.info(f"✅ Найден новый уникальный PID: {new_pid} в песочнице {sandbox_name}")
                return new_pid

            elapsed = time.time() - start_time
            if elapsed % 30 == 0:
                self.logger.info(f"⏳ Ожидание нового PID для {sandbox_name}... ({elapsed:.0f}с/{timeout}с)")

            time.sleep(check_interval)

        return None

    def is_instance_running(self, sandbox_name):
        """Проверка, запущен ли экземпляр в указанной песочнице"""
        try:
            from input.hwnd_tracker import HWNDTracker

            hwnd_tracker = HWNDTracker()
            registered_hwnds = hwnd_tracker.get_all_registered_hwnds()

            # Проверяем зарегистрированные HWND
            for pid, hwnd in registered_hwnds.items():
                try:
                    if psutil.pid_exists(pid) and win32gui.IsWindow(hwnd):
                        return True
                except:
                    continue

            # Альтернативная проверка по launched_pids
            if hasattr(self, 'launched_pids') and self.launched_pids:
                for pid in self.launched_pids:
                    try:
                        proc = psutil.Process(pid)
                        if proc.is_running():
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки процесса для {sandbox_name}: {e}")
            return False

    def stop_all_instances(self):
        """Остановка всех экземпляров"""
        try:
            self.logger.info("🛑 Остановка всех экземпляров Dota 2")

            stopped_count = 0
            for instance in self.config['instances']:
                if self.stop_single_instance(instance):
                    stopped_count += 1

            # ✅ Очищаем HWND Tracker при остановке
            try:
                from input.hwnd_tracker import HWNDTracker
                hwnd_tracker = HWNDTracker()
                hwnd_tracker.cleanup_invalid_entries()
            except:
                pass

            self.launched_pids.clear()
            self.logger.info(f"✅ Остановлено {stopped_count} экземпляров")
            return stopped_count > 0

        except Exception as e:
            self.logger.error(f"❌ Ошибка остановки экземпляров: {e}")
            return False

    def stop_single_instance(self, instance_config):
        """Остановка одного экземпляра"""
        try:
            sandbox_name = instance_config['sandbox_name']
            self.logger.info(f"🛑 Остановка экземпляра в песочнице: {sandbox_name}")

            sandboxie_path = self.config['sandboxie']['path']
            command = [sandboxie_path, f'/box:{sandbox_name}', '/terminate']

            process = subprocess.run(command, capture_output=True, text=True)

            if process.returncode == 0:
                self.logger.info(f"✅ Экземпляр {sandbox_name} остановлен")
                return True
            else:
                self.logger.warning(f"⚠️ Ошибка остановки {sandbox_name}: {process.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка остановки экземпляра: {e}")
            return False

    def get_status(self):
        """Получение статуса всех экземпляров"""
        try:
            status_info = {
                'total_instances': len(self.config['instances']),
                'enabled_instances': len([i for i in self.config['instances'] if i.get('enabled', True)]),
                'running_instances': 0,
                'instances': []
            }

            for instance in self.config['instances']:
                sandbox_name = str(instance['sandbox_name'])
                is_running = self.is_instance_running(sandbox_name)

                if is_running:
                    status_info['running_instances'] += 1

                instance_status = {
                    'name': instance['name'],
                    'sandbox_name': sandbox_name,
                    'enabled': instance.get('enabled', True),
                    'running': is_running,
                    'priority': instance.get('priority', 999)
                }

                status_info['instances'].append(instance_status)

            return status_info

        except Exception as e:
            self.logger.error(f"❌ Ошибка получения статуса: {e}")
            return None

    def print_status(self):
        """Вывод статуса в консоль"""
        status = self.get_status()
        if not status:
            return

        print("\n" + "=" * 60)
        print("🎮 СТАТУС ЭКЗЕМПЛЯРОВ DOTA 2 В SANDBOXIE")
        print("=" * 60)
        print(f"📊 Всего экземпляров: {status['total_instances']}")
        print(f"✅ Включено: {status['enabled_instances']}")
        print(f"🚀 Запущено: {status['running_instances']}")
        print("\n📋 Детальный статус:")

        for instance in sorted(status['instances'], key=lambda x: x['priority']):
            enabled_icon = "✅" if instance['enabled'] else "❌"
            running_icon = "🟢" if instance['running'] else "🔴"

            print(
                f"  {enabled_icon} {running_icon} {instance['name']} ({instance['sandbox_name']}) - Приоритет: {instance['priority']}")

        print("=" * 60)


def main():
    """Основная функция для тестирования"""
    import sys

    manager = SandboxManager()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'start':
            manager.launch_all_instances()
        elif command == 'stop':
            manager.stop_all_instances()
        elif command == 'status':
            manager.print_status()
        elif command == 'config':
            print(f"📁 Файл конфигурации: {manager.config_file}")
            manager.create_default_config()
        else:
            print("❌ Неизвестная команда")
            print("📋 Доступные команды: start, stop, status, config")
    else:
        print("🎮 МЕНЕДЖЕР SANDBOXIE ДЛЯ DOTA 2")
        print("=" * 40)
        print("📋 Доступные команды:")
        print("  python sandbox_manager.py start   - Запустить все экземпляры")
        print("  python sandbox_manager.py stop    - Остановить все экземпляры")
        print("  python sandbox_manager.py status  - Показать статус")
        print("  python sandbox_manager.py config  - Создать конфигурацию")


if __name__ == "__main__":
    main()
