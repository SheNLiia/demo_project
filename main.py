from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt
from database import Database
from products_window import ProductsWindow
import sys


class RoleSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Выбор роли")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        title_label = QLabel("Выберите роль для входа")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Кнопки выбора роли
        role_buttons_layout = QVBoxLayout()

        # Администратор
        admin_btn = QPushButton("Администратор")
        admin_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                font-weight: bold; 
                padding: 12px; 
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        admin_btn.clicked.connect(lambda: self.select_role("Администратор"))
        role_buttons_layout.addWidget(admin_btn)

        # Менеджер
        manager_btn = QPushButton("Менеджер")
        manager_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007bff; 
                color: white; 
                font-weight: bold; 
                padding: 12px; 
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
        manager_btn.clicked.connect(lambda: self.select_role("Менеджер"))
        role_buttons_layout.addWidget(manager_btn)

        # Клиент
        client_btn = QPushButton("Клиент")
        client_btn.setStyleSheet("""
            QPushButton { 
                background-color: #28a745; 
                color: white; 
                font-weight: bold; 
                padding: 12px; 
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        client_btn.clicked.connect(lambda: self.select_role("Клиент"))
        role_buttons_layout.addWidget(client_btn)

        # Гость
        guest_btn = QPushButton("Гость")
        guest_btn.setStyleSheet("""
            QPushButton { 
                background-color: #6c757d; 
                color: white; 
                font-weight: bold; 
                padding: 12px; 
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        guest_btn.clicked.connect(lambda: self.select_role("Гость"))
        role_buttons_layout.addWidget(guest_btn)

        layout.addLayout(role_buttons_layout)
        self.setLayout(layout)

    def select_role(self, role):
        """Переход к окну авторизации для выбранной роли"""
        if role == "Гость":
            # Для гостя сразу открываем окно товаров с передачей базы данных
            self.open_products_window("Гость", None, "Гость")
        else:
            # Для других ролей открываем окно авторизации
            self.login_window = LoginWindow(role, self.db)
            self.login_window.show()
            self.hide()

    def open_products_window(self, role, user_id, user_name):
        """Открывает окно с товарами с учетом роли"""
        self.products_window = ProductsWindow(role, user_id, user_name, self.db)
        self.products_window.show()
        self.close()


class LoginWindow(QWidget):
    def __init__(self, role, db):
        super().__init__()
        self.role = role
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Авторизация - {self.role}")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        title_label = QLabel(f"Вход как {self.role}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Поля для ввода
        form_layout = QVBoxLayout()

        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Введите ваш email")
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)

        password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите ваш пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)

        layout.addLayout(form_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet("""
            QPushButton { 
                background-color: #6c757d; 
                color: white; 
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        buttons_layout.addWidget(back_btn)

        login_btn = QPushButton("Войти")
        login_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007bff; 
                color: white; 
                font-weight: bold; 
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
        login_btn.clicked.connect(self.check_login)
        buttons_layout.addWidget(login_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def check_login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if not self.db.connection:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД!")
            return

        query = """
                SELECT u.id, u.u_name, u.surname, r.r_name
                FROM users u
                         JOIN roles r ON u.role_id = r.id
                WHERE u.email = %s \
                  AND u.u_password = %s \
                  AND r.r_name = %s \
                """

        result = self.db.execute_query(query, (email, password, self.role))

        if result:
            user = result[0]
            user_id = user['id']
            name = user['u_name']
            surname = user['surname']
            role = user['r_name']

            full_name = f"{name} {surname}"

            QMessageBox.information(self, "Успех", f"Добро пожаловать, {full_name}!")

            # Открываем окно товаров с ролью пользователя
            self.open_products_window(role, user_id, full_name)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный email или пароль для выбранной роли!")
            self.password_input.clear()

    def go_back(self):
        """Возврат к выбору роли"""
        from main import RoleSelectionWindow
        self.role_window = RoleSelectionWindow()
        self.role_window.show()
        self.close()

    def open_products_window(self, role, user_id, user_name):
        """Открывает окно с товарами с учетом роли"""
        self.products_window = ProductsWindow(role, user_id, user_name, self.db)
        self.products_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RoleSelectionWindow()
    window.show()
    sys.exit(app.exec())