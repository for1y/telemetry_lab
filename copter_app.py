from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsPolygonItem, \
    QMenu
from PyQt5.QtGui import QPen, QColor, QPixmap, QCursor, QPolygonF, QTransform, QBrush
from PyQt5.QtCore import Qt, QTimer

from copter_class import CopterController #, copter

from interface import Ui_MainWindow



cord_graph = 25
scene_size = 200





class CopterApp(QMainWindow, Ui_MainWindow):
    def __init__(self):

        self.copter_controller = CopterController()

        self.is_setting_route = False
        self.is_setting_zone_mode = False

        self.restricted_zone_points = []
        self.restricted_zones = []
        self.restricted_zone_polygons = []
        # Дополнительные атрибуты
        self.distance_line = None  # Линия расстояния до зоны
        self.distance_text = None  # Текст расстояния

        super().__init__()
        self.setupUi(self)

        # -------------------------------
        # Графическая сцена (QGraphicsScene)
        # -------------------------------
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Установка фильтра событий
        self.graphicsView.viewport().installEventFilter(self)
        self.scene.setSceneRect(-scene_size, -scene_size, scene_size * 2, scene_size * 2)

        # Рисуем коптер и делаем так, чтобы координаты его были в центре
        copter_image = QPixmap('image_folder/copter.png').scaled(25, 25)
        self.pixmap_item = QGraphicsPixmapItem(copter_image)
        x, y = copter_image.width() / 2, copter_image.width() / 2
        self.pixmap_item.setTransformOriginPoint(x, y)
        # self.copter_on_scene = self.scene.addPixmap(copter_image)
        self.scene.addItem(self.pixmap_item)
        self.pixmap_item.setVisible(False)
        self.pixmap_item.setPos(0, 0)

        # Привязываем чекбоксы
        self.checkBox_showCopter.stateChanged.connect(self.on_checkBox_showCopter)
        self.checkBox_showRestrictedZone.stateChanged.connect(self.on_checkBox_showRestrictedZone)
        self.checkBox_showDistance.stateChanged.connect(self.on_checkBox_showDistance)
        # Привязываем кнопки
        self.toolButton_setRestrictedZone.clicked.connect(self.enable_set_zone_mode)
        self.toolButton_setRoute.clicked.connect(self.set_route_to_copter)
        # Настраиваем таймер для обновления положения коптера
        self.timer = QTimer()
        self.timer.timeout.connect(self.draw_copter)
        self.timer.start(3000)  # Обновление каждые 200 мс (5 раз в секунду)

        # self.scene.setSceneRect()
        self.draw_grid(int(self.cords_to_scene(1)), int(self.cords_to_scene(5)))

    def enable_set_zone_mode(self):
        """Включаем режим установки зоны и меняем курсор."""
        self.is_setting_zone_mode = True
        self.graphicsView.setCursor(QCursor(Qt.CrossCursor))

    def eventFilter(self, source, event):
        """Обработка событий мыши."""
        if source is self.graphicsView.viewport() and self.is_setting_zone_mode:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # Добавляем флажок при нажатии левой кнопки
                    print(event.pos())
                    self.add_flag(event.pos())

                elif event.button() == Qt.RightButton:
                    # Завершаем установку зоны при правом клике
                    self.finish_zone()
                    print('right')
            return True
        elif self.is_setting_route:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    scene_pos = self.graphicsView.mapToScene(event.pos())

                    self.is_setting_route = False
                    self.graphicsView.setCursor(QCursor(Qt.ArrowCursor))
                    self.graphicsView.viewport().update()

        return super().eventFilter(source, event)

    def add_flag(self, position):
        """Добавляем флажок на сцену."""
        scene_pos = self.graphicsView.mapToScene(position)
        flag = QGraphicsPixmapItem(
            QPixmap('image_folder/red_flag.png').scaled(self.cords_to_scene(2), self.cords_to_scene(2)))
        flag.setPos(scene_pos.x(), scene_pos.y() - self.cords_to_scene(2))  # Центрируем флажок
        self.scene.addItem(flag)

        # Сохраняем точку
        self.restricted_zone_points.append(scene_pos)

    def finish_zone(self):
        """Завершаем установку зоны и рисуем замкнутый контур."""
        if len(self.restricted_zone_points) < 3:
            print("Недостаточно точек для создания зоны!")
            self.is_setting_zone_mode = False
            self.graphicsView.setCursor(QCursor(Qt.ArrowCursor))
            return  # Завершаем выполнение метода, если недостаточно точек

        # Добавляем текущую зону в список зон
        self.restricted_zones.append(self.restricted_zone_points[:])  # Копируем список
        self.restricted_zone_points.clear()

        # Рисуем полигоны для всех зон
        pen = QPen(QColor(255, 0, 0), 2)  # Красная обводка
        brush = QBrush(QColor(255, 0, 0, 50))  # Полупрозрачная заливка (50 — уровень прозрачности)
        self.restricted_zone_polygons = []  # Обновляем список полигонов

        for zone in self.restricted_zones:
            polygon = QPolygonF(zone)
            polygon_item = QGraphicsPolygonItem(polygon)
            polygon_item.setPen(pen)  # Устанавливаем обводку
            polygon_item.setBrush(brush)  # Устанавливаем заливку
            polygon_item.setVisible(self.checkBox_showRestrictedZone.isChecked())
            self.restricted_zone_polygons.append(polygon_item)
            self.scene.addItem(polygon_item)

        # Отключаем режим установки зоны
        self.is_setting_zone_mode = False
        self.graphicsView.setCursor(QCursor(Qt.ArrowCursor))
        self.graphicsView.viewport().update()

    def contextMenuEvent(self, event):
        """Контекстное меню для редактирования зоны."""
        # Создаем объект QTransform
        transform = QTransform()

        # Получаем элемент под курсором
        clicked_item = self.scene.itemAt(self.graphicsView.mapToScene(event.pos()), transform)
        if isinstance(clicked_item, QGraphicsPixmapItem):  # Если это флажок
            menu = QMenu(self)
            delete_action = menu.addAction("Удалить")
            move_action = menu.addAction("Переместить")
            action = menu.exec_(self.mapToGlobal(event.pos()))

            if action == delete_action:
                self.scene.removeItem(clicked_item)
                # Удаляем точку из списка
                self.restricted_zone_points = [
                    point for point in self.restricted_zone_points
                    if not self.is_close(clicked_item.pos(), point)
                ]
                self.update_zone()
            elif action == move_action:
                print("Перемещение флажка: Пока не реализовано")

    def update_zone(self):
        """Обновляем опасную зону после изменения флажков."""
        if self.restricted_zone_polygon:
            self.scene.removeItem(self.restricted_zone_polygon)
        if len(self.restricted_zone_points) > 2:
            polygon = QPolygonF(self.restricted_zone_points)
            self.restricted_zone_polygon = QGraphicsPolygonItem(polygon)
            pen = QPen(QColor(255, 0, 0), 2)  # Красная обводка
            self.restricted_zone_polygon.setPen(pen)
            self.scene.addItem(self.restricted_zone_polygon)

    @staticmethod
    def is_close(pos1, pos2, threshold=5):
        """Проверяем, находятся ли две точки рядом."""
        return (abs(pos1.x() - pos2.x()) <= threshold and
                abs(pos1.y() - pos2.y()) <= threshold)

    def on_checkBox_showCopter(self, state):
        if state == Qt.Checked:
            self.pixmap_item.setVisible(True)

        elif state == Qt.Unchecked:
            self.pixmap_item.setVisible(False)

    def on_checkBox_showRestrictedZone(self, state):
        """Обрабатывает состояние чекбокса 'Show Restricted Zone'."""
        if state == Qt.Checked:
            # Отображаем все полигоны запретных зон
            for polygon in self.restricted_zone_polygons:
                polygon.setVisible(True)
        else:
            # Скрываем все полигоны запретных зон
            for polygon in self.restricted_zone_polygons:
                polygon.setVisible(False)

    def on_checkBox_showDistance(self, state):
        """Обрабатывает изменение состояния чекбокса 'Show Distance to Nearest Restricted Zone'."""
        if state == Qt.Checked:
            # Если чекбокс включен, обновляем визуализацию расстояния
            self.update_distance_visualization()
        else:
            # Если чекбокс выключен, удаляем линию и текст
            if self.distance_line:
                self.scene.removeItem(self.distance_line)
                self.distance_line = None
            if self.distance_text:
                self.scene.removeItem(self.distance_text)
                self.distance_text = None

    def calculate_distance_to_zone(self, copter_coords):
        """Вычисляет расстояние от коптера до ближайшей зоны."""
        min_distance = float('inf')
        nearest_point = None

        # Перебираем все объекты QGraphicsPolygonItem
        for polygon_item in self.restricted_zone_polygons:
            polygon = polygon_item.polygon()  # Получаем QPolygonF из объекта
            for i in range(polygon.count()):
                point = polygon.at(i)  # Получаем точку из полигона
                distance = ((copter_coords[0] - point.x()) ** 2 + (copter_coords[1] - point.y()) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = point

        return self.scene_to_cords(min_distance), nearest_point

    def update_distance_visualization(self):
        """Обновляет отображение линии и текста расстояния до ближайшей зоны."""
        if not self.checkBox_showDistance.isChecked():
            # Удаляем линию и текст, если чекбокс не активен
            if self.distance_line:
                self.scene.removeItem(self.distance_line)
                self.distance_line = None
            if self.distance_text:
                self.scene.removeItem(self.distance_text)
                self.distance_text = None
            return

        # Получаем координаты коптера
        copter_coords = self.copter_controller.cords
        copter_pos = [self.cords_to_scene(copter_coords[0]), self.cords_to_scene(copter_coords[1])]

        # Вычисляем расстояние до ближайшей зоны
        distance, nearest_point = self.calculate_distance_to_zone(copter_pos)

        if nearest_point:
            # Обновляем или создаем линию
            if self.distance_line:
                self.scene.removeItem(self.distance_line)
            self.distance_line = self.scene.addLine(copter_pos[0], copter_pos[1],
                                                    nearest_point.x(), nearest_point.y(),
                                                    QPen(QColor(255, 0, 0), 2))

            # Обновляем или создаем текст расстояния
            if self.distance_text:
                self.scene.removeItem(self.distance_text)
            self.distance_text = QGraphicsTextItem(f"{distance:.2f} m")
            self.distance_text.setDefaultTextColor(QColor(255, 0, 0))
            self.distance_text.setPos((copter_pos[0] + nearest_point.x()) / 2,
                                      (copter_pos[1] + nearest_point.y()) / 2)
            self.scene.addItem(self.distance_text)

    def set_route_to_copter(self):
        self.is_setting_route = True
        self.graphicsView.setCursor(QCursor(Qt.CrossCursor))

    def cords_to_scene(self, cord):
        return int(cord * scene_size / float(cord_graph))

    def scene_to_cords(self, scene_cord):
        return int(scene_cord * float(cord_graph) / scene_size)

    def draw_copter(self):
        cords = self.copter_controller._get_cords()
        # self.copter_on_scene.setPos(cords[0], cords[1])
        # coords_text = f"(x:{cords[0]:.3f}, y:{cords[1]:.3f}, x:{cords[2]:.3f})"
        self.pixmap_item.setPos(self.cords_to_scene(cords[0]), self.cords_to_scene(cords[1]))
#         print(coords_text)
        # self.pixmap_item.setPos(0, 0)
        self.update_distance_visualization()

    def draw_grid(self, spacing=25, major_spacing=100):
        """Рисует координатную сетку с подписями осей, адаптируясь к размеру сцены."""
        # Получаем размеры текущей сцены
        scene_rect = self.scene.sceneRect()
        x_min, x_max = int(scene_rect.left()), int(scene_rect.right())
        y_min, y_max = int(scene_rect.top()), int(scene_rect.bottom())

        # Определяем стили линий
        pen_minor = QPen(QColor(200, 200, 200), 1)  # Тонкие линии
        pen_major = QPen(QColor(150, 150, 150), 2)  # Толстые линии
        pen_axes = QPen(QColor(0, 0, 0), 3)  # Оси X и Y

        # Рисуем вертикальные линии
        for x in range(x_min, x_max + 1, spacing):
            if x % major_spacing == 0 and x != 0:
                self.scene.addLine(x, y_min, x, y_max, pen_major)
            elif x != 0:
                self.scene.addLine(x, y_min, x, y_max, pen_minor)

        # Рисуем горизонтальные линии
        for y in range(y_min, y_max + 1, spacing):
            if y % major_spacing == 0 and y != 0:
                self.scene.addLine(x_min, y, x_max, y, pen_major)
            elif y != 0:
                self.scene.addLine(x_min, y, x_max, y, pen_minor)

        # Рисуем оси X и Y
        self.scene.addLine(x_min, 0, x_max, 0, pen_axes)  # Ось X
        self.scene.addLine(0, y_min, 0, y_max, pen_axes)  # Ось Y

        # Добавляем метки на осях
        for x in range(x_min, x_max + 1, major_spacing):
            if x != 0:
                text = QGraphicsTextItem(str(int(self.scene_to_cords(x))))
                text.setDefaultTextColor(Qt.black)
                text.setPos(x - 15, -15)  # Коррекция позиции текста
                self.scene.addItem(text)

        for y in range(y_min, y_max + 1, major_spacing):
            if y != 0:
                text = QGraphicsTextItem(str(int(self.scene_to_cords(y))))
                text.setDefaultTextColor(Qt.black)
                text.setPos(5, y - 10)  # Коррекция позиции текста
                self.scene.addItem(text)

        # Указываем направление осей
        arrow_size = 10
        # Стрелка вправо
        self.scene.addLine(x_max, 0, x_max - arrow_size, arrow_size / 2, pen_axes)  # Верхняя линия стрелки
        self.scene.addLine(x_max, 0, x_max - arrow_size, -arrow_size / 2, pen_axes)  # Нижняя линия стрелки

        # Стрелка вверх
        self.scene.addLine(0, y_max, -arrow_size / 2, y_max - arrow_size, pen_axes)  # Левая линия стрелки
        self.scene.addLine(0, y_max, arrow_size / 2, y_max - arrow_size, pen_axes)  # Правая линия стрелки

# if __name__ == "__main__":
#     app = QApplication([])
#     window = DroneApp()
#     window.show()
#     app.exec_()
