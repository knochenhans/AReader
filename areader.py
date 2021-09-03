from os import error, mkdir, replace
import tempfile
import regex
import json
import os.path
import html
import sys
from shutil import copyfile
from gi.repository import Gtk, WebKit2, Gdk, GdkPixbuf, GLib, Gio
import gi
from regex.regex import findall, search
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

temp = tempfile.TemporaryFile()
temp_dir = tempfile.mkdtemp()

# TODO: Maybe show font mapping dialog for non-mapped fonts?

fonts = {
    "helvetica.font": "Helvetica",
    "courier.font": "Courier New",
    "times.font": "Times New Roman"
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
        # TODO: This algorithm is a mess but it forks for now
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

    def create_from_file(self, filename):
        # TODO: Needs error handling!

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
            mkdir(temp_dir + "/" + self.database)

            # Write all nodes as html
            for node in self.nodes:
                node.write_as_html(self.database + "/")
        return True


def link_receiver(user_content_manager, javascript_result):
    result = json.loads(javascript_result.get_js_value().to_json(0))

    if not app.window.load_node_by_path(result["path"], result["line"]):
        print('Unable to open node: ' + result["path"])


class DatabaseDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title="Database Information",
                            transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 100)

        label = Gtk.Label(
            label="This is a dialog to display additional information")

        box = self.get_content_area()
        box.add(label)
        self.show_all()


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(750, 600)

        self.databases = []

        self.scrolled_window = Gtk.ScrolledWindow()
        self.webview = WebKit2.WebView()

        self.setup_content_manager()
        self.setup_layout()
        self.setup_style()

        pixbuf = GdkPixbuf.Pixbuf.new_from_file('cursor_select.cur')
        cursor = Gdk.Cursor.new_from_pixbuf(
            Gdk.Display.get_default(), pixbuf, 5, 5)
        self.get_window().set_cursor(cursor)

    def setup_style(self):
        css = b'@import url("gtk.css");'
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        context = Gtk.StyleContext()
        screen = Gdk.Screen.get_default()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def setup_content_manager(self):
        # Inject styles and functions

        content_manager = self.webview.get_user_content_manager()

        # with open('normalize.css', 'r') as style:
        #     content_manager.add_style_sheet(WebKit2.UserStyleSheet(style.read(
        #     ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))

        with open('style.css', 'r') as style:
            content_manager.add_style_sheet(WebKit2.UserStyleSheet(style.read(
            ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))

        with open('functions.js', 'r') as functions:
            content_manager.add_script(WebKit2.UserScript(source=functions.read(
            ), injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, injection_time=WebKit2.UserScriptInjectionTime.END))

        # Callback function for links (overriding html links)
        content_manager.register_script_message_handler('signal')
        content_manager.connect(
            'script-message-received::signal', link_receiver)

    def setup_layout(self):
        # Setup layout

        self.vbox = Gtk.VBox()
        self.add(self.vbox)

        self.button_box = Gtk.HBox()

        self.contents_btn = Gtk.Button(label="Contents")
        self.index_btn = Gtk.Button(label="Index")
        self.help_btn = Gtk.Button(label='Help')
        self.retrace_btn = Gtk.Button(label='Retrace')
        self.browse_prev_btn = Gtk.Button(label='Browse <')
        self.browse_next_btn = Gtk.Button(label='Browse >')

        width = 70
        height = 25

        self.contents_btn.set_property('width-request', width)
        self.contents_btn.set_property('height-request', height)

        self.index_btn.set_property('width-request', width)
        self.index_btn.set_property('height-request', height)

        self.help_btn.set_property('width-request', width)
        self.help_btn.set_property('height-request', height)

        self.retrace_btn.set_property('width-request', width)
        self.retrace_btn.set_property('height-request', height)

        self.browse_prev_btn.set_property('width-request', width)
        self.browse_prev_btn.set_property('height-request', height)

        self.browse_next_btn.set_property('width-request', width)
        self.browse_next_btn.set_property('height-request', height)

        self.contents_btn.connect('clicked', self.on_click_contents_btn)
        self.index_btn.connect('clicked', self.on_click_index_btn)
        self.help_btn.connect('clicked', self.on_click_help_btn)
        self.retrace_btn.connect('clicked', self.on_click_retrace_btn)
        self.browse_prev_btn.connect('clicked', self.on_click_browse_prev_btn)
        self.browse_next_btn.connect('clicked', self.on_click_browse_next_btn)

        self.button_box.pack_start(self.contents_btn, False, True, 0)
        self.button_box.pack_start(self.index_btn, False, True, 0)
        self.button_box.pack_start(self.help_btn, False, True, 0)
        self.button_box.pack_start(self.retrace_btn, False, True, 0)
        self.button_box.pack_start(self.browse_prev_btn, False, True, 0)
        self.button_box.pack_start(self.browse_next_btn, False, True, 0)

        self.vbox.pack_start(self.button_box, False, False, 0)
        self.vbox.pack_start(self.scrolled_window, True, True, 0)

        self.contents_btn.set_sensitive(False)
        self.index_btn.set_sensitive(False)
        self.help_btn.set_sensitive(False)
        self.retrace_btn.set_sensitive(False)
        self.browse_prev_btn.set_sensitive(False)
        self.browse_next_btn.set_sensitive(False)

        self.scrolled_window.add(self.webview)
        self.show_all()

    def load_file(self):
        dialog = Gtk.FileChooserDialog(
            title='Please choose a file', parent=self, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        filter_any = Gtk.FileFilter()
        filter_any.set_name('AmigaGuide files')
        filter_any.add_pattern('*.guide')
        dialog.add_filter(filter_any)

        filename = ""

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()

        if filename:
            self.databases.append(Database())
            self.current_database = self.databases[-1]
            self.current_database.create_from_file(filename)

            self.base_dir = filename[:filename.rfind(
                '/')]

        self.current_node = self.current_database.nodes[0]

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

        self.load_node(node=self.current_database.nodes[0], retrace=False)

    def show_database_info(self):
        dialog = DatabaseDialog(self)
        dialog.present()

    def on_click_contents_btn(self, button):
        self.load_node(node=self.current_database.nodes[0], retrace=True)

    def on_click_index_btn(self, button):
        if self.current_node.index:
            self.load_node_by_path(self.current_node.index)

        if self.current_database.index:
            self.load_node_by_path(self.current_database.index)

    def on_click_help_btn(self, button):
        if self.current_node.help:
            self.load_node_by_path(self.current_node.help)

        if self.current_database.help:
            self.load_node_by_path(self.current_database.help)

    def on_click_retrace_btn(self, button):
        if len(self.history) > 0:
            self.load_node(self.history.pop(), retrace=False)

    def on_click_browse_prev_btn(self, button):
        if self.current_node.prev:
            self.load_node_by_path(self.current_node.prev)

    def on_click_browse_next_btn(self, button):
        if self.current_node.next:
            self.load_node_by_path(self.current_node.next)

    def update_buttons(self, node):
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
            if self.current_database.help:
                help = True
            else:
                help = False

        self.contents_btn.set_sensitive(help)

        if node.index:
            index = True
        else:
            if self.current_database.index:
                index = True
            else:
                index = False

        self.contents_btn.set_sensitive(index)

        if len(self.history) > 0:
            history = True
        else:
            history = False

        self.retrace_btn.set_sensitive(history)

    def load_node(self, node, line=0, retrace=True):
        # TODO: Needs error handling!

        self.webview.load_uri('file://' + temp_dir + '/' +
                              self.current_database.database + '/' + node.name + '.html')

        self.set_title(node.title)

        font_family = 'font-family: ''' + self.current_database.font + ';'
        font_size = 'font-size: ''' + \
            str(self.current_database.font_size) + 'px;'
        if self.current_database.wordwrap:
            white_space = 'white-space: pre-wrap;'
        else:
            white_space = 'white-space: pre;'

        self.webview.get_user_content_manager().add_style_sheet(WebKit2.UserStyleSheet(
            'html {'
            + font_family
            + font_size
            + white_space
            + '}', injected_frames=WebKit2.UserContentInjectedFrames.ALL_FRAMES, level=WebKit2.UserStyleLevel.USER))

        if retrace:
            self.history.append(self.current_node)

        self.update_buttons(node)

        self.current_node = node

        # self.webview.run_javascript('alert_box();')

        return True

    def load_node_by_path(self, path, line=0):
        path_chunks = path.split('/')
        if len(path_chunks) == 1:
            # Simple internal link
            node = self.current_database.find_node_by_path(path)

            if node:
                return self.load_node(node, line)
        else:
            # External link

            # Check if file exists (last chunk is main node, so ignore)
            file = self.base_dir + '/' + '/'.join(path_chunks[:-1])
            if os.path.isfile(file):
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


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.example.areader",
            **kwargs
        )
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("open", None)
        action.connect("activate", self.on_open)
        self.add_action(action)

        action = Gio.SimpleAction.new("show_database_info", None)
        action.connect("activate", self.on_database_info)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder()
        builder.add_from_file("menu.xml")

        self.set_menubar(builder.get_object("menubar"))

    def do_activate(self):
        if not self.window:
            self.window = AppWindow(application=self, title="AReader")

        self.window.present()

    def on_open(self, action, param):
        self.window.load_file()

    def on_database_info(self, action, param):
        self.window.show_database_info()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.present()

    def on_quit(self, action, param):
        self.quit()


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)

# TODO: Topaz font for menu buttons
# TODO: Limit button style to buttons (not entire application)
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
# TODO: Rework temp files so they get deleted after program exit
# TODO: Problems when loading the same document again
