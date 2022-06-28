import configparser
import json
import os
from pathlib import Path
from os import error, replace, path
from shutil import copyfile
import shutil
import sys
import tempfile
from tokenize import String
from platformdirs import user_config_dir
import regex
from PySide6.QtCore import QUrl, QObject, Slot
from PySide6.QtGui import QIcon, QCursor, QPixmap, QFontDatabase, QFont, QAction
from PySide6.QtWidgets import (QApplication, QLineEdit,
                               QMainWindow, QPushButton, QToolBar)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog

from lexer import *

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()

# TODO: Maybe show font mapping dialog for non-mapped fonts?

fonts = {
    "helvetica.font": "Helvetica",
    "courier.font": "Courier New",
    "times.font": "Times New Roman",
    "topaz": "Topaz"
}


class Node:
    def __init__(self, database):
        self.database = database
        self.name = ""
        self.text = ""
        self.next = ""
        self.embed = ""
        self.font = ""
        self.font_size = 0
        self.help = ""
        self.index = ""
        self.keywords = []
        self.macro = ""
        self.onclose = ""
        self.onopen = ""
        self.prev = ""
        self.proportional = False
        self.smartwrap = False
        self.tab = []
        self.title = ""
        self.toc = ""
        self.wordwrap = False

    def write_as_html(self, path):
        html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><title>' + \
            self.title + '</title>\n'

        html += '<link rel="stylesheet" href="../style.css">\n'
        html += '<script type="text/javascript" src="../functions.js"></script>\n'

        # Enable communication between the application and Javascript
        html += '''<script src='qrc:///qtwebchannel/qwebchannel.js'></script>\n'''

        html += '</head><body><p id="' + self.name + \
            '" class="node ' + self.name + '">' + self.text + '</p></body></html>'

        # Write as html files (make sure to use the right extension, otherwise webkit.load_uri() sometimes reads them as raw files)
        with open(temp_dir + '/' + path + self.name + '.html', 'w') as output_file:
            output_file.write(html)


