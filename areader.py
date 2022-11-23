import configparser
import json
import os
from pathlib import Path
from os import path
from shutil import copyfile
import shutil
import sys
import tempfile
from platformdirs import user_config_dir
import regex
from PySide6.QtCore import QUrl, QObject, Slot
from PySide6.QtGui import QIcon, QCursor, QPixmap, QFontDatabase, QFont, QAction
from PySide6.QtWidgets import (QApplication, QLineEdit,
                               QMainWindow, QPushButton, QToolBar)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog

from database import Database

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()

# TODO: Maybe show font mapping dialog for non-mapped fonts?


class MainWindow(QMainWindow):

    def load_node(self, node, line=0, retrace=True):
        self.webEngineView.load(QUrl('file://' + temp_dir + '/' + self.current_database.get_property('database') + '/' + node.get_property('name') + '.html'))
        if retrace:
            self.history.append(self.current_node)

        self.update_buttons(node)

        self.current_node = node

        return True

    def load_node_by_path(self, node_path, line=0):
        path_chunks = node_path.split('/')
        if len(path_chunks) == 1:
            # Simple internal link
            node = self.current_database.find_node_by_path(node_path)

            if node:
                return self.load_node(node, line)
        else:
            # External link

            # Check if file exists (last chunk is main node, so ignore)
            file = self.base_dir + '/' + '/'.join(path_chunks[:-1])
            if path.isfile(file):
                # if path_chunks[-2].split(".")[-1] == "ilbm":
                #     print("ilbm")
                #     res = subprocess.check_output(["/usr/bin/ilbmtoppm", file, ">", "/tmp/test.ppm"], shell=True)
                # else:
                # Load database
                database = Database()
                if database.create_from_file(file, temp_dir):
                    self.databases.append(database)
                    self.current_database = self.databases[-1]
                    return self.load_node(self.current_database.find_node_by_path(path_chunks[-1]), line)
                else:
                    return False

    def __init__(self, filename: str = '') -> None:
        super().__init__()

        self.setWindowTitle("AReader")

        fileMenu = self.menuBar().addMenu("&File")
        loadAction = QAction("Load…", self, shortcut="Ctrl+L", triggered=self.load_file_clicked)
        fileMenu.addAction(loadAction)

        # self.window.load_file()
        self.resize(750, 600)

        app.setOverrideCursor(QCursor(QPixmap('cursor_select.cur'), 0, 0))

        self.databases = []

        self.webEngineView = QWebEngineView()
        # self.setCentralWidget(self.webEngineView)

        self.contents_btn = QPushButton("Contents")
        self.index_btn = QPushButton("Index")
        self.help_btn = QPushButton('Help')
        self.retrace_btn = QPushButton('Retrace')
        self.browse_prev_btn = QPushButton('Browse <')
        self.browse_next_btn = QPushButton('Browse >')

        self.contents_btn.setFixedSize(84, 22)
        self.index_btn.setFixedSize(84, 22)
        self.help_btn.setFixedSize(84, 22)
        self.retrace_btn.setFixedSize(84, 22)
        self.browse_prev_btn.setFixedSize(84, 22)
        self.browse_next_btn.setFixedSize(84, 22)

        self.contents_btn.clicked.connect(self.on_click_contents_btn)
        self.index_btn.clicked.connect(self.on_click_index_btn)
        self.help_btn.clicked.connect(self.on_click_help_btn)
        self.retrace_btn.clicked.connect(self.on_click_retrace_btn)
        self.browse_prev_btn.clicked.connect(self.on_click_browse_prev_btn)
        self.browse_next_btn.clicked.connect(self.on_click_browse_next_btn)

        hbox = QHBoxLayout(self)
        hbox.setSpacing(2)
        hbox.setContentsMargins(2, 2, 2, 2)
        hbox.addWidget(self.contents_btn)
        hbox.addWidget(self.index_btn)
        hbox.addWidget(self.help_btn)
        hbox.addWidget(self.retrace_btn)
        hbox.addWidget(self.browse_prev_btn)
        hbox.addWidget(self.browse_next_btn)
        hbox.addStretch()

        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(hbox)
        vbox.addWidget(self.webEngineView)

        widget = QWidget()
        widget.setLayout(vbox)
        widget.setStyleSheet("background-color: rgb(170, 170, 170);")

        self.setCentralWidget(widget)

        self.appname = "AReader"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()

        self.load_config()

        # self.load_file()

        channel = QWebChannel(self.webEngineView)
        self.webEngineView.page().setWebChannel(channel)

        self.helper_bridge = Bridge()
        channel.registerObject("bridge", self.helper_bridge)

        self.webEngineView.loadFinished.connect(loadFinished)

        if filename:
            self.load_file(filename)

    def load_config(self) -> None:
        self.config["window"] = {}
        self.config["files"] = {}

        if self.config.read(user_config_dir(self.appname) + '/config.ini'):
            self.resize(int(self.config["window"]["width"]),
                        int(self.config["window"]["height"]))

    def save_config(self) -> None:
        self.config["window"]["width"] = str(self.geometry().width())
        self.config["window"]["height"] = str(self.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        with open(user_config_dir(self.appname) + "/config.ini", "w") as config_file:
            self.config.write(config_file)

    def load_file(self, filename: str) -> None:
        self.config["files"]["last_open_path"] = os.path.dirname(os.path.abspath(filename))

        self.databases.append(Database())
        self.current_database = self.databases[-1]
        self.current_database.create_from_file(filename, temp_dir)

        self.base_dir = filename[:filename.rfind('/')]

        self.current_node = self.current_database.nodes[0]

        # Copy some needed files (fonts, cursors, beep sound, etc)

        copyfile('topaz_a1200_v1.0-webfont.woff2',
                 temp_dir + '/topaz_a1200_v1.0-webfont.woff2')
        copyfile('topaz_a1200_v1.0-webfont.woff',
                 temp_dir + '/topaz_a1200_v1.0-webfont.woff')
        copyfile('beep.mp3',
                 temp_dir + '/beep.mp3')
        copyfile('style.css',
                 temp_dir + '/style.css')
        copyfile('functions.js',
                 temp_dir + '/functions.js')

        QFontDatabase.addApplicationFont('Topaz_a1200_v1.0.ttf')

        button_style = "QPushButton:pressed { border-top: 2px solid black; \
                border-right: 2px solid white; \
                border-bottom: 2px solid white; \
                border-left: 2px solid black; } \
                QPushButton { font-family: 'Topaz a600a1200a400'; \
                font-size: 16px; \
                background-color: rgb(170, 170, 170); \
                border-top: 2px solid white; \
                border-right: 2px solid black; \
                border-bottom: 2px solid black; \
                border-left: 2px solid white; } \
                QPushButton:disabled { color: black; \
                    background-color: rgb(100, 100, 100) }; "

        self.contents_btn.setStyleSheet(button_style)
        self.index_btn.setStyleSheet(button_style)
        self.help_btn.setStyleSheet(button_style)
        self.retrace_btn.setStyleSheet(button_style)
        self.browse_prev_btn.setStyleSheet(button_style)
        self.browse_next_btn.setStyleSheet(button_style)

        # self.webEngineView.setStyleSheet(
        # "QScrollBar { border: 5px solid red; }")

        self.history = []

        self.load_node(node=self.current_database.nodes[0], retrace=False)

        if filename:
            self.databases.append(Database())
            self.current_database = self.databases[-1]
            self.current_database.create_from_file(filename, temp_dir)

            self.base_dir = filename[:filename.rfind('/')]

        self.current_node = self.current_database.nodes[0]

        # Copy some needed files (fonts, cursors, beep sound)

        copyfile('topaz_a1200_v1.0-webfont.woff2', temp_dir + '/topaz_a1200_v1.0-webfont.woff2')
        copyfile('topaz_a1200_v1.0-webfont.woff', temp_dir + '/topaz_a1200_v1.0-webfont.woff')
        copyfile('cursor_select.cur', temp_dir + '/cursor_select.cur')
        copyfile('cursor_link.cur', temp_dir + '/cursor_link.cur')
        copyfile('beep.mp3', temp_dir + '/beep.mp3')

        self.history = []

        self.load_node(node=self.current_database.nodes[0], retrace=False)

    def load_file_clicked(self) -> None:
        if self.config.has_option("files", "last_open_path"):
            last_open_path = self.config["files"]["last_open_path"]

            filename = QFileDialog.getOpenFileName(
                self, "Select an AmigaGuide file…", filter="AmigaGuide files (*.guide)", dir=last_open_path)[0]
        else:
            filename = QFileDialog.getOpenFileName(
                self, "Select an AmigaGuide file…", filter="AmigaGuide files (*.guide)")[0]

        if filename:
            self.load_file(filename)

    def closeEvent(self, event):
        temp.close()
        shutil.rmtree(temp_dir)
        self.save_config()

    def on_click_contents_btn(self):
        self.load_node(node=self.current_database.nodes[0], retrace=True)

    def on_click_index_btn(self):
        if 'index' in self.current_node.properties:
            self.load_node_by_path(self.current_node.get_property('index'))

        if 'index' in self.current_database.properties:
            self.load_node_by_path(self.current_database.get_property('index'))

    def on_click_help_btn(self):
        if 'help' in self.current_node.properties:
            self.load_node_by_path(self.current_node.properties['help'])

        if 'help' in self.current_database.properties:
            self.load_node_by_path(self.current_database.properties['help'])

    def on_click_retrace_btn(self):
        if len(self.history) > 0:
            self.load_node(self.history.pop(), retrace=False)

    def on_click_browse_prev_btn(self):
        if 'prev' in self.current_node.properties:
            self.load_node_by_path(self.current_node.properties['prev'])

    def on_click_browse_next_btn(self):
        if 'next' in self.current_node.properties:
            self.load_node_by_path(self.current_node.properties['next'])

    def update_buttons(self, node):
        self.browse_next_btn.setEnabled('next' in node.properties)
        self.browse_prev_btn.setEnabled('prev' in node.properties)
        self.contents_btn.setEnabled('toc' in node.properties)

        if 'toc' in node.properties:
            enabled = True
        else:
            if 'help' in self.current_database.properties:
                enabled = True
            else:
                enabled = False

            self.help_btn.setEnabled(enabled)

        if 'index' in node.properties:
            enabled = True
        else:
            if 'index' in self.current_database.properties:
                enabled = True
            else:
                enabled = False

        self.index_btn.setEnabled(enabled)

        if len(self.history) > 0:
            enabled = True
        else:
            enabled = False

        self.retrace_btn.setEnabled(enabled)


def loadFinished():
    # Apply database page settings
    mainWin.setWindowTitle(mainWin.current_node.get_property('title'))

    style = 'font-family: \"' + mainWin.current_database.get_property('font') + '\"; font-size: ' + str(mainWin.current_database.get_property('font-size')) + 'px;'

    if mainWin.current_database.get_property('wordwrap'):
        style += 'white-space: pre-wrap;'
    else:
        style += 'white-space: pre;'

    mainWin.webEngineView.page().runJavaScript(
        "setStyle('body', '" + style + "');")
    mainWin.webEngineView.page().runJavaScript(
        "setStyle('button', '" + style + "');")


# Bridge for communication between Python and JavaScript of the page

class Bridge(QObject):
    @Slot(str)
    def button_clicked(self, data):
        json_data = json.loads(data)
        if "path" and "line" in json_data:
            if not mainWin.load_node_by_path(json_data["path"], json_data["line"]):
                print('Unable to open node: ' + json_data["path"])


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) == 2:
        mainWin = MainWindow(sys.argv[1])
    else:
        mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())

# TODO: Save last opened documents
# TODO: Save last opened path
# TODO: Maybe introduce subfolders with unique ids?
# TODO: Implement tabstops
# TODO: Tabs in documents not working correctly (arcdir.dopus5.guide)
# TODO: Implement document width
# TODO: Process line parameter for links
# TODO: Find out how index and content actually work
# TODO: Problems with retrace for external documents
# TODO: Database info window
# TODO: Highlight (last) selected links (manually color links? ("visited selector matches all element whose _href link already visited_."))
# TODO: Problems when loading the same document again
