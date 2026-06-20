# sheets_monitor.py
from core.connection_manager import GoogleSheetsManager
import time


def print_connection_stats():
    """Вывести статистику подключений"""
    stats = GoogleSheetsManager.get_stats()

    print("📊 Статистика подключений Google Sheets:")
    print(f"Всего подключений: {stats['total_connections']}")

    for key, info in stats['connections'].items():
        print(f"  {key}:")
        print(f"    Создано: {time.ctime(info['created_at'])}")
        print(f"    Последнее использование: {time.ctime(info['last_used'])}")
        print(f"    Возраст: {info['age_minutes']:.1f} минут")


def cleanup_connections():
    """Очистить старые подключения"""
    GoogleSheetsManager.cleanup_old_connections(max_age_hours=1)
    print("🧹 Очистка старых подключений завершена")


if __name__ == "__main__":
    print_connection_stats()
    cleanup_connections()
