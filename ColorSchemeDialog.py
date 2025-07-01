import wx
import vtk
import json


class ColorMapPanel(wx.Panel):
    def __init__(self, parent, ctf, callback_add_point, callback_update_points, callback_set_range,min_val,max_val):
        super(ColorMapPanel, self).__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self.ctf = ctf
        self.callback_add_point = callback_add_point
        self.callback_update_points = callback_update_points
        self.callback_set_range = callback_set_range

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

        self.SetMinSize((400, 60))

        # Точки как [(value, color)]
        # Массив для хранения точек
        self.points = []
        # Получаем количество узлов
        num_nodes = ctf.GetSize()
        for i in range(num_nodes):
            node = [0.0] * 6  # Важно: список из 6 элементов
            ctf.GetNodeValue(i, node)
            self.points.append((node[0], (node[1], node[2], node[3])))
        # self.points = [
        #     (min_val, (1.0, 0.0, 0.0)),
        #     (max_val, (0.0, 0.0, 1.0))
        # ]
        self.selected_index = -1
        self.dragging = False
        self.mouse_down_pos = None

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        w, h = self.GetSize()

        bmp = wx.Bitmap(w, h + 20)
        mem_dc = wx.MemoryDC(bmp)
        mem_dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        mem_dc.Clear()

        # Градиент
        for x in range(w):
            value = x / w
            rgb = self.ctf.GetColor(value)
            r, g, b = rgb
            color = wx.Colour(int(r * 255), int(g * 255), int(b * 255))
            mem_dc.SetPen(wx.Pen(color))
            mem_dc.DrawLine(x, 0, x, h)

        # Точки
        for i, (value, color) in enumerate(self.points):
            norm_value = self.map_value_to_normalized(value)
            px = int(norm_value * w)
            wx_color = wx.Colour(
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255)
            )
            mem_dc.SetBrush(wx.Brush(wx_color))
            mem_dc.SetPen(wx.Pen("black", width=1))
            mem_dc.DrawCircle(px, h // 2, 6)

        # Легенда
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        mem_dc.SetFont(font)
        mem_dc.SetTextForeground(wx.Colour(0, 0, 0))
        for value, _ in self.points:
            norm_value = self.map_value_to_normalized(value)
            px = int(norm_value * w)
            mem_dc.DrawText(f"{value:.2f}", px - 15, h + 2)

        dc.Blit(0, 0, w, h + 20, mem_dc, 0, 0)
        mem_dc.SelectObject(wx.NullBitmap)

    def map_value_to_normalized(self, value):
        min_val, max_val = self.callback_set_range(get_only=True)
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    def map_normalized_to_value(self, norm_value):
        min_val, max_val = self.callback_set_range(get_only=True)
        return min_val + norm_value * (max_val - min_val)

    def OnLeftDown(self, event):
        x = event.GetX()
        y = event.GetY()
        w, h = self.GetSize()

        self.mouse_down_pos = (x, y)

        # Проверяем попадание на точку
        for i, (value, _) in enumerate(self.points):
            norm_value = self.map_value_to_normalized(value)
            px = int(norm_value * w)
            if abs(px - x) < 6 and abs(y - h // 2) < 6:
                self.selected_index = i
                return

        # Клик вне точек → добавляем новую точку
        norm_click = max(0.0, min(1.0, x / w))
        real_value = self.map_normalized_to_value(norm_click)
        self.add_new_point(real_value)

    def add_new_point(self, default_value=0.0):
        new_value_str = wx.GetTextFromUser(
            "Введите значение для новой точки:",
            "Добавление точки",
            default_value=f"{default_value:.4f}"
        )
        if not new_value_str:
            return
        try:
            new_value = float(new_value_str)
            dialog = wx.ColourDialog(None)
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                r = color.Red() / 255.0
                g = color.Green() / 255.0
                b = color.Blue() / 255.0
                self.points.append((new_value, (r, g, b)))
                self.points.sort(key=lambda p: p[0])
                self.callback_update_points(self.points)
        except ValueError:
            wx.MessageBox("Введите корректное число.", "Ошибка", wx.OK | wx.ICON_ERROR)

    def edit_point(self, index):
        value, color = self.points[index]

        # Редактирование значения
        new_value_str = wx.GetTextFromUser(
            "Введите новое значение:",
            "Редактирование точки",
            default_value=f"{value:.4f}"
        )
        if not new_value_str:
            return
        try:
            new_value = float(new_value_str)
        except ValueError:
            wx.MessageBox("Неверный формат числа.", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        # Редактирование цвета
        current_qt_color = wx.Colour(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        )

        dialog = wx.ColourDialog(None)
        dialog.GetColourData().SetColour(current_qt_color)
        if dialog.ShowModal() == wx.ID_OK:
            new_color = dialog.GetColourData().GetColour()
            r = new_color.Red() / 255.0
            g = new_color.Green() / 255.0
            b = new_color.Blue() / 255.0
            self.points[index] = (new_value, (r, g, b))
            self.points.sort(key=lambda p: p[0])
            self.callback_update_points(self.points)
            self.Refresh()

    def OnMotion(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.dragging = True
            x = event.GetX()
            w, _ = self.GetSize()
            norm_value = max(0.0, min(1.0, x / w))
            real_value = self.map_normalized_to_value(norm_value)

            if self.selected_index >= 0:
                self.points[self.selected_index] = (real_value, self.points[self.selected_index][1])
                self.points.sort(key=lambda p: p[0])
                self.callback_update_points(self.points)

    def OnLeftUp(self, event):
        if self.selected_index >= 0 and not self.dragging:
            self.edit_point(self.selected_index)

        self.dragging = False
        self.selected_index = -1
        self.mouse_down_pos = None

    def OnRightDown(self, event):
        x = event.GetX()
        w, h = self.GetSize()

        for i, (value, _) in enumerate(self.points):
            norm_value = self.map_value_to_normalized(value)
            px = int(norm_value * w)
            if abs(px - x) < 6:
                self.points.pop(i)
                self.callback_update_points(self.points)
                self.Refresh()
                return


class ColorMapEditorFrame(wx.Dialog):
    def __init__(self, parent, title, ctf, min_val, max_val):
        super(ColorMapEditorFrame, self).__init__(parent, title=title, size=(700, 210))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Цветовая функция
        self.ctf = ctf#vtk.vtkColorTransferFunction()

        # Панель цветовой схемы
        self.color_panel = ColorMapPanel(
            self.panel,
            self.ctf,
            callback_add_point=self.add_color_point,
            callback_update_points=self.update_ctf,
            callback_set_range=self.get_min_max, min_val=min_val, max_val=max_val
        )
        # Поля ввода Min/Max
        range_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.min_input = wx.TextCtrl(self.panel, value=str(min_val), size=(80, -1))
        self.min_input.SetValue(str(min_val))
        self.max_input = wx.TextCtrl(self.panel, value=str(min_val), size=(80, -1))
        self.max_input.SetValue(str(max_val))
        self.btn_apply_range = wx.Button(self.panel, label="Применить диапазон")

        self.btn_apply_range.Bind(wx.EVT_BUTTON, self.apply_min_max)

        range_sizer.Add(wx.StaticText(self.panel, label="Min:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        range_sizer.Add(self.min_input, flag=wx.RIGHT, border=10)
        range_sizer.Add(wx.StaticText(self.panel, label="Max:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        range_sizer.Add(self.max_input, flag=wx.RIGHT, border=10)
        range_sizer.Add(self.btn_apply_range)

        # Кнопки
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_reset = wx.Button(self.panel, label="Сбросить")
        self.btn_save = wx.Button(self.panel, label="Сохранить")
        self.btn_load = wx.Button(self.panel, label="Загрузить")

        self.btn_reset.Bind(wx.EVT_BUTTON, self.reset_ctf)
        self.btn_save.Bind(wx.EVT_BUTTON, self.save_scheme)
        self.btn_load.Bind(wx.EVT_BUTTON, self.load_scheme)

        btn_sizer.Add(self.btn_reset, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_save, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_load, 0, wx.ALL, 5)

        # Кнопка передачи диапазона
        upload_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upload_button = wx.Button(self.panel, label="Применить")
        upload_sizer.Add(self.upload_button, 0, wx.ALL, 5)
        self.upload_button.Bind(wx.EVT_BUTTON, self.on_ok)

        # Сборка интерфейса
        self.sizer.Add(self.color_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(range_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)
        self.sizer.Add(upload_sizer, 0, wx.ALIGN_CENTER| wx.ALL)
        self.panel.SetSizer(self.sizer)

        self.Centre()
        self.Show(True)

        # Начальные значения
        self.min_val = min_val
        self.max_val = max_val
        self.update_ctf(self.color_panel.points)

    def on_ok(self, event):
        # Можно добавить проверку ввода
        self.EndModal(wx.ID_OK)
        
    def get_min_max(self, get_only=False):
        if get_only:
            return self.min_val, self.max_val
        try:
            self.min_val = float(self.min_input.GetValue())
            self.max_val = float(self.max_input.GetValue())
        except ValueError:
            wx.MessageBox("Введите корректные числа для Min и Max.", "Ошибка", wx.OK | wx.ICON_ERROR)
            return
        self.update_ctf(self.color_panel.points)

    def apply_min_max(self, event=None):
        self.get_min_max()
        self.update_ctf(self.color_panel.points)

    def add_color_point(self, value):
        dialog = wx.ColourDialog(None)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            r = color.Red() / 255.0
            g = color.Green() / 255.0
            b = color.Blue() / 255.0
            self.color_panel.points.append((value, (r, g, b)))
            self.color_panel.points.sort(key=lambda p: p[0])
            self.update_ctf(self.color_panel.points)

    def update_ctf(self, points):
        self.ctf.RemoveAllPoints()
        for value, (r, g, b) in points:
            norm_value = (value - self.min_val) / (self.max_val - self.min_val)
            self.ctf.AddRGBPoint(norm_value, r, g, b)
        self.color_panel.Refresh()

    def reset_ctf(self, event=None):
        self.min_input.SetValue(str(self.min_val))
        self.max_input.SetValue(str(self.max_val))
        self.color_panel.points = [
            (self.min_val, (0.0, 0.0, 1.0)),
            (self.max_val, (1.0, 0.0, 0.0))
        ]
        self.update_ctf(self.color_panel.points)

    def save_scheme(self, event=None):
        with wx.FileDialog(self, "Сохранить цветовую схему", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = dlg.GetPath()
            data = {
                "min": self.min_val,
                "max": self.max_val,
                "points": [{"value": v, "color": [r, g, b]} for v, (r, g, b) in self.color_panel.points]
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def load_scheme(self, event=None):
        with wx.FileDialog(self, "Загрузить цветовую схему", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = dlg.GetPath()
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.min_val = data["min"]
                    self.max_val = data["max"]
                    self.min_input.SetValue(str(self.min_val))
                    self.max_input.SetValue(str(self.max_val))
                    self.color_panel.points = [(item["value"], tuple(item["color"])) for item in data["points"]]
                    self.update_ctf(self.color_panel.points)
            except Exception as e:
                wx.MessageBox(f"Ошибка загрузки файла:\n{e}", "Ошибка", wx.OK | wx.ICON_ERROR)

    def ApplyColorScheme(self):
        #Получаем количество узлов
        num_nodes = self.color_panel.ctf.GetSize()
        points = []
        for i in range(num_nodes):
            node = [0.0] * 6  # Важно: список из 6 элементов
            self.color_panel.ctf.GetNodeValue(i, node)
            node[0] = self.min_val+(self.max_val-self.min_val)*node[0]
            points.append((node[0],(node[1],node[2],node[3])))
        self.color_panel.ctf.RemoveAllPoints()
        for value, (r, g, b) in points:
            self.color_panel.ctf.AddRGBPoint(value, r, g, b)
        return self.color_panel.ctf

if __name__ == "__main__":
    app = wx.App(0)
    dlg = ColorMapEditorFrame(None, "test", vtk.vtkColorTransferFunction(), -100, 500)
    dlg.ShowModal()