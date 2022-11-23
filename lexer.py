import copy
from enum import Enum, auto
import re
import string


class TOKEN_TYPE(Enum):
    UNDEFINED = auto()
    COMMENT = auto()
    NEWLINE = auto()
    WHITESPACE = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    SEPARATOR = auto()
    OPERATOR = auto()
    STRING = auto()


class Token():
    def __init__(self, type: TOKEN_TYPE = TOKEN_TYPE.UNDEFINED, value: str = ''):
        self.type = type
        self.value = value


class STATE(Enum):
    STRING = auto()
    COMMAND = auto()


Spec = [
    (r'^(\n)', TOKEN_TYPE.NEWLINE),
    (r'^(\s+)', TOKEN_TYPE.WHITESPACE),
    (r'^(@)', TOKEN_TYPE.IDENTIFIER),
    (r'^([\{\}])', TOKEN_TYPE.SEPARATOR),
    (r'^(\d+(\.\d)?)', TOKEN_TYPE.NUMBER),
    (r'^"(.*?)"', TOKEN_TYPE.STRING),
    (r'^\'(.*?)\'', TOKEN_TYPE.STRING),
    (r'^([a-zA-ZäÄöÖüÜß0-9\.\-_]+)', TOKEN_TYPE.IDENTIFIER),
    (r'^(.*?)(?=\s)', TOKEN_TYPE.IDENTIFIER),
]


class Lexer():
    def __init__(self):
        self.string = ''
        self.cursor = 0
        self.current_linepos = 0
        self.current_line = 0

    def load_file(self, filename: str) -> str:
        with open(filename, 'r', encoding='cp1252') as file:
            return file.read()

    def lex_file(self, filename: str) -> list[Token]:
        return self.lex(self.load_file(filename))

    def is_EOF(self) -> bool:
        return self.cursor == len(self.string)

    def has_more_tokens(self) -> bool:
        return self.cursor < len(self.string)

    def get_next_token(self) -> Token:
        if not self.has_more_tokens():
            raise EOFError

        string = self.string[self.cursor:]

        for spec in Spec:
            match = re.match(spec[0], string)

            if not match:
                continue

            self.cursor += match.end()

            return Token(value=match.group(1), type=spec[1])

        raise ValueError(f'Unexpected token: "{string[0]}"')

    def init_string_token(self) -> Token:
        return Token(type=TOKEN_TYPE.STRING)

    # def get_line(self) -> Token:
    #     string = self.string[self.cursor:]

    def lex(self, string: str) -> list[Token]:
        self.string = string

        tokens = []
        state = STATE.STRING
        string_token = self.init_string_token()

        last_pos = 0

        # string = string.replace('<', '&lt;')
        # string = string.replace('>', '&gt;')

        while True:
            if state == STATE.STRING:
                pattern = re.compile(r'(?<!\\)@')

                match = pattern.search(string, last_pos)

                if match:
                    if match.start() > 0:
                        if re.match(r'.@(?!{)', string[match.start() - 1:]):
                            last_pos += 1
                            continue

                    pos = match.start()

                    string_token.value += string[self.cursor:pos]

                    if string_token.value:
                        tokens.append(string_token)
                    state = STATE.COMMAND
                else:
                    # Not a real command, ignore
                    break

                self.cursor += len(string_token.value)
            else:
                try:
                    token = self.get_next_token()
                except EOFError:
                    break
                except ValueError as e:
                    print(f'Failed lexing: {e}')
                    break
                else:
                    if state == STATE.COMMAND:
                        match token.type:
                            case TOKEN_TYPE.SEPARATOR:
                                if token.value == '}':
                                    string_token = self.init_string_token()
                                    state = STATE.STRING
                                tokens.append(token)
                            case TOKEN_TYPE.WHITESPACE:
                                continue
                            case TOKEN_TYPE.NEWLINE:
                                tokens.append(token)
                                string_token = self.init_string_token()
                                state = STATE.STRING
                            case _:
                                tokens.append(token)
                last_pos = self.cursor
        return tokens