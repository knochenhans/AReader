import tempfile
import regex
import json
import os.path
from shutil import copyfile
from airium import Airium
from gi.repository import Gtk, WebKit2
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()


class Node:
    def __init__(self):
        self.name = ""
        self.title = ""
        self.index = ""
        self.text = ""
        self.subfolder = ""


class Database:
    def __init__(self):
        self.database = ""
        self.master = ""
        self.VER = ""
        self.author = ""
        self.c = ""
        self.nodes = []

    def find_node_by_path(self, path):
        node = None
        for node in self.nodes:
            if node.subfolder + node.name == path:
                return node
        return node


def load_database(filename):
    database = Database()

    with open(filename, 'r', encoding='cp1252') as input_file:
        in_node = False

        for l, line in enumerate(input_file):
            if not in_node:
                if l == 0:
                    match = regex.match(r'@database (.*?)$', line,
                                        flags=regex.IGNORECASE)
                    if match:
                        database.database = match.group(1).strip('\"')
                        continue
                # else: not a guide file

                match = regex.match(r'@master (.*?)$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.master = match.group(1).strip('\"')
                    continue

                match = regex.match(
                    r'@ver (.*?)$', line, flags=regex.IGNORECASE)
                if match:
                    database.VER = match.group(1).strip('\"')
                    continue

                match = regex.match(r'@author (.*?)$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.author = match.group(1).strip('\"')
                    continue

                match = regex.match(r'@c (.*?)$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.c = match.group(1).strip('\"')
                    continue

                # Node
                match = regex.match(r'@node (.*?) (.*?)$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    node = Node()
                    node.name = match.group(1).strip('\"')
                    node.title = match.group(2).strip('\"')
                    database.nodes.append(node)
                    in_node = True
                    continue
            else:
                match = regex.match(r'@endnode', line,
                                    flags=regex.IGNORECASE)
                if match:
                    in_node = False
                    continue

                match = regex.match(
                    r'@index (.*?)$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].index = match.group(1).strip('\"')
                    continue

                match = regex.search(
                    r'@{(.*?) link (.*?)\s*?([0-9]+)?}', line, flags=regex.IGNORECASE)
                if match:
                    link_path = match.group(2).strip('\"')
                    link_line = 0

                    if len(match.groups()) == 3:
                        link_line = match.group(3)

                    line = line[:match.start()] + '<a href="" data-path="' + link_path + '" data-line="' + str(
                        link_line) + '">' + match.group(1).strip('\"') + '</a>' + line[match.end():]

                line = regex.sub(r'@{b}', '<b>', line,
                                 flags=regex.IGNORECASE)
                line = regex.sub(r'@{ub}', '</b>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'\n', '<br>', line)

                # Replace spaces with protected spaces, only outside of tags
                line = regex.sub(r'(?<!<[^>]*) ', '&nbsp;', line)

                database.nodes[-1].text += line

    return database


def node_to_html(node):

    html = Airium()

    html('<!DOCTYPE html>')
    with html.html(lang="en"):
        with html.head():
            html.meta(charset="utf-8")
            html.title(_t=node.title)

        with html.body():
            with html.p(id=node.name, klass=node.name):
                html(node.text)
            with html.script(type="text/javascript"):
                html('''
                document.querySelectorAll('a').forEach(item => {
                    item.addEventListener('click', event => {
                        // Send JSON message to application
                        window.webkit.messageHandlers.signal.postMessage({"path": item.dataset.path, "line": item.dataset.line});

                        // Keep href from being parsed
                        return false;
                    })
                })
                ''')
    return str(html)


def link_receiver(user_content_manager, javascript_result):
    result = json.loads(javascript_result.get_js_value().to_json(0))

    window.load_node_by_path(result["path"], result["line"])


class Window(Gtk.Window):
    def __init__(self, webview):
        Gtk.Window.__init__(self, title="Dialog Example")

        copyfile('style.css', temp_dir + '/style.css')
        copyfile('Topaz_a1200_v1.0.ttf', temp_dir + '/Topaz_a1200_v1.0.ttf')

        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        scrolled_window = Gtk.ScrolledWindow()

        content_manager = webview.get_user_content_manager()

        with open('style.css', 'r') as s:
            style = WebKit2.UserStyleSheet(s.read(), 0, 0)

            content_manager.add_style_sheet(style)

        content_manager.register_script_message_handler("signal")

        content_manager.connect(
            "script-message-received::signal", link_receiver)

        # Load File

        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        filter_any = Gtk.FileFilter()
        filter_any.set_name("AmigaGuide files")
        filter_any.add_pattern("*.guide")
        dialog.add_filter(filter_any)

        filename = ""

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()

        self.root = filename[:filename.rfind('/')]

        self.database = load_database(filename)

        self.load_node(self.database.nodes[0])

        scrolled_window.add(webview)
        self.add(scrolled_window)

    def load_node(self, node, line=0):
        if not os.path.isfile(temp_dir + '/' + node.subfolder + node.name):
            with open(temp_dir + '/' + node.subfolder + node.name, 'w') as output_file:
                output_file.write(node_to_html(node))
                output_file.close()

        webview.load_uri('file://' + temp_dir + '/' +
                         node.subfolder + node.name)

    def load_node_by_path(self, path, line=0):
        # Check if path is another guide file
        if path.find('.guide') >= 0:
            if os.path.isfile(self.root + '/' + path[:path.rfind('/')]):
                print(path)
        # else:
        node = self.database.find_node_by_path(path)

        if node:
            self.load_node(node, line)


webview = WebKit2.WebView()
window = Window(webview)
window.show_all()
Gtk.main()
