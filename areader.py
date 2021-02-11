import tempfile
import regex
import json
import os.path
from shutil import copyfile
from gi.repository import Gtk, WebKit2
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()

fonts = {
    "helvetica.font": "helvetica",
}


class Node:
    def __init__(self):
        self.subfolder = ""
        self.name = ""
        self.title = ""
        self.index = ""
        self.text = ""
        self.next = ""
        self.prev = ""
        self.toc = ""
        self.help = ""


class Database:
    def __init__(self):
        self.database = ""
        self.nodes = []
        self.master = ""
        self.VER = ""
        self.author = ""
        self.c = ""
        self.help = ""
        self.index = ""
        self.tab = 8
        self.settabs = []
        self.font = "Topaz"
        self.font_size = 16

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
                # Database
                if l == 0:
                    match = regex.match(r'@database \"?(.*?)\"?$', line,
                                        flags=regex.IGNORECASE)
                    if match:
                        database.database = match.group(1)
                        continue
                # else: not a guide file

                # TODO: Do something with master information
                match = regex.match(r'@master \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.master = match.group(1)
                    continue

                match = regex.match(
                    r'@ver \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.VER = match.group(1)
                    continue

                match = regex.match(r'@author \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.author = match.group(1)
                    continue

                match = regex.match(r'@c \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.c = match.group(1)
                    continue

                match = regex.match(r'@help \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.help = match.group(1)
                    continue

                match = regex.match(r'@index \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.index = match.group(1)
                    continue

                match = regex.match(r'@tab ([0-9])$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.tab = int(match.group(1))
                    continue

                # TODO: Do something with the data stored here
                match = regex.match(r'@\{settabs (.*?)\}', line,
                                    flags=regex.IGNORECASE)
                if match:
                    for m in regex.findall(r'([0-9]+)', match.group(1)):
                        database.settabs.append(m)
                    continue

                match = regex.match(r'@font \"?(.*?)\"? ([0-9]+)$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    database.font = fonts[match.group(1)]
                    database.font_size = int(match.group(2))
                    continue

                # Node
                match = regex.match(r'@node \"?(.*?)\"? \"?(.*?)\"?$', line,
                                    flags=regex.IGNORECASE)
                if match:
                    node = Node()
                    node.name = match.group(1)
                    node.title = match.group(2)
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
                    r'@index \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].index = match.group(1)
                    continue

                match = regex.match(
                    r'@next \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].next = match.group(1)
                    continue

                match = regex.match(
                    r'@prev \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].prev = match.group(1)
                    continue

                match = regex.match(
                    r'@toc \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].toc = match.group(1)
                    continue

                match = regex.match(
                    r'@help \"?(.*?)\"?$', line, flags=regex.IGNORECASE)
                if match:
                    database.nodes[-1].help = match.group(1)
                    continue

                # Text

                # TODO: Implement quit script
                line = regex.sub(r'@\{\"?(.*?)\"? quit\}', r'<a href="javascript:quit()">\1</a>',
                                 line, flags=regex.IGNORECASE)

                line = regex.sub(r'@\{\"?(.*?)\"? close\}', r'<a href="javascript:quit()">\1</a>',
                                 line, flags=regex.IGNORECASE)

                line = regex.sub(r'@\{\"?(.*?)\"? beep\s*?\"?([0-9]+)\"?\}', r'<a href="javascript:beep()">\1</a>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{\"?(.*?)\"? link \"?(.*?)\"?\s*?\"?([0-9]+)\"?\}', r'<a href="" data-path="\2" data-line="\3">\1</a>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{\"?(.*?)\"? link \"?(.*?)\"?\}', r'<a href="" data-path="\2" data-line="0">\1</a>', line,
                                 flags=regex.IGNORECASE)

                # TODO: Do something with system commands
                line = regex.sub(r'@\{\"?(.*?)\"? system \"?(.*?)\"?\}', r'<a href="">\1</a>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{b\}', '<b>', line,
                                 flags=regex.IGNORECASE)
                line = regex.sub(r'@\{ub\}', '</b>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{i\}', '<i>', line,
                                 flags=regex.IGNORECASE)
                line = regex.sub(r'@\{ui\}', '</i>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{u\}', '<span class="u">', line,
                                 flags=regex.IGNORECASE)
                line = regex.sub(r'@\{uu\}', '</span>', line,
                                 flags=regex.IGNORECASE)

                # TODO: "This command is affected by the tab and settabs commands."
                line = regex.sub(r'@\{tab\}', '        ', line,
                                 flags=regex.IGNORECASE)

                # Should actually scan for the next fg command and set spans accordingly
                line = regex.sub(r'@\{fg highlight\}(.*?)@\{fg text\}', r'<span class="fg highlight">\1</span>', line,
                                 flags=regex.IGNORECASE)

                line = regex.sub(r'@\{line\}', '\n', line)

                line = regex.sub(r'\n', '<br>', line)

                # Replace spaces with protected spaces, only outside of tags
                line = regex.sub(r'@\{amigaguide\}',
                                 '<b>Amigaguide(R)</b>', line)

                database.nodes[-1].text += line

    return database


def node_to_html(node):
    html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><title>' + \
        node.title + '</title></head><body><p id="' + node.name + \
        '" class="node ' + node.name + '">' + node.text + '</p></body></html>'

    return html


def link_receiver(user_content_manager, javascript_result):
    result = json.loads(javascript_result.get_js_value().to_json(0))

    window.load_node_by_path(result["path"], result["line"])


class Window(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="AReader")

        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        scrolled_window = Gtk.ScrolledWindow()

        self.webview = WebKit2.WebView()

        content_manager = self.webview.get_user_content_manager()

        # with open('normalize.css', 'r') as style:
        #     content_manager.add_style_sheet(WebKit2.UserStyleSheet(style.read(
        #     ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))
        # style.close()

        with open('style.css', 'r') as style:
            content_manager.add_style_sheet(WebKit2.UserStyleSheet(style.read(
            ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))
        style.close()

        with open('functions.js', 'r') as functions:
            content_manager.add_script(WebKit2.UserScript(source=functions.read(
            ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, injection_time=WebKit2.UserScriptInjectionTime.END))
        functions.close()

        content_manager.register_script_message_handler("signal")

        content_manager.connect(
            "script-message-received::signal", link_receiver)

        # Layout

        vbox = Gtk.VBox()
        self.add(vbox)

        button_box = Gtk.HBox()

        self.contents_btn = Gtk.Button(label="Contents")
        self.index_btn = Gtk.Button(label="Index")
        self.help_btn = Gtk.Button(label="Help")
        self.retrace_btn = Gtk.Button(label="Retrace")
        self.browse_prev_btn = Gtk.Button(label="Browse <")
        self.browse_next_btn = Gtk.Button(label="Browse >")

        self.contents_btn.connect("clicked", self.on_click_contents_btn)
        self.index_btn.connect("clicked", self.on_click_index_btn)
        self.help_btn.connect("clicked", self.on_click_help_btn)
        self.retrace_btn.connect("clicked", self.on_click_retrace_btn)
        self.browse_prev_btn.connect("clicked", self.on_click_browse_prev_btn)
        self.browse_next_btn.connect("clicked", self.on_click_browse_next_btn)

        button_box.pack_start(self.contents_btn, True, True, 0)
        button_box.pack_start(self.index_btn, True, True, 0)
        button_box.pack_start(self.help_btn, True, True, 0)
        button_box.pack_start(self.retrace_btn, True, True, 0)
        button_box.pack_start(self.browse_prev_btn, True, True, 0)
        button_box.pack_start(self.browse_next_btn, True, True, 0)

        vbox.pack_start(button_box, False, False, 0)
        vbox.pack_start(scrolled_window, True, True, 0)

        self.contents_btn.set_sensitive(False)
        self.index_btn.set_sensitive(False)
        self.help_btn.set_sensitive(False)
        self.retrace_btn.set_sensitive(False)
        self.browse_prev_btn.set_sensitive(False)
        self.browse_next_btn.set_sensitive(False)

        filename = self.load_file()

        copyfile('topaz_a1200_v1.0-webfont.woff2',
                 temp_dir + '/topaz_a1200_v1.0-webfont.woff2')
        copyfile('topaz_a1200_v1.0-webfont.woff',
                 temp_dir + '/topaz_a1200_v1.0-webfont.woff')
        copyfile('cursor_select.cur',
                 temp_dir + '/cursor_select.cur')
        copyfile('cursor_link.cur',
                 temp_dir + '/cursor_link.cur')
        copyfile('beep.mp3',
                 temp_dir + '/beep.mp3')

        self.history = []

        if filename:
            self.root = filename[:filename.rfind('/')]

            self.database = load_database(filename)

        self.current_node = self.database.nodes[0]

        self.load_node(node=self.database.nodes[0], retrace=False)

        scrolled_window.add(self.webview)

    def load_file(self):
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
        return filename

    def on_click_contents_btn(self, button):
        self.load_node(node=self.database.nodes[0], retrace=True)

    def on_click_index_btn(self, button):
        if self.current_node.index:
            self.load_node_by_path(self.current_node.index)

        if self.database.index:
            self.load_node_by_path(self.database.index)

    def on_click_help_btn(self, button):
        if self.current_node.help:
            self.load_node_by_path(self.current_node.help)

        if self.database.help:
            self.load_node_by_path(self.database.help)

    def on_click_retrace_btn(self, button):
        if len(self.history) > 0:
            self.load_node(self.history.pop(), retrace=False)

    def on_click_browse_prev_btn(self, button):
        if self.current_node.prev:
            self.load_node_by_path(self.current_node.prev)

    def on_click_browse_next_btn(self, button):
        if self.current_node.next:
            self.load_node_by_path(self.current_node.next)

    def load_node(self, node, line=0, retrace=True):
        if not os.path.isfile(temp_dir + '/' + node.subfolder + node.name):
            with open(temp_dir + '/' + node.subfolder + node.name, 'w') as output_file:
                output_file.write(node_to_html(node))
                output_file.close()

        self.webview.load_uri('file://' + temp_dir + '/' +
                              node.subfolder + node.name)

        self.set_title(node.name)

        self.webview.get_user_content_manager().add_style_sheet(WebKit2.UserStyleSheet('''
        html {
            font-family: ''' + self.database.font + ''';
            font-size: ''' + str(self.database.font_size) + '''px;
        }''', injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))

        # Buttons

        if node.next:
            next = True
        else:
            next = False

        self.browse_next_btn.set_sensitive(next)

        if node.prev:
            prev = True
        else:
            prev = False

        self.browse_prev_btn.set_sensitive(prev)

        if node.toc:
            toc = True
        else:
            toc = False

        self.contents_btn.set_sensitive(toc)

        if node.help:
            help = True
        else:
            if self.database.help:
                help = True
            else:
                help = False

        self.contents_btn.set_sensitive(help)

        if node.index:
            index = True
        else:
            if self.database.index:
                index = True
            else:
                index = False

        self.contents_btn.set_sensitive(index)

        if retrace:
            self.history.append(self.current_node)

        self.current_node = node

        if len(self.history) > 0:
            history = True
        else:
            history = False

        self.retrace_btn.set_sensitive(history)

    def load_node_by_path(self, path, line=0):
        # Check if path is another guide file
        if path.find('.guide') >= 0:
            if os.path.isfile(self.root + '/' + path[:path.rfind('/')]):
                print(path)
        # else:
        node = self.database.find_node_by_path(path)

        if node:
            self.load_node(node, line)


window = Window()
window.show_all()
Gtk.main()
