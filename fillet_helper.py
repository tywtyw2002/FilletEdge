from .fillet_ui import FilletHelperDialog
import wx
import pcbnew
# from pcbnew import *
import math

___version___ = "1.0"


UNIX_CONV = 1000000


def get_angle(v):
    return math.atan2(v.y, v.x)


def from_degree(angle):
     return pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T)


class FilletWorker:

    def __init__(self, gui, board):
        self.board = board
        self.gui = gui
        self.move_to_cut = False
        self.keep_original = False
        self.fillet_value = -1
        self._tmp_split_shapes = {}

    def update_settings(self, check_value=True):
        self.move_to_cut = self.gui.cb_move_cut.GetValue()
        self.keep_original = self.gui.cb_keep_old.GetValue()

        if not check_value:
            return

        # fillet value
        fillet_value = self.gui.txt_fillet_value.GetValue().strip()

        try:
            fillet_value = float(fillet_value)
            if fillet_value <= 0:
                raise ValueError()
        except ValueError:
            wx.LogWarning('Invalid Fillet Value.\nFillet Value Must > 0.')

        # calc value w/ units
        unit = self.gui.select_unit.GetStringSelection().upper()
        if unit == 'MM':
            fillet_value = pcbnew.FromMM(fillet_value)
        elif unit == 'INCH':
            fillet_value = pcbnew.FromMils(fillet_value / 1000)
        elif unit == 'mil':
            fillet_value = pcbnew.FromMils(fillet_value)
        else:
            wx.LogWarning('Invalid Fillet Units.')
            raise

        self.fillet_value = fillet_value

    def get_select_shape(self):
        selected = []

        for ele in self.board.GetDrawings():
            if ele.IsSelected() and isinstance(ele, pcbnew.PCB_SHAPE):
                selected.append(ele)

        return selected

    def deselect_all(self):
        for ele in self.board.GetDrawings():
            if ele.IsSelected() and isinstance(ele, pcbnew.PCB_SHAPE):
                ele.ClearSelected()

    def do_fillet(self, a, b):
        # must be cw rotate
        # swap if ccw rotate
        theta = 0

        a_s = a.GetStart()
        a_e = a.GetEnd()

        b_s = b.GetStart()
        b_e = b.GetEnd()

        a_reverse = 1
        b_reverse = 1
        a_set = a.SetStart
        b_set = b.SetStart
        co_point = pcbnew.wxPoint(a_s.x, a_s.y)

        if a_e == b_s or a_e == b_e:
            co_point = pcbnew.wxPoint(a_e.x, a_e.y)
            a_set = a.SetEnd
            a_reverse = -1
        elif a_s != b_s and a_s != b_e:
            wx.LogWarning('Unable to Fillet, 2 lines not share any point.')
            return

        if b_e == co_point:
            b_reverse = -1
            b_set = b.SetEnd

        a_v = pcbnew.VECTOR2I(
            (a.GetEndX() - a.GetStartX()) * a_reverse,
            -(a.GetEndY() - a.GetStartY()) * a_reverse
        )
        b_v = pcbnew.VECTOR2I(
            (b.GetEndX() - b.GetStartX()) * b_reverse,
            -(b.GetEndY() - b.GetStartY()) * b_reverse
        )

        # theta = a_v.Angle() * a_reverse - b_v.Angle() * b_reverse
        # theta = a_v.Angle() - b_v.Angle()
        theta = get_angle(a_v) - get_angle(b_v)

        if theta < -math.pi:
            theta += math.pi * 2
        elif theta > math.pi:
            theta -= math.pi * 2

        deg = math.degrees(theta)

        # wx.LogMessage(f"A:{a_s}, {a_e}, {a_v.Angle()}, {a_v.getWxPoint()}, {a_reverse}\n")
        # wx.LogMessage(f"B:{b_s}, {b_e}, {b_v.Angle()}, {b_v.getWxPoint()}, {b_reverse}\n")
        # wx.LogMessage(f"C:{co_point}, T: {theta} ({deg})\n")

        offset = self.fillet_value
        # y_offset = self.fillet_value
        if int(deg) != 90 and int(deg) != -90:
            # wx.LogMessage(str(deg))
            offset = abs(offset * math.tan((math.pi - theta) / 2))

        a_point = pcbnew.wxPoint(
            int(co_point.x + offset * math.cos(get_angle(a_v))),
            int(co_point.y - offset * math.sin(get_angle(a_v)))
        )
        b_point = pcbnew.wxPoint(
            int(co_point.x + offset * math.cos(get_angle(b_v))),
            int(co_point.y - offset * math.sin(get_angle(b_v)))
        )

        a_set(pcbnew.VECTOR2I(a_point))
        b_set(pcbnew.VECTOR2I(b_point))

        # check length
        if a.GetLength() == 0:
            self.board.RemoveNative(a)

        if b.GetLength() == 0:
            self.board.RemoveNative(b)

        # set arc
        s_arc = pcbnew.PCB_SHAPE()
        s_arc.SetShape(pcbnew.SHAPE_T_ARC)

        c_v = a_v.Resize(1000000) + b_v.Resize(1000000)
        c_angle = get_angle(c_v)
        # wx.LogMessage(f"CT:{c_v.getWxPoint()}, T: {c_angle} ({math.degrees(c_angle)})\n")

        if offset == self.fillet_value:
            # 90 or -90
            s_arc.SetCenter(pcbnew.VECTOR2I(
                a_point.x + b_point.x - co_point.x,
                a_point.y + b_point.y - co_point.y
            ))
        else:
            coffset = abs(self.fillet_value / math.cos((math.pi - theta) / 2))
            s_arc.SetCenter(pcbnew.VECTOR2I(
                co_point.x + int(coffset * math.cos(c_angle)),
                co_point.y - int(coffset * math.sin(c_angle))
            ))

        # if theta > 0 and a_reverse > 0 and b_reverse > 0:
        #     s_arc.SetStart(a_point)
        # else:
        #     s_arc.SetStart(b_point)
        # if theta > 0 and c_angle > 0:
        # if deg >= 0 and a_reverse > 0 and b_reverse > 0:
        if deg < 0:
            s_arc.SetStart(pcbnew.VECTOR2I(a_point))
        else:
            s_arc.SetStart(pcbnew.VECTOR2I(b_point))

        s_arc.SetArcAngleAndEnd(from_degree(180 - abs(deg)))

        # if deg > 0:
        #     s_arc.SetArcAngleAndEnd(deg * 10)
        # else:
        #     s_arc.SetArcAngleAndEnd(deg * 10, True)

        s_arc.SetLayer(a.GetLayer())
        s_arc.SetWidth(a.GetWidth())

        if self.move_to_cut:
            a.SetLayer(44)
            a.SetWidth(150000)
            b.SetLayer(44)
            b.SetWidth(150000)
            s_arc.SetLayer(44)
            s_arc.SetWidth(150000)

        self.board.Add(s_arc)

        # pcbnew.Refresh()
    def calc_orientation(self, p, q, r):
        # https://www.geeksforgeeks.org/orientation-3-ordered-points/amp/
        val = ((q.y - p.y) * (r.x - q.x)) - ((q.x - p.x) * (r.y - q.y))
        if val > 0:
            return 1
        elif val < 0:
            return 2
        else:
            return 0

    def do_line_break(self, a, b):
        # check 2 lines co-point
        a_s = a.GetStart()
        a_e = a.GetEnd()
        b_s = b.GetStart()
        b_e = b.GetEnd()

        if a_s == b_s or a_s == b_e:
            wx.LogWarning('Unable to Break\n Two lines are co-point.')
            return

        # check 2 lines parallel.
        a_dt = a_e.x - a_s.x
        if a_dt == 0:
            slope_a = None
        else:
            slope_a = abs((a_e.y - a_s.y) / a_dt)

        b_dt = b_e.x - b_s.x
        if b_dt == 0:
            slope_b = None
        else:
            slope_b = abs((b_e.y - b_s.y) / b_dt)
        # slope_b = (b.GetEndY() - b.GetStartY()) / (b.GetEndX() - b.GetStartX())

        if slope_a == slope_b:
            wx.LogWarning('Unable to Break\n Two lines are parallel.')
            return

        ao1 = self.calc_orientation(a_s, a_e, b_s)
        ao2 = self.calc_orientation(a_s, a_e, b_e)
        bo1 = self.calc_orientation(b_s, b_e, a_s)
        bo2 = self.calc_orientation(b_s, b_e, a_e)

        if ao1 == ao2 or bo1 == bo2:
            wx.LogWarning('Unable to Break\n Two lines are not intersect.')
            return

        # Get Intersect Point
        t_u = (a_s.x - b_s.x) * (b_s.y - b_e.y) - (a_s.y - b_s.y) * (b_s.x - b_e.x)
        t_d = (a_s.x - a_e.x) * (b_s.y - b_e.y) - (a_s.y - a_e.y) * (b_s.x - b_e.x)
        t = t_u / t_d

        # u_u = (a_s.x - b_s.x) * (a_s.y - a_e.y) - (a_s.y - b_s.y) * (a_s.x - a_e.x)
        # u_d = (a_s.x - a_e.x) * (b_s.y - b_e.y) - (a_s.y - a_e.y) * (b_s.x - b_e.x)
        # u = u_u / u_d

        x = a_s.x + t * (a_e.x - a_s.x)
        y = a_s.y + t * (a_e.y - a_s.y)

        # c = pcbnew.wxPoint(int(x), int(y))
        c = pcbnew.VECTOR2I(int(x), int(y))
        # wx.LogMessage(f"{c}\n")
        # do break
        self._do_lint_break(a, c)
        self._do_lint_break(b, c)

    def _do_lint_break(self, line, c):
        start = line.GetStart()
        end = line.GetEnd()
        end_copy = pcbnew.VECTOR2I(end.x, end.y)

        layer = line.GetLayer()
        width = line.GetWidth()

        if self.move_to_cut:
            line.SetLayer(44)
            line.SetWidth(150000)
            layer = 44
            width = 150000

        if start != c and end != c:
            line.SetEnd(c)

            new_line = pcbnew.PCB_SHAPE()
            new_line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            new_line.SetLayer(layer)
            new_line.SetWidth(width)

            new_line.SetStart(c)
            new_line.SetEnd(end_copy)
            self.board.Add(new_line)

    def do_simple_fillet(self, a, b):
        # Simple Fillet at 90 degree
        # A.end == B.start
        point = a.GetEnd()

        v_x = a.GetEndX() - a.GetStartX()
        v_y = a.GetEndY() - a.GetStartY()
        vec = pcbnew.VECTOR2I(v_x, v_y)

        if a.GetStartX() == a.GetEndX():
            # vertical line
            a.SetEndY(point[1] + self.fillet_value)
            b.SetStartX(point[0] + self.fillet_value)
        else:
            # Horizontal
            a.SetEndX(point[0] - self.fillet_value)
            b.SetStartY(point[1] - self.fillet_value)

    def do_rect_fillet(self, shape):
        # Rect fillet. Max fillet Value <= rect width.
        rect_width = abs(shape.GetStartX() - shape.GetEndX())
        rect_height = abs(shape.GetStartY() - shape.GetEndY())

        rect_min_lenght = min(rect_width, rect_height)

        if self.fillet_value > rect_min_lenght:
            wx.LogWarning('Unable to Fillet, Fillet Value greater than Rect min edge length.')
            return

        ret = self.split_shape_rect(shape)
        if ret != wx.ID_OK:
            return ret

        segs = self._tmp_split_shapes

        for idx in range(4):
            a = segs[idx]
            b = segs[(idx + 1) % 4]
            # wx.LogMessage(f"{idx}, A:{a}, B: {b}\n")
            # wx.LogMessage(f"{idx}\n")
            self.do_fillet(a, b)

        pcbnew.Refresh()

    def cmd_fillet_shape(self):
        self.update_settings()
        selected = self.get_select_shape()

        if not selected:
            wx.LogWarning('Unable to Fillet, not shape selected.')
            return

        if len(selected) == 1:
            if selected[0].GetShape() == pcbnew.SHAPE_T_RECT:
                return self.do_rect_fillet(selected[0])
            else:
                wx.LogWarning('Unable to Fillet, not enough shapes selected.')
                return

        self.do_fillet(selected[0], selected[1])
        pcbnew.Refresh()

    def cmd_break_line(self):
        self.update_settings(check_value=False)
        selected = self.get_select_shape()

        if not selected:
            wx.LogWarning('Unable to Break, no line selected.')
            return

        if len(selected) != 2:
            wx.LogWarning('Unable to Break\n Need two lines to break.')
            return

        self.do_line_break(selected[0], selected[1])
        pcbnew.Refresh()

    def cmd_split_shape(self):
        self.update_settings(check_value=False)
        selected = self.get_select_shape()
        tc = len(selected)
        c = 0
        sc = 0

        for shape in selected:
            if shape.GetShape() == pcbnew.SHAPE_T_RECT:
                ret = self.split_shape_rect(shape)
                c += 1
                if ret == wx.ID_OK:
                    sc += 1

        pcbnew.Refresh()

        if c == sc and c == tc:
            # wx.LogMessage('All Selected Shape are splited.')
            return

        msg = ["Done"]

        if c != tc:
            msg.append(f"Vaild Rect: {c}/{tc}")
        if c != sc:
            msg.append(f"Success Split: {sc}/{c}")

        wx.LogMessage("\n".join(msg))

    def split_shape_rect(self, shape):
        if (not isinstance(shape, pcbnew.PCB_SHAPE)
                and shape.GetShape() != pcbnew.SHAPE_T_RECT):
            wx.LogWarning('Only Rect Shape can split.')
            return wx.ID_NO

        layer = shape.GetLayer()
        line_width = shape.GetWidth()

        # tmp storage shapes for fillet
        self._tmp_split_shapes = {}

        if self.move_to_cut:
            layer = 44
            line_width = 150000

        points = list(shape.GetRectCorners())
        points.append(points[0])

        for idx in range(4):
            s_seg = pcbnew.PCB_SHAPE()
            s_seg.SetShape(pcbnew.SHAPE_T_SEGMENT)

            s_seg.SetStart(points[idx])
            s_seg.SetEnd(points[idx + 1])

            s_seg.SetLayer(layer)
            s_seg.SetWidth(line_width)

            self.board.Add(s_seg)
            self._tmp_split_shapes[idx] = s_seg
            # wx.LogMessage(f"{idx}, {s_seg}\n")

        if not self.keep_original:
            shape.ClearSelected()
            self.board.RemoveNative(shape)
            del shape

        return wx.ID_OK


