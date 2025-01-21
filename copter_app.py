from math import atan2, degrees

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPen, QColor, QPixmap, QCursor, QPolygonF, QTransform, QBrush
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsPolygonItem, \
    QMenu, QMessageBox, QInputDialog

from copter_class import CopterController
from interface import Ui_MainWindow

from my_logger import logger as glogger

cord_graph = 25
scene_size = 200
danger_zone_threshold = 10


class CopterApp(QMainWindow, Ui_MainWindow):
    copter_controller = CopterController()

    def __init__(self):

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
        self.graphicsView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Установка фильтра событий
        self.graphicsView.viewport().installEventFilter(self)
        self.scene.setSceneRect(-scene_size, -scene_size, scene_size * 2, scene_size * 2)

        # Рисуем коптер и делаем так, чтобы координаты его были в центре
        copter_image = QPixmap('image_folder/copter.png').scaled(25, 25)
        self.pixmap_item = QGraphicsPixmapItem(copter_image)
        x, y = int(copter_image.width() / 2), int(copter_image.width() / 2)
        self.pixmap_item.setTransformOriginPoint(x, y)
        # self.copter_on_scene = self.scene.addPixmap(copter_image)
        self.scene.addItem(self.pixmap_item)
        self.pixmap_item.setVisible(True)
        self.pixmap_item.setPos(0, 0)

        # Привязываем чекбоксы
        self.checkBox_showCopter.stateChanged.connect(self.on_checkBox_showCopter)
        self.checkBox_showRestrictedZone.stateChanged.connect(self.on_checkBox_showRestrictedZone)
        self.checkBox_showDistance.stateChanged.connect(self.on_checkBox_showDistance)

        self.checkBox_Warning.stateChanged.connect(self.on_checkBox_Warning)

        self.checkBox_stopInZone.stateChanged.connect(self.on_checkBox_stopInZone)

        # Привязываем кнопки
        self.toolButton_setRestrictedZone.clicked.connect(self.enable_set_zone_mode)
        self.toolButton_setRoute.clicked.connect(self.set_route_to_copter)

        # Настраиваем таймер для обновления положения коптера
        self.timer = QTimer()
        self.timer.timeout.connect(self.draw_copter)
        self.timer.start(2000)  # Обновление каждые 200 мс (5 раз в секунду)

        # Настраиваем таймер для ожидания попадания в запретную зону
        self.warning_timer = QTimer()
        self.warning_timer.timeout.connect(self.follow_to_zone)

        self.stopInZone_timer = QTimer()
        self.stopInZone_timer.timeout.connect(self.stopInZone)

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
                    x, y = self.scene_to_cords(scene_pos.x()), self.scene_to_cords(scene_pos.y())
                    z = self.copter_controller.cords[2]
                    self.copter_controller.set_target_position([x, y, z])
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
            glogger.debug('Включена видимость коптера')

        elif state == Qt.Unchecked:
            self.pixmap_item.setVisible(False)
            glogger.debug('Отключена видимость коптера')

    def on_checkBox_showRestrictedZone(self, state):
        """Обрабатывает состояние чекбокса 'Show Restricted Zone'."""
        if state == Qt.Checked:
            # Отображаем все полигоны запретных зон
            for polygon in self.restricted_zone_polygons:
                polygon.setVisible(True)
            glogger.debug('Включена видимость запретных зон')
        else:
            # Скрываем все полигоны запретных зон
            for polygon in self.restricted_zone_polygons:
                polygon.setVisible(False)
            glogger.debug('Отключена видимость запретных зон')

    def on_checkBox_showDistance(self, state):
        """Обрабатывает изменение состояния чекбокса 'Show Distance to Nearest Restricted Zone'."""
        if state == Qt.Checked:
            glogger.debug('Включен расчет дистанции до запретной зоны')
            # Если чекбокс включен, обновляем визуализацию расстояния
            self.update_distance_visualization()
        else:
            glogger.debug('Выключен расчет дистанции до запретной зоны')
            # Если чекбокс выключен, удаляем линию и текст
            if self.distance_line:
                self.scene.removeItem(self.distance_line)
                self.distance_line = None
            if self.distance_text:
                self.scene.removeItem(self.distance_text)
                self.distance_text = None

    def on_checkBox_Warning(self, state):
        if state == Qt.Checked:
            glogger.debug('Включено педупреждение при приближении к запреной зоне')
            self.warning_timer.start(2000)
        else:
            glogger.debug('Отключено педупреждение при приближении к запреной зоне')
            self.warning_timer.stop()

    def on_checkBox_stopInZone(self, state):
        if state == Qt.Checked:
            glogger.debug('Enable stop when entering a restricted area')
            self.stopInZone_timer.start(2000)
        else:
            glogger.debug('Disabled stop when entering a restricted area')
            self.stopInZone_timer.stop()

    def stopInZone(self):
        """Проверяет, находится ли коптер внутри запретной зоны, и запрашивает новую высоту."""
        copter_coords = self.copter_controller.cords  # Получаем текущие координаты коптера
        current_x, current_y, current_z = copter_coords

        for polygon_item in self.restricted_zone_polygons:
            polygon = polygon_item.polygon()  # Получаем QPolygonF из объекта
            if polygon.containsPoint(QPointF(current_x, current_y), Qt.OddEvenFill):
                # Коптер находится в запретной зоне
                self.warning_and_set_height(current_z)
                break

    def warning_and_set_height(self, current_z):
        """Выводит предупреждающее окно и запрашивает новую высоту."""
        # Предупреждающее окно
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Предупреждение")
        msg.setText("Коптер находится в запретной зоне!")
        msg.setInformativeText(f"Текущая высота: {current_z:.2f} м. Пожалуйста, задайте новую высоту.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

        # Запрос новой высоты
        new_height, ok = QInputDialog.getDouble(
            self,
            "Задать новую высоту",
            "Введите новую высоту (м):",
            decimals=2,
            min=0.0,  # Минимальная высота
            max=1000.0  # Максимальная высота
        )
        if ok:
            # Применяем новую высоту
            self.copter_controller.set_target_position([current_z, new_height, current_z])
            print(f"Установлена новая высота: {new_height:.2f} м")


    def follow_to_zone(self):
        """Проверяет расстояние до ближайшей зоны и выводит предупреждение, если нужно."""
        # Получаем координаты коптера
        copter_coords = self.copter_controller.cords

        # Вычисляем расстояние до ближайшей зоны

        if self.nearest_point and self.distance_to_danger_zone < danger_zone_threshold:
            # Рассчитываем направление в градусах (от коптера до ближайшей точки)
            delta_x = self.nearest_point[0] - copter_coords[0]
            delta_y = self.nearest_point[1] - copter_coords[1]
            angle = degrees(atan2(delta_y, delta_x))  # Угол в градусах
            if angle < 0:
                angle += 360  # Приводим угол к диапазону 0-360

            # Создаем всплывающее окно
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Предупреждение")
            msg.setText("Коптер приближается к запретной зоне!")
            msg.setInformativeText(f"Расстояние: {self.distance_to_danger_zone:.3f} м\nНаправление: {angle:.2f}°")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def calculate_distance_to_zone(self, copter_coords) -> float:
        """Вычисляет минимальное расстояние от коптера до ближайшей зоны."""
        min_distance = float('inf')
        nearest_point = None

        # Перебираем все объекты QGraphicsPolygonItem
        if self.restricted_zone_polygons:
            for polygon_item in self.restricted_zone_polygons:
                polygon = polygon_item.polygon()  # Получаем QPolygonF из объекта

                # Перебираем стороны полигона
                for i in range(polygon.count()):
                    p1 = polygon.at(i)
                    p2 = polygon.at((i + 1) % polygon.count())  # Следующая вершина (замкнутый контур)

                    # Вычисляем расстояние от точки до текущего отрезка
                    distance, closest_point = self._point_to_segment_distance(copter_coords, (p1.x(), p1.y()),
                                                                              (p2.x(), p2.y()))

                    # print(distance, ' main')
                    if distance < min_distance:
                        min_distance = distance
                        nearest_point = closest_point
        return min_distance, nearest_point

    def _point_to_segment_distance(self, point, segment_start, segment_end):
        """Вычисляет расстояние от точки до отрезка и ближайшую точку на отрезке."""
        px, py = point
        x1, y1 = segment_start
        x2, y2 = segment_end

        # Вектор отрезка
        dx, dy = x2 - x1, y2 - y1

        # Длина отрезка в квадрате
        segment_length_squared = dx ** 2 + dy ** 2
        if segment_length_squared == 0:  # Отрезок вырождается в точку
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5, (x1, y1)

        # Проекция точки на прямую, содержащую отрезок, с нормализацией
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / segment_length_squared))

        # Координаты ближайшей точки на отрезке
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Расстояние от точки до ближайшей точки на отрезке
        distance: float = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
        distance = distance * cord_graph / scene_size
        # print(distance, ' +')
        return (distance), (closest_x, closest_y)

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
        self.distance_to_danger_zone, nearest_point = self.calculate_distance_to_zone(copter_pos)

        if nearest_point:
            self.nearest_point = nearest_point
            # Обновляем или создаем линию
            if self.distance_line:
                self.scene.removeItem(self.distance_line)
            self.distance_line = self.scene.addLine(copter_pos[0], copter_pos[1],
                                                    self.nearest_point[0], self.nearest_point[1],
                                                    QPen(QColor(255, 0, 0), 2))

            # Обновляем или создаем текст расстояния
            if self.distance_text:
                self.scene.removeItem(self.distance_text)
            self.distance_text = QGraphicsTextItem(f"{self.distance_to_danger_zone:.2f} m")
            self.distance_text.setDefaultTextColor(QColor(255, 0, 0))
            self.distance_text.setPos((copter_pos[0] + self.nearest_point[0]) / 2,
                                      (copter_pos[1] + self.nearest_point[1]) / 2)
            self.scene.addItem(self.distance_text)

    def set_route_to_copter(self):
        self.is_setting_route = True
        self.graphicsView.setCursor(QCursor(Qt.CrossCursor))

    def cords_to_scene(self, cord) -> int:
        return int(cord * scene_size / float(cord_graph))

    def scene_to_cords(self, scene_cord) -> float:
        if scene_cord != float('inf'):
            return int(scene_cord * float(cord_graph) / scene_size)
        return float('inf')

    def draw_copter(self):
        if self.checkBox_showCopter.isChecked():
            print('draw')
        cords = self.copter_controller.cords

        self.pixmap_item.setPos(self.cords_to_scene(cords[0]), self.cords_to_scene(cords[1]))

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
