from pathlib import Path
import regex
from node import Node
from lexer import Lexer, TOKEN_TYPE, Token

fonts = {
    "helvetica.font": "Helvetica",
    "courier.font": "Courier New",
    "times.font": "Times New Roman",
    "topaz": "Topaz"
}


class Database:
    def __init__(self):
        self.properties = {}
        self.properties['font'] = "Topaz"
        self.properties['font-size'] = 16
        self.properties['width'] = 100
        self.properties['smartwrap'] = False
        self.properties['wordwrap'] = False
        self.properties['height'] = 0
        self.nodes = []

        # Status variable for node parser
        # self.in_node = False

    def get_property(self, key: str, default_value=''):
        if key in self.properties:
            return self.properties[key]
        else:
            return default_value

    def find_node_by_path(self, path):
        for node in self.nodes:
            if node.get_property('name') == path:
                return node
        return None

    def process_inline_command(self, string):
        # chunks = self.breakup_command(string)
        chunks = []

        output = ''

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

        other = ''

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

    def create_from_file(self, filename: str, path: str):
        # TODO: Needs error handling!

        lexer = Lexer()

        tokens = lexer.lex_file(filename)
        # tokens = lexer.lex('Example:\n\n              @macro bold "\@{b} $1 \@{ub}"')

        try:
            node = self.convert(tokens)
        except ValueError as e:
            print(e)

        # Load guide file, extract database and node information, create subfolder with html files for nodes
        # with open(filename, 'r', encoding='cp1252') as input_file:
        #     in_node = False

        #     for l, line in enumerate(input_file):

        #         # Replace HTML specific characters so they won’t interfere with the actual HTML code
        #         line = line.replace('<', '&lt;')
        #         line = line.replace('>', '&gt;')
        #         # line = html.escape(line, True) # Doesn’t work for some reason
        #         line = self.find_command(line)

        #         # Replace in-nodes lines with tags and insert into target document
        #         if self.in_node:
        #             self.nodes[-1].text += line

        #     self.nodes[-1].text = self.replace_pseudo_tags(self.nodes[-1].text)

        # Create subfolder for database files
        Path(path + "/" + self.get_property('database')).mkdir(parents=False, exist_ok=True)

        # Write all nodes as html
        for node in self.nodes:
            node.write_as_html(self.get_property('database') + "/", path)
        return True

    def pop_until(self, type: TOKEN_TYPE, value: str) -> list[Token]:
        for idx, token in enumerate(self.tokens_line):
            if token.type == type and token.value == value:
                tokens = self.tokens_line[:idx]
                self.tokens_line = self.tokens_line[idx + 1:]
                return tokens
        return []

    def pop_until_newline(self) -> list[Token]:
        tokens = []

        while True:
            try:
                token = self.tokens.pop(0)
            except IndexError:
                return tokens

            if token.type == TOKEN_TYPE.NEWLINE:
                return tokens
            tokens.append(token)

    def tokens_to_string(self, tokens: list[Token]) -> str:
        string = ''
        for token in tokens:
            string += str(token.value) + ' '
        return string.strip()

    def pop_value(self, type: TOKEN_TYPE = TOKEN_TYPE.UNDEFINED):
        try:
            token = self.tokens_line.pop(0)
        except IndexError:
            return ''

        if token.type == type or type == TOKEN_TYPE.UNDEFINED:
            return token.value

        # raise ValueError(f'Unexpected parameter type: {self.tokens_line[0].type} ({self.tokens_line[0].value}), expected {type}')
        print(f'Unexpected parameter type: {self.tokens_line[0].type} ({self.tokens_line[0].value}), expected {type}')
        return ''

    def convert(self, tokens: list[Token]) -> Node:
        self.tokens = tokens
        node = None

        while self.tokens:
            self.tokens_line = self.pop_until_newline()

            while self.tokens_line:
                token = self.tokens_line[0]

                match token.type:
                    case TOKEN_TYPE.STRING:
                        self.tokens_line.pop(0)
                        if node:
                            text = token.value

                            # Replace HTML specific characters so they won’t interfere with the actual HTML code
                            text = text.replace('<', '&lt;')
                            text = text.replace('>', '&gt;')

                            node.text += text
                        else:
                            # raise UnboundLocalError(f'String outside node found.')
                            print(f'String outside of node found: "{token.value}"')

                    case TOKEN_TYPE.IDENTIFIER:
                        if token.value == '@':
                            self.tokens_line.pop(0)

                            if self.tokens_line[0].type == TOKEN_TYPE.SEPARATOR and self.tokens_line[0].value == '{':

                                # Inline commands
                                self.tokens_line.pop(0)
                                command = self.pop_until(TOKEN_TYPE.SEPARATOR, '}')

                                if node:
                                    match len(command):
                                        case 2:
                                            if command[1].type == TOKEN_TYPE.IDENTIFIER:
                                                match command[0].value.lower():
                                                    case 'beep':
                                                        node.text = '<button type="button" onclick="beep();">' + command[0].value + '</button>'
                                        case 3 | 4:
                                            if command[1].type == TOKEN_TYPE.IDENTIFIER:
                                                match command[0].value.lower():
                                                    case 'system':
                                                        # TODO: Do something with system commands
                                                        node.text += '<button type="button">' + command[0].value + '</button>'
                                                if command[1].value.lower() == 'link':
                                                    if len(command) == 3:
                                                        line = 0
                                                    else:
                                                        line = int(command[3].value)

                                                    node.text += "<button type='button' onclick='document.bridge.button_clicked(JSON.stringify({path: \"" + command[2].value + "\", line: \"" + str(
                                                        line) + "\"}))'>" + command[0].value + "</button>"

                            else:
                                command = self.tokens_line.pop(0)

                                try:
                                    if node:
                                        if command.value.lower() in ['next', 'prev', 'toc', 'index', 'title']:
                                            node.properties[command.value.lower()] = self.pop_value()
                                        elif command.value.lower() == 'endnode':
                                            self.nodes.append(node)

                                        match command.value.lower():
                                            case 'link':
                                                pass
                                    else:
                                        if command.value.lower() in ['next', 'prev', 'toc', 'endnode']:
                                            raise UnboundLocalError(f'Node link {command.value.lower()} info found but no node is open.')

                                    if command.value.lower() in ['next', 'prev', 'toc', 'endnode']:
                                        continue

                                    # self.tab = int(self.pop_value(TOKEN_TYPE.NUMBER))
                                    if command.value.lower() in ['database', 'master', '$ver:', 'author', '(c)', 'help', 'width', 'tab', 'rem', 'remark', 'index']:
                                        self.properties[command.value.lower()] = self.tokens_to_string(self.tokens_line)
                                        break
                                    else:
                                        match command.value.lower():
                                            case 'font':
                                                font = self.pop_value()
                                                try:
                                                    self.properties[command.value.lower()] = fonts[font]
                                                except IndexError:
                                                    print(f'Font {font} not found in font list, ignoring')
                                                self.properties['font-size'] = int(self.pop_value(TOKEN_TYPE.NUMBER)) + 5

                                            case 'wordwrap':
                                                self.properties[command.value.lower()] = True

                                            case 'node':
                                                node = Node(self)
                                                name = self.pop_value()

                                                if name:
                                                    node.properties['name'] = name
                                                    node.properties['title'] = name

                                                title = self.pop_value()

                                                if title:
                                                    node.properties['title'] = title

                                            case 'macro':
                                                break

                                            case _:
                                                # raise ValueError(f'Unknown node found: {command.value}')
                                                print(f'Unknown node type found: {command.value}')
                                                break
                                except ValueError as e:
                                    print(f'Error while parsing parameter for token "{command.value}": {e}')

        if node:
            return node
        raise ValueError('Conversion ended with empty node')
