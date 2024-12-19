import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel
)
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt


class DroneControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Control")
        self.setGeometry(100, 100, 1000, 800)

        # Создаем главный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Основной горизонтальный layout
        self.main_layout = QHBoxLayout(self.central_widget)

        # Левая часть: графическое поле
        self.setup_graphics_view()

        # Средняя часть: информация о коптере
        self.setup_drone_info()

        # Правая часть: кнопки управления
        self.setup_control_buttons()

        # Изначальные координаты коптера
        self.drone_x = 100
        self.drone_y = -50
        self.update_drone()

    def setup_graphics_view(self):
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(-400, -400, 800, 800)

        # Рисуем оси
        self.draw_axes()

        # Добавляем графическое представление в основной layout
        self.main_layout.addWidget(self.view, stretch=3)

    def setup_drone_info(self):
        # Лейаут для информации о коптере
        self.info_layout = QVBoxLayout()

        # Метка для отображения координат
        self.coords_label = QLabel("Координаты коптера: (100, -50)")
        self.coords_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info_layout.addWidget(self.coords_label)

        # Заполнение оставшегося пространства
        self.info_layout.addStretch()

        # Обернуть в виджет и добавить в основной layout
        self.info_widget = QWidget()
        self.info_widget.setLayout(self.info_layout)
        self.main_layout.addWidget(self.info_widget, stretch=1)

    def setup_control_buttons(self):
        # Лейаут для кнопок управления
        self.buttons_layout = QVBoxLayout()

        # Пример кнопок управления
        move_up_button = QPushButton("Поднять коптер")
        move_up_button.clicked.connect(self.move_up)

        move_down_button = QPushButton("Опустить коптер")
        move_down_button.clicked.connect(self.move_down)

        move_left_button = QPushButton("Влево")
        move_left_button.clicked.connect(self.move_left)

        move_right_button = QPushButton("Вправо")
        move_right_button.clicked.connect(self.move_right)

        # Добавляем кнопки на layout
        self.buttons_layout.addWidget(move_up_button)
        self.buttons_layout.addWidget(move_down_button)
        self.buttons_layout.addWidget(move_left_button)
        self.buttons_layout.addWidget(move_right_button)

        # Заполнение оставшегося пространства
        self.buttons_layout.addStretch()

        # Обернуть в виджет и добавить в основной layout
        self.buttons_widget = QWidget()
        self.buttons_widget.setLayout(self.buttons_layout)
        self.main_layout.addWidget(self.buttons_widget, stretch=1)

    def draw_axes(self):
        pen = QPen(Qt.black, 2)

        # Рисуем ось X
        self.scene.addLine(-400, 0, 400, 0, pen)

        # Рисуем стрелку для оси X
        self.scene.addLine(390, -10, 400, 0, pen)  # Верхняя часть стрелки
        self.scene.addLine(390, 10, 400, 0, pen)  # Нижняя часть стрелки

        # Рисуем ось Y
        self.scene.addLine(0, -400, 0, 400, pen)

        # Рисуем стрелку для оси Y
        self.scene.addLine(-10, -390, 0, -400, pen)  # Левая часть стрелки
        self.scene.addLine(10, -390, 0, -400, pen)  # Правая часть стрелки

    def update_drone(self):
        # Удаляем старые элементы
        self.scene.clear()
        self.draw_axes()

        # Рисуем коптер
        drone_radius = 10
        drone = QGraphicsEllipseItem(
            self.drone_x - drone_radius,
            self.drone_y - drone_radius,
            2 * drone_radius,
            2 * drone_radius
        )
        drone.setBrush(QBrush(Qt.blue))
        self.scene.addItem(drone)

        # Обновляем текст с координатами
        coordinates_text = f"({self.drone_x}, {self.drone_y})"
        text_item = QGraphicsTextItem(coordinates_text)
        text_item.setDefaultTextColor(Qt.red)
        text_item.setPos(self.drone_x + 15, self.drone_y - 15)
        self.scene.addItem(text_item)

        # Обновляем метку с координатами
        self.coords_label.setText(f"Координаты коптера: {coordinates_text}")

    def move_up(self):
        self.drone_y -= 10
        self.update_drone()

    def move_down(self):
        self.drone_y += 10
        self.update_drone()

    def move_left(self):
        self.drone_x -= 10
        self.update_drone()

    def move_right(self):
        self.drone_x += 10
        self.update_drone()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DroneControlApp()
    window.show()
    sys.exit(app.exec_())