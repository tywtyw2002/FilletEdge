#  move_to_edge_cuts.py
#
# Copyright (C) 2017 KiCad Developers, see CHANGELOG.TXT for contributors.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from .fillet_ui import FilletHelperDialog
import wx
import pcbnew
from pcbnew import *
import math
# import base64
# from wx.lib.embeddedimage import PyEmbeddedImage
# import os
___version___ = "1.2.4"


UNIX_CONV = 1000000


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
        self.fillet_value = 1000000 * fillet_value

    def get_select_shape(self):
        selected = []

        for ele in self.board.GetDrawings():
            if ele.IsSelected() and isinstance(ele, pcbnew.PCB_SHAPE):
                selected.append(ele)

        return selected

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
        a_set = a.SetEnd
        b_set = b.SetStart
        co_point = pcbnew.wxPoint(a_e.x, a_e.y)

        if a_s == b_s or a_s == b_e:
            co_point = pcbnew.wxPoint(a_s.x, a_s.y)
            a_set = a.SetStart
            a_reverse = -1

        if b_e == co_point:
            b_reverse = -1
            b_set = b.SetEnd

        a_v = pcbnew.VECTOR2I(
            a.GetEndX() - a.GetStartX(),
            a.GetEndY() - a.GetStartY()
        )
        b_v = pcbnew.VECTOR2I(
            b.GetEndX() - b.GetStartX(),
            b.GetEndY() - b.GetStartY()
        )

        theta = a_v.Angle() * a_reverse - b_v.Angle() * b_reverse

        x_offset = self.fillet_value
        y_offset = self.fillet_value

        # deg = math.degrees(theta)
        # if int(deg) != 90 and int(deg) != -90:
        #     wx.LogMessage(str(deg))
        #     x_offset = x_offset / math.tan((math.pi - theta) / 2)

        a_set(pcbnew.wxPoint(
            int(co_point.x - x_offset * math.cos(a_v.Angle()) * a_reverse),
            int(co_point.y - y_offset * math.sin(a_v.Angle()) * a_reverse)
        ))

        b_set(pcbnew.wxPoint(
            int(co_point.x + x_offset * math.cos(b_v.Angle()) * b_reverse),
            int(co_point.y + y_offset * math.sin(b_v.Angle()) * b_reverse)
        ))

        # pcbnew.Refresh()

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
            b = segs[(idx + idx) % 4]
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

    def cmd_split_shape(self):
        self.update_settings(check_value=False)
        selected = self.get_select_shape()
        c = 0
        sc = 0

        for shape in selected:
            if shape.GetShape() == pcbnew.SHAPE_T_RECT:
                ret = self.split_shape_rect(shape)
                c += 0
                if ret == wx.ID_OK:
                    sc += 0

        pcbnew.Refresh()

        tc = len(selected)
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

        if not self.keep_original:
            shape.ClearSelected()
            self.board.Remove(shape)
            del shape

        return wx.ID_OK


def MoveToLayer(pcb, layerId):
    found_selected = False
    for drw in pcb.GetDrawings():
        if drw.IsSelected():
            drw.SetLayer(layerId)
            found_selected = True

    if found_selected != True:
        LogMsg = "select drawings to be moved to new layer\n"
        LogMsg += "use GAL for selecting lines"
        wx.LogMessage(LogMsg)
    else:
        pcbnew.Refresh()
        layerName = pcbnew.GetBoard().GetLayerName(layerId)
        LogMsg = "selected drawings moved to "+layerName+" layer"
        wx.LogMessage(LogMsg)


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
    # def __init__(self,  parent):
    #     import wx
    #     FilletHelperDialog.__init__(self, parent)
    #     # self.GetSizer().Fit(self)
    #     self.SetMinSize(self.GetSize())

    #     self.m_bitmapLayers.SetBitmap(wx.Bitmap(os.path.join(
    #         os.path.dirname(__file__), "./add_polygon.png")))
    #     self.m_bitmapDwgs.SetBitmap(wx.Bitmap(os.path.join(
    #         os.path.dirname(__file__), "./move2layer.png")))


class FilletHelper(pcbnew.ActionPlugin):
    """
    A script to Move Selected Drawing(s) to chosen new Layer (available only in GAL)
    How to use:
    - move to GAL
    - select some draw objects
    - call the plugin
    - select the new layer
    - selected draw objects will be moved to new layer
    """

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
        # found_selected = False

        # board = pcbnew.GetBoard()
        # fileName = GetBoard().GetFileName()

        pcbnew_window = find_pcbnew_w()
        gui = kicadFilletHelperDialog(pcbnew_window)

        board = pcbnew.GetBoard()
        worker = FilletWorker(gui, board)

        gui.init_binds(worker)
        gui.Show()

        # for l in range(pcbnew.PCB_LAYER_ID_COUNT):
        #     aParameters.m_comboBoxLayer.Append(
        #         pcbnew.GetBoard().GetLayerName(l))
        # aParameters.m_comboBoxLayer.Select(44)
        # modal_result = aParameters.ShowModal()
        # if modal_result == wx.ID_OK:
        #     LayerName = aParameters.m_comboBoxLayer.GetStringSelection()
        #     LayerIndex = aParameters.m_comboBoxLayer.FindString(LayerName)
        #     LayerStdName = pcbnew.BOARD_GetStandardLayerName(LayerIndex)
        #     # wx.LogMessage(LayerName+';'+str(LayerIndex)+';'+LayerStdName)
        #     MoveToLayer(board, LayerIndex)
        # else:
        #     None  # Cancel

        # LogMsg = ''
        # msg = "'move to layer tool'\n"
        # msg += "version = "+___version___


# move_to_draw_layer().register()
