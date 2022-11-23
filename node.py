class NodeLinks():
    def __init__(self):
        self.help = ''
        self.index = ''
        self.prev = ''
        self.next = ''
        self.toc = ''

class Node:
    def __init__(self, database):
        self.database = database
        self.properties = {}
        self.properties['smartwrap'] = False
        self.properties['wordwrap'] = False
        self.properties['proportional'] = False
        self.properties['font'] = "Topaz"
        self.properties['font-size'] = 16
        self.text = ''

    def get_property(self, key: str, default_value = ''):
        if key in self.properties:
            return self.properties[key]
        else:
            return default_value

    def write_as_html(self, path: str, dir: str):
        html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><title>' + self.get_property('title') + '</title>\n'

        html += '<link rel="stylesheet" href="../style.css">\n'
        html += '<script type="text/javascript" src="../functions.js"></script>\n'

        # Enable communication between the application and Javascript
        html += '''<script src='qrc:///qtwebchannel/qwebchannel.js'></script>\n'''

        html += '</head><body><p id="' + self.get_property('name') + '" class="node ' + self.get_property('name') + '">' + self.text + '</p></body></html>'

        # Write as html files (make sure to use the right extension, otherwise webkit.load_uri() sometimes reads them as raw files)
        with open(dir + '/' + path + self.get_property('name') + '.html', 'w') as output_file:
            output_file.write(html)