class Database:
    def __init__(self):
        self.ver = ""
        self.c = ""
        self.author = ""
        self.database = ""
        self.font = "Topaz"
        self.font_size = 16
        self.height = 0
        self.help = ""
        self.index = ""
        self.macro = ""
        self.master = ""
        self.onclose = ""
        self.onopen = ""
        self.remark = ""
        self.smartwrap = False
        self.tab = []
        self.width = 100
        self.wordwrap = False
        self.xref = ""
        # self.settabs = []
        self.nodes = []

        # Status variable for node parser
        self.in_node = False

    def find_node_by_path(self, path):
        node = None
        for node in self.nodes:
            if node.name == path:
                return node
        return node

    def breakup_command(self, string):
        # Break up command strings into chunks marked by either whitespaces or quotation marks (including whitespaces)
        chunks = []

        open = False

        i = 0

        while i >= 0 and i < len(string):
            if string[i] == " ":
                if not open:
                    if i == 0:
                        # Remove starting whitespaces
                        string = string[i + 1:]
                    else:
                        # Only break up if this string is not in quotation marks
                        chunks.append(string[:i])
                        string = string[i + 1:]
                        i = 0
                else:
                    i = i + 1
            elif string[i] == "\"":
                if not open:
                    # Quotation mark found, stop processing until ending mark is found
                    open = True
                    string = string[1:]
                else:
                    # Ending mark found, save complete string up to this point
                    open = False
                    chunks.append(string[:i])
                    string = string[i + 1:]
                i = 0
            else:
                # Nothing found, next character
                i = i + 1
        # Append remaining string
        if len(string) > 0:
            chunks.append(string)
        return chunks

    def concat_chunks(self, chunks, start=1):
        # Concatenate chunks for line commands
        # TODO: Find a way to keep getting line commands getting broken up
        string = ""
        for i, chunk in enumerate(chunks):
            if i >= start:
                string += chunk + " "
        return string.strip()

    def process_line_command(self, string):
        chunks = self.breakup_command(string)

        if chunks[0].lower() == 'database':
            self.database = chunks[1]

        if chunks[0].lower() == 'master':
            self.master = chunks[1]

        if chunks[0].lower() == '$ver:':
            self.ver = self.concat_chunks(chunks)

        if chunks[0].lower() == 'author':
            self.author = self.concat_chunks(chunks)

        if chunks[0].lower() == '(c)':
            self.c = self.concat_chunks(chunks)

        if chunks[0].lower() == 'help':
            self.help = chunks[1]

        if chunks[0].lower() == 'index':
            self.index = chunks[1]

        if chunks[0].lower() == 'tab':
            self.tab = int(chunks[1])

        if chunks[0].lower() == 'font':
            self.font = fonts[chunks[1]]
            self.font_size = int(chunks[2]) + 5

        if chunks[0].lower() == 'rem' or chunks[0].lower() == 'remark':
            if len(chunks) > 1:
                self.remark = chunks[1]

        if chunks[0].lower() == 'width':
            self.width = int(chunks[1])

        if chunks[0].lower() == 'wordwrap':
            self.wordwrap = True

        if chunks[0].lower() == 'node':
            node = Node(self)
            node.name = chunks[1]
            if len(chunks) > 2:
                node.title = chunks[2]
            else:
                node.title = node.name
            self.nodes.append(node)
            self.in_node = True

        if self.in_node:
            if chunks[0].lower() == 'index':
                self.nodes[-1].index = chunks[1]
            if chunks[0].lower() == 'next':
                self.nodes[-1].next = chunks[1]
            if chunks[0].lower() == 'prev':
                self.nodes[-1].prev = chunks[1]
            if chunks[0].lower() == 'toc':
                self.nodes[-1].toc = chunks[1]
            if chunks[0].lower() == 'help':
                self.nodes[-1].help = chunks[1]
            if chunks[0].lower() == 'endnode':
                self.in_node = False

    def process_inline_command(self, string):
        chunks = self.breakup_command(string)

        output = ""

        if len(chunks) == 1:
            if chunks[0].lower() == 'u':
                output = '<span class="u">'
            if chunks[0].lower() == 'uu':
                output = '</span>'
            if chunks[0].lower() == 'b':
                output = '<b>'
            if chunks[0].lower() == 'ub':
                output = '</b>'
            if chunks[0].lower() == 'i':
                output = '<i>'
            if chunks[0].lower() == 'ui':
                output = '</i>'
            if chunks[0].lower() == 'line':
                output = '<br/>'
            if chunks[0].lower() == 'amigaguide':
                output = '<b>Amigaguide(R)</b>'
        elif len(chunks) == 2:
            if chunks[0].lower() == 'fg' or chunks[0].lower() == 'bg':
                # Translate to pseudo tags to convert later with replace_pseudo_tags()
                if chunks[1].lower() == 'back'\
                        or chunks[1].lower() == 'background'\
                        or chunks[1].lower() == 'fill'\
                        or chunks[1].lower() == 'filltext'\
                        or chunks[1].lower() == 'highlight'\
                        or chunks[1].lower() == 'shadow'\
                        or chunks[1].lower() == 'shine'\
                        or chunks[1].lower() == 'text':
                    output = '<' + chunks[0].lower() + \
                        ' ' + chunks[1].lower() + '>'
            # TODO: Implement quit script
            if chunks[1].lower() == 'close' or chunks[1].lower() == 'quit':
                output = '<button type="button" onclick="quit();">' + \
                    chunks[0] + '</button>'
        elif len(chunks) >= 2:
            if chunks[1].lower() == 'beep':
                output = '<button type="button" onclick="beep();">' + \
                    chunks[0] + '</button>'
            # TODO: Do something with system commands
            if chunks[1].lower() == 'system':
                output = '<button type="button">' + \
                    chunks[0] + '</button>'
            if chunks[1].lower() == 'link':
                if len(chunks) > 3:
                    line = int(chunks[3])
                else:
                    line = 0
                output = "<button type='button' onclick='document.bridge.button_clicked(JSON.stringify({path: \"" + \
                    chunks[2] + "\", line: \"" + \
                    str(line) + "\"}))'>" + chunks[0] + "</button>"

        return output

    def find_command(self, line):
        i = 0
        while i >= 0 and i < len(line):
            # Check if there’s any @ in the text
            i = line.find('@', i)
            if i >= 0:
                # Check if we need to ignore the command (lead by a "\")
                if i > 0:
                    match = regex.match(r'\\', line[i - 1:i])
                    if match:
                        # Remove "\" as we don't want it in the output
                        line = line[:i - 1] + line[i:]
                        # Continue after the "@"
                        # TODO: This is a rather dirty solution, find a way to jump over the whole command
                        continue

                match = regex.match(r'@\{(.*?)\}', line[i:])
                if match:
                    # Inline command, replace with tag and keep searching
                    tag = self.process_inline_command(match.group(1))
                    line = line[:i] + tag + line[i + match.end():]
                    i += len(tag)
                else:
                    # Line command, process and delete line (or leave line alone if no command)
                    match = regex.match(r'^\s*?@(.*?)$', line)
                    if match:
                        self.process_line_command(match.group(1))
                        line = ''
                    else:
                        i = i + 1
                        continue
        return line

    def replace_pseudo_tags(self, text):
        # TODO: This algorithm is a mess but it works for now
        # Find pseudo tags like 'fg back' and replace with spans accordingly

        found = True
        last_found = 0  # index for last found pseudo tag

        # Defaults
        default_colours = {
            'fg': 'text',
            'bg': 'back'
        }

        # Colours from last match
        last_colours = default_colours.copy()

        other = ""

        while found:
            re = regex.search(pattern=r'<(fg|bg) (.*?)>',
                              string=text, pos=last_found)

            if re:
                layer = re.group(1)
                style = re.group(2)

                span = ''
                other = ''

                # Close span if there was a change to any colour layer
                if last_colours['fg'] != default_colours['fg'] or last_colours['bg'] != default_colours['bg']:
                    # A span is already open, close span
                    span += '</span>'

                    # Prepare second style to add (for overlaying layers)
                    if layer == 'fg' and last_colours['bg'] != default_colours['bg']:
                        other = ' bg-' + last_colours['bg']

                    if layer == 'bg' and last_colours['fg'] != default_colours['fg']:
                        other = ' fg-' + last_colours['fg']

                if style != default_colours[layer]:
                    # No span open, open a new one and add prepared second style
                    span += '<span class="' + layer + \
                        '-' + style + other + '">'
                elif other:
                    # Just keep last style
                    span += '<span class="' + other.strip() + '">'

                text = text[:re.start(0)] + span + text[re.end(0):]
                last_found = re.start(0) + len(span)
                last_colours[layer] = style

            else:
                found = False

        return text

    def create_from_file(self, filename: str):
        # TODO: Needs error handling!

        lexer = Lexer()

        tokens = lexer.lex_file(filename)

        # Load guide file, extract database and node information, create subfolder with html files for nodes
        with open(filename, 'r', encoding='cp1252') as input_file:
            in_node = False

            for l, line in enumerate(input_file):

                # Replace HTML specific characters so they won’t interfere with the actual HTML code
                line = line.replace('<', '&lt;')
                line = line.replace('>', '&gt;')
                # line = html.escape(line, True) # Doesn’t work for some reason
                line = self.find_command(line)

                # Replace in-nodes lines with tags and insert into target document
                if self.in_node:
                    self.nodes[-1].text += line

            self.nodes[-1].text = self.replace_pseudo_tags(self.nodes[-1].text)

            # Create subfolder for database files
            Path(temp_dir + "/" + self.database).mkdir(parents=False, exist_ok=True)

            # Write all nodes as html
            for node in self.nodes:
                node.write_as_html(self.database + "/")
        return True


