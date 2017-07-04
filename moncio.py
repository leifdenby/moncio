from sympy import Symbol
from xml.etree.ElementTree import Element
from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """


class MoncConfig():
    def __init__(self, fields):
        self.fields = fields

    def write(self, xml_filename):
        pass

    def _get_server_configuration(self):
        server_configuration = Element("server-configuration")
        thread_pool = Element("thread_pool")
        thread_pool.set("number", "100")
        server_configuration.append(thread_pool)

        return server_configuration

    def _get_data_groups(self):
        group = Element("group")
        group.set("name", "all_fields_group")

        for f in self.fields:
            field_node = Element("member")
            field_node.set("name", f.name)
            group.append(field_node)

        return [group, ]

    def _get_data_writing(self, filename, write_time_frequency, title):
        data_writing = Element('data-writing')
        file = Element("file")
        file.set("filename", filename)
        file.set("write_time_frequency", "%f" % write_time_frequency)
        file.set("title", title)
        data_writing.append(file)

        return data_writing

    def render_xml(self):
        root_node = Element("io-configuration")
        root_node.append(self._get_server_configuration())

        for group in self._get_data_groups():
            root_node.append(group)

        # TODO
        root_node.append(self._get_data_writing("diagnostics.nc", write_time_frequency=100, title="default_title"))

        rough_string = ElementTree.tostring(root_node, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


class Field():
    def __init__(self, name, coarsening=0, op=None, child_nodes=[], op_arguments=[]):
        self.name = name
        self.op = op
        self.coarsening = coarsening
        self.child_nodes = child_nodes
        self.op_arguments = op_arguments

    def __add__(self, other):
        assert self.coarsening == other.coarsening
        return Field("%s + %s" % (self.name, other.name), op="ADD", child_nodes=(self, other))

    def __mul__(self, other):
        assert self.coarsening == other.coarsening
        return Field("%s * %s" % (self.name, other.name), op="MUL", child_nodes=(self, other))

    def __sub__(self, other):
        assert self.coarsening == other.coarsening
        return Field("%s - %s" % (self.name, other.name), op="SUB", child_nodes=(self, other))

    def __str__(self):
        if not self.op is None:
            args = self.op_arguments and ":" + ",".join(["{}={}".format(k, v) for (k, v) in self.op_arguments.items()]) or ""
            return "{}{} ({})".format(self.op, args, ", ".join([str(n) for n in self.child_nodes]))
        else:
            return self.name

    def mean(self, axis):
        return Field("mean", op="MEAN", child_nodes=[self,], op_arguments=dict(axis=axis))

    def coarsen(self, level):
        return Field("coarse", op="COARSEN", child_nodes=[self,], op_arguments=dict(level=level), coarsening=self.coarsening+1)

    def build_xml(self):
        raise NotImplementedError


if __name__ == "__main__":
    w = Field('w')
    v = Field('v')

    wv = w*v

    print wv
    w_prime_horizontal = w.mean(axis=0) - w
    w_prime_horizontal.name = "w_prime_horizontal"
    # print w.mean(axis=0).coarsen(level=1) - w

    fields = [w, v, w_prime_horizontal]
    monc_configuration = MoncConfig(fields=fields)

    print monc_configuration.render_xml()
