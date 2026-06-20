# connection_manager.py
import gspread
import time
import threading
from google.oauth2.service_account import Credentials


class GoogleSheetsManager:
    """Глобальный менеджер подключений к Google Sheets"""

    _connections = {}
    _lock = threading.Lock()

    @classmethod
    def get_connection(cls, spreadsheet_name, credentials_file="config/credentials.json"):
        """Получить или создать подключение к таблице"""

        connection_key = f"{spreadsheet_name}_{credentials_file}"

        if connection_key not in cls._connections:
            with cls._lock:
                if connection_key not in cls._connections:
                    print(f"🔗 Создание нового подключения к {spreadsheet_name}")

                    try:
                        # Создаем подключение с Keep-Alive
                        scopes = [
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive'
                        ]

                        credentials = Credentials.from_service_account_file(
                            credentials_file, scopes=scopes
                        )

                        try:
                            import gspread.httpsession
                            http_session = gspread.httpsession.HTTPSession(
                                headers={'Connection': 'Keep-Alive'}
                            )
                            # Используем импортированный в начале файла gspread
                            import gspread as gs_module
                            client = gs_module.Client(auth=credentials, http_session=http_session)
                        except (ImportError, AttributeError):
                            # Fallback для старых версий gspread - используем глобальный модуль
                            import gspread as gs_module
                            client = gs_module.authorize(credentials)

                        # Открываем таблицу
                        try:
                            spreadsheet = client.open(spreadsheet_name)
                            print(f"✅ Подключен к существующей таблице: {spreadsheet_name}")
                        except gspread.SpreadsheetNotFound:
                            spreadsheet = client.create(spreadsheet_name)
                            print(f"✅ Создана новая таблица: {spreadsheet_name}")

                        # Получаем первый лист
                        try:
                            worksheet = spreadsheet.sheet1
                        except Exception:
                            worksheet = spreadsheet.add_worksheet(title="Heroes", rows="100", cols="10")

                        cls._connections[connection_key] = {
                            'client': client,
                            'spreadsheet': spreadsheet,
                            'worksheet': worksheet,
                            'created_at': time.time(),
                            'last_used': time.time()
                        }

                    except Exception as e:
                        print(f"❌ Ошибка создания подключения к {spreadsheet_name}: {e}")
                        raise

        # Обновляем время последнего использования
        cls._connections[connection_key]['last_used'] = time.time()
        return cls._connections[connection_key]

    @classmethod
    def refresh_connection(cls, spreadsheet_name, credentials_file="config/credentials.json"):
        """Принудительное обновление подключения"""
        connection_key = f"{spreadsheet_name}_{credentials_file}"

        print(f"🔄 Обновление подключения к {spreadsheet_name}")

        with cls._lock:
            if connection_key in cls._connections:
                del cls._connections[connection_key]

        return cls.get_connection(spreadsheet_name, credentials_file)

    @classmethod
    def cleanup_old_connections(cls, max_age_hours=2):
        """Очистка старых подключений"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        with cls._lock:
            keys_to_remove = []
            for key, connection in cls._connections.items():
                age = current_time - connection['last_used']
                if age > max_age_seconds:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                print(f"🧹 Удаление старого подключения: {key}")
                del cls._connections[key]

    @classmethod
    def get_stats(cls):
        """Получить статистику подключений"""
        with cls._lock:
            return {
                'total_connections': len(cls._connections),
                'connections': {
                    key: {
                        'created_at': conn['created_at'],
                        'last_used': conn['last_used'],
                        'age_minutes': (time.time() - conn['created_at']) / 60
                    }
                    for key, conn in cls._connections.items()
                }
            }
