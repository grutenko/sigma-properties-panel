import wx
import wx.propgrid
import json

from color_scheme import ColorSchemeProperty, ColorScheme, GradientEditor


class PropertiesPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.pg = wx.propgrid.PropertyGrid(
            self, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER
        )
        self.pg.RegisterEditor(GradientEditor(), "gradient_editor")
        p = self.pg.Append(wx.propgrid.StringProperty("Имя объекта", "name"))
        p = self.pg.Append(wx.propgrid.FloatProperty("Масштаб", "scale"))
        p.SetEditor(wx.propgrid.PGEditor_TextCtrlAndButton)
        c = self.pg.Append(wx.propgrid.PropertyCategory("Цветовая схема"))
        p = self.pg.AppendIn(c,
            ColorSchemeProperty(
                "Мин. напряжения",
                "color_scheme_min",
                ColorScheme.basic(
                    wx.Colour(0, 0, 0), -100, wx.Colour(255, 255, 255), 500
                ),
            )
        )
        self.pg.SetPropertyEditor(p, "gradient_editor")
        p = self.pg.AppendIn(c,
            ColorSchemeProperty(
                "Сред. напряжения",
                "color_scheme_mid",
                ColorScheme.basic(
                    wx.Colour(0, 0, 0), -100, wx.Colour(255, 255, 255), 500
                ),
            )
        )
        self.pg.SetPropertyEditor(p, "gradient_editor")
        p = self.pg.AppendIn(c, 
            ColorSchemeProperty( 
                "Макс. напряжения",
                "color_scheme_max",
                ColorScheme.basic(
                    wx.Colour(0, 0, 0), -100, wx.Colour(255, 255, 255), 500
                ),
            )
        )
        self.pg.SetPropertyEditor(p, "gradient_editor")
        self.pg.Update()
        sz.Add(self.pg, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

        with open("ColorsParaView.json", "r") as f:
            data = json.load(f)
            color_schema = {}
            for o in data:
                color_schema[o["Name"]] = o["RGBPoints"]
            self.pg.SetPropertyValue("color_scheme_min", ColorScheme.from_paraview(color_schema["Smin_Val"]))
            self.pg.SetPropertyValue("color_scheme_mid", ColorScheme.from_paraview(color_schema["Smid_Val"]))
            self.pg.SetPropertyValue("color_scheme_max", ColorScheme.from_paraview(color_schema["Smax_Val"]))
