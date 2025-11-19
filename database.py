import pymysql
from pymysql import Error


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Подключение к базе данных"""
        try:
            self.connection = pymysql.connect(
                host='localhost',
                user='root',
                password='root',
                database='demois',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ База данных подключена!")
            return True
        except Error as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return False

    def execute_query(self, query, params=None):
        """Выполнение SQL запроса"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())

                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return cursor.lastrowid

        except Error as e:
            print(f"❌ Ошибка запроса: {e}")
            self.connection.rollback()
            return None

    def close(self):
        """Закрытие соединения с БД"""
        if self.connection:
            self.connection.close()
            print("🔌 Соединение с БД закрыто")