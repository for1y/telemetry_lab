
import sys

from PyQt5.QtWidgets import QApplication

from copter_app import CopterApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CopterApp()
    window.show()
    app.exec_()

    # copter.show_telemetry(5)
    # print(copter.get_cords())
    # copter.set_target_position([10.0, 10.0, 10.0])
    # copter.block_swiching(True)
    # copter.block_swiching(False)
    # copter.show_telemetry()
