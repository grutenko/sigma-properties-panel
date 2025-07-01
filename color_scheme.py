import wx
import wx.propgrid
import dataclasses
import json
from typing import List

from ruler import RulerWidget

@dataclasses.dataclass
class ColorScheme:
    schema: List

    def min_value(self):
        return min(map(lambda o: o[3], self.schema))

    def max_value(self):
        return max(map(lambda o: o[3], self.schema))

    @classmethod
    def basic(cls, c0: wx.Colour, p0: float, c1: wx.Colour, p1: float):
        return cls(
            schema=[
                (c0.GetRed(), c0.GetGreen(), c0.GetBlue(), p0),
                (c1.GetRed(), c1.GetGreen(), c1.GetBlue(), p1),
            ]
        )

    def range(self):
        return abs(self.min_value() - self.max_value())

    def save(self, f):
        f.write(self.to_string())

    @classmethod
    def load(cls, f):
        s = f.read()
        return cls.from_string(s)

    def to_string(self):
        schema = list(map(lambda o: list(o), self.schema))
        return json.dumps(schema)
    
    @classmethod
    def from_string(cls, json_str: str):
        schema = json.loads(json_str)
        schema = list(map(lambda o: (o[0], o[1], o[2], o[3]), schema))
        return cls(schema)
    
def get_interpol_color_by_pos(color_scheme: ColorScheme, pos: float):
    if pos < color_scheme.min_value() or pos > color_scheme.max_value():
        return wx.Colour(0, 0, 0)
    for i in range(len(color_scheme.schema) - 1):
        c0 = color_scheme.schema[i]
        c1 = color_scheme.schema[i + 1]
        if c0[3] <= pos <= c1[3]:
            ratio = (pos - c0[3]) / (c1[3] - c0[3])
            r = int(c0[0] + ratio * (c1[0] - c0[0]))
            g = int(c0[1] + ratio * (c1[1] - c0[1]))
            b = int(c0[2] + ratio * (c1[2] - c0[2]))
            return wx.Colour(r, g, b)
    return wx.Colour(255, 255, 255)


class ColorSchemePicker(wx.Panel):
    def __init__(self, parent, value: ColorScheme, size=wx.DefaultSize):
        super().__init__(parent, size=size)
        self.value = value
        sz = wx.BoxSizer(wx.VERTICAL)
        self.ruler = RulerWidget(self, threshold=50)
        sz.Add(self.ruler, 0, wx.EXPAND)
        self.gradient = wx.Panel(
            self, style=wx.WANTS_CHARS | wx.NO_FULL_REPAINT_ON_RESIZE | wx.CLIP_CHILDREN
        )
        self.gradient.SetDoubleBuffered(True)
        self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        sz.Add(self.gradient, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.dragged_index = None
        self.dragged_last_pos = None
        self.dragged = False
        self.gradient.Bind(wx.EVT_MOTION, self.on_motion)
        self.gradient.Bind(wx.EVT_SIZE, self.on_size)
        self.gradient.Bind(wx.EVT_PAINT, self.on_paint)
        self.gradient.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.gradient.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.gradient.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self.gradient.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)

    def delete_color(self, index):
        if 0 <= index < len(self.value.schema):
            del self.value.schema[index]
            self.ruler.draw()
            self.gradient.Refresh()
            self.gradient.Update()

    def on_right_down(self, event):
        index = self.pick_index(event.GetPosition().Get()[0])
        if index != -1:
            m = wx.Menu()
            m.Append(wx.ID_DELETE, "Удалить цвет")
            self.Bind(
                wx.EVT_MENU,
                lambda e: self.delete_color(index),
                m.FindItemById(wx.ID_DELETE),
            )
            m.Append(wx.ID_EDIT, "Изменить цвет")
            self.Bind(
                wx.EVT_MENU,
                lambda e: self.edit_color(index),
                m.FindItemById(wx.ID_EDIT),
            )
            self.PopupMenu(m, event.GetPosition())
        else:
            if self.gradient.HasCapture():
                self.gradient.ReleaseMouse()
            m = wx.Menu()
            m.Append(wx.ID_ADD, "Добавить цвет")
            self.Bind(wx.EVT_MENU, self.on_add_color, m.FindItemById(wx.ID_ADD))
            self.PopupMenu(m, event.GetPosition())

    def edit_color(self, index):
        r, g, b, p = self.value.schema[index]
        data = wx.ColourData()
        data.SetColour(wx.Colour(r, g, b))
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(None, data)
        if dlg.ShowModal() == wx.ID_OK:
            c = dlg.GetColourData().GetColour()
            self.value.schema[index] = (c.GetRed(), c.GetGreen(), c.GetBlue(), p)
            self.gradient.Refresh()
            self.gradient.Update()

    def on_add_color(self, event):
        data = wx.ColourData()
        data.SetColour(wx.Colour(0, 0, 0))
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(None, data)
        if dlg.ShowModal() == wx.ID_OK:
            c = dlg.GetColourData().GetColour()
            x = self.gradient.GetSize().GetWidth() / 2
            p = (
                x / self.gradient.GetSize().GetWidth()
            ) * self.value.range() + self.value.min_value()
            self.value.schema.append((c.Red(), c.Green(), c.Blue(), p))
            self.value.schema.sort(key=lambda o: o[3])
            self.ruler.draw()
            self.gradient.Refresh()
            self.gradient.Update()
        dlg.Destroy()

    def on_enter_window(self, event):
        self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        self.ruler.set_cursor(None)
        self.gradient.Refresh()
        self.gradient.Update()

    def on_left_down(self, event):
        self.dragged_index = self.pick_index(event.GetPosition().Get()[0])
        self.dragged_last_pos = event.GetPosition().Get()[0]

    def on_left_up(self, event):
        self.dragged_index = None
        self.dragged_last_pos = None

        if not self.dragged:
            x = event.GetPosition().Get()[0]
            index = self.pick_index(x)
            if index == -1:
                data = wx.ColourData()
                data.SetColour(wx.Colour(0, 0, 0))
                data.SetChooseFull(True)
                dlg = wx.ColourDialog(None, data)
                if dlg.ShowModal() == wx.ID_OK:
                    c = dlg.GetColourData().GetColour()
                    p = (
                        x / self.gradient.GetSize().GetWidth()
                    ) * self.value.range() + self.value.min_value()
                    self.value.schema.append((c.Red(), c.Green(), c.Blue(), p))
                    self.value.schema.sort(key=lambda o: o[3])
                    self.ruler.draw()
                    self.gradient.Refresh()
                    self.gradient.Update()
                dlg.Destroy()
            else:
                r, g, b, p = self.value.schema[index]
                data = wx.ColourData()
                data.SetColour(wx.Colour(r, g, b))
                data.SetChooseFull(True)
                dlg = wx.ColourDialog(None, data)
                if dlg.ShowModal() == wx.ID_OK:
                    c = dlg.GetColourData().GetColour()
                    self.value.schema[index] = (c.Red(), c.Green(), c.Blue(), p)
                    self.ruler.draw()
                    self.gradient.Refresh()
                    self.gradient.Update()
                dlg.Destroy()

        self.dragged = False

        if self.gradient.HasCapture():
            self.gradient.ReleaseMouse()

    def pick_index(self, x):
        width = self.gradient.GetSize().GetWidth()
        for i, (r, g, b, p) in enumerate(self.value.schema):
            pos = (p - self.value.min_value()) * (width / self.value.range())
            if abs(x - pos) < 5:
                return i
        return -1

    def on_motion(self, event):
        width = self.gradient.GetSize().GetWidth()
        self.ruler.set_cursor(event.GetPosition().Get()[0])
        if self.dragged_index is not None:
            self.dragged = event.Dragging() and event.LeftIsDown()
        self.dragged = True
        if self.dragged_index != -1 and event.Dragging() and event.LeftIsDown():
            self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
            if not self.gradient.HasCapture():
                self.gradient.CaptureMouse()
            self.gradient.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
            x = event.GetPosition().Get()[0] - self.dragged_last_pos
            self.dragged_last_pos = event.GetPosition().Get()[0]
            p = x * (self.value.range() / width)
            r, g, b, p_old = self.value.schema[self.dragged_index]
            self.value.schema[self.dragged_index] = (r, g, b, p_old + p)
            self.value.schema.sort(key=lambda o: o[3])
            self.ruler.draw()
            self.gradient.Refresh()
            self.gradient.Update()
        else:
            if self.pick_index(event.GetPosition().Get()[0]) != -1:
                self.gradient.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            else:
                self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))

    def on_size(self, event):
        width = self.GetSize().GetWidth()
        self.ruler.set_scale(width / self.value.range(), draw=False)
        self.ruler.set_offset(-self.value.min_value())
        self.ruler.draw()
        self.gradient.Refresh()
        self.gradient.Update()

    def get_color(self, value):
        if value < self.value.min_value() or value > self.value.max_value():
            return wx.Colour(0, 0, 0)
        for i in range(len(self.value.schema) - 1):
            c0 = self.value.schema[i]
            c1 = self.value.schema[i + 1]
            if c0[3] <= value <= c1[3]:
                ratio = (value - c0[3]) / (c1[3] - c0[3])
                r = int(c0[0] + ratio * (c1[0] - c0[0]))
                g = int(c0[1] + ratio * (c1[1] - c0[1]))
                b = int(c0[2] + ratio * (c1[2] - c0[2]))
                return wx.Colour(r, g, b)
        return wx.Colour(255, 255, 255)

    def on_paint(self, event):
        dc = wx.PaintDC(self.gradient)
        width, height = (
            self.gradient.GetSize().GetWidth(),
            self.gradient.GetSize().GetHeight(),
        )
        if width == 0 or height == 0:
            return
        height = self.gradient.GetSize().GetHeight()
        for i in range(width):
            value = self.value.min_value() + (i / width) * self.value.range()
            color = self.get_color(value)
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(i, 0, i, height)

        for r, g, b, p in self.value.schema:
            x = int((p - self.value.min_value()) / self.value.range() * width)
            dc.SetPen(
                wx.Pen(wx.Colour(255 - r, 255 - g, 255 - b), 1, wx.PENSTYLE_SOLID)
            )
            dc.DrawRectangle(int(x - 5), int(height / 2 - 5), 10, 10)

        self.ruler.set_scale(width / self.value.range(), draw=False)
        self.ruler.set_offset(-self.value.min_value())
        self.ruler.draw()


class ColorSchemeDialog(wx.Dialog):
    def __init__(self, parent, value: ColorScheme):
        super().__init__(
            parent,
            title="Настройка цветовой схемы",
            style=wx.DEFAULT_DIALOG_STYLE,
            size=wx.Size(400, 130),
        )
        sz = wx.BoxSizer(wx.VERTICAL)
        self.picker = ColorSchemePicker(self, value, size=wx.Size(350, 50))
        sz.Add(self.picker, 0, wx.EXPAND | wx.BOTTOM, 10)
        btn_sz = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_load = wx.Button(self, wx.ID_OPEN, "Загрузить")
        self.btn_save = wx.Button(self, wx.ID_SAVE, "Сохранить")
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sz.Add(self.btn_load)
        btn_sz.Add(self.btn_save)
        sz.Add(btn_sz, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        btn_sz.AddStretchSpacer()
        self.btn_cancel = wx.Button(self, label="Отменить")
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        btn_sz.Add(self.btn_cancel, 0, wx.EXPAND)
        self.btn_apply = wx.Button(self, label="Применить")
        self.btn_apply.Bind(wx.EVT_BUTTON, self.on_apply)
        self.btn_apply.SetDefault()
        btn_sz.Add(self.btn_apply, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def on_apply(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def get_value(self):
        return self.picker.value

    def on_save(self, event):
        wildcard = "Color Scheme Files (*.colorscheme)|*.colorscheme|All files (*.*)|*.*"

        with wx.FileDialog(
            self,
            message="Сохранить цветовую схему",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                with open(dlg.GetPath(), "w") as f:
                    self.picker.value.save(f)

    def on_load(self, event):
        wildcard = "Color Scheme Files (*.colorscheme)|*.colorscheme|All files (*.*)|*.*"

        with wx.FileDialog(
            self,
            message="Открыть цветовую схему",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                with open(dlg.GetPath(), "r") as f:
                    self.picker.value = ColorScheme.load(f)
                    self.picker.Refresh()
                    self.picker.Update()

class GradientPanel(wx.Panel):
    def __init__(self, parent, style, pos, size):
        super().__init__(parent, style=style, pos=pos, size=size)
        self.value = None
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.gradient = wx.Panel(self)
        sz.Add(self.gradient, 1, wx.EXPAND)
        self.button = wx.Button(self, label="...", style=wx.BU_EXACTFIT)
        sz.Add(self.button, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.gradient.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        if self.value is None:
            return

        panel = event.GetEventObject()
        dc = wx.PaintDC(panel)
        rect: wx.Rect = panel.GetClientRect()
        rect.Deflate(0, 2)

        width = rect.width
        height = rect.height

        if width == 0 or height == 0:
            return
        for i in range(width):
            value = self.value.min_value() + (i / width) * self.value.range()
            color = get_interpol_color_by_pos(self.value, value)
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(i + rect.GetLeft(), rect.GetTop(), i + rect.GetLeft(), height + rect.GetTop())

    def set_color_scheme(self, color_scheme):
        self.value = color_scheme
        self.Refresh()
        self.Update()


class GradientEditor(wx.propgrid.PGEditor):
    def CreateControls(self, propgrid, property, pos, size):
        panel = GradientPanel(propgrid, style=wx.NO_BORDER, pos=pos, size=size)
        panel.Layout()
        panel.set_color_scheme(property.GetValue())

        return wx.propgrid.PGWindowList(panel)
    
    def UpdateControl(self, property: wx.propgrid.PGProperty, ctrl: wx.Window) -> None:
        ctrl.set_color_scheme(property.GetValue())

    def SetControlStringValue(self, property: wx.propgrid.PGProperty, ctrl: wx.Window, txt: str) -> None:
        ctrl.set_color_scheme(property.GetValue())
    
    def get_color(self, scheme, value):
        if value < scheme.min_value() or value > scheme.max_value():
            return wx.Colour(0, 0, 0)
        for i in range(len(scheme.schema) - 1):
            c0 = scheme.schema[i]
            c1 = scheme.schema[i + 1]
            if c0[3] <= value <= c1[3]:
                ratio = (value - c0[3]) / (c1[3] - c0[3])
                r = int(c0[0] + ratio * (c1[0] - c0[0]))
                g = int(c0[1] + ratio * (c1[1] - c0[1]))
                b = int(c0[2] + ratio * (c1[2] - c0[2]))
                return wx.Colour(r, g, b)
        return wx.Colour(255, 255, 255)
    
    def DrawValue(self, dc, rect, property, text):
        propvalue = ColorScheme.from_string(text)
        stops = getattr(propvalue, 'schema')
        self.value = propvalue

        if not stops or len(stops) < 2:
            dc.SetBrush(wx.Brush(wx.WHITE))
            dc.DrawRectangle(rect)
            return

        width = rect.width
        height = rect.height

        # Рисуем градиент слева направо
        if width == 0 or height == 0:
            return
        for i in range(width):
            value = propvalue.min_value() + (i / width) * propvalue.range()
            color = self.get_color(propvalue, value)
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(i + rect.GetLeft(), rect.GetTop(), i + rect.GetLeft(), height + rect.GetTop())

    def OnPaint(self, event):
        if self.value is None:
            return

        panel = event.GetEventObject()
        dc = wx.PaintDC(panel)
        rect: wx.Rect = panel.GetClientRect()
        rect.Deflate(0, 2)

        self.DrawValue(dc, rect, None, self.value.to_string())

    def OnEvent(self, propgrid: wx.propgrid.PropertyGrid, property: wx.propgrid.PGProperty, wnd_primary: wx.Window, event: wx.Event) -> bool:
        """
        OnEvent(propgrid, property, wnd_primary, event) -> bool
        
        Handles events.
        """
        return True
    
    def OnClick(self, event):
        ...
    
class ColorSchemeProperty(wx.propgrid.PGProperty):
    def __init__(self, label, name, value=None):
        super().__init__(label, name)
        self.SetValue(value)
    
    def GetValueAsString(self, argFlags = 0):
        return self.GetValue().to_string()
    
    def OnEvent(self, propgrid: wx.propgrid.PropertyGrid, wnd_primary: wx.Window, event: wx.Event) -> bool:
        if event.GetEventType() == wx.wxEVT_BUTTON:
            dlg = ColorSchemeDialog(propgrid, self.GetValue())
            if dlg.ShowModal() == wx.ID_OK:
                self.SetValue(dlg.get_value())
        return True