from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QMessageBox,
                             QLineEdit, QComboBox, QDialog, QFormLayout,
                             QDateEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor


class OrdersWindow(QMainWindow):
    def __init__(self, role, user_id, user_name, db):
        super().__init__()
        self.role = role
        self.user_id = user_id
        self.user_name = user_name
        self.db = db
        self.all_orders = []

        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        """Создание интерфейса окна заказов"""
        self.setWindowTitle(f"Заказы - {self.role}")
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Заголовок с информацией о пользователе
        user_info = QLabel(f"Вы вошли как: {self.user_name} ({self.role})")
        user_info.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(user_info)

        # === ПАНЕЛЬ УПРАВЛЕНИЯ ===
        controls_layout = QHBoxLayout()

        # Кнопка возврата к товарам
        back_btn = QPushButton("Назад к товарам")
        back_btn.clicked.connect(self.back_to_products)
        controls_layout.addWidget(back_btn)

        # Кнопка добавления заказа для администратора
        if self.role == "Администратор":
            add_btn = QPushButton("Добавить заказ")
            add_btn.clicked.connect(self.add_order)
            controls_layout.addWidget(add_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # === ПАНЕЛЬ ПОИСКА И ФИЛЬТРОВ ===
        if self.role in ["Менеджер", "Администратор"]:
            filters_layout = QHBoxLayout()

            # Поиск
            filters_layout.addWidget(QLabel("Поиск:"))
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Поиск по артикулу заказа...")
            self.search_input.textChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.search_input)

            # Фильтр по статусу
            filters_layout.addWidget(QLabel("Статус:"))
            self.status_filter = QComboBox()
            self.status_filter.addItems(["Все статусы", "Новый", "Завершен"])
            self.status_filter.currentTextChanged.connect(self.apply_filters)
            filters_layout.addWidget(self.status_filter)

            filters_layout.addStretch()
            layout.addLayout(filters_layout)

        # Заголовок таблицы
        title = QLabel("Список заказов")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Таблица заказов
        self.orders_table = QTableWidget()
        if self.role == "Администратор":
            self.orders_table.setColumnCount(7)
            self.orders_table.setHorizontalHeaderLabels([
                "Артикул заказа",
                "Статус заказа",
                "Адрес пункта выдачи",
                "Дата заказа",
                "Дата доставки",
                "Клиент",
                "Действия"
            ])
        else:
            self.orders_table.setColumnCount(5)
            self.orders_table.setHorizontalHeaderLabels([
                "Артикул заказа",
                "Статус заказа",
                "Адрес пункта выдачи",
                "Дата заказа",
                "Дата доставки"
            ])

        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.orders_table.setAlternatingRowColors(True)

        layout.addWidget(self.orders_table)

        central_widget.setLayout(layout)

    def load_orders(self):
        """Загрузка всех заказов из базы данных"""
        try:
            query = """
                    SELECT o.receipt_code, \
                           o.order_status, \
                           CONCAT(tp.city, ', ', tp.street, ', д. ', tp.num_house) as pickup_address, \
                           o.order_date, \
                           o.delivery_date, \
                           CONCAT(u.u_name, ' ', u.surname)                        as client_name, \
                           o.id
                    FROM orders o
                             LEFT JOIN take_points tp ON o.pickup_point_id = tp.id
                             LEFT JOIN users u ON o.client_id = u.id
                    ORDER BY o.order_date DESC \
                    """

            orders = self.db.execute_query(query)

            if orders is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить заказы")
                return

            self.all_orders = orders
            self.display_orders(self.all_orders)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки заказов: {str(e)}")
            print(f"❌ Ошибка в load_orders: {e}")

    def display_orders(self, orders):
        """Отображение заказов в таблице"""
        try:
            self.orders_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                # Безопасно получаем значения
                receipt_code = str(order.get('receipt_code', ''))
                order_status = str(order.get('order_status', ''))
                pickup_address = str(order.get('pickup_address', ''))
                order_date = str(order.get('order_date', ''))
                delivery_date = str(order.get('delivery_date', ''))
                client_name = str(order.get('client_name', ''))
                order_id = order.get('id')

                # Артикул заказа
                self.orders_table.setItem(row, 0, QTableWidgetItem(receipt_code))

                # Статус заказа
                status_item = QTableWidgetItem(order_status)
                if order_status == 'Завершен':
                    status_item.setBackground(QColor('#90EE90'))  # Светло-зеленый
                elif order_status == 'Новый':
                    status_item.setBackground(QColor('#FFB6C1'))  # Светло-розовый
                self.orders_table.setItem(row, 1, status_item)

                # Адрес пункта выдачи
                self.orders_table.setItem(row, 2, QTableWidgetItem(pickup_address))

                # Дата заказа
                self.orders_table.setItem(row, 3, QTableWidgetItem(order_date))

                # Дата доставки
                delivery_item = QTableWidgetItem(delivery_date)
                self.orders_table.setItem(row, 4, delivery_item)

                # Для администратора добавляем клиента и действия
                if self.role == "Администратор":
                    # Клиент
                    self.orders_table.setItem(row, 5, QTableWidgetItem(client_name))

                    # Действия
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Редактировать")
                    edit_btn.clicked.connect(lambda checked, o=order: self.edit_order(o))
                    actions_layout.addWidget(edit_btn)

                    delete_btn = QPushButton("Удалить")
                    delete_btn.clicked.connect(lambda checked, o=order: self.delete_order(o))
                    actions_layout.addWidget(delete_btn)

                    actions_widget.setLayout(actions_layout)
                    self.orders_table.setCellWidget(row, 6, actions_widget)

        except Exception as e:
            print(f"❌ Ошибка в display_orders: {e}")

    def apply_filters(self):
        """Применение фильтров и поиска"""
        try:
            if not self.all_orders:
                return

            # Получаем текущие значения фильтров
            search_text = self.search_input.text().lower()
            status_filter = self.status_filter.currentText()

            # Начинаем со всех заказов
            filtered_orders = self.all_orders.copy()

            # Применяем поиск
            if search_text:
                filtered_orders = [
                    o for o in filtered_orders
                    if search_text in str(o.get('receipt_code', '')).lower()
                ]

            # Применяем фильтр по статусу
            if status_filter != "Все статусы":
                filtered_orders = [
                    o for o in filtered_orders
                    if o.get('order_status') == status_filter
                ]

            # Отображаем отфильтрованные заказы
            self.display_orders(filtered_orders)

        except Exception as e:
            print(f"❌ Ошибка в apply_filters: {e}")

    def add_order(self):
        """Добавление нового заказа"""
        dialog = OrderDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()  # Обновляем список

    def edit_order(self, order):
        """Редактирование заказа"""
        dialog = OrderDialog(self.db, self, order)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()  # Обновляем список

    def delete_order(self, order):
        """Удаление заказа"""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить заказ #{order.get('receipt_code')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем связанные записи в order_items
                delete_items_query = "DELETE FROM order_items WHERE order_id = %s"
                self.db.execute_query(delete_items_query, (order.get('id'),))

                # Удаляем заказ
                delete_query = "DELETE FROM orders WHERE id = %s"
                self.db.execute_query(delete_query, (order.get('id'),))

                QMessageBox.information(self, "Успех", "Заказ успешно удален!")
                self.load_orders()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении заказа: {str(e)}")

    def back_to_products(self):
        """Возврат к окну товаров"""
        from products_window import ProductsWindow
        self.products_window = ProductsWindow(self.role, self.user_id, self.user_name, self.db)
        self.products_window.show()
        self.close()


class OrderDialog(QDialog):
    def __init__(self, db, parent=None, order=None):
        super().__init__(parent)
        self.db = db
        self.order = order
        self.is_editing = order is not None

        self.setWindowTitle("Редактирование заказа" if self.is_editing else "Добавление заказа")
        self.setModal(True)
        self.setup_ui()

        if self.is_editing:
            self.load_order_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Форма
        form_layout = QFormLayout()

        # Артикул заказа (только для редактирования)
        if self.is_editing:
            self.receipt_code_input = QLineEdit()
            self.receipt_code_input.setReadOnly(True)
            form_layout.addRow("Артикул заказа:", self.receipt_code_input)
        else:
            # Для нового заказа генерируем артикул автоматически
            self.receipt_code_input = None

        # Статус заказа
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Новый", "Завершен"])
        form_layout.addRow("Статус заказа:", self.status_combo)

        # Пункт выдачи
        self.pickup_combo = QComboBox()
        self.load_pickup_points()
        form_layout.addRow("Пункт выдачи:", self.pickup_combo)

        # Клиент
        self.client_combo = QComboBox()
        self.load_clients()
        form_layout.addRow("Клиент:", self.client_combo)

        # Дата заказа
        self.order_date_input = QDateEdit()
        self.order_date_input.setDate(QDate.currentDate())
        self.order_date_input.setCalendarPopup(True)
        form_layout.addRow("Дата заказа:", self.order_date_input)

        # Дата доставки
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setDate(QDate.currentDate().addDays(7))
        self.delivery_date_input.setCalendarPopup(True)
        form_layout.addRow("Дата доставки:", self.delivery_date_input)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_pickup_points(self):
        """Загрузка пунктов выдачи"""
        points = self.db.execute_query("""
                                       SELECT id, CONCAT(city, ', ', street, ', д. ', num_house) as address
                                       FROM take_points
                                       """)
        self.pickup_combo.clear()
        if points:
            for point in points:
                self.pickup_combo.addItem(point['address'], point['id'])

    def load_clients(self):
        """Загрузка клиентов"""
        clients = self.db.execute_query("""
                                        SELECT id, CONCAT(u_name, ' ', surname) as full_name
                                        FROM users
                                        WHERE role_id = 3 -- Только клиенты
                                        """)
        self.client_combo.clear()
        if clients:
            for client in clients:
                self.client_combo.addItem(client['full_name'], client['id'])

    def load_order_data(self):
        """Загрузка данных заказа для редактирования"""
        if not self.order:
            return

        # Устанавливаем значения
        if self.receipt_code_input:
            self.receipt_code_input.setText(str(self.order.get('receipt_code', '')))

        # Статус
        status = self.order.get('order_status')
        if status:
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

        # Даты
        order_date = self.order.get('order_date')
        if order_date:
            self.order_date_input.setDate(QDate.fromString(order_date, Qt.DateFormat.ISODate))

        delivery_date = self.order.get('delivery_date')
        if delivery_date:
            self.delivery_date_input.setDate(QDate.fromString(delivery_date, Qt.DateFormat.ISODate))

        # Клиент
        client_name = self.order.get('client_name')
        if client_name:
            index = self.client_combo.findText(client_name)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)

    def accept(self):
        """Сохранение заказа"""
        try:
            # Получаем ID выбранных значений
            pickup_point_id = self.pickup_combo.currentData()
            client_id = self.client_combo.currentData()

            if not all([pickup_point_id, client_id]):
                QMessageBox.warning(self, "Ошибка", "Выберите пункт выдачи и клиента!")
                return

            if self.is_editing:
                # Обновление существующего заказа
                query = """
                        UPDATE orders \
                        SET order_status    = %s, \
                            pickup_point_id = %s, \
                            client_id       = %s, \
                            order_date      = %s, \
                            delivery_date   = %s
                        WHERE id = %s \
                        """
                params = (
                    self.status_combo.currentText(),
                    pickup_point_id,
                    client_id,
                    self.order_date_input.date().toString(Qt.DateFormat.ISODate),
                    self.delivery_date_input.date().toString(Qt.DateFormat.ISODate),
                    self.order.get('id')
                )
            else:
                # Добавление нового заказа
                # Генерируем артикул заказа
                last_order = self.db.execute_query("SELECT receipt_code FROM orders ORDER BY id DESC LIMIT 1")
                if last_order and last_order[0]['receipt_code']:
                    new_receipt_code = int(last_order[0]['receipt_code']) + 1
                else:
                    new_receipt_code = 1000

                query = """
                        INSERT INTO orders
                        (order_status, pickup_point_id, client_id, order_date, delivery_date, receipt_code)
                        VALUES (%s, %s, %s, %s, %s, %s) \
                        """
                params = (
                    self.status_combo.currentText(),
                    pickup_point_id,
                    client_id,
                    self.order_date_input.date().toString(Qt.DateFormat.ISODate),
                    self.delivery_date_input.date().toString(Qt.DateFormat.ISODate),
                    new_receipt_code
                )

            result = self.db.execute_query(query, params)
            if result is not None:
                QMessageBox.information(self, "Успех",
                                        "Заказ успешно обновлен!" if self.is_editing else "Заказ успешно добавлен!")
                super().accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Ошибка при сохранении заказа!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении заказа: {str(e)}")