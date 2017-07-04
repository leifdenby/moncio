from sympy import Symbol
import numpy as np

from xml.etree.ElementTree import Element
from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """

def make_config_with_default_groups(fields):
    groups_by_dimension = [[],[],[]]

    for field in fields:
        dims = len(field.shape) - 1
        groups_by_dimension[dims].append(field)

    field_groups = [MoncConfigFieldGroup("{}d".format(n+1), field) for (n, field) in enumerate(groups_by_dimension)]

    field_groups = filter(lambda g: len(g.fields) > 0, field_groups)

    return MoncConfig(field_groups=field_groups)


class MoncConfigFieldGroup:
    def __init__(self, name, fields):
        self.fields = fields
        self.name = name


class MoncConfig():
    def __init__(self, field_groups):
        self.field_groups = field_groups

    def write(self, xml_filename):
        pass

    def _get_server_configuration(self):
        server_configuration = Element("server-configuration")
        thread_pool = Element("thread_pool")
        thread_pool.set("number", "100")
        server_configuration.append(thread_pool)

        return server_configuration

    def _get_data_groups(self):
        group_nodes = []

        for group in self.field_groups:
            group_node = Element("group")
            group_node.set("name", group.name)

            for f in group.fields:
                field_node = Element("member")
                field_node.set("name", f.name)
                group_node.append(field_node)
            
            group_nodes.append(group_node)

        return group_nodes

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

    @property
    def shape(self):
        return np.ones((3,))/2**self.coarsening


if __name__ == "__main__":
    w = Field('w')
    v = Field('v')

    wv = w*v

    print wv
    w_prime_horizontal = w.mean(axis=0) - w
    w_prime_horizontal.name = "w_prime_horizontal"
    # print w.mean(axis=0).coarsen(level=1) - w

    fields = [w, v, w_prime_horizontal]
    monc_configuration = make_config_with_default_groups(fields)

    print monc_configuration.render_xml()
