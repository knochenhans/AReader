import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2
from airium import Airium
from shutil import copyfile
import json
import regex
import tempfile

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()


class Database:
    def __init__(self):
        self.database = ""
        self.master = ""
        self.VER = ""
        self.author = ""
        self.c = ""


class Node:
    def __init__(self):
        self.name = ""
        self.title = ""
        self.index = ""
        self.text = ""


def receiver(user_content_manager, javascript_result):
    result = json.loads(javascript_result.get_js_value().to_json(0))
    window.on_load_uri(result["path"], result["line"])


class FileChooserWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="FileChooser Example")

        box = Gtk.Box(spacing=6)
        self.add(box)

        button1 = Gtk.Button(label="Choose File")
        button1.connect("clicked", self.on_file_clicked)
        box.add(button1)

        button2 = Gtk.Button(label="Choose Folder")
        button2.connect("clicked", self.on_folder_clicked)
        box.add(button2)

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Open clicked")
            print("File selected: " + dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_py = Gtk.FileFilter()
        filter_py.set_name("Python files")
        filter_py.add_mime_type("text/x-python")
        dialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def on_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK
        )
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Select clicked")
            print("Folder selected: " + dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()


class DialogWindow(Gtk.Window):
    def __init__(self, webview):
        Gtk.Window.__init__(self, title="Dialog Example")

        # self.set_border_width(6)

        #button = Gtk.Button(label="Open dialog")
        #button.connect("clicked", self.on_button_clicked)

        # self.add(button)

        filechooser = FileChooserWindow()
        filechooser.show_all()

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

        content_manager.connect("script-message-received::signal", receiver)

        with open('cyberblanker.guide', 'r', encoding='cp1252') as input_file:
            database = Database()
            nodes = []

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
                        nodes.append(node)
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
                        nodes[-1].index = match.group(1).strip('\"')
                        continue

                    match = regex.search(
                        r'@{(.*?) link (.*?) ([0-9]+)?}', line, flags=regex.IGNORECASE)
                    if match:
                        if match.group(2) is not None:
                            line = line[:match.start()] + '<a href="" data-path="' + match.group(2).strip('\"') + '" data-line="' + \
                                match.group(3).strip(
                                    '\"') + '">' + match.group(1).strip('\"') + '</a>' + line[match.end():]

                    line = regex.sub(r'@{b}', '<b>', line,
                                     flags=regex.IGNORECASE)
                    line = regex.sub(r'@{ub}', '</b>', line,
                                     flags=regex.IGNORECASE)

                    line = regex.sub(r'\n', '<br>', line)

                    # Replace spaces with protected spaces, only outside of tags
                    line = regex.sub(r'(?<!<[^>]*) ', '&nbsp;', line)

                    nodes[-1].text += line

        for node in nodes:
            html_data = Airium()

            html_data('<!DOCTYPE html>')
            with html_data.html(lang="en"):
                with html_data.head():
                    html_data.meta(charset="utf-8")
                    html_data.title(_t=node.title)
                    #html_data.link(rel="stylesheet", href="./style.css")

                with html_data.body():
                    with html_data.p(id=node.name, klass=node.name):
                        html_data(node.text)
                    with html_data.script(type="text/javascript"):
                        html_data('''
                        document.querySelectorAll('a').forEach(item => {
                            item.addEventListener('click', event => {
                                // Send JSON message to application
                                window.webkit.messageHandlers.signal.postMessage({"path": item.dataset.path, "line": item.dataset.line});

                                // Keep href from being parsed
                                return false;
                            })
                        })
                        ''')

            html = str(html_data)  # casting to string extracts the value
            with open(temp_dir + '/' + node.name, 'w') as output_file:
                output_file.write(html)
                output_file.close()

        webview.load_uri('file://' + temp_dir + '/' + nodes[0].name)
        scrolled_window.add(webview)

        self.add(scrolled_window)

    def on_load_uri(self, path, line):
        webview.load_uri('file://' + temp_dir + '/' + path)


webview = WebKit2.WebView()
window = DialogWindow(webview)
window.show_all()
Gtk.main()
