#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.0.3 on Sat Dec 11 02:41:57 2021
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class FilletHelperDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: FilletHelperDialog.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetSize((400, 300))
        self.SetTitle("frame")

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)

        sizer_4 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, "Fillet Settings"), wx.VERTICAL)
        sizer_3.Add(sizer_4, 0, wx.EXPAND, 0)

        sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4.Add(sizer_8, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Units:")
        label_1.SetMinSize((80, 16))
        sizer_8.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.select_unit = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=["mm", "mil", "inch"], style=wx.CB_DROPDOWN)
        self.select_unit.SetMinSize((80, 25))
        self.select_unit.SetSelection(0)
        sizer_8.Add(self.select_unit, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4.Add(sizer_9, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Value:")
        label_2.SetMinSize((80, 16))
        sizer_9.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.txt_fillet_value = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.txt_fillet_value.SetMinSize((80, 25))
        sizer_9.Add(self.txt_fillet_value, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_5 = wx.StaticBoxSizer(wx.StaticBox(self.panel_1, wx.ID_ANY, "Options"), wx.VERTICAL)
        sizer_3.Add(sizer_5, 0, wx.EXPAND, 0)

        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(sizer_6, 1, wx.EXPAND, 0)

        sizer_6.Add((10, 25), 0, 0, 0)

        self.cb_move_cut = wx.CheckBox(self.panel_1, wx.ID_ANY, "Move to Cuts Layer")
        self.cb_move_cut.SetValue(1)
        sizer_6.Add(self.cb_move_cut, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(sizer_7, 1, wx.EXPAND, 0)

        sizer_7.Add((10, 25), 0, 0, 0)

        self.cb_keep_old = wx.CheckBox(self.panel_1, wx.ID_ANY, "Keep Original Shape (Split)")
        self.cb_keep_old.SetValue(0)
        sizer_7.Add(self.cb_keep_old, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)

        sizer_2.Add((120, 20), 0, 0, 0)

        self.btn_fillet = wx.Button(self.panel_1, wx.ID_ANY, "Fillet")
        self.btn_fillet.SetMinSize((100, 30))
        sizer_2.Add(self.btn_fillet, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        sizer_2.Add((120, 20), 0, 0, 0)

        self.btn_split = wx.Button(self.panel_1, wx.ID_ANY, "Split Rect")
        self.btn_split.SetMinSize((100, 30))
        sizer_2.Add(self.btn_split, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.btn_break = wx.Button(self.panel_1, wx.ID_ANY, "Break Line")
        self.btn_break.SetMinSize((100, 30))
        sizer_2.Add(self.btn_break, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.btn_unselect = wx.Button(self.panel_1, wx.ID_ANY, "Unselect All")
        self.btn_unselect.SetMinSize((100, 30))
        sizer_2.Add(self.btn_unselect, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        sizer_2.Add((120, 80), 0, 0, 0)

        self.btn_close = wx.Button(self.panel_1, wx.ID_ANY, "close")
        self.btn_close.SetMinSize((-1, 30))
        sizer_2.Add(self.btn_close, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()
        # end wxGlade