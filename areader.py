from os import mkdir, replace
import tempfile
import regex
import json
import os.path
from shutil import copyfile
from gi.repository import Gtk, WebKit2
import gi
from regex.regex import findall
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()

fonts = {
    "helvetica.font": "helvetica",
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
            self.title + '</title></head><body><p id="' + self.name + \
            '" class="node ' + self.name + '">' + self.text + '</p></body></html>'

        # Write as html files (we need to make sure to use the right extension, otherwise webkit.load_uri() sometimes reads them as raw files)
        with open(temp_dir + '/' + path + self.name + '.html', 'w') as output_file:
            output_file.write(html)
            output_file.close()


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
        #self.settabs = []
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
            self.font_size = int(chunks[2])

        if chunks[0].lower() == 'rem' or chunks[0].lower() == 'remark':
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
            # Should actually scan for the next fg command and set spans accordingly
            if chunks[0].lower() == 'fg' or chunks[0].lower() == 'bg':
                if chunks[1].lower() == 'highlight'\
                        or chunks[1].lower() == 'shine'\
                        or chunks[1].lower() == 'shadow'\
                        or chunks[1].lower() == 'fill'\
                        or chunks[1].lower() == 'filltext'\
                        or chunks[1].lower() == 'back':
                    output = '<span class="' + \
                        chunks[0].lower() + ' ' + chunks[1].lower() + '">'
                if chunks[1].lower() == 'text':
                    output = '</span>'
            # TODO: Implement quit script
            if chunks[1].lower() == 'close' or chunks[1].lower() == 'quit':
                output = '<a href="javascript:quit()">' + chunks[0] + '</a>'
        elif len(chunks) >= 2:
            if chunks[1].lower() == 'beep':
                output = '<a href="javascript:beep()">' + \
                    chunks[0] + '</a>'
            # TODO: Do something with system commands
            if chunks[1].lower() == 'system':
                output = '<a href="">' + \
                    chunks[0] + '</a>'
            if chunks[1].lower() == 'link':
                if len(chunks) > 3:
                    line = int(chunks[3])
                else:
                    line = 0
                output = '<a href="" data-path="' + \
                    chunks[2] + '" data-line="' + \
                    str(line) + '">' + chunks[0] + '</a>'

        return output

    def find_command(self, line):
        i = 0
        while i >= 0 and i < len(line):
            # Check if there’s any @ in the text
            i = line.find('@', i)
            if i >= 0:
                # Check if we need to ignore the command (lead by a "\")
                if i > 0:
                    if line.find('\\', i - 1) >= 0:
                        i = i + 1
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
                        line = ""
                    else:
                        i = i + 1
                        continue
        return line

    def load_from_file(self, filename):

        # Load guide file, extract database and node information, create subfolder with html files for nodes
        with open(filename, 'r', encoding='cp1252') as input_file:
            in_node = False

            for l, line in enumerate(input_file):

                line = line.replace('<', '&lt;')
                line = line.replace('>', '&gt;')
                line = self.find_command(line)
                line = line.replace('\@', '@')

                # Replace in-nodes lines with tags
                if self.in_node:
                    self.nodes[-1].text += line

            # Create subfolder for database files
            mkdir(temp_dir + "/" + self.database)

            # Write all nodes as html
            for node in self.nodes:
                node.write_as_html(self.database + "/")


def link_receiver(user_content_manager, javascript_result):
    result = json.loads(javascript_result.get_js_value().to_json(0))

    window.load_node_by_path(result["path"], result["line"])


class Window(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="AReader")

        self.set_default_size(675, 620)
        self.connect("destroy", Gtk.main_quit)
        scrolled_window = Gtk.ScrolledWindow()

        self.webview = WebKit2.WebView()

        # Inject styles and functions

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

        # Callback function for links to nodes (overriding html links)

        content_manager.register_script_message_handler("signal")

        content_manager.connect(
            "script-message-received::signal", link_receiver)

        # Setup Layout

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

        # Copy some needed files (fonts, cursors, beep sound)

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
            self.database = Database()

            self.database.load_from_file(filename)

            self.root = filename[:filename.rfind(
                '/')] + "/" + self.database.database

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
        self.webview.load_uri('file://' + temp_dir + '/' +
                              self.database.database + '/' + node.name + '.html')

        self.set_title(node.name)

        font_family = 'font-family: ''' + self.database.font + ';'
        font_size = 'font-size: ''' + str(self.database.font_size) + 'px;'
        if self.database.wordwrap:
            white_space = 'white-space: pre-wrap;'
        else:
            white_space = 'white-space: pre;'

        self.webview.get_user_content_manager().add_style_sheet(WebKit2.UserStyleSheet(
            'html {'
            + font_family
            + font_size
            + white_space
            + '}', injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))

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
        # Check if path is an external guide file
        # if path.find('.guide') >= 0:
        # if os.path.isfile(self.root + '/' + path[:path.rfind('/')]):
        # print(path)
        # else:
        path_parts = path.split('/')
        if len(path_parts) == 1:
            # Simple internal link
            node = self.database.find_node_by_path(path)

            if node:
                self.load_node(node, line)


window = Window()
window.show_all()
Gtk.main()

# TODO: Application menu
# TODO: Style menu buttons
# TODO: Link to external databases
# TODO: Implement tabstops
# TODO: Tabs in documents not working correctly (arcdir.dopus5.guide)
# TODO: Implement width
# TODO: Problems with spans
