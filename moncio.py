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
    def __init__(self, name, inv_shape=np.ones((3,)), op=None, child_nodes=[], op_arguments=[]):
        self.name = name
        self.op = op
        self.inv_shape = inv_shape
        self.child_nodes = child_nodes
        self.op_arguments = op_arguments

    def __add__(self, other):
        assert np.all(self.inv_shape == other.inv_shape)
        return Field("%s + %s" % (self.name, other.name), op="ADD", child_nodes=(self, other), inv_shape=self.inv_shape)

    def __mul__(self, other):
        assert np.all(self.inv_shape == other.inv_shape)
        return Field("%s * %s" % (self.name, other.name), op="MUL", child_nodes=(self, other), inv_shape=self.inv_shape)

    def __sub__(self, other):
        assert np.all(self.inv_shape == other.inv_shape)
        return Field("%s - %s" % (self.name, other.name), op="SUB", child_nodes=(self, other), inv_shape=self.inv_shape)

    def __str__(self):
        if not self.op is None:
            args = self.op_arguments and ":" + ",".join(["{}={}".format(k, v) for (k, v) in self.op_arguments.items()]) or ""
            return "{}{} ({})".format(self.op, args, ", ".join([str(n) for n in self.child_nodes]))
        else:
            return self.name

    def mean(self, axis):
        assert(self.inv_shape[axis] != np.inf)
        inv_shape = np.array(self.inv_shape)
        inv_shape[axis] = np.inf
        return Field("mean", op="MEAN", child_nodes=[self,], op_arguments=dict(axis=axis), inv_shape=inv_shape)

    def repeat(self, axis):
        assert(self.inv_shape[axis] == np.inf)
        inv_shape = np.array(self.inv_shape)
        inv_shape[axis] = 1
        return Field("repeat", op="REPEAT", child_nodes=[self,], op_arguments=dict(axis=axis), inv_shape=inv_shape)

    def coarsen(self, level):
        inv_shape = np.ndarray(self.inv_shape)*2**level
        return Field("coarse", op="COARSEN", child_nodes=[self,], op_arguments=dict(level=level), inv_shape=inv_shape)

    def build_xml(self):
        raise NotImplementedError

    @property
    def shape(self):
        shape = np.ones((3,))/self.inv_shape
        shape = filter(lambda d: d != 0.0, shape)
        return shape


if __name__ == "__main__":
    w = Field('w')
    v = Field('v')

    wv = w*v

    print wv
    w_horizontal_mean = w.mean(axis=0).mean(axis=1)
    w_horizontal_mean.name = "w_horizonal_mean"
    # print w.mean(axis=0).coarsen(level=1) - w

    w_prime_horz = w_horizontal_mean.repeat(axis=1).repeat(axis=0) - w
    w_prime_horz.name = "w_prime_horz"

    fields = [w, v, w_horizontal_mean, w_prime_horz]
    monc_configuration = make_config_with_default_groups(fields)

    print monc_configuration.render_xml()