def find_pcbnew_w():
    windows = wx.GetTopLevelWindows()
    pcbneww = [w for w in windows if "pcbnew" in w.GetTitle().lower()]
    if len(pcbneww) != 1:
        return None
    return pcbneww[0]


class kicadFilletHelperDialog(FilletHelperDialog):
    def SetSizeHints(self, sz1, sz2):
        if wx.__version__ < '4.0':
            self.SetSizeHintsSz(sz1, sz2)
        else:
            super(kicadFilletHelperDialog, self).SetSizeHints(sz1, sz2)

    def init_binds(self, worker):
        self.worker = worker

        self.btn_close.Bind(
            wx.EVT_BUTTON,
            lambda e: self.Show(False)
        )

        self.btn_split.Bind(
            wx.EVT_BUTTON,
            lambda e: worker.cmd_split_shape()
        )

        self.btn_fillet.Bind(
            wx.EVT_BUTTON,
            lambda e: worker.cmd_fillet_shape()
        )

        self.btn_break.Bind(
            wx.EVT_BUTTON,
            lambda e: worker.cmd_break_line()
        )

        self.btn_unselect.Bind(
            wx.EVT_BUTTON,
            lambda e: worker.deselect_all()
        )



class FilletHelper(pcbnew.ActionPlugin):

    def defaults(self):
        """
        Method defaults must be redefined
        self.name should be the menu label to use
        self.category should be the category (not yet used)
        self.description should be a comprehensive description
          of the plugin
        """
        import os
        self.name = "Fillet Helper"
        self.category = "Modify PCB"
        self.description = "Fillet Lines, Split Rect."
        self.icon_file_name = os.path.join(
            os.path.dirname(__file__),
            "./fillet.png"
        )
        self.show_toolbar_button = True

    def Run(self):
        pcbnew_window = find_pcbnew_w()
        gui = kicadFilletHelperDialog(pcbnew_window)

        board = pcbnew.GetBoard()
        worker = FilletWorker(gui, board)

        gui.init_binds(worker)
        gui.ToggleWindowStyle(wx.STAY_ON_TOP)
        gui.Show()