class MainWindow(QMainWindow):

    def load_node(self, node, line=0, retrace=True):
        self.webEngineView.load(QUrl('file://' + temp_dir + '/' +
                                     self.current_database.database + '/' + node.name + '.html'))
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
                if database.create_from_file(file):
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
        self.current_database.create_from_file(filename)

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
            self.current_database.create_from_file(filename)

            self.base_dir = filename[:filename.rfind(
                '/')]

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
        if self.current_node.index:
            self.load_node_by_path(self.current_node.index)

        if self.current_database.index:
            self.load_node_by_path(self.current_database.index)

    def on_click_help_btn(self):
        if self.current_node.help:
            self.load_node_by_path(self.current_node.help)

        if self.current_database.help:
            self.load_node_by_path(self.current_database.help)

    def on_click_retrace_btn(self):
        if len(self.history) > 0:
            self.load_node(self.history.pop(), retrace=False)

    def on_click_browse_prev_btn(self):
        if self.current_node.prev:
            self.load_node_by_path(self.current_node.prev)

    def on_click_browse_next_btn(self):
        if self.current_node.next:
            self.load_node_by_path(self.current_node.next)

    def update_buttons(self, node):
        if node.next:
            enabled = True
        else:
            enabled = False

        self.browse_next_btn.setEnabled(enabled)

        if node.prev:
            enabled = True
        else:
            enabled = False

        self.browse_prev_btn.setEnabled(enabled)

        if node.toc:
            enabled = True
        else:
            enabled = False

        self.contents_btn.setEnabled(enabled)

        if node.help:
            enabled = True
        else:
            if self.current_database.help:
                enabled = True
            else:
                enabled = False

        self.help_btn.setEnabled(enabled)

        if node.index:
            enabled = True
        else:
            if self.current_database.index:
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
    mainWin.setWindowTitle(mainWin.current_node.title)

    style = 'font-family: \"' + mainWin.current_database.font + '\"; \
        font-size: ' + str(mainWin.current_database.font_size) + 'px;'

    if mainWin.current_database.wordwrap:
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
