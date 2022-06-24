import copy
from enum import Enum, auto
import string


class TOKEN_TYPE(Enum):
    UNDEFINED = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    SEPARATOR = auto()
    OPERATOR = auto()
    LITERAL = auto()


class Token():
    def __init__(self, line: int = 0, type: TOKEN_TYPE = TOKEN_TYPE.UNDEFINED, value: str = ''):
        self.line = line
        self.type = type
        self.value = value


class STATE(Enum):
    ADD = auto()
    INIT = auto()
    READ = auto()


class LAST_FOUND(Enum):
    ALNUM = auto()
    PUNCT = auto()
    WHITESPACE = auto()


class Lexer():
    def __init__(self):
        pass

    def load_file(self, filename: str) -> list[str]:
        with open(filename, 'r') as file:
            return file.read().splitlines()

    def lex_file(self, filename: str) -> list[Token]:
        return self.lex(self.load_file(filename))

    def lex(self, lines: list[str]) -> list[Token]:
        tokens = []

        #lines = self.load_file(filename)

        state = STATE.INIT
        last_found = LAST_FOUND.WHITESPACE

        current_token = None

        in_string = False
        in_command = False
        escaped = False

        for line_idx, line in enumerate(lines):

            c_idx = 0

            running = True

            while running:
                c = ''

                if c_idx == len(line):
                    # Add last token
                    state = STATE.ADD
                    running = False
                else:
                    c = line[c_idx]

                match state:
                    case STATE.ADD:
                        # Close and add current token
                        if current_token:
                            if current_token.value:
                                tokens.append(current_token)

                                current_token = None

                        state = STATE.INIT

                    case STATE.INIT:
                        # Prepare new token:
                        if not current_token:
                            current_token = Token(line_idx)
                        state = STATE.READ

                    case STATE.READ:
                        if in_string:
                            if c == '"':
                                in_string = False

                                if current_token:
                                    if current_token.value:
                                        tokens.append(current_token)

                                current_token = Token(line_idx, TOKEN_TYPE.SEPARATOR, c)

                                state = STATE.ADD
                            else:
                                if current_token:
                                    current_token.value += c
                                    current_token.type = TOKEN_TYPE.LITERAL

                            c_idx += 1

                        elif in_command:
                            if c.isspace():
                                state = STATE.ADD
                                last_found = LAST_FOUND.WHITESPACE

                            elif c.isalpha():
                                if current_token:
                                    current_token.type = TOKEN_TYPE.IDENTIFIER
                                    match current_token.type:
                                        case _:
                                            current_token.value += c
                                last_found = LAST_FOUND.ALNUM

                            elif c.isnumeric():
                                if current_token:
                                    match current_token.type:
                                        case TOKEN_TYPE.NUMBER | TOKEN_TYPE.IDENTIFIER:
                                            current_token.value += c
                                        case _:
                                            current_token.type = TOKEN_TYPE.NUMBER
                                            current_token.value += c
                                last_found = LAST_FOUND.ALNUM

                            elif c in string.punctuation:
                                match c:
                                    # case '*' | '+' | '/' | '=' | '<' | '>':
                                    #     if current_token:
                                    #         if current_token.value:
                                    #             tokens.append(current_token)

                                    #     current_token = Token(line_idx, TOKEN_TYPE.OPERATOR, c)

                                    #     state = STATE.ADD

                                    # case '.':
                                    #     if current_token:
                                    #         if current_token.value and current_token.type == TOKEN_TYPE.NUMBER:
                                    #             current_token.value += c

                                    # case '-':
                                    #     if current_token:
                                    #         if current_token.value:
                                    #             tokens.append(current_token)

                                    #     current_token = Token(line_idx, TOKEN_TYPE.OPERATOR, c)

                                    #     state = STATE.ADD

                                    # case ',' | ';' | ':':
                                    #     if current_token:
                                    #         if current_token.value:
                                    #             tokens.append(current_token)

                                    #     current_token = Token(line_idx, TOKEN_TYPE.SEPARATOR, c)

                                    #     state = STATE.ADD

                                    # case '$':
                                    #     match last_found:
                                    #         case LAST_FOUND.ALNUM:
                                    #             if current_token:
                                    #                 current_token.value += c

                                    #                 state = STATE.ADD
                                    case '"':
                                        if not in_string:
                                            in_string = True

                                            if current_token:
                                                if current_token.value:
                                                    tokens.append(current_token)

                                                current_token.line = line_idx
                                                current_token.type = TOKEN_TYPE.SEPARATOR
                                                current_token.value = c

                                                state = STATE.ADD

                                            # if current_token:
                                            #     current_token.type = TOKEN_TYPE.LITERAL
                                        else:
                                            in_string = False

                                    case '{' | '}':
                                        match last_found:
                                            case LAST_FOUND.WHITESPACE | LAST_FOUND.PUNCT:
                                                if current_token:
                                                    current_token.value = c
                                                    current_token.type = TOKEN_TYPE.SEPARATOR

                                                state = STATE.ADD

                                            case LAST_FOUND.ALNUM:
                                                if current_token:
                                                    tokens.append(current_token)

                                                current_token = Token(line_idx, TOKEN_TYPE.SEPARATOR, c)

                                                state = STATE.ADD
                                        
                                        if c == '}':
                                            in_command = False

                                last_found = LAST_FOUND.PUNCT

                            c_idx += 1

                        elif escaped:
                            if current_token:
                                current_token.value += c
                                current_token.type = TOKEN_TYPE.LITERAL
                            escaped = False
                            
                            c_idx += 1

                        else:
                            # Regular text
                            if c == '\\':
                                escaped = True
                            elif c == '@':
                                in_command = True

                                if current_token:
                                    if current_token.value:
                                        tokens.append(current_token)

                                current_token = Token(line_idx, TOKEN_TYPE.IDENTIFIER, c)

                                state = STATE.ADD
                            else:
                                if current_token:
                                    current_token.value += c
                                    current_token.type = TOKEN_TYPE.LITERAL

                            c_idx += 1

        return tokens
