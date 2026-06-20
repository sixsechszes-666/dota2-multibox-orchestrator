# sync_manager.py
from features.hero_sync import HeroSynchronizer
import socket
import time


class SyncManager:
    """Менеджер для управления синхронизацией между экземплярами"""

    def __init__(self):
        self.sync = HeroSynchronizer()
        self.computer_name = socket.gethostname()
        print(f"🖥️ Инициализирован SyncManager для компьютера: {self.computer_name}")
        print(f"📊 Используется таблица: PC_Sync_Status")

    def start_new_match(self, match_id=None):
        """Начать новый матч (очистить все резервирования)"""
        match_id = self.sync.start_new_match(match_id)
        if match_id:
            print(f"🎮 Новый матч начат: {match_id}")
            print(f"🔄 Все герои теперь доступны для выбора")
        return match_id

    def show_current_match_status(self):
        """Показать статус текущего матча"""
        # Определяем текущий матч
        current_time = int(time.time())
        match_interval = 30 * 60  # 30 минут
        match_time_slot = current_time // match_interval
        current_match_id = f"match_{match_time_slot}"

        print(f"\n📊 СТАТУС ТЕКУЩЕГО МАТЧА: {current_match_id}")
        print(f"🖥️ Компьютер: {self.computer_name}")

        status = self.sync.get_match_status(current_match_id)
        if status:
            print(f"👥 Героев выбрано: {status['heroes_count']}")
            print(f"🎭 Выбранные герои: {status['heroes']}")

            print("\n👥 ЭКЗЕМПЛЯРЫ В ТЕКУЩЕМ МАТЧЕ:")
            for instance_id, info in status['instances'].items():
                print(f"  🎯 {instance_id}: {info['hero']} на {info['computer']}")
        else:
            print("❌ Не удалось получить статус матча")

    def show_all_status(self):
        """Показать полный статус синхронизации"""
        print(f"\n📊 ПОЛНЫЙ СТАТУС СИНХРОНИЗАЦИИ (PC_Sync_Status):")
        print(f"🖥️ Текущий компьютер: {self.computer_name}")

        try:
            all_records = self.sync.worksheet.get_all_records()

            matches = {}
            for record in all_records:
                match_id = record.get('Match_ID', '')
                if match_id and match_id not in matches:
                    matches[match_id] = []

                if record.get('Status') == 'taken' and record.get('Hero') != "=== NEW MATCH ===":
                    matches[match_id].append({
                        'hero': record.get('Hero'),
                        'instance': record.get('Instance_ID'),
                        'computer': record.get('Computer')
                    })

            for match_id, heroes in matches.items():
                print(f"\n🎮 Матч: {match_id}")
                print(f"   👥 Героев выбрано: {len(heroes)}")
                for hero_info in heroes:
                    print(f"   🎭 {hero_info['hero']} - {hero_info['instance']} ({hero_info['computer']})")

        except Exception as e:
            print(f"❌ Ошибка получения статуса: {e}")


if __name__ == "__main__":
    import sys

    print("🔧 PC_Sync_Status Manager (Auto Match Rotation)")
    print("=" * 50)

    manager = SyncManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            manager.show_current_match_status()
        elif command == "all":
            manager.show_all_status()
        elif command == "new":
            manager.start_new_match()
        else:
            print("❌ Неизвестная команда")
            print("📋 Доступные команды:")
            print("  status - показать статус текущего матча")
            print("  all    - показать все матчи")
            print("  new    - начать новый матч принудительно")
    else:
        manager.show_current_match_status()