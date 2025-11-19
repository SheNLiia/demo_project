from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QMessageBox,
                             QLineEdit, QComboBox, QDialog, QFormLayout,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QTextEdit,
                             QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QFont
from PIL import Image
import os


class ProductsWindow(QMainWindow):
    def __init__(self, role, user_id, user_name, db):
        super().__init__()
        self.role = role
        self.user_id = user_id
        self.user_name = user_name
        self.db = db
        self.all_products = []
        self.current_image_path = None

        self.setup_ui()
        self.load_products()

        if self.role in ["Менеджер", "Администратор"]:
            self.load_filters_data()

    def setup_ui(self):
        """Создание интерфейса окна товаров"""
        self.setWindowTitle(f"Товары - {self.role}")
        self.setMinimumSize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Заголовок с информацией о пользователе
        user_info = QLabel(f"Вы вошли как: {self.user_name} ({self.role})")
        user_info.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(user_info)

        # === ПАНЕЛЬ УПРАВЛЕНИЯ ===
        controls_layout = QHBoxLayout()

        # Кнопка возврата
        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.go_back)
        controls_layout.addWidget(back_btn)

        # Кнопка заказов для менеджера и администратора
        if self.role in ["Менеджер", "Администратор"]:
            orders_btn = QPushButton("Заказы")
            orders_btn.clicked.connect(self.open_orders_window)
            controls_layout.addWidget(orders_btn)

        # Кнопки управления для администратора
        if self.role == "Администратор":
            add_btn = QPushButton("Добавить товар")
            add_btn.clicked.connect(self.add_product)
            controls_layout.addWidget(add_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # === ПАНЕЛЬ ПОИСКА И ФИЛЬТРОВ ===
        if self.role in ["Менеджер", "Администратор"]:
            filters_layout = QVBoxLayout()

            # Поиск
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("Поиск:"))
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Поиск по названию, артикулу...")
            self.search_input.textChanged.connect(self.apply_filters)
            search_layout.addWidget(self.search_input)
            filters_layout.addLayout(search_layout)

            # Фильтры и сортировка
            filter_layout = QHBoxLayout()

            # Фильтр по поставщику
            filter_layout.addWidget(QLabel("Поставщик:"))
            self.supplier_filter = QComboBox()
            self.supplier_filter.currentTextChanged.connect(self.apply_filters)
            filter_layout.addWidget(self.supplier_filter)

            # Фильтр по категории
            filter_layout.addWidget(QLabel("Категория:"))
            self.category_filter = QComboBox()
            self.category_filter.currentTextChanged.connect(self.apply_filters)
            filter_layout.addWidget(self.category_filter)

            # Сортировка
            filter_layout.addWidget(QLabel("Сортировка:"))
            self.sort_combo = QComboBox()
            self.sort_combo.addItems([
                "Без сортировки",
                "Количество ↑",
                "Количество ↓",
                "Цена ↑",
                "Цена ↓",
                "Скидка ↑",
                "Скидка ↓"
            ])
            self.sort_combo.currentTextChanged.connect(self.apply_filters)
            filter_layout.addWidget(self.sort_combo)

            filters_layout.addLayout(filter_layout)
            layout.addLayout(filters_layout)

        # Заголовок таблицы
        title = QLabel("Список товаров")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Таблица товаров
        self.products_table = QTableWidget()
        if self.role == "Администратор":
            self.products_table.setColumnCount(10)
            self.products_table.setHorizontalHeaderLabels([
                "Артикул",
                "Наименование",
                "Категория",
                "Производитель",
                "Поставщик",
                "Цена",
                "Количество",
                "Скидка %",
                "Описание",
                "Действия"
            ])
        else:
            self.products_table.setColumnCount(8)
            self.products_table.setHorizontalHeaderLabels([
                "Артикул",
                "Наименование",
                "Категория",
                "Производитель",
                "Цена",
                "Количество",
                "Скидка %",
                "Описание"
            ])

        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.doubleClicked.connect(self.on_table_double_click)

        layout.addWidget(self.products_table)

        central_widget.setLayout(layout)

    def load_filters_data(self):
        """Загрузка данных для фильтров"""
        try:
            # Загружаем поставщиков
            suppliers = self.db.execute_query("SELECT s_name FROM suppliers")
            self.supplier_filter.clear()
            self.supplier_filter.addItem("Все поставщики")

            if suppliers:
                for supplier in suppliers:
                    if supplier and 's_name' in supplier and supplier['s_name']:
                        self.supplier_filter.addItem(supplier['s_name'])

            # Загружаем категории
            categories = self.db.execute_query("SELECT category_name FROM categories")
            self.category_filter.clear()
            self.category_filter.addItem("Все категории")

            if categories:
                for category in categories:
                    if category and 'category_name' in category and category['category_name']:
                        self.category_filter.addItem(category['category_name'])

        except Exception as e:
            print(f"❌ Ошибка загрузки фильтров: {e}")

    def load_products(self):
        """Загрузка всех товаров из базы данных"""
        try:
            query = """
                    SELECT p.article, \
                           p.p_name, \
                           c.category_name, \
                           b.b_name, \
                           s.s_name, \
                           p.price, \
                           p.quantity, \
                           p.discount_percent, \
                           p.description, \
                           p.image_path, \
                           p.id
                    FROM products p
                             LEFT JOIN categories c ON p.category_id = c.id
                             LEFT JOIN brends b ON p.brend_id = b.id
                             LEFT JOIN suppliers s ON p.supplier_id = s.id \
                    """

            products = self.db.execute_query(query)

            if products is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить товары")
                return

            self.all_products = products
            self.display_products(self.all_products)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки товаров: {str(e)}")
            print(f"❌ Ошибка в load_products: {e}")

    def display_products(self, products):
        """Отображение товаров в таблице"""
        try:
            self.products_table.setRowCount(len(products))

            for row, product in enumerate(products):
                # Безопасно получаем значения
                article = str(product.get('article', ''))
                p_name = str(product.get('p_name', ''))
                category_name = str(product.get('category_name', ''))
                b_name = str(product.get('b_name', ''))
                s_name = str(product.get('s_name', ''))
                price = float(product.get('price', 0))
                quantity = int(product.get('quantity', 0))
                discount = int(product.get('discount_percent', 0))
                description = str(product.get('description', ''))
                product_id = product.get('id')

                # Артикул
                self.products_table.setItem(row, 0, QTableWidgetItem(article))

                # Наименование
                self.products_table.setItem(row, 1, QTableWidgetItem(p_name))

                # Категория
                self.products_table.setItem(row, 2, QTableWidgetItem(category_name))

                # Производитель
                self.products_table.setItem(row, 3, QTableWidgetItem(b_name))

                # Для администратора добавляем поставщика
                if self.role == "Администратор":
                    self.products_table.setItem(row, 4, QTableWidgetItem(s_name))
                    col_offset = 1
                else:
                    col_offset = 0

                # Цена
                price_col = 4 + col_offset
                if discount > 0:
                    final_price = price * (1 - discount / 100)
                    price_text = f"~~{price:.2f}~~ → {final_price:.2f} ₽"
                    price_item = QTableWidgetItem(price_text)
                    price_item.setForeground(QColor('red'))
                else:
                    price_item = QTableWidgetItem(f"{price:.2f} ₽")

                self.products_table.setItem(row, price_col, price_item)

                # Количество
                quantity_col = 5 + col_offset
                quantity_item = QTableWidgetItem(str(quantity))
                self.products_table.setItem(row, quantity_col, quantity_item)

                # Скидка
                discount_col = 6 + col_offset
                discount_item = QTableWidgetItem(str(discount))
                self.products_table.setItem(row, discount_col, discount_item)

                # Описание
                desc_col = 7 + col_offset
                desc_item = QTableWidgetItem(description[:100] + "..." if len(description) > 100 else description)
                self.products_table.setItem(row, desc_col, desc_item)

                # Действия для администратора
                if self.role == "Администратор":
                    actions_col = 9
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Редактировать")
                    edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                    actions_layout.addWidget(edit_btn)

                    delete_btn = QPushButton("Удалить")
                    delete_btn.clicked.connect(lambda checked, p=product: self.delete_product(p))
                    actions_layout.addWidget(delete_btn)

                    actions_widget.setLayout(actions_layout)
                    self.products_table.setCellWidget(row, actions_col, actions_widget)

                # Подсвечиваем строки
                self.highlight_row(row, product, col_offset)

        except Exception as e:
            print(f"❌ Ошибка в display_products: {e}")

    def apply_filters(self):
        """Применение фильтров и поиска"""
        try:
            if not self.all_products:
                return

            # Получаем текущие значения фильтров
            search_text = self.search_input.text().lower()
            supplier_filter = self.supplier_filter.currentText()
            category_filter = self.category_filter.currentText()
            sort_option = self.sort_combo.currentText()

            # Начинаем со всех товаров
            filtered_products = self.all_products.copy()

            # Применяем поиск
            if search_text:
                filtered_products = [
                    p for p in filtered_products
                    if (search_text in str(p.get('p_name', '')).lower() or
                        search_text in str(p.get('article', '')).lower() or
                        search_text in str(p.get('description', '')).lower() or
                        search_text in str(p.get('b_name', '')).lower())
                ]

            # Применяем фильтр по поставщику
            if supplier_filter != "Все поставщики":
                filtered_products = [
                    p for p in filtered_products
                    if p.get('s_name') == supplier_filter
                ]

            # Применяем фильтр по категории
            if category_filter != "Все категории":
                filtered_products = [
                    p for p in filtered_products
                    if p.get('category_name') == category_filter
                ]

            # Применяем сортировку
            if sort_option != "Без сортировки":
                if sort_option == "Количество ↑":
                    filtered_products.sort(key=lambda x: x.get('quantity', 0) or 0)
                elif sort_option == "Количество ↓":
                    filtered_products.sort(key=lambda x: x.get('quantity', 0) or 0, reverse=True)
                elif sort_option == "Цена ↑":
                    filtered_products.sort(key=lambda x: x.get('price', 0) or 0)
                elif sort_option == "Цена ↓":
                    filtered_products.sort(key=lambda x: x.get('price', 0) or 0, reverse=True)
                elif sort_option == "Скидка ↑":
                    filtered_products.sort(key=lambda x: x.get('discount_percent', 0) or 0)
                elif sort_option == "Скидка ↓":
                    filtered_products.sort(key=lambda x: x.get('discount_percent', 0) or 0, reverse=True)

            # Отображаем отфильтрованные товары
            self.display_products(filtered_products)

        except Exception as e:
            print(f"❌ Ошибка в apply_filters: {e}")

    def highlight_row(self, row, product, col_offset=0):
        """Подсветка строк в зависимости от условий"""
        try:
            discount = product.get('discount_percent', 0) or 0
            quantity = product.get('quantity', 0) or 0

            # Подсветка если скидка больше 15%
            if discount > 15:
                for col in range(self.products_table.columnCount()):
                    item = self.products_table.item(row, col)
                    if item:
                        item.setBackground(QColor('#2E8B57'))

            # Подсветка если товара нет в наличии
            elif quantity == 0:
                for col in range(self.products_table.columnCount()):
                    item = self.products_table.item(row, col)
                    if item:
                        item.setBackground(QColor('#87CEEB'))

        except Exception as e:
            print(f"❌ Ошибка в highlight_row: {e}")

    def on_table_double_click(self, index):
        """Обработка двойного клика по таблице"""
        if self.role == "Администратор":
            row = index.row()
            product_data = {}
            for col in range(9):  # Все колонки кроме действий
                item = self.products_table.item(row, col)
                if item:
                    if col == 0:
                        product_data['article'] = item.text()
                    elif col == 1:
                        product_data['p_name'] = item.text()
                    elif col == 2:
                        product_data['category_name'] = item.text()
                    elif col == 3:
                        product_data['b_name'] = item.text()
                    elif col == 4:
                        product_data['s_name'] = item.text()
                    elif col == 5:
                        price_text = item.text()
                        if '→' in price_text:
                            price_text = price_text.split('→')[1].strip().split(' ')[0]
                        product_data['price'] = float(price_text)
                    elif col == 6:
                        product_data['quantity'] = int(item.text())
                    elif col == 7:
                        product_data['discount_percent'] = int(item.text())
                    elif col == 8:
                        product_data['description'] = item.text()

            # Находим полные данные товара
            for product in self.all_products:
                if product.get('article') == product_data['article']:
                    self.edit_product(product)
                    break

    def add_product(self):
        """Добавление нового товара"""
        dialog = ProductDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()  # Обновляем список

    def edit_product(self, product):
        """Редактирование товара"""
        dialog = ProductDialog(self.db, self, product)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()  # Обновляем список

    def delete_product(self, product):
        """Удаление товара"""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить товар '{product.get('p_name')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Проверяем, есть ли товар в заказах
                check_query = "SELECT COUNT(*) as count FROM order_items WHERE product_article = %s"
                result = self.db.execute_query(check_query, (product.get('article'),))

                if result and result[0]['count'] > 0:
                    QMessageBox.warning(self, "Ошибка", "Нельзя удалить товар, который присутствует в заказе!")
                    return

                # Удаляем изображение если есть
                if product.get('image_path'):
                    try:
                        if os.path.exists(product.get('image_path')):
                            os.remove(product.get('image_path'))
                    except Exception as e:
                        print(f"Ошибка удаления файла: {e}")

                # Удаляем товар из БД
                delete_query = "DELETE FROM products WHERE article = %s"
                self.db.execute_query(delete_query, (product.get('article'),))

                QMessageBox.information(self, "Успех", "Товар успешно удален!")
                self.load_products()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении товара: {str(e)}")

    def open_orders_window(self):
        """Открытие окна заказов"""
        from orders_window import OrdersWindow
        self.orders_window = OrdersWindow(self.role, self.user_id, self.user_name, self.db)
        self.orders_window.show()
        self.close()

    def go_back(self):
        """Возврат к выбору роли"""
        from main import RoleSelectionWindow
        self.role_window = RoleSelectionWindow()
        self.role_window.show()
        self.close()


