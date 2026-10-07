# -*- coding: utf-8 -*-
"""
Лаба 4 — Часть 1: Интерактивная сцена.
Лаба 4 — Часть 2: Аффинные преобразования через однородные матрицы 3×3.

Файл собран командой: часть 1 (создание полигонов) + часть 2
(аффинные преобразования). Часть 2 отделена от части 1
комментарием-чертой, чтобы каждый участник видел границы своей зоны
ответственности.
"""

import math
import tkinter as tk
from tkinter import messagebox

# ЧАСТЬ 2. МАТРИЦЫ 3x3 И АФФИННЫЕ ПРЕОБРАЗОВАНИЯ

def mat_mul(A, B):
    """Произведение двух матриц 3×3."""
    C = [[0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0]]
    for i in range(3):
        for j in range(3):
            s = 0.0
            for k in range(3):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


def mat_vec_mul(M, v):
    """Умножение матрицы 3×3 на однородный вектор (x, y, 1)."""
    x, y, w = v
    rx = M[0][0] * x + M[0][1] * y + M[0][2] * w
    ry = M[1][0] * x + M[1][1] * y + M[1][2] * w
    rw = M[2][0] * x + M[2][1] * y + M[2][2] * w
    return rx, ry, rw


def translation_matrix(dx, dy):
    """T(dx, dy) — смещение."""
    return [[1.0, 0.0, float(dx)],
            [0.0, 1.0, float(dy)],
            [0.0, 0.0, 1.0]]


def rotation_matrix_origin(angle_deg):
    """R(φ) — поворот на угол φ вокруг начала координат."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0],
            [s,  c, 0.0],
            [0.0, 0.0, 1.0]]


def scaling_matrix_origin(sx, sy):
    """S(sx, sy) — масштабирование относительно начала координат."""
    return [[float(sx), 0.0, 0.0],
            [0.0, float(sy), 0.0],
            [0.0, 0.0, 1.0]]


def rotation_matrix_about(angle_deg, cx, cy):
    """
    Поворот на угол φ вокруг точки (cx, cy):
        M = T(cx, cy) · R(φ) · T(-cx, -cy)
    """
    return mat_mul(
        mat_mul(translation_matrix(cx, cy), rotation_matrix_origin(angle_deg)),
        translation_matrix(-cx, -cy)
    )


def scaling_matrix_about(sx, sy, cx, cy):
    """
    Масштабирование относительно точки (cx, cy):
        M = T(cx, cy) · S(sx, sy) · T(-cx, -cy)
    """
    return mat_mul(
        mat_mul(translation_matrix(cx, cy), scaling_matrix_origin(sx, sy)),
        translation_matrix(-cx, -cy)
    )


# ЧАСТЬ 1. ИНТЕРАКТИВНАЯ СЦЕНА

class PolygonApp:
    def __init__(self, root):
        self.root = root
        root.title("Лаба 4: интерактивная сцена + аффинные преобразования")

        # Данные
        self.polygons = []          # список завершённых полигонов
                                    # каждый: {'vertices': [(x,y), ...], 'closed': bool}
        self.current_vertices = []  # вершины полигона, который сейчас создаётся
        self.active_polygon = None  # индекс выбранного полигона (или None)

        # Инструмент
        self.tool = tk.StringVar(value="polygon")
        self.mode = tk.StringVar(value="create")

        # Интерфейс
        self._build_toolbar()
        self._build_transform_bar()   # <- часть 2 добавляет свою панель
        self._build_canvas()
        self._bind_events()

        self.redraw()

    # ИНТЕРФЕЙС (часть 1)
    def _build_toolbar(self):
        bar = tk.Frame(self.root)
        bar.pack(side="top", fill="x")

        tk.Label(bar, text="Инструмент:").pack(side="left", padx=5)
        for text, value in [("Точка", "point"),
                            ("Ребро", "edge"),
                            ("Полигон", "polygon")]:
            tk.Radiobutton(bar, text=text, variable=self.tool,
                           value=value,
                           command=self._on_tool_change).pack(side="left")

        tk.Button(bar, text="Очистить",
                  command=self.clear_scene).pack(side="left", padx=10)

        tk.Label(bar, text="Режим:").pack(side="left", padx=5)
        tk.Radiobutton(bar, text="Создание", variable=self.mode,
                       value="create").pack(side="left")
        tk.Radiobutton(bar, text="Выбор", variable=self.mode,
                       value="select").pack(side="left")

        # сюда часть 2 добавляет панель аффинных преобразований
        self.extra_bar = tk.Frame(self.root)
        self.extra_bar.pack(side="top", fill="x")

    def _build_canvas(self):
        self.canvas = tk.Canvas(self.root, width=900, height=600,
                                bg="white", highlightthickness=1,
                                highlightbackground="gray")
        self.canvas.pack(fill="both", expand=True)

    def _bind_events(self):
        self.canvas.bind("<Button-1>",  self.on_left_click)
        self.canvas.bind("<Button-3>",  self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>",    self.on_motion)
        self.root.bind("<Return>",      lambda e: self.finish_polygon())
        self.root.bind("<Escape>",      lambda e: self.cancel_current())

    #  СОЗДАНИЕ ПОЛИГОНОВ (часть 1)
    def on_left_click(self, event):
        x, y = event.x, event.y

        if self.mode.get() == "select":
            self._select_polygon_at(x, y)
            return

        # режим создания
        if self.tool.get() == "point":
            self.polygons.append({"vertices": [(x, y)], "closed": True})
            self.redraw()

        elif self.tool.get() == "edge":
            if len(self.current_vertices) == 0:
                self.current_vertices.append((x, y))
            else:
                self.current_vertices.append((x, y))
                self.polygons.append({"vertices": list(self.current_vertices),
                                      "closed": True})
                self.current_vertices = []
            self.redraw()

        elif self.tool.get() == "polygon":
            self.current_vertices.append((x, y))
            self.redraw()

    def on_right_click(self, event):
        if self.tool.get() == "polygon" and self.current_vertices:
            self.finish_polygon()

    def on_double_click(self, event):
        if self.tool.get() == "polygon" and self.current_vertices:
            self.finish_polygon()

    def finish_polygon(self):
        if len(self.current_vertices) >= 2:
            self.polygons.append({"vertices": list(self.current_vertices),
                                  "closed": True})
        self.current_vertices = []
        self.redraw()

    def cancel_current(self):
        self.current_vertices = []
        self.redraw()

    #  ВЫБОР АКТИВНОГО ПОЛИГОНА (часть 1)
    def _select_polygon_at(self, x, y, radius=10):
        """Ищет полигон под курсором. Приоритет — ближайшая вершина."""
        best_idx = None
        best_dist = radius

        for i, poly in enumerate(self.polygons):
            for (vx, vy) in poly["vertices"]:
                d = ((vx - x) ** 2 + (vy - y) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best_idx = i

        self.active_polygon = best_idx
        self.redraw()

    #  ОЧИСТКА (часть 1)
    def clear_scene(self):
        self.polygons = []
        self.current_vertices = []
        self.active_polygon = None
        self.redraw()

    #  ОТРИСОВКА (часть 1)
    def on_motion(self, event):
        if self.mode.get() == "create" and self.current_vertices:
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")

        # завершённые полигоны
        for i, poly in enumerate(self.polygons):
            self._draw_polygon(poly, active=(i == self.active_polygon))

        # текущий полигон в процессе создания
        if self.current_vertices:
            self._draw_current()

        # центр активного полигона (часть 2)
        self._draw_active_center()

        # подпись состояния
        self.canvas.create_text(
            10, 10, anchor="nw", fill="gray",
            text=f"Инструмент: {self.tool.get()} | "
                 f"Режим: {self.mode.get()} | "
                 f"Полигонов: {len(self.polygons)} | "
                 f"Активный: {self.active_polygon}"
        )

    def _draw_polygon(self, poly, active=False):
        verts = poly["vertices"]
        color = "red" if active else "black"
        width = 3 if active else 2

        # одна вершина - точка
        if len(verts) == 1:
            x, y = verts[0]
            r = 4
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill="white", outline=color, width=width - 1)
            return

        # две вершины - ребро
        if len(verts) == 2:
            x1, y1 = verts[0]
            x2, y2 = verts[1]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            for (x, y) in verts:
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                        fill="white", outline=color)
            return

        # общий случай - N вершин
        flat = [c for v in verts for c in v]
        if poly["closed"] and len(verts) >= 2:
            self.canvas.create_polygon(flat, outline=color, fill="",
                                       width=width)
        else:
            self.canvas.create_line(*flat, fill=color, width=width)

        for (x, y) in verts:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                    fill="white", outline=color)

    def _draw_current(self):
        verts = self.current_vertices

        if len(verts) >= 2:
            flat = [c for v in verts for c in v]
            self.canvas.create_line(*flat, fill="blue", width=2)

        for (x, y) in verts:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                    fill="white", outline="blue")

        if self.tool.get() == "polygon":
            mx = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
            my = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
            x, y = verts[-1]
            self.canvas.create_line(x, y, mx, my, fill="blue", dash=(4, 4))

        if self.tool.get() == "polygon":
            self.canvas.create_text(
                10, 30, anchor="nw", fill="blue",
                text="Enter или ПКМ — завершить полигон, Esc — отмена"
            )

    #  СМЕНА ИНСТРУМЕНТА (часть 1)
    def _on_tool_change(self):
        if self.current_vertices:
            self.finish_polygon()

    #  ЧАСТЬ 2. АФФИННЫЕ ПРЕОБРАЗОВАНИЯ — UI И ОБРАБОТЧИКИ

    # ---------- построение панели преобразований ----------
    def _build_transform_bar(self):
        bar = self.extra_bar

        # ----- ряд 1: смещение, поворот вокруг точки -----
        row1 = tk.Frame(bar)
        row1.pack(side="top", fill="x")

        # Смещение
        f = tk.LabelFrame(row1, text="Смещение")
        f.pack(side="left", padx=3, pady=2)
        self.dx_var = tk.StringVar(value="40")
        self.dy_var = tk.StringVar(value="-30")
        tk.Label(f, text="dx").pack(side="left")
        tk.Entry(f, textvariable=self.dx_var, width=5).pack(side="left")
        tk.Label(f, text="dy").pack(side="left")
        tk.Entry(f, textvariable=self.dy_var, width=5).pack(side="left")
        tk.Button(f, text="→", command=self.do_translate).pack(side="left", padx=3)

        # Поворот вокруг точки
        f = tk.LabelFrame(row1, text="Поворот вокруг точки")
        f.pack(side="left", padx=3, pady=2)
        self.ang_pt_var = tk.StringVar(value="30")
        self.rcx_var = tk.StringVar(value="450")
        self.rcy_var = tk.StringVar(value="300")
        tk.Label(f, text="φ°").pack(side="left")
        tk.Entry(f, textvariable=self.ang_pt_var, width=5).pack(side="left")
        tk.Label(f, text="cx").pack(side="left")
        tk.Entry(f, textvariable=self.rcx_var, width=5).pack(side="left")
        tk.Label(f, text="cy").pack(side="left")
        tk.Entry(f, textvariable=self.rcy_var, width=5).pack(side="left")
        tk.Button(f, text="→", command=self.do_rotate_point).pack(side="left", padx=3)

        # ----- ряд 2: поворот вокруг центра, масштабы -----
        row2 = tk.Frame(bar)
        row2.pack(side="top", fill="x")

        # Поворот вокруг центра полигона
        f = tk.LabelFrame(row2, text="Поворот вокруг центра полигона")
        f.pack(side="left", padx=3, pady=2)
        self.ang_c_var = tk.StringVar(value="30")
        tk.Label(f, text="φ°").pack(side="left")
        tk.Entry(f, textvariable=self.ang_c_var, width=5).pack(side="left")
        tk.Button(f, text="→", command=self.do_rotate_center).pack(side="left", padx=3)

        # Масштаб относительно точки
        f = tk.LabelFrame(row2, text="Масштаб отн. точки")
        f.pack(side="left", padx=3, pady=2)
        self.sx_pt_var = tk.StringVar(value="1.25")
        self.sy_pt_var = tk.StringVar(value="1.25")
        self.scx_var = tk.StringVar(value="450")
        self.scy_var = tk.StringVar(value="300")
        tk.Label(f, text="sx").pack(side="left")
        tk.Entry(f, textvariable=self.sx_pt_var, width=5).pack(side="left")
        tk.Label(f, text="sy").pack(side="left")
        tk.Entry(f, textvariable=self.sy_pt_var, width=5).pack(side="left")
        tk.Label(f, text="cx").pack(side="left")
        tk.Entry(f, textvariable=self.scx_var, width=5).pack(side="left")
        tk.Label(f, text="cy").pack(side="left")
        tk.Entry(f, textvariable=self.scy_var, width=5).pack(side="left")
        tk.Button(f, text="→", command=self.do_scale_point).pack(side="left", padx=3)

        # Масштаб относительно центра
        f = tk.LabelFrame(row2, text="Масштаб отн. центра")
        f.pack(side="left", padx=3, pady=2)
        self.sx_c_var = tk.StringVar(value="0.8")
        self.sy_c_var = tk.StringVar(value="0.8")
        tk.Label(f, text="sx").pack(side="left")
        tk.Entry(f, textvariable=self.sx_c_var, width=5).pack(side="left")
        tk.Label(f, text="sy").pack(side="left")
        tk.Entry(f, textvariable=self.sy_c_var, width=5).pack(side="left")
        tk.Button(f, text="→", command=self.do_scale_center).pack(side="left", padx=3)

        # ----- ряд 3: статус + матрица -----
        row3 = tk.Frame(bar)
        row3.pack(side="top", fill="x")
        tk.Label(row3, text="Последнее преобразование:").pack(side="left", padx=(5, 2))
        self.status_var = tk.StringVar(value="—")
        tk.Label(row3, textvariable=self.status_var,
                 fg="darkblue").pack(side="left")
        self.matrix_text = tk.Text(row3, height=3, width=42,
                                   font=("Courier", 9), state="disabled")
        self.matrix_text.pack(side="left", padx=5)

    # ---------- вспомогательное: центр полигона ----------
    def polygon_center(self, poly):
        """
        Центр (центроид) полигона по формуле площадей:
            A  = 1/2 · Σ (x_i · y_{i+1} - x_{i+1} · y_i)
            Cx = 1/(6A) · Σ (x_i + x_{i+1}) · (x_i · y_{i+1} - x_{i+1} · y_i)
            Cy = 1/(6A) · Σ (y_i + y_{i+1}) · (x_i · y_{i+1} - x_{i+1} · y_i)
        Для вырожденных случаев (точка, ребро) — среднее/середина.
        """
        verts = poly["vertices"]
        n = len(verts)
        if n == 0:
            return None
        if n == 1:
            return float(verts[0][0]), float(verts[0][1])
        if n == 2:
            return ((verts[0][0] + verts[1][0]) / 2.0,
                    (verts[0][1] + verts[1][1]) / 2.0)

        A = 0.0
        cx = 0.0
        cy = 0.0
        for i in range(n):
            x1, y1 = verts[i]
            x2, y2 = verts[(i + 1) % n]
            cross = x1 * y2 - x2 * y1
            A += cross
            cx += (x1 + x2) * cross
            cy += (y1 + y2) * cross
        A *= 0.5
        if abs(A) < 1e-9:
            cx = sum(v[0] for v in verts) / n
            cy = sum(v[1] for v in verts) / n
            return cx, cy
        return cx / (6.0 * A), cy / (6.0 * A)

    # ---------- вывод матрицы в панель ----------
    def _show_matrix(self, name, M):
        self.status_var.set(name)
        s = ""
        for row in M:
            s += "[" + "  ".join(f"{v:7.3f}" for v in row) + "]\n"
        self.matrix_text.config(state="normal")
        self.matrix_text.delete("1.0", "end")
        self.matrix_text.insert("1.0", s.strip())
        self.matrix_text.config(state="disabled")

    # ---------- применение матрицы к активному полигону ----------
    def _apply_matrix_to_active(self, M, name):
        if self.active_polygon is None or \
           not (0 <= self.active_polygon < len(self.polygons)):
            messagebox.showinfo(
                "Преобразование",
                "Сначала выберите полигон (режим «Выбор», клик по вершине)."
            )
            return
        poly = self.polygons[self.active_polygon]
        new_verts = []
        for (x, y) in poly["vertices"]:
            nx, ny, w = mat_vec_mul(M, (x, y, 1.0))
            if abs(w) < 1e-12:
                w = 1.0
            new_verts.append((nx / w, ny / w))
        poly["vertices"] = new_verts
        self._show_matrix(name, M)
        self.redraw()

    # ---------- обёртки для кнопок ----------
    def _num(self, var, name):
        try:
            return float(var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка ввода",
                                 f"Не удалось прочитать число: {name}")
            return None

    def do_translate(self):
        dx = self._num(self.dx_var, "dx")
        if dx is None:
            return
        dy = self._num(self.dy_var, "dy")
        if dy is None:
            return
        self._apply_matrix_to_active(translation_matrix(dx, dy),
                                     f"Смещение ({dx:g}, {dy:g})")

    def do_rotate_point(self):
        ang = self._num(self.ang_pt_var, "φ")
        if ang is None:
            return
        cx = self._num(self.rcx_var, "cx")
        if cx is None:
            return
        cy = self._num(self.rcy_var, "cy")
        if cy is None:
            return
        self._apply_matrix_to_active(rotation_matrix_about(ang, cx, cy),
                                     f"Поворот {ang:g}° вокруг ({cx:g},{cy:g})")

    def do_rotate_center(self):
        ang = self._num(self.ang_c_var, "φ")
        if ang is None:
            return
        if self.active_polygon is None or \
           not (0 <= self.active_polygon < len(self.polygons)):
            messagebox.showinfo("Преобразование",
                                "Сначала выберите полигон.")
            return
        poly = self.polygons[self.active_polygon]
        cx, cy = self.polygon_center(poly)
        self._apply_matrix_to_active(rotation_matrix_about(ang, cx, cy),
                                     f"Поворот {ang:g}° вокруг центра")

    def do_scale_point(self):
        sx = self._num(self.sx_pt_var, "sx")
        if sx is None:
            return
        sy = self._num(self.sy_pt_var, "sy")
        if sy is None:
            return
        cx = self._num(self.scx_var, "cx")
        if cx is None:
            return
        cy = self._num(self.scy_var, "cy")
        if cy is None:
            return
        self._apply_matrix_to_active(scaling_matrix_about(sx, sy, cx, cy),
                                     f"Масштаб {sx:g}×{sy:g} отн. ({cx:g},{cy:g})")

    def do_scale_center(self):
        sx = self._num(self.sx_c_var, "sx")
        if sx is None:
            return
        sy = self._num(self.sy_c_var, "sy")
        if sy is None:
            return
        if self.active_polygon is None or \
           not (0 <= self.active_polygon < len(self.polygons)):
            messagebox.showinfo("Преобразование",
                                "Сначала выберите полигон.")
            return
        poly = self.polygons[self.active_polygon]
        cx, cy = self.polygon_center(poly)
        self._apply_matrix_to_active(scaling_matrix_about(sx, sy, cx, cy),
                                     f"Масштаб {sx:g}×{sy:g} отн. центра")

    # ---------- визуализация центра активного полигона ----------
    def _draw_active_center(self):
        if self.active_polygon is None:
            return
        if not (0 <= self.active_polygon < len(self.polygons)):
            return
        poly = self.polygons[self.active_polygon]
        c = self.polygon_center(poly)
        if c is None:
            return
        cx, cy = c
        # зеленоватая точка + подпись координат
        r = 4
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill="lime", outline="darkgreen", width=1)
        self.canvas.create_text(cx + 8, cy, anchor="w",
                                fill="darkgreen",
                                text=f"центр ({cx:.1f}, {cy:.1f})")

#  ЧАСТЬ 3. ГЕОМЕТРИЧЕСКИЕ ПРОВЕРКИ В РЕАЛЬНОМ ВРЕМЕНИ

def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


SNAP_PX = 1.0   

def point_on_segment(p, a, b, eps=SNAP_PX):
    if abs(orient(a, b, p)) > eps:
        return False
    return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
            min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps)




def _dist_point_line(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-12:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    return abs(orient(a, b, p)) / L

def point_on_segment(p, a, b, tol=SNAP_PX):
    if _dist_point_line(p, a, b) > tol:
        return False
    if p[0] < min(a[0], b[0]) - tol or p[0] > max(a[0], b[0]) + tol:
        return False
    if p[1] < min(a[1], b[1]) - tol or p[1] > max(a[1], b[1]) + tol:
        return False
    return True

def classify_point_vs_edge(p, a, b, tol=SNAP_PX):
    if point_on_segment(p, a, b,tol):
        return 'on'
    o = orient(a, b, p)
    return 'left' if o > 0 else 'right'


def segment_intersection(a, b, c, d, eps=1e-9):
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    denom = r[0] * s[1] - r[1] * s[0]

    if abs(denom) < eps:
        if abs(orient(a, b, c)) > eps:
            return None, None
        rr = r[0] * r[0] + r[1] * r[1]
        if rr < eps:
            return (a, 'endpoint') if point_on_segment(a, c, d) else (None, None)
        t0 = ((c[0] - a[0]) * r[0] + (c[1] - a[1]) * r[1]) / rr
        t1 = ((d[0] - a[0]) * r[0] + (d[1] - a[1]) * r[1]) / rr
        lo, hi = min(t0, t1), max(t0, t1)
        lo, hi = max(lo, 0.0), min(hi, 1.0)
        if lo > hi:
            return None, None
        if abs(lo - hi) < eps:
            return (a[0] + lo * r[0], a[1] + lo * r[1]), 'endpoint'
        mid = 0.5 * (lo + hi)
        return (a[0] + mid * r[0], a[1] + mid * r[1]), 'collinear'

    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / denom
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / denom
    if -eps <= t <= 1.0 + eps and -eps <= u <= 1.0 + eps:
        p = (a[0] + t * r[0], a[1] + t * r[1])
        on_ab = abs(t) < eps or abs(t - 1.0) < eps
        on_cd = abs(u) < eps or abs(u - 1.0) < eps
        return p, ('endpoint' if (on_ab or on_cd) else 'proper')
    return None, None


def point_in_polygon(p, verts, eps=1e-9):
    n = len(verts)
    if n == 0:
        return 'outside'
    if n == 1:
        return 'on_boundary' if point_on_segment(p, verts[0], verts[0]) else 'outside'
    if n == 2:
        return 'on_boundary' if point_on_segment(p, verts[0], verts[1]) else 'outside'

    for i in range(n):
        if point_on_segment(p, verts[i], verts[(i + 1) % n], eps):
            return 'on_boundary'

    x, y = p
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if (yi > y) != (yj > y):
            x_int = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_int:
                inside = not inside
        j = i
    return 'inside' if inside else 'outside'


def _polygon_edges(verts):
    n = len(verts)
    if n < 2:
        return []
    if n == 2:
        return [(verts[0], verts[1])]
    return [(verts[i], verts[(i + 1) % n]) for i in range(n)]


def _all_edges(app):
    edges = []
    for poly in app.polygons:
        edges.extend(_polygon_edges(poly["vertices"]))
    return edges


#  Установка части 3 в уже созданный PolygonApp

def install_part3(app):
    """
    Монки-патч: добавляет к экземпляру PolygonApp инструменты части 3,
    не изменяя исходный класс.
    """

    # ---------- состояние ----------
    app.p3_edge_pts         = []   # точки строящегося отрезка (0, 1 или 2)
    app.p3_segments         = []   # построенные вспомогательные отрезки
    app.p3_intersections    = []   # (p, kind, seg1, seg2)
    app.p3_probe_points     = []   # (p, [(poly_index, 'inside'|'outside'|'on_boundary'), ...])
    app.p3_classify_pt      = None # точка для классификации
    app.p3_classify_results = []   # [(a, b, 'left'|'right'|'on'), ...]

    # ---------- UI ----------
    bar = tk.Frame(app.extra_bar)
    bar.pack(side="top", fill="x")

    f = tk.LabelFrame(bar, text="Часть 3: геометрия в реальном времени")
    f.pack(side="left", padx=3, pady=2)

    tk.Label(f, text="Инструмент:").pack(side="left")
    tk.Radiobutton(f, text="Пересечение рёбер",
                   variable=app.tool, value="p3_intersect",
                   command=app._on_tool_change).pack(side="left")
    tk.Radiobutton(f, text="Точка в полигоне",
                   variable=app.tool, value="p3_inside",
                   command=app._on_tool_change).pack(side="left")
    tk.Radiobutton(f, text="Слева/справа от ребра",
                   variable=app.tool, value="p3_classify",
                   command=app._on_tool_change).pack(side="left")

    tk.Button(f, text="Сбросить геометрию",
              command=lambda: _p3_reset(app)).pack(side="left", padx=6)

    tk.Label(bar,
             text="• «Пересечение рёбер»: 2 клика = вспомогательное ребро.\n"
                  "• «Точка в полигоне» и «Классификация»: 1 клик.\n"
                  "• В режиме «Выбор» инструменты части 3 не мешают выбору.",
             fg="gray", justify="left").pack(side="left", padx=6)

    # ---------- сохраняем оригинальные связанные методы ----------
    orig_left   = app.on_left_click
    orig_right  = app.on_right_click
    orig_motion = app.on_motion
    orig_redraw = app.redraw

    # ---------- новые обработчики ----------
    def on_left_click_p3(event):
        if app.mode.get() == "select":
            orig_left(event)
            return
        t = app.tool.get()
        if t == "p3_intersect":
            _p3_click_intersect(app, event.x, event.y)
        elif t == "p3_inside":
            _p3_click_inside(app, event.x, event.y)
        elif t == "p3_classify":
            _p3_click_classify(app, event.x, event.y)
        else:
            orig_left(event)

    def on_right_click_p3(event):
        if app.tool.get() == "p3_intersect" and app.p3_edge_pts:
            app.p3_edge_pts = []
            app.redraw()
            return
        orig_right(event)

    def on_motion_p3(event):
        if app.tool.get() == "p3_intersect" and app.p3_edge_pts:
            app.redraw()
        else:
            orig_motion(event)

    def redraw_p3():
        orig_redraw()
        _p3_draw(app)

    # ---------- КЛЮЧЕВОЕ: переподписываем обработчики на canvas ----------
    # tkinter держит callback с момента первого bind(...),
    # поэтому подмены app.on_* недостаточно — нужен новый bind.
    app.canvas.bind("<Button-1>", on_left_click_p3)
    app.canvas.bind("<Button-3>", on_right_click_p3)
    app.canvas.bind("<Motion>",   on_motion_p3)

    # redraw() вызывается из Python-кода как self.redraw(),
    # поэтому достаточно подменить атрибут экземпляра.
    app.redraw = redraw_p3

    # сохраним ссылки (на случай отладки / снятия патча)
    app._p3_handlers = (on_left_click_p3, on_right_click_p3,
                        on_motion_p3, redraw_p3)

#  Обработчики кликов

def _p3_reset(app):
    app.p3_edge_pts         = []
    app.p3_segments         = []
    app.p3_intersections    = []
    app.p3_probe_points     = []
    app.p3_classify_pt      = None
    app.p3_classify_results = []
    app.redraw()


def _p3_click_intersect(app, x, y):
    """2 клика задают вспомогательное ребро; ищем пересечения с рёбрами полигонов."""
    app.p3_edge_pts.append((x, y))
    if len(app.p3_edge_pts) < 2:
        app.redraw()
        return

    a, b = app.p3_edge_pts[0], app.p3_edge_pts[1]
    app.p3_segments.append((a, b))

    # ищем пересечения с каждым ребром каждого полигона
    for (c, d) in _all_edges(app):
        p, kind = segment_intersection(a, b, c, d)
        if p is not None:
            app.p3_intersections.append((p, kind, (a, b), (c, d)))

    app.p3_edge_pts = []
    app.redraw()


def _p3_click_inside(app, x, y):
    """Клик задаёт точку; проверяем её принадлежность каждому полигону."""
    p = (x, y)
    results = []
    for i, poly in enumerate(app.polygons):
        res = point_in_polygon(p, poly["vertices"])
        results.append((i, res))
    app.p3_probe_points.append((p, results))
    app.redraw()


def _p3_click_classify(app, x, y):
    """Клик задаёт точку; классифицируем её относительно рёбер активного
       полигона (или всех полигонов, если активный не выбран)."""
    p = (x, y)
    if (app.active_polygon is not None and
            0 <= app.active_polygon < len(app.polygons)):
        edges = _polygon_edges(app.polygons[app.active_polygon]["vertices"])
    else:
        edges = _all_edges(app)

    app.p3_classify_pt = p
    app.p3_classify_results = [
        (a, b, classify_point_vs_edge(p, a, b)) for (a, b) in edges
    ]
    app.redraw()


#  Отрисовка поверх сцены

def _p3_draw(app):
    c = app.canvas

    # 1) построенные вспомогательные отрезки
    for (a, b) in app.p3_segments:
        c.create_line(a[0], a[1], b[0], b[1], fill="magenta", width=2)

    # 2) текущий отрезок, тянущийся за мышью
    if app.p3_edge_pts:
        x, y = app.p3_edge_pts[0]
        mx = c.winfo_pointerx() - c.winfo_rootx()
        my = c.winfo_pointery() - c.winfo_rooty()
        c.create_line(x, y, mx, my, fill="magenta", width=2, dash=(5, 3))
        c.create_oval(x - 4, y - 4, x + 4, y + 4,
                      fill="magenta", outline="purple")
        c.create_text(10, 50, anchor="nw", fill="magenta",
                      text="Кликните вторую точку отрезка — "
                           "найдём пересечения с рёбрами полигонов "
                           "(ПКМ — отмена)")

    # 3) точки пересечения
    for (p, kind, s1, s2) in app.p3_intersections:
        x, y = p
        color = {"proper": "orange",
                 "endpoint": "red",
                 "collinear": "purple"}.get(kind, "orange")
        r = 5
        c.create_oval(x - r, y - r, x + r, y + r,
                      fill=color, outline="black", width=1)
        c.create_text(x + 8, y - 10, anchor="w", fill="black",
                      font=("", 8),
                      text=f"{kind} ({x:.1f}, {y:.1f})")

    # 4) точки-пробы (проверка принадлежности полигону)
    for (p, results) in app.p3_probe_points:
        x, y = p
        has_in = any(r == 'inside' for _, r in results)
        has_on = any(r == 'on_boundary' for _, r in results)
        if has_on:
            fill = "gold"
        elif has_in:
            fill = "lime green"
        else:
            fill = "salmon"
        c.create_oval(x - 6, y - 6, x + 6, y + 6,
                      fill=fill, outline="black", width=2)
        lines = [f"P{i}: {r}" for i, r in results]
        if lines:
            c.create_text(x + 10, y + 8, anchor="nw",
                          fill="black", font=("", 8),
                          text="\n".join(lines))

    # 5) классификация точки относительно рёбер
    if app.p3_classify_pt is not None:
        x, y = app.p3_classify_pt
        c.create_oval(x - 5, y - 5, x + 5, y + 5,
                      fill="cyan", outline="blue", width=2)
        c.create_text(x + 8, y + 8, anchor="w", fill="blue",
                      font=("", 8),
                      text=f"точка ({x:.1f}, {y:.1f})")
        for (a, b, rel) in app.p3_classify_results:
            mx = 0.5 * (a[0] + b[0])
            my = 0.5 * (a[1] + b[1])
            fill = {"left": "green", "right": "red", "on": "blue"}[rel]
            sym  = {"left": "L", "right": "R", "on": "="}[rel]
            c.create_oval(mx - 7, my - 7, mx + 7, my + 7,
                          fill=fill, outline="black")
            c.create_text(mx, my, text=sym,
                          fill="white", font=("", 8, "bold"))

#  Запуск

if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonApp(root)
    install_part3(app)        
    root.mainloop()