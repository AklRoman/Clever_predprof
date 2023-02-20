import sys
import serial
import cv2

from picamera import PiCamera

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit
from PyQt5.QtGui import QIcon, QPixmap

from PyQt5.QtCore import pyqtSignal

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.flush()

camera = PiCamera()


def find_contours_of_cards(image):
    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    T, thresh_img = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)
    (cnts, _) = cv2.findContours(thresh_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.imshow('Image', thresh_img)
    cv2.waitKey(0)
    return cnts


def count_number_of_dices(cnts, image):
    count = 0
    for i in range(0, len(cnts)):
        x, y, w, h = cv2.boundingRect(cnts[i])
        if 100 > w > 20 and 100 > h > 20:
            img_crop = image[y:y + h, x:x + w]
            cv2.imshow('Image', img_crop)
            cv2.waitKey(0)
            print(w, h)
            count += 1
    return count


class cQLineEdit(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, widget):
        super().__init__(widget)

    def mousePressEvent(self, event):
        self.clicked.emit()


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('start_page.ui', self)
        self.setMouseTracking(True)
        self.group = 'start_group'
        self.inf_running = False
        self.count_running = False

        self.edit = cQLineEdit(self.start_group)
        self.edit.setGeometry(820, 200, 300, 100)
        self.edit.setText('1')
        self.edit.clicked.connect(self.key)

        self.result_group.hide()
        self.res_home.clicked.connect(lambda: self.change_page('start_group'))

        self.history_group.hide()
        self.hist_home.clicked.connect(lambda: self.change_page('start_group'))

        self.settings_group.hide()
        self.s_home.clicked.connect(lambda: self.change_page('start_group'))
        self.right_btn.clicked.connect(lambda: self.time())
        self.left_btn.clicked.connect(lambda: self.time())
        self.return_test.clicked.connect(lambda: self.check())
        self.baraban_test.clicked.connect(lambda: self.check())
        self.camera_test.clicked.connect(lambda: self.check())

        self.start_btn.clicked.connect(lambda: self.run_count())
        self.inf_btn.clicked.connect(lambda: self.run_inf())
        self.history.clicked.connect(lambda: self.change_page('history_group'))
        self.settings.clicked.connect(lambda: self.change_page('settings_group'))

        for i in range(10):
            name = 'b' + str(i)
            getattr(self, name).clicked.connect(lambda: self.print())
            getattr(self, name).hide()
        self.del_n.clicked.connect(lambda: self.delete())
        self.del_n.hide()

    def check(self):
        if self.sender().objectName() == 'return_test':
            ser.write(b'R')
        elif self.sender().objectName() == 'camera_test':
            camera.capture('/home/pi/Desktop/image.jpg')
            main_image = cv2.imread('/home/pi/Desktop/image.jpg')
            gray_main_image = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
            contours = find_contours_of_cards(gray_main_image)
            SCOORE = count_number_of_dices(contours, gray_main_image)
            self.change_page('result_group')
            self.photo_label.setPixmap(QPixmap('/home/pi/Desktop/image.jpg'))
            self.res_label.setText(f'У вас выпало {SCOORE}!')
        else:
            timeout = int(self.time_run.text())
            ser.write(b'B')
            ser.write(str(timeout).encode('utf-8'))

    def change_page(self, name):
        getattr(self, self.group).hide()
        getattr(self, name).show()
        self.group = name

    def time(self):
        if self.sender().objectName() == 'left_btn':
            if int(self.time_run.text()) > 10:
                self.time_run.setText(str(int(self.time_run.text()) - 1))
        if self.sender().objectName() == 'right_btn':
            if int(self.time_run.text()) < 30:
                self.time_run.setText(str(int(self.time_run.text()) + 1))

    def key(self):
        self.edit.setText('')
        for i in range(10):
            name = 'b' + str(i)
            getattr(self, name).show()
        self.del_n.show()

    def closing(self):
        for i in range(10):
            name = 'b' + str(i)
            getattr(self, name).hide()
        self.del_n.hide()

    def print(self):
        self.edit.setText(self.edit.text() + self.sender().text())

    def delete(self):
        self.edit.setText(self.edit.text()[:-1])

    def run_count(self):
        self.closing()
        timeout = int(self.time_run.text())
        try:
            n = int(self.edit.text())
        except Exception:
            n = 1
        ser.write(b'C')
        ser.write(str(n).encode('utf-8'))
        ser.write(str(timeout).encode('utf-8'))
        i = 0
        while True:
            number = ser.read()
            if number != b'':
                if int.from_bytes(number, byteorder='big') == 18:
                    camera.capture('/home/pi/Desktop/image.jpg')
                    main_image = cv2.imread('/home/pi/Desktop/image.jpg')
                    gray_main_image = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
                    contours = find_contours_of_cards(gray_main_image)
                    SCOORE = count_number_of_dices(contours, gray_main_image)
                    self.change_page('result_group')
                    self.photo_label.setPixmap(QPixmap('/home/pi/Desktop/image.jpg'))
                    self.res_label.setText(f'У вас выпало {SCOORE}!')
                    i += 1
            if i == n:
                break

    def run_inf(self):
        self.closing()
        timeout = int(self.time_run.text())
        if not self.count_running:
            if not self.inf_running:
                self.inf_btn.setIcon(QIcon(r"C:\Users\koval_2u358u1\Downloads\free-icon-cross-sign-57165.png"))
                self.inf_running = True
                ser.write(b'I')
                ser.write(str(timeout).encode('utf-8'))
                while True:
                    number = ser.read()
                    if number != b'':
                        if int.from_bytes(number, byteorder='big') == 18:
                            camera.capture('/home/pi/Desktop/image.jpg')
                            main_image = cv2.imread('/home/pi/Desktop/image.jpg')
                            gray_main_image = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
                            contours = find_contours_of_cards(gray_main_image)
                            SCOORE = count_number_of_dices(contours, gray_main_image)
                            self.change_page('result_group')
                            self.photo_label.setPixmap(QPixmap('/home/pi/Desktop/image.jpg'))
                            self.res_label.setText(f'У вас выпало {SCOORE}!')
                        if int.from_bytes(number, byteorder='big') == 17:
                            break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