class ProductDialog(QDialog):
    def __init__(self, db, parent=None, product=None):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.current_image_path = None
        self.is_editing = product is not None

        self.setWindowTitle("Редактирование товара" if self.is_editing else "Добавление товара")
        self.setModal(True)
        self.setup_ui()

        if self.is_editing:
            self.load_product_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Форма
        form_layout = QFormLayout()

        # Артикул
        self.article_input = QLineEdit()
        form_layout.addRow("Артикул:", self.article_input)

        # Наименование
        self.name_input = QLineEdit()
        form_layout.addRow("Наименование:", self.name_input)

        # Категория
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Категория:", self.category_combo)

        # Производитель
        self.brand_combo = QComboBox()
        self.load_brands()
        form_layout.addRow("Производитель:", self.brand_combo)

        # Поставщик
        self.supplier_combo = QComboBox()
        self.load_suppliers()
        form_layout.addRow("Поставщик:", self.supplier_combo)

        # Цена
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        form_layout.addRow("Цена:", self.price_input)

        # Количество
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999999)
        form_layout.addRow("Количество:", self.quantity_input)

        # Скидка
        self.discount_input = QSpinBox()
        self.discount_input.setMaximum(100)
        form_layout.addRow("Скидка %:", self.discount_input)

        # Описание
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_input)

        # Изображение
        image_layout = QHBoxLayout()
        self.image_btn = QPushButton("Выбрать изображение")
        self.image_btn.clicked.connect(self.select_image)
        self.image_label = QLabel("Изображение не выбрано")
        image_layout.addWidget(self.image_btn)
        image_layout.addWidget(self.image_label)
        form_layout.addRow("Изображение:", image_layout)

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

    def load_categories(self):
        """Загрузка категорий"""
        categories = self.db.execute_query("SELECT id, category_name FROM categories")
        self.category_combo.clear()
        if categories:
            for category in categories:
                self.category_combo.addItem(category['category_name'], category['id'])

    def load_brands(self):
        """Загрузка брендов"""
        brands = self.db.execute_query("SELECT id, b_name FROM brends")
        self.brand_combo.clear()
        if brands:
            for brand in brands:
                self.brand_combo.addItem(brand['b_name'], brand['id'])

    def load_suppliers(self):
        """Загрузка поставщиков"""
        suppliers = self.db.execute_query("SELECT id, s_name FROM suppliers")
        self.supplier_combo.clear()
        if suppliers:
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier['s_name'], supplier['id'])

    def load_product_data(self):
        """Загрузка данных товара для редактирования"""
        if not self.product:
            return

        self.article_input.setText(self.product.get('article', ''))
        self.name_input.setText(self.product.get('p_name', ''))
        self.price_input.setValue(float(self.product.get('price', 0)))
        self.quantity_input.setValue(int(self.product.get('quantity', 0)))
        self.discount_input.setValue(int(self.product.get('discount_percent', 0)))
        self.description_input.setText(self.product.get('description', ''))

        # Устанавливаем выбранные значения в комбобоксы
        category_name = self.product.get('category_name')
        if category_name:
            index = self.category_combo.findText(category_name)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        brand_name = self.product.get('b_name')
        if brand_name:
            index = self.brand_combo.findText(brand_name)
            if index >= 0:
                self.brand_combo.setCurrentIndex(index)

        supplier_name = self.product.get('s_name')
        if supplier_name:
            index = self.supplier_combo.findText(supplier_name)
            if index >= 0:
                self.supplier_combo.setCurrentIndex(index)

        # Загружаем путь к изображению
        image_path = self.product.get('image_path')
        if image_path and os.path.exists(image_path):
            self.current_image_path = image_path
            self.image_label.setText(os.path.basename(image_path))

    def select_image(self):
        """Выбор изображения"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            try:
                # Создаем папку для изображений если её нет
                if not os.path.exists("product_images"):
                    os.makedirs("product_images")

                # Обрабатываем изображение
                with Image.open(file_path) as img:
                    # Изменяем размер
                    img = img.resize((300, 200))

                    # Сохраняем в папку приложения
                    filename = f"product_{self.article_input.text() or 'new'}.png"
                    save_path = os.path.join("product_images", filename)
                    img.save(save_path)

                    self.current_image_path = save_path
                    self.image_label.setText(os.path.basename(save_path))

            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось обработать изображение: {str(e)}")

    def accept(self):
        """Сохранение товара"""
        try:
            # Валидация
            if not self.article_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите артикул!")
                return

            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите наименование!")
                return

            # Получаем ID выбранных значений
            category_id = self.category_combo.currentData()
            brand_id = self.brand_combo.currentData()
            supplier_id = self.supplier_combo.currentData()

            if not all([category_id, brand_id, supplier_id]):
                QMessageBox.warning(self, "Ошибка", "Выберите категорию, производителя и поставщика!")
                return

            if self.is_editing:
                # Обновление существующего товара
                query = """
                        UPDATE products \
                        SET p_name           = %s, \
                            category_id      = %s, \
                            brend_id         = %s, \
                            supplier_id      = %s, \
                            price            = %s, \
                            quantity         = %s, \
                            discount_percent = %s, \
                            description      = %s, \
                            image_path       = %s
                        WHERE article = %s \
                        """
                params = (
                    self.name_input.text(),
                    category_id,
                    brand_id,
                    supplier_id,
                    self.price_input.value(),
                    self.quantity_input.value(),
                    self.discount_input.value(),
                    self.description_input.toPlainText(),
                    self.current_image_path,
                    self.product.get('article')
                )
            else:
                # Добавление нового товара
                # Проверяем уникальность артикула
                check_query = "SELECT COUNT(*) as count FROM products WHERE article = %s"
                result = self.db.execute_query(check_query, (self.article_input.text(),))

                if result and result[0]['count'] > 0:
                    QMessageBox.warning(self, "Ошибка", "Товар с таким артикулом уже существует!")
                    return

                query = """
                        INSERT INTO products
                        (article, p_name, category_id, brend_id, supplier_id, price, quantity, discount_percent, \
                         description, image_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                        """
                params = (
                    self.article_input.text(),
                    self.name_input.text(),
                    category_id,
                    brand_id,
                    supplier_id,
                    self.price_input.value(),
                    self.quantity_input.value(),
                    self.discount_input.value(),
                    self.description_input.toPlainText(),
                    self.current_image_path
                )

            result = self.db.execute_query(query, params)
            if result is not None:
                QMessageBox.information(self, "Успех",
                                        "Товар успешно обновлен!" if self.is_editing else "Товар успешно добавлен!")
                super().accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Ошибка при сохранении товара!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении товара: {str(e)}")