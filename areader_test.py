import unittest
from areader import Database, Node
from lexer import *
from textwrap import dedent


class DatabaseTests(unittest.TestCase):

    def test_pseudo_tags_simple1(self):
        database = Database()
        node = Node(database)
        node.text = "<fg back>test<fg text>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), '<span class="fg-back">test</span>')

    def test_pseudo_tags_simple2(self):
        database = Database()
        node = Node(database)
        node.text = "<fg back><fg highlight><fg text>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), '<span class="fg-back"></span><span class="fg-highlight"></span>')

    def test_pseudo_tags_simple3(self):
        database = Database()
        node = Node(database)
        node.text = "<fg back><fg highlight><fg text><bg shine><bg back>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), '<span class="fg-back"></span><span class="fg-highlight"></span><span class="bg-shine"></span>')

    def test_pseudo_tags_nested1(self):
        database = Database()
        node = Node(database)
        node.text = "<fg back><bg text><fg text><bg back>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), '<span class="fg-back"></span><span class="bg-text fg-back"></span><span class="bg-text"></span>')

    def test_pseudo_tags_nested2(self):
        database = Database()
        node = Node(database)
        node.text = "bla<fg back>test<bg text>background<fg text>test<bg back>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), 'bla<span class="fg-back">test</span><span class="bg-text fg-back">background</span><span class="bg-text">test</span>')

    def test_pseudo_tags_nested3(self):
        database = Database()
        node = Node(database)
        node.text = "<fg back><bg text>background<fg text><bg back>"

        database.nodes.append(node)
        self.assertEqual(database.replace_pseudo_tags(
            node.text), '<span class="fg-back"></span><span class="bg-text fg-back">background</span><span class="bg-text"></span>')

    def test_find_command(self):
        self.maxDiff = None

        input = '''\@{b}		Turns @{b}bold@{ub} on.
\@{ub}		Turns @{b}bold@{ub} off.
 
@{"  Index  " beep 0}
x@{i}italic@{ui}x
x@{u}underline@{uu}x'''
        output = '''@{b}		Turns <b>bold</b> on.
@{ub}		Turns <b>bold</b> off.
 
<a href="javascript:beep()">  Index  </a>
x<i>italic</i>x
x<span class="u">underline</span>x'''

        database = Database()
        self.assertEqual(database.find_command(input), output)
        # print(database.find_command(input))

    def test_breakup_command_empty(self):
        database = Database()
        output = []
        self.assertEqual(database.breakup_command(
            ''), output)

    def test_breakup_command_simple(self):
        database = Database()
        output = ['test']
        self.assertEqual(database.breakup_command(
            'test'), output)

    def test_breakup_command(self):
        database = Database()
        output = ['test', 'is', 'a', 'is a', 'test']
        self.assertEqual(database.breakup_command(
            'test "is" a "is a" test'), output)

    def test_inline_commands(self):
        # TODO: Add more tests
        database = Database()
        output = '<b>Amigaguide(R)</b>'
        self.assertEqual(database.process_inline_command('amigaguide'), output)


class LexerTests(unittest.TestCase):

    def test_lex1(self):
        lexer = Lexer()

        text = '''This is a test.\n    @{mylink "Another node" "node2"}'''

        tokens = lexer.lex(text)

        self.assertEqual(tokens[0].value, 'This is a test.\n    ')
        self.assertEqual(tokens[0].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[1].value, '@')
        self.assertEqual(tokens[1].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[2].value, '{')
        self.assertEqual(tokens[2].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[3].value, 'mylink')
        self.assertEqual(tokens[3].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[4].value, 'Another node')
        self.assertEqual(tokens[4].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[5].value, 'node2')
        self.assertEqual(tokens[5].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[6].value, '}')
        self.assertEqual(tokens[6].type, TOKEN_TYPE.SEPARATOR)

    def test_lex2(self):
        lexer = Lexer()

        text = '''- @{" MUI " LINK "MUI"} 3.x (am besten MUI 3.6)'''

        tokens = lexer.lex(text)

        self.assertEqual(tokens[0].value, '- ')
        self.assertEqual(tokens[0].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[1].value, '@')
        self.assertEqual(tokens[1].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[2].value, '{')
        self.assertEqual(tokens[2].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[3].value, ' MUI ')
        self.assertEqual(tokens[3].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[4].value, 'LINK')
        self.assertEqual(tokens[4].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[5].value, 'MUI')
        self.assertEqual(tokens[5].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[6].value, '}')
        self.assertEqual(tokens[6].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[7].value, ' 3.x (am besten MUI 3.6)')
        self.assertEqual(tokens[7].type, TOKEN_TYPE.STRING)

    def test_lex3(self):
        lexer = Lexer()

        text = '''Dies ist @{b}kein offizieller@{ub} FTP-Server'''

        tokens = lexer.lex(text)

        self.assertEqual(tokens[0].value, 'Dies ist ')
        self.assertEqual(tokens[0].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[1].value, '@')
        self.assertEqual(tokens[1].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[2].value, '{')
        self.assertEqual(tokens[2].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[3].value, 'b')
        self.assertEqual(tokens[3].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[4].value, '}')
        self.assertEqual(tokens[4].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[5].value, 'kein offizieller')
        self.assertEqual(tokens[5].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[6].value, '@')
        self.assertEqual(tokens[6].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[7].value, '{')
        self.assertEqual(tokens[7].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[8].value, 'ub')
        self.assertEqual(tokens[8].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[9].value, '}')
        self.assertEqual(tokens[9].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[10].value, ' FTP-Server')
        self.assertEqual(tokens[10].type, TOKEN_TYPE.STRING)

    def test_lex4(self):
        lexer = Lexer()

        text = '''This is an example of a \@{bold "bold"} macro@{ub}.'''

        tokens = lexer.lex(text)

        self.assertEqual(tokens[0].value, 'This is an example of a \@{bold "bold"} macro')
        self.assertEqual(tokens[0].type, TOKEN_TYPE.STRING)
        self.assertEqual(tokens[1].value, '@')
        self.assertEqual(tokens[1].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[2].value, '{')
        self.assertEqual(tokens[2].type, TOKEN_TYPE.SEPARATOR)
        self.assertEqual(tokens[3].value, 'ub')
        self.assertEqual(tokens[3].type, TOKEN_TYPE.IDENTIFIER)
        self.assertEqual(tokens[4].value, '}')
        self.assertEqual(tokens[4].type, TOKEN_TYPE.SEPARATOR)


if __name__ == '__main__':
    unittest.main()
