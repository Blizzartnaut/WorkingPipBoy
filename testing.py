import sys
from PyQt5.QtWidgets import QApplication, QWidget

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.resize(450,250)
    window.setWindowTitle('Hello World')
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()