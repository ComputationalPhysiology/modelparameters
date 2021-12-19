from __future__ import print_function, division

from pyglet.gl import *
from pyglet import font

from plot_object import PlotObject
from util import strided_range, billboard_matrix
from util import get_direction_vectors
from util import dot_product, vec_sub, vec_mag
from ...core import S
from ...core.compatibility import is_sequence, range


class PlotAxes(PlotObject):

    def __init__(self, *args, **kwargs):
        # initialize style parameter
        style = kwargs.pop('style', '').lower()

        # allow alias kwargs to override style kwarg
        if kwargs.pop('none', None) is not None:
            style = 'none'
        if kwargs.pop('frame', None) is not None:
            style = 'frame'
        if kwargs.pop('box', None) is not None:
            style = 'box'
        if kwargs.pop('ordinate', None) is not None:
            style = 'ordinate'

        if style in ['', 'ordinate']:
            self._render_object = PlotAxesOrdinate(self)
        elif style in ['frame', 'box']:
            self._render_object = PlotAxesFrame(self)
        elif style in ['none']:
            self._render_object = None
        else:
            raise ValueError(("Unrecognized axes style %s.") % (style))

        # initialize stride parameter
        stride = kwargs.pop('stride', 0.25)
        try:
            stride = eval(stride)
        except TypeError:
            pass
        if is_sequence(stride):
            if len(stride) != 3:
                raise ValueError("length should be equal to 3")
            self._stride = stride
        else:
            self._stride = [stride, stride, stride]
        self._tick_length = float(kwargs.pop('tick_length', 0.1))

        # setup bounding box and ticks
        self._origin = [0, 0, 0]
        self.reset_bounding_box()

        def flexible_boolean(input, default):
            if input in [True, False]:
                return input
            if input in ['f', 'F', 'false', 'False']:
                return False
            if input in ['t', 'T', 'true', 'True']:
                return True
            return default

        # initialize remaining parameters
        self.visible = flexible_boolean(kwargs.pop('visible', ''), True)
        self._overlay = flexible_boolean(kwargs.pop('overlay', ''), True)
        self._colored = flexible_boolean(kwargs.pop('colored', ''), False)
        self._label_axes = flexible_boolean(
            kwargs.pop('label_axes', ''), False)
        self._label_ticks = flexible_boolean(
            kwargs.pop('label_ticks', ''), True)

        # setup label font
        self.font_face = kwargs.pop('font_face', 'Arial')
        self.font_size = kwargs.pop('font_size', 28)

        # this is also used to reinit the
        # font on window close/reopen
        self.reset_resources()

    def reset_resources(self):
        self.label_font = None

    def reset_bounding_box(self):
        self._bounding_box = [[None, None], [None, None], [None, None]]
        self._axis_ticks = [[], [], []]

    def draw(self):
        if self._render_object:
            glPushAttrib(GL_ENABLE_BIT | GL_POLYGON_BIT | GL_DEPTH_BUFFER_BIT)
            if self._overlay:
                glDisable(GL_DEPTH_TEST)
            self._render_object.draw()
            glPopAttrib()

    def adjust_bounds(self, child_bounds):
        b = self._bounding_box
        c = child_bounds
        for i in [0, 1, 2]:
            if abs(c[i][0]) is S.Infinity or abs(c[i][1]) is S.Infinity:
                continue
            b[i][0] = [min([b[i][0], c[i][0]]), c[i][0]][b[i][0] is None]
            b[i][1] = [max([b[i][1], c[i][1]]), c[i][1]][b[i][1] is None]
            self._recalculate_axis_ticks(i)

    def _recalculate_axis_ticks(self, axis):
        b = self._bounding_box
        if b[axis][0] is None or b[axis][1] is None:
            self._axis_ticks[axis] = []
        else:
            self._axis_ticks[axis] = strided_range(b[axis][0], b[axis][1],
                                                   self._stride[axis])

    def toggle_visible(self):
        self.visible = not self.visible

    def toggle_colors(self):
        self._colored = not self._colored


class PlotAxesBase(PlotObject):

    def __init__(self, parent_axes):
        self._p = parent_axes

    def draw(self):
        color = [([0.2, 0.1, 0.3], [0.2, 0.1, 0.3], [0.2, 0.1, 0.3]),
                 ([0.9, 0.3, 0.5], [0.5, 1.0, 0.5], [0.3, 0.3, 0.9])][self._p._colored]
        self.draw_background(color)
        self.draw_axis(2, color[2])
        self.draw_axis(1, color[1])
        self.draw_axis(0, color[0])

    def draw_background(self, color):
        pass  # optional

    def draw_axis(self, axis, color):
        raise NotImplementedError()

    def draw_text(self, text, position, color, scale=1.0):
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)

        if self._p.label_font is None:
            self._p.label_font = font.load(self._p.font_face,
                                           self._p.font_size,
                                           bold=True, italic=False)

        label = font.Text(self._p.label_font, text,
                          color=color,
                          valign=font.Text.BASELINE,
                          halign=font.Text.CENTER)

        glPushMatrix()
        glTranslatef(*position)
        billboard_matrix()
        scale_factor = 0.005 * scale
        glScalef(scale_factor, scale_factor, scale_factor)
        glColor4f(0, 0, 0, 0)
        label.draw()
        glPopMatrix()

    def draw_line(self, v, color):
        o = self._p._origin
        glBegin(GL_LINES)
        glColor3f(*color)
        glVertex3f(v[0][0] + o[0], v[0][1] + o[1], v[0][2] + o[2])
        glVertex3f(v[1][0] + o[0], v[1][1] + o[1], v[1][2] + o[2])
        glEnd()


class PlotAxesOrdinate(PlotAxesBase):

    def __init__(self, parent_axes):
        super(PlotAxesOrdinate, self).__init__(parent_axes)

    def draw_axis(self, axis, color):
        ticks = self._p._axis_ticks[axis]
        radius = self._p._tick_length / 2.0
        if len(ticks) < 2:
            return

        # calculate the vector for this axis
        axis_lines = [[0, 0, 0], [0, 0, 0]]
        axis_lines[0][axis], axis_lines[1][axis] = ticks[0], ticks[-1]
        axis_vector = vec_sub(axis_lines[1], axis_lines[0])

        # calculate angle to the z direction vector
        pos_z = get_direction_vectors()[2]
        d = abs(dot_product(axis_vector, pos_z))
        d = d / vec_mag(axis_vector)

        # don't draw labels if we're looking down the axis
        labels_visible = abs(d - 1.0) > 0.02

        # draw the ticks and labels
        for tick in ticks:
            self.draw_tick_line(axis, color, radius, tick, labels_visible)

        # draw the axis line and labels
        self.draw_axis_line(axis, color, ticks[0], ticks[-1], labels_visible)

    def draw_axis_line(self, axis, color, a_min, a_max, labels_visible):
        axis_line = [[0, 0, 0], [0, 0, 0]]
        axis_line[0][axis], axis_line[1][axis] = a_min, a_max
        self.draw_line(axis_line, color)
        if labels_visible:
            self.draw_axis_line_labels(axis, color, axis_line)

    def draw_axis_line_labels(self, axis, color, axis_line):
        if not self._p._label_axes:
            return
        axis_labels = [axis_line[0][::], axis_line[1][::]]
        axis_labels[0][axis] -= 0.3
        axis_labels[1][axis] += 0.3
        a_str = ['X', 'Y', 'Z'][axis]
        self.draw_text("-" + a_str, axis_labels[0], color)
        self.draw_text("+" + a_str, axis_labels[1], color)

    def draw_tick_line(self, axis, color, radius, tick, labels_visible):
        tick_axis = {0: 1, 1: 0, 2: 1}[axis]
        tick_line = [[0, 0, 0], [0, 0, 0]]
        tick_line[0][axis] = tick_line[1][axis] = tick
        tick_line[0][tick_axis], tick_line[1][tick_axis] = -radius, radius
        self.draw_line(tick_line, color)
        if labels_visible:
            self.draw_tick_line_label(axis, color, radius, tick)

    def draw_tick_line_label(self, axis, color, radius, tick):
        if not self._p._label_axes:
            return
        tick_label_vector = [0, 0, 0]
        tick_label_vector[axis] = tick
        tick_label_vector[{0: 1, 1: 0, 2: 1}[axis]] = [-1, 1, 1][
            axis] * radius * 3.5
        self.draw_text(str(tick), tick_label_vector, color, scale=0.5)


class PlotAxesFrame(PlotAxesBase):

    def __init__(self, parent_axes):
        super(PlotAxesFrame, self).__init__(parent_axes)

    def draw_background(self, color):
        pass

    def draw_axis(self, axis, color):
        raise NotImplementedError()
