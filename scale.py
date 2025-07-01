import wx
import wx.propgrid
import dataclasses


@dataclasses.dataclass
class Scale:
    v_min: float
    v_max: float
    v: float


class ScaleEditorPanel(wx.Panel):
    def __init__(self, parent, pos, size):
        super().__init__(parent, pos=pos, size=size)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.min_field = wx.TextCtrl(self, size=wx.Size(30, -1))
        sz.Add(self.min_field, 0, wx.EXPAND | wx.RIGHT, border=5)
        self.slider = wx.Slider(
            self,
            value=50,
            minValue=0,
            maxValue=100,
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS
        )
        self.slider.Bind(wx.EVT_SLIDER, self.on_slider)
        sz.Add(self.slider, 1, wx.EXPAND | wx.RIGHT, border=5)
        self.max_field = wx.TextCtrl(self, size=wx.Size(30, -1))
        sz.Add(self.max_field, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def set_value(self, value):
        self.min_field.SetValue(str(value.v_min))
        self.max_field.SetValue(str(value.v_max))
        self.slider.SetMin(value.v_min)
        self.slider.SetMax(value.v_max)
        self.slider.SetValue(value.v)
        self.slider.Update()
        

    def get_value(self):
        ...

class ScaleEditor(wx.propgrid.PGEditor):
    def CreateControls(self, propgrid, property, pos, size):
        ctrl = ScaleEditorPanel(propgrid, pos, size)
        ctrl.set_value(property.GetValue())
        return wx.propgrid.PGWindowList(ctrl)
    
    def DrawValue(self, dc: wx.DC, rect: wx.Rect, property, text):
        scale = property.GetValue()
        dc.DrawText(str(scale.v), rect.GetTopLeft())

    def OnEvent(
        self,
        propgrid: wx.propgrid.PropertyGrid,
        property: wx.propgrid.PGProperty,
        wnd_primary: wx.Window,
        event: wx.Event,
    ) -> bool:
        return True


class ScaleProperty(wx.propgrid.PGProperty):
    def GetValueAsString(self, argFlags = 0):
        return str(self.m_value.v)
