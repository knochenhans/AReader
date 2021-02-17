import unittest
from areader import Database, Node


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


if __name__ == '__main__':
    unittest.main()
