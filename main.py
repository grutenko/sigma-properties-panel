import wx

from properties import PropertiesPanel

if __name__ == "__main__":
    app = wx.App(0)
    f = wx.Frame(None)
    sz = wx.BoxSizer(wx.VERTICAL)
    p = PropertiesPanel(f)
    sz.Add(p, 1, wx.EXPAND)
    f.SetSizer(sz)
    f.Layout()
    f.Show()
    app.MainLoop()