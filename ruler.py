import wx
import math


class RulerWidget(wx.Panel):
    def __init__(self, parent, threshold=50, orientation=wx.HORIZONTAL, invert=False):
        super().__init__(parent)
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.orientation = orientation
        self.threshold = threshold
        self.pixels_per_unit = 20
        self.factor = 1
        self.parts = 5
        self.update_factor()
        self.invert = invert
        self.offset = 0.0
        self.cursor = None
        self.SetMinSize(
            wx.Size(15, 15) if orientation == wx.HORIZONTAL else wx.Size(15, 15)
        )
        self.SetSize(
            wx.Size(-1, 15) if orientation == wx.HORIZONTAL else wx.Size(15, -1)
        )
        self.Layout()
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.Refresh()


    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return
        
        gc.SetFont(
            wx.Font(
                8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
            ),
            wx.Colour(0, 0, 0),
        )
        if self.orientation == wx.HORIZONTAL:
            if not self.invert:
                self.paint_horizontal(gc, w, h)
            else:
                self.paint_horizontal_inverted(gc, w, h)
            if self.cursor is not None:
                gc.StrokeLine(self.cursor, 0, self.cursor, h)
        elif self.orientation == wx.VERTICAL:
            if not self.invert:
                self.paint_vertical(gc, w, h)
            else:
                 self.paint_vertical_inverted(gc, w, h)
            if self.cursor is not None:
                gc.StrokeLine(0, self.cursor, w, self.cursor)

    def round_to_multiple(self, value, step):
        return round(value / step) * step
            

    def paint_horizontal(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        index = self.round_to_multiple((i - pixoffset) / self.pixels_per_unit, self.factor)

        while i < w:
            gc.DrawText(str(index), i + 2, 0)
            gc.StrokeLine(i, h, i, 0)
            i += mod
            index += self.factor

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        while i < w:
            gc.StrokeLine(i, h / 2, i, h)
            i += mod

    def paint_horizontal_inverted(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset  % mod
        if self.offset < 0:
            i -= mod

        index = self.round_to_multiple((i - pixoffset) / self.pixels_per_unit, self.factor)

        while i < w:
            gc.DrawText(str(index), (w - i) + 2, 0)
            gc.StrokeLine((w - i), h, w - i, 0)
            i += mod
            index += self.factor

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        while i < w:
            gc.StrokeLine(w - i, h / 2, w - i, h)
            i += mod

    def paint_vertical(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        index = self.round_to_multiple((i - pixoffset) / self.pixels_per_unit, self.factor)
        while i < h:
            gc.PushState()
            gc.Translate(0, i)
            gc.Rotate(-math.pi / 2)
            gc.DrawText(str(index), 0, 0)
            gc.PopState()
            gc.StrokeLine(0, i, w, i)
            index += self.factor
            i += mod

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod
        
        while i < h:
            gc.StrokeLine(w / 2, i, w, i)
            i += mod


    def paint_vertical_inverted(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset  % mod
        if self.offset < 0:
            i -= mod

        index = self.round_to_multiple((i - pixoffset) / self.pixels_per_unit, self.factor)
        while i < h:
            gc.PushState()
            gc.Translate(0, h - i)
            gc.Rotate(-math.pi / 2)
            gc.DrawText(str(index), 0, 0)
            gc.PopState()
            gc.StrokeLine(0, h - i, w, h - i)
            index += self.factor
            i += mod

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod
        
        while i < h:
            gc.StrokeLine(w / 2, h - i, w, h - i)
            i += mod


    def update_factor(self):
        available_factors = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 100000, 1000000]
        factor = 1
        if self.pixels_per_unit > self.threshold * 2:
            while factor * self.pixels_per_unit > self.threshold * 2:
                factor /= 2
        else:
            i = 0
            while factor * self.pixels_per_unit < self.threshold:
                factor = available_factors[i]
                i += 1
        self.factor = factor

    def set_scale(self, pixels_per_unit: float, draw = True):
        if self.pixels_per_unit != pixels_per_unit:
            self.pixels_per_unit = pixels_per_unit
            self.update_factor()
        if draw:
            self.draw()

    def set_offset(self, axis_value: float, draw = True):
        """Sets the offset of the ruler in coords."""
        self.offset = axis_value
        if draw:
            self.draw()

    def set_cursor(self, axis_value: float | None, draw = True):
        """Sets the cursor position on the ruler. in pixels."""
        self.cursor = axis_value
        if draw:
            self.draw()

    def draw(self):
        self.Refresh()
        self.Update()