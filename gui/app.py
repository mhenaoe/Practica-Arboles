"""
app.py — Interfaz gráfica de DocuTree. Tema claro estilo DataTree.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arbol import ArbolDocumental
from src.coleccion import ColeccionDocumental
from src.estructuras import ListaDocumentos, NodoArbol

# ── Paleta ─────────────────────────────────────────────────────────────────────
C = {
    "bg":       "#ffffff",
    "sidebar":  "#f6faf7",
    "content":  "#f9fbf9",
    "border":   "#e2e8e4",
    "border2":  "#e8ede9",
    "card":     "#ffffff",
    "accent":   "#1D9E75",
    "accent2":  "#5DCAA5",
    "accent3":  "#9FE1CB",
    "text":     "#1a2e22",
    "text2":    "#2a3d30",
    "text3":    "#4a6e58",
    "muted":    "#7aab8a",
    "dim":      "#93b8a0",
    "dimmer":   "#9fbfa9",
    "badge":    "#dcf2e8",
    "badge_fg": "#0f6e56",
    "nav_fg":   "#4a7560",
    "nav_act":  "#0f6e56",
    "nav_abg":  "#e0f2e9",
    "nav_hov":  "#ecf5ef",
    "err":      "#b84a1a",
    "err_bg":   "#fff3ef",
    "inp":      "#f6faf7",
    "inp_bdr":  "#d4e8da",
    "hint":     "#f0faf4",
    "hint_bdr": "#c8e8d4",
    "ll":       "#f4faf6",
    "ll_bdr":   "#c8e8d4",
    "tbl":      "#edf2ee",
    "tbl_h":    "#f6faf7",
}

FIELDS    = ["id", "nombre", "edad", "ciudad", "direccion.barrio", "direccion.codigo_postal"]

OPERATORS = [
    "Igual a  (=)",
    "Diferente  (≠)",
    "Mayor que  (>)",
    "Mayor o igual  (≥)",
    "Menor que  (<)",
    "Menor o igual  (≤)",
]
OPERATOR_MAP: dict[str, str] = {
    "Igual a  (=)":        "$eq",
    "Diferente  (≠)":      "$ne",
    "Mayor que  (>)":      "$gt",
    "Mayor o igual  (≥)":  "$gte",
    "Menor que  (<)":      "$lt",
    "Menor o igual  (≤)":  "$lte",
}
STRING_FIELDS = frozenset({"nombre", "ciudad", "direccion.barrio", "direccion.codigo_postal"})
NUMERIC_OPS   = frozenset({"$gt", "$gte", "$lt", "$lte"})

_NAME_RE = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$")
_TEXT_RE = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s\-]+$")
_CP_RE   = re.compile(r"^\d{1,10}$")

NAV = [
    ("Dashboard",  "dashboard"),
    ("Explorador", "explorer"),
    ("Insertar",   "insert"),
    ("Buscar",     "search"),
    ("Estructura", "structure"),
]

# ── Fuentes (detección en tiempo de ejecución) ─────────────────────────────────
class F:
    SANS = "Helvetica Neue"
    MONO = "Menlo"

    @classmethod
    def setup(cls) -> None:
        available = set(tkfont.families())
        cls.SANS = next(
            (f for f in ["SF Pro Display", "Inter", "Helvetica Neue", "Arial"]
             if f in available), "Helvetica Neue")
        cls.MONO = next(
            (f for f in ["SF Mono", "Menlo", "Monaco", "Consolas", "Courier New"]
             if f in available), "Courier New")

    @classmethod
    def r(cls, size: int) -> tuple:
        return (cls.SANS, size)

    @classmethod
    def b(cls, size: int) -> tuple:
        return (cls.SANS, size, "bold")

    @classmethod
    def m(cls, size: int) -> tuple:
        return (cls.MONO, size)

    @classmethod
    def mb(cls, size: int) -> tuple:
        return (cls.MONO, size, "bold")


class RoundedButton(tk.Canvas):
    """Boton con esquinas redondeadas (rounded rectangle, radio=7px)."""

    def __init__(self, parent, text: str, bg: str, fg: str, command,
                 font=None, padx: int = 16, pady: int = 8,
                 border: str | None = None, **kw):
        self._text   = text
        self._bg     = bg
        self._fg     = fg
        self._border = border
        self._cmd    = command
        self._font   = font or F.r(11)

        weight = self._font[2] if len(self._font) > 2 else "normal"
        fobj = tkfont.Font(family=self._font[0],
                           size=abs(self._font[1]), weight=weight)
        tw = fobj.measure(text)
        th = fobj.metrics("linespace")
        self._W = tw + padx * 2
        self._H = th + pady * 2

        try:
            cbg = parent.cget("bg")
        except Exception:
            cbg = C["bg"]

        super().__init__(parent, width=self._W, height=self._H,
            highlightthickness=0, bd=0, bg=cbg, **kw)

        self._hover = self._shift(bg, -12)
        self._press = self._shift(bg, -26)
        self._paint(self._bg)

        self.bind("<Enter>",           lambda _: self._paint(self._hover))
        self.bind("<Leave>",           lambda _: self._paint(self._bg))
        self.bind("<Button-1>",        self._on_press)
        self.bind("<ButtonRelease-1>", lambda _: self._paint(self._bg))

    @staticmethod
    def _shift(color: str, delta: int) -> str:
        r = max(0, min(255, int(color[1:3], 16) + delta))
        g = max(0, min(255, int(color[3:5], 16) + delta))
        b = max(0, min(255, int(color[5:7], 16) + delta))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _rounded_pts(self, radius: int = 7) -> list:
        m = 0.5
        x0, y0 = m, m
        x1, y1 = self._W - m, self._H - m
        r = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
        steps = 10
        pts: list[float] = []
        for cx, cy, a0 in [
            (x1 - r, y0 + r, -90),
            (x1 - r, y1 - r,   0),
            (x0 + r, y1 - r,  90),
            (x0 + r, y0 + r, 180),
        ]:
            for i in range(steps + 1):
                a = math.radians(a0 + 90 * i / steps)
                pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        return pts

    def _paint(self, bg: str) -> None:
        self.delete("all")
        pts = self._rounded_pts()
        self.create_polygon(pts, fill=bg, outline="")
        if self._border:
            self.create_polygon(pts, fill="", outline=self._border, width=1.5)
        self.create_text(self._W // 2, self._H // 2,
            text=self._text, fill=self._fg, font=self._font)

    def _on_press(self, _=None) -> None:
        self._paint(self._press)
        if self._cmd:
            self.after(80, self._cmd)


class DocuTreeGUI:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        F.setup()

        self.root.title("DocuTree  ·  Mini MongoDB")
        self.root.configure(bg=C["sidebar"])
        self.root.geometry("1200x700")
        self.root.minsize(980, 620)

        self.coleccion: ColeccionDocumental | None = None
        self.doc_roots: list[NodoArbol] = []
        self.active_view = "dashboard"
        self._nav: dict[str, dict] = {}
        self._insert_entries: dict[str, tuple] = {}

        self._setup_styles()
        self._build_layout()
        self._load_collection()
        self._switch_view("dashboard")

    # ── Estilos ttk ───────────────────────────────────────────────────────────

    def _setup_styles(self) -> None:
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview",
            background=C["card"], foreground=C["text2"],
            fieldbackground=C["card"], rowheight=30,
            font=F.r(11), borderwidth=0)
        s.configure("Treeview.Heading",
            background=C["tbl_h"], foreground=C["muted"],
            font=F.b(10), borderwidth=0, relief=tk.FLAT)
        s.map("Treeview",
            background=[("selected", C["hint"])],
            foreground=[("selected", C["text"])])
        s.configure("TCombobox",
            fieldbackground=C["inp"], background=C["inp"],
            foreground=C["text"], selectbackground=C["accent2"],
            arrowcolor=C["muted"])
        s.map("TCombobox", fieldbackground=[("readonly", C["inp"])])

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.sidebar = tk.Frame(self.root, bg=C["sidebar"], width=214)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Frame(self.root, bg=C["border"], width=1).pack(side=tk.LEFT, fill=tk.Y)

        self.main_area = tk.Frame(self.root, bg=C["bg"])
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_main()

    # ══════════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════════

    def _build_sidebar(self) -> None:
        # Logo
        logo = tk.Frame(self.sidebar, bg=C["sidebar"], padx=16, pady=14)
        logo.pack(fill=tk.X)
        tk.Frame(self.sidebar, bg=C["border2"], height=1).pack(fill=tk.X)

        icon_box = tk.Frame(logo, bg=C["accent"], width=34, height=34)
        icon_box.pack(side=tk.LEFT)
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text="DT", bg=C["accent"], fg="#fff",
            font=F.mb(10)).place(relx=0.5, rely=0.5, anchor="center")

        tf = tk.Frame(logo, bg=C["sidebar"])
        tf.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(tf, text="DocuTree",
            bg=C["sidebar"], fg=C["text"], font=F.b(13)).pack(anchor="w")
        tk.Label(tf, text="v1.0  ·  Universidad",
            bg=C["sidebar"], fg=C["muted"], font=F.r(9)).pack(anchor="w")

        # Nav
        self._sb_label("MENU")
        for label, view in NAV:
            self._nav_item(label, view)

        # Arbol schema
        tk.Frame(self.sidebar, bg=C["border2"], height=1).pack(fill=tk.X, pady=(8, 0))
        self._sb_label("Arbol Documental")

        schema = [
            (0, "●", "documento"),
            (1, "·", "id"),
            (1, "·", "nombre"),
            (1, "·", "edad"),
            (1, "·", "ciudad"),
            (1, "●", "direccion"),
            (2, "·", "barrio"),
            (2, "·", "cod. postal"),
        ]
        dot_colors = {0: C["accent"], 1: C["accent2"], 2: C["accent3"]}
        for lvl, dot, name in schema:
            f = tk.Frame(self.sidebar, bg=C["sidebar"])
            f.pack(fill=tk.X)
            tk.Label(f, text=dot, bg=C["sidebar"], fg=dot_colors[lvl],
                font=F.r(11), padx=16 + lvl * 12, pady=2).pack(side=tk.LEFT)
            tk.Label(f, text=name, bg=C["sidebar"], fg=C["muted"],
                font=F.m(10)).pack(side=tk.LEFT)

        # Footer
        tk.Frame(self.sidebar, bg=C["border2"], height=1).pack(fill=tk.X, side=tk.BOTTOM)
        foot = tk.Frame(self.sidebar, bg=C["sidebar"], padx=16, pady=12)
        foot.pack(fill=tk.X, side=tk.BOTTOM)
        self._foot_docs = tk.Label(foot, text="0 documentos",
            bg=C["sidebar"], fg=C["muted"], font=F.r(11))
        self._foot_docs.pack(anchor="w")
        tk.Label(foot, text="NodoArbol + ListaDocumentos",
            bg=C["sidebar"], fg=C["dimmer"], font=F.r(9)).pack(anchor="w")

    def _sb_label(self, text: str) -> None:
        tk.Label(self.sidebar, text=text,
            bg=C["sidebar"], fg=C["dim"],
            font=F.b(9), padx=16, pady=6).pack(anchor="w")

    def _nav_item(self, label: str, view: str) -> None:
        outer = tk.Frame(self.sidebar, bg=C["sidebar"])
        outer.pack(fill=tk.X)

        ind = tk.Frame(outer, bg=C["sidebar"], width=3)
        ind.pack(side=tk.LEFT, fill=tk.Y)

        inner = tk.Frame(outer, bg=C["sidebar"], padx=14, pady=9)
        inner.pack(fill=tk.BOTH, expand=True)
        lbl = tk.Label(inner, text=label,
            bg=C["sidebar"], fg=C["nav_fg"], font=F.r(12), anchor="w")
        lbl.pack(fill=tk.X)

        self._nav[view] = {"outer": outer, "inner": inner, "lbl": lbl, "ind": ind}

        all_w = [outer, inner, lbl]

        def click(_=None, v=view):
            self._switch_view(v)

        def enter(_=None):
            if self.active_view != view:
                for w in all_w:
                    w.config(bg=C["nav_hov"])

        def leave(_=None):
            if self.active_view != view:
                for w in all_w:
                    w.config(bg=C["sidebar"])

        for w in all_w:
            w.bind("<Button-1>", click)
            w.bind("<Enter>",    enter)
            w.bind("<Leave>",    leave)

    # ══════════════════════════════════════════════════════════════════
    #  AREA PRINCIPAL
    # ══════════════════════════════════════════════════════════════════

    def _build_main(self) -> None:
        top = tk.Frame(self.main_area, bg=C["bg"], padx=20, pady=11)
        top.pack(fill=tk.X)
        tk.Frame(self.main_area, bg=C["border"], height=1).pack(fill=tk.X)

        self._page_title = tk.Label(top, text="Dashboard",
            bg=C["bg"], fg=C["text"], font=F.b(14))
        self._page_title.pack(side=tk.LEFT)

        self._mk_btn(top, "Nuevo", C["accent"], "#fff",
            lambda: self._switch_view("insert"),
            font=F.b(11), px=18, py=8).pack(side=tk.RIGHT)

        # Barra de busqueda (pildora) — click abre la vista de busqueda
        RoundedButton(top,
            text="  Buscar documento...",
            bg=C["hint"], fg=C["muted"],
            command=lambda: self._switch_view("search"),
            font=F.r(11), padx=18, pady=8,
            border=C["hint_bdr"]).pack(side=tk.RIGHT, padx=(0, 10))

        # Contenido scrollable
        co = tk.Frame(self.main_area, bg=C["content"])
        co.pack(fill=tk.BOTH, expand=True)

        self._cc = tk.Canvas(co, bg=C["content"], highlightthickness=0)
        self._vsb = tk.Scrollbar(co, orient="vertical", command=self._cc.yview)
        self.content = tk.Frame(self._cc, bg=C["content"])
        self.content.bind("<Configure>",
            lambda _: self._cc.configure(scrollregion=self._cc.bbox("all")))
        self._cwin = self._cc.create_window((0, 0), window=self.content, anchor="nw")
        self._cc.configure(yscrollcommand=self._vsb.set)
        self._cc.bind("<Configure>",
            lambda e: self._cc.itemconfig(self._cwin, width=e.width))
        self._cc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._vsb.pack(side=tk.RIGHT, fill=tk.Y)

        for w in (self._cc, self.content):
            w.bind("<MouseWheel>",
                lambda e: self._cc.yview_scroll(-1 if e.delta > 0 else 1, "units"))
            w.bind("<Button-4>", lambda _: self._cc.yview_scroll(-1, "units"))
            w.bind("<Button-5>", lambda _: self._cc.yview_scroll(1, "units"))

    # ── Cambio de vista ────────────────────────────────────────────────────────

    def _switch_view(self, view: str, data=None) -> None:
        self.active_view = view
        titles = {
            "dashboard": "Dashboard",
            "explorer":  "Explorador de documentos",
            "insert":    "Insertar documento",
            "search":    "Buscar",
            "structure": "Estructura de datos",
            "detail":    "Detalle del documento",
        }
        self._page_title.config(text=titles.get(view, view))

        for v, refs in self._nav.items():
            active = v == view
            bg = C["nav_abg"] if active else C["sidebar"]
            refs["outer"].config(bg=bg)
            refs["inner"].config(bg=bg)
            refs["lbl"].config(
                bg=bg,
                fg=C["nav_act"] if active else C["nav_fg"],
                font=F.b(12) if active else F.r(12))
            refs["ind"].config(bg=C["accent"] if active else C["sidebar"])

        self._cc.yview_moveto(0)
        for w in self.content.winfo_children():
            w.destroy()

        {
            "dashboard": self._v_dashboard,
            "explorer":  self._v_explorer,
            "insert":    self._v_insert,
            "search":    self._v_search,
            "structure": self._v_structure,
            "detail":    lambda: self._v_detail(data),
        }.get(view, lambda: None)()

    # ── Datos ──────────────────────────────────────────────────────────────────

    def _load_collection(self) -> None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "datos", "documentos.json")
        try:
            self.coleccion = ColeccionDocumental("documentos")
            self.coleccion.cargar_desde_archivo(path)
            self.doc_roots = list(self.coleccion.documentos)
            self._foot_docs.config(text=f"{len(self.doc_roots)} documentos")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _docs(self) -> list[dict]:
        return [ArbolDocumental.a_dict(r) for r in self.doc_roots]

    # ── Widgets comunes ────────────────────────────────────────────────────────

    def _mk_btn(self, parent, text, bg, fg, cmd,
                font=None, px=18, py=8, border=None) -> RoundedButton:
        return RoundedButton(parent, text=text, bg=bg, fg=fg,
            command=cmd, font=font or F.r(11),
            padx=px, pady=py, border=border)

    def _card(self, pady=(0, 14)) -> tk.Frame:
        wrap = tk.Frame(self.content, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill=tk.X, padx=20, pady=pady)
        inner = tk.Frame(wrap, bg=C["card"], padx=18, pady=18)
        inner.pack(fill=tk.BOTH, expand=True)
        return inner

    def _badge(self, parent, text: str) -> tk.Label:
        return tk.Label(parent, text=text,
            bg=C["badge"], fg=C["badge_fg"], font=F.m(10), padx=8, pady=2)

    def _input_entry(self, parent, placeholder: str) -> tk.Entry:
        e = tk.Entry(parent, bg=C["inp"], fg=C["muted"],
            insertbackground=C["accent"], font=F.r(11),
            relief=tk.FLAT, highlightthickness=1,
            highlightbackground=C["inp_bdr"], highlightcolor=C["accent"])
        e.insert(0, placeholder)

        def fi(_):
            if e.get() == placeholder:
                e.delete(0, tk.END)
                e.config(fg=C["text"])

        def fo(_):
            if not e.get():
                e.insert(0, placeholder)
                e.config(fg=C["muted"])

        e.bind("<FocusIn>",  fi)
        e.bind("<FocusOut>", fo)
        return e

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: DASHBOARD
    # ══════════════════════════════════════════════════════════════════

    def _v_dashboard(self) -> None:
        docs = self._docs()
        tk.Frame(self.content, bg=C["content"], height=20).pack()

        # Stat cards
        row = tk.Frame(self.content, bg=C["content"])
        row.pack(fill=tk.X, padx=20, pady=(0, 14))
        for lbl, val, sub in [
            ("Documentos",  str(len(docs)), "registros totales"),
            ("Nodos arbol", "7",            "campos por documento"),
            ("Profundidad", "3",            "niveles maximos"),
            ("Operadores",  "6",            "$eq $ne $gt $gte $lt $lte"),
        ]:
            c = tk.Frame(row, bg=C["card"],
                highlightthickness=1, highlightbackground=C["border"],
                padx=14, pady=14)
            c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
            tk.Label(c, text=lbl, bg=C["card"], fg=C["muted"],
                font=F.r(11)).pack(anchor="w")
            tk.Label(c, text=val, bg=C["card"], fg=C["text"],
                font=F.b(22)).pack(anchor="w", pady=2)
            tk.Label(c, text=sub, bg=C["card"], fg=C["dimmer"],
                font=F.r(9)).pack(anchor="w")

        # Registros recientes
        card = self._card(pady=(0, 14))
        hdr = tk.Frame(card, bg=C["card"])
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr, text="Registros recientes",
            bg=C["card"], fg=C["text"], font=F.b(12)).pack(side=tk.LEFT)
        self._mk_btn(hdr, "Ver todos", C["inp"], C["text3"],
            lambda: self._switch_view("explorer"),
            font=F.r(10), px=14, py=6,
            border=C["inp_bdr"]).pack(side=tk.RIGHT)

        cols = ("nombre", "edad", "ciudad", "nodo")
        tv = ttk.Treeview(card, columns=cols, show="headings",
            height=4, selectmode="browse")
        for col, w, lbl in [("nombre", 200, "NOMBRE"), ("edad", 60, "EDAD"),
                             ("ciudad", 130, "CIUDAD"), ("nodo", 120, "NODOS")]:
            tv.heading(col, text=lbl)
            tv.column(col, width=w, anchor="center" if col == "edad" else "w")
        for d in docs[:4]:
            tv.insert("", tk.END, values=(
                d.get("nombre", ""), d.get("edad", ""),
                d.get("ciudad", ""), "7 nodos"))
        tv.pack(fill=tk.X)
        tv.bind("<Double-1>", lambda e: self._tv_detail(tv))

        # Como funciona
        info = self._card(pady=(0, 20))
        tk.Label(info, text="Como funciona DocuTree",
            bg=C["card"], fg=C["text"], font=F.b(12)).pack(anchor="w", pady=(0, 10))
        cf = tk.Frame(info, bg=C["card"])
        cf.pack(fill=tk.X)
        for title, body in [
            ("Arbol Documental  —  NodoArbol",
             "Cada documento JSON se almacena como un arbol de nodos. "
             "Las claves son nodos internos y los valores primitivos son hojas. "
             "El acceso a campos anidados usa notacion de punto: direccion.barrio."),
            ("Lista Enlazada  —  ListaDocumentos",
             "La coleccion es una ListaDocumentos: lista enlazada de NodoColeccion. "
             "Cada nodo apunta a la raiz del arbol de un documento. "
             "Insercion en O(1) gracias al puntero de cola _cola."),
        ]:
            b = tk.Frame(cf, bg=C["hint"],
                highlightthickness=1, highlightbackground=C["hint_bdr"],
                padx=12, pady=12)
            b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
            tk.Label(b, text=title, bg=C["hint"], fg=C["text"],
                font=F.b(11)).pack(anchor="w", pady=(0, 5))
            tk.Label(b, text=body, bg=C["hint"], fg=C["text3"],
                font=F.r(10), wraplength=230, justify=tk.LEFT).pack(anchor="w")

    def _tv_detail(self, tv: ttk.Treeview) -> None:
        sel = tv.selection()
        if not sel:
            return
        vals = tv.item(sel[0], "values")
        name = vals[0] if vals else ""
        d = next((x for x in self._docs() if x.get("nombre") == name), None)
        if d:
            self._switch_view("detail", data=d.get("id"))

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: EXPLORADOR
    # ══════════════════════════════════════════════════════════════════

    def _v_explorer(self) -> None:
        docs = self._docs()
        tk.Frame(self.content, bg=C["content"], height=20).pack()

        card = self._card(pady=(0, 20))
        hdr = tk.Frame(card, bg=C["card"])
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr, text=f"Todos los documentos  ({len(docs)})",
            bg=C["card"], fg=C["text"], font=F.b(12)).pack(side=tk.LEFT)
        self._mk_btn(hdr, "Nuevo", C["accent"], "#fff",
            lambda: self._switch_view("insert"),
            font=F.b(10), px=10, py=4).pack(side=tk.RIGHT)

        cols = ("nombre", "edad", "ciudad", "barrio", "cp", "acc")
        tv = ttk.Treeview(card, columns=cols, show="headings",
            height=min(len(docs), 14))
        specs = [
            ("nombre", "NOMBRE",      190, "w"),
            ("edad",   "EDAD",         55, "center"),
            ("ciudad", "CIUDAD",      120, "w"),
            ("barrio", "BARRIO",      140, "w"),
            ("cp",     "COD. POSTAL", 110, "center"),
            ("acc",    "ACCION",       80, "center"),
        ]
        for col, lbl, w, anc in specs:
            tv.heading(col, text=lbl)
            tv.column(col, width=w, anchor=anc)

        for d in docs:
            direc = d.get("direccion", {})
            if not isinstance(direc, dict):
                direc = {}
            tv.insert("", tk.END, iid=str(d.get("id", "")),
                values=(
                    d.get("nombre", ""),
                    d.get("edad", ""),
                    d.get("ciudad", ""),
                    direc.get("barrio", ""),
                    direc.get("codigo_postal", ""),
                    "ver  /  eliminar",
                ))

        def on_click(event):
            row = tv.identify_row(event.y)
            col = tv.identify_column(event.x)
            if not row:
                return
            doc_id = int(row)
            if col == "#6":
                bbox = tv.bbox(row, "acc")
                if bbox and event.x - bbox[0] > bbox[2] // 2:
                    self._delete_doc(doc_id)
                else:
                    self._switch_view("detail", data=doc_id)
            else:
                self._switch_view("detail", data=doc_id)

        tv.bind("<Button-1>", on_click)
        tv.pack(fill=tk.X)

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: INSERTAR
    # ══════════════════════════════════════════════════════════════════

    def _v_insert(self) -> None:
        tk.Frame(self.content, bg=C["content"], height=20).pack()
        card = self._card(pady=(0, 20))

        tk.Label(card, text="Insertar nuevo documento",
            bg=C["card"], fg=C["text"], font=F.b(13)).pack(anchor="w", pady=(0, 16))

        self._insert_entries = {}
        pairs = [
            [("Nombre completo", "nombre", "Ej. Juan Perez"),
             ("Edad",            "edad",   "25")],
            [("Ciudad",          "ciudad", "Medellin"),
             ("Barrio",          "barrio", "El Poblado")],
            [("Codigo postal",   "cp",     "050021"),
             None],
        ]
        for pair in pairs:
            row = tk.Frame(card, bg=C["card"])
            row.pack(fill=tk.X, pady=(0, 12))
            for item in pair:
                if item is None:
                    tk.Frame(row, bg=C["card"]).pack(
                        side=tk.LEFT, fill=tk.X, expand=True)
                    continue
                lbl_text, key, ph = item
                col = tk.Frame(row, bg=C["card"])
                col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 14))
                tk.Label(col, text=lbl_text.upper(),
                    bg=C["card"], fg=C["muted"],
                    font=F.b(8)).pack(anchor="w", pady=(0, 4))
                e = self._input_entry(col, ph)
                e.pack(fill=tk.X, ipady=6)
                self._insert_entries[key] = (e, ph)

        # Hint
        hf = tk.Frame(card, bg=C["hint"],
            highlightthickness=1, highlightbackground=C["hint_bdr"])
        hf.pack(fill=tk.X, pady=(4, 16))
        tk.Label(hf,
            text="El documento se convertira a NodoArbol y se agregara a la\n"
                 "ListaDocumentos mediante agregar() en tiempo O(1).",
            bg=C["hint"], fg=C["text3"],
            font=F.r(10), justify=tk.LEFT,
            padx=12, pady=10).pack(anchor="w")

        bf = tk.Frame(card, bg=C["card"])
        bf.pack(anchor="w")
        self._mk_btn(bf, "Insertar en coleccion", C["accent"], "#fff",
            self._do_insert, font=F.b(11), px=18, py=8).pack(side=tk.LEFT, padx=(0, 10))
        self._mk_btn(bf, "Cancelar", C["inp"], C["muted"],
            lambda: self._switch_view("explorer"),
            font=F.r(11), px=16, py=8,
            border=C["inp_bdr"]).pack(side=tk.LEFT)

        self._insert_err = tk.Label(card, text="",
            bg=C["card"], fg=C["err"], font=F.r(10))
        self._insert_err.pack(anchor="w", pady=(8, 0))

    def _do_insert(self) -> None:
        vals = {}
        for key, (e, ph) in self._insert_entries.items():
            v = e.get().strip()
            vals[key] = "" if v == ph else v

        nombre = vals.get("nombre", "")
        if not nombre:
            self._insert_err.config(text="⚠  El nombre es obligatorio.")
            return
        if not _NAME_RE.match(nombre):
            self._insert_err.config(
                text="⚠  El nombre solo puede contener letras y espacios (sin numeros ni caracteres especiales).")
            return

        edad_str = vals.get("edad", "")
        if not edad_str:
            self._insert_err.config(text="⚠  La edad es obligatoria.")
            return
        if not edad_str.isdigit() or not (1 <= int(edad_str) <= 120):
            self._insert_err.config(
                text="⚠  La edad debe ser un numero entero entre 1 y 120.")
            return
        edad = int(edad_str)

        ciudad = vals.get("ciudad", "")
        if not ciudad:
            self._insert_err.config(text="⚠  La ciudad es obligatoria.")
            return
        if not _TEXT_RE.match(ciudad):
            self._insert_err.config(
                text="⚠  La ciudad solo puede contener letras, espacios y guiones.")
            return

        barrio = vals.get("barrio", "")
        if not barrio:
            self._insert_err.config(text="⚠  El barrio es obligatorio.")
            return
        if not _TEXT_RE.match(barrio):
            self._insert_err.config(
                text="⚠  El barrio solo puede contener letras, espacios y guiones.")
            return

        cp = vals.get("cp", "")
        if not cp:
            self._insert_err.config(text="⚠  El codigo postal es obligatorio.")
            return
        if not _CP_RE.match(cp):
            self._insert_err.config(
                text="⚠  El codigo postal solo puede contener digitos.")
            return

        all_docs = self._docs()
        new_id = max((d.get("id", 0) for d in all_docs), default=0) + 1

        new_doc = {
            "id": new_id,
            "nombre": vals["nombre"],
            "edad": edad,
            "ciudad": vals.get("ciudad", ""),
            "direccion": {
                "barrio": vals.get("barrio", ""),
                "codigo_postal": vals.get("cp", ""),
            },
        }

        raiz = ArbolDocumental.desde_dict(new_doc)
        self.coleccion.documentos.agregar(raiz)
        self.doc_roots = list(self.coleccion.documentos)
        self._foot_docs.config(text=f"{len(self.doc_roots)} documentos")
        messagebox.showinfo("Exito", f"Documento #{new_id} insertado correctamente.")
        self._switch_view("structure")

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: BUSCAR
    # ══════════════════════════════════════════════════════════════════

    def _v_search(self) -> None:
        tk.Frame(self.content, bg=C["content"], height=20).pack()
        card = self._card(pady=(0, 20))

        tk.Label(card, text="Buscar en la coleccion",
            bg=C["card"], fg=C["text"], font=F.b(13)).pack(anchor="w", pady=(0, 12))

        qb = tk.Frame(card, bg=C["card"])
        qb.pack(fill=tk.X, pady=(0, 4))

        for col_idx, lbl in enumerate(["CAMPO", "OPERADOR", "VALOR"]):
            tk.Label(qb, text=lbl, bg=C["card"], fg=C["muted"],
                font=F.b(8)).grid(row=0, column=col_idx,
                    sticky="w", padx=(0, 10), pady=(0, 4))

        self._sq_field = tk.StringVar(value=FIELDS[0])
        self._sq_op    = tk.StringVar(value=OPERATORS[0])

        fc = ttk.Combobox(qb, textvariable=self._sq_field, values=FIELDS,
            state="readonly", width=22)
        fc.grid(row=1, column=0, padx=(0, 10))
        fc.bind("<<ComboboxSelected>>", lambda _: self._live_filter())

        oc = ttk.Combobox(qb, textvariable=self._sq_op, values=OPERATORS,
            state="readonly", width=18)
        oc.grid(row=1, column=1, padx=(0, 10))
        oc.bind("<<ComboboxSelected>>", lambda _: self._live_filter())

        self._sq_val_e = tk.Entry(qb, bg=C["inp"], fg=C["text"],
            insertbackground=C["accent"], font=F.r(11),
            width=18, relief=tk.FLAT,
            highlightthickness=1, highlightbackground=C["inp_bdr"],
            highlightcolor=C["accent"])
        self._sq_val_e.grid(row=1, column=2, padx=(0, 10), ipady=5)
        self._sq_val_e.bind("<KeyRelease>", lambda _: self._live_filter())
        self._sq_val_e.bind("<Return>",     lambda _: self._do_search())

        self._mk_btn(qb, "Buscar", C["accent"], "#fff",
            self._do_search, font=F.b(10), px=12, py=5).grid(row=1, column=3)

        tk.Label(card, text=f"DocuTree O(N · C · k)  —  {len(self.doc_roots)} documentos indexados",
            bg=C["card"], fg=C["muted"], font=F.r(9)).pack(anchor="w", pady=(10, 10))

        self._sres_frame = tk.Frame(card, bg=C["card"])
        self._sres_frame.pack(fill=tk.X)
        self._render_search_rows(self._docs())

    def _do_search(self) -> None:
        if not self.coleccion:
            return
        if not self._validate_op_field():
            return
        field = self._sq_field.get()
        op    = self._get_op()
        raw   = self._sq_val_e.get().strip()

        if not raw:
            self._render_search_rows(self._docs())
            return

        try:
            val: object = int(raw)
        except ValueError:
            try:
                val = float(raw)
            except ValueError:
                val = raw

        filtro = {field: val} if op == "$eq" else {field: {op: val}}
        try:
            result_docs = [ArbolDocumental.a_dict(r)
                           for r in self.coleccion.find(filtro)]
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self._render_search_rows(result_docs)

    def _render_search_rows(self, docs: list[dict]) -> None:
        for w in self._sres_frame.winfo_children():
            w.destroy()
        if not docs:
            tk.Label(self._sres_frame, text="Sin resultados.",
                bg=C["card"], fg=C["muted"],
                font=F.r(11), pady=20).pack()
            return
        for d in docs:
            row = tk.Frame(self._sres_frame, bg=C["card"],
                highlightthickness=1, highlightbackground=C["border"])
            row.pack(fill=tk.X, pady=4)
            left = tk.Frame(row, bg=C["card"], padx=12, pady=8)
            left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tk.Label(left, text=d.get("nombre", ""),
                bg=C["card"], fg=C["text"], font=F.b(12)).pack(anchor="w")
            tk.Label(left,
                text=f"{d.get('edad', '')} anos  —  {d.get('ciudad', '')}",
                bg=C["card"], fg=C["muted"], font=F.r(10)).pack(anchor="w")
            self._badge(row, f"#{d.get('id', '')}").pack(side=tk.RIGHT, padx=12)
            did = d.get("id")
            for w in (row, left):
                w.bind("<Button-1>",
                    lambda _, i=did: self._switch_view("detail", data=i))

    # ── Helpers de búsqueda ────────────────────────────────────────────────────

    def _get_op(self) -> str:
        return OPERATOR_MAP.get(self._sq_op.get(), "$eq")

    def _show_search_warning(self, msg: str) -> None:
        for w in self._sres_frame.winfo_children():
            w.destroy()
        f = tk.Frame(self._sres_frame, bg=C["err_bg"],
            highlightthickness=1, highlightbackground="#f5c6b8",
            padx=14, pady=10)
        f.pack(fill=tk.X, pady=8)
        tk.Label(f, text=f"⚠  {msg}",
            bg=C["err_bg"], fg=C["err"],
            font=F.r(10), justify=tk.LEFT, wraplength=480).pack(anchor="w")

    def _validate_op_field(self) -> bool:
        field = self._sq_field.get()
        op    = self._get_op()
        if op in NUMERIC_OPS and field in STRING_FIELDS:
            self._show_search_warning(
                f"El operador '{self._sq_op.get()}' solo funciona con campos numéricos "
                f"(id, edad).\n\nEl campo '{field}' contiene texto. "
                f"Usa  'Igual a (=)'  o  'Diferente (≠)'  para campos de texto.")
            return False
        return True

    # ── Filtro en vivo ─────────────────────────────────────────────────────────

    def _live_filter(self) -> None:
        raw   = self._sq_val_e.get().strip()
        field = self._sq_field.get()
        op    = self._get_op()

        if not raw:
            self._render_search_rows(self._docs())
            return

        if not self._validate_op_field():
            return

        if op == "$eq":
            needle = raw.lower()
            results = []
            for d in self._docs():
                if "." in field:
                    parts = field.split(".")
                    v: object = d
                    for p in parts:
                        v = v.get(p, "") if isinstance(v, dict) else ""
                else:
                    v = d.get(field, "")
                if needle in str(v).lower():
                    results.append(d)
            self._render_search_rows(results)
        else:
            self._render_search_rows(self._docs_filtered(raw))

    def _docs_filtered(self, raw: str) -> list[dict]:
        if not self.coleccion or not raw:
            return self._docs()
        field = self._sq_field.get()
        op    = self._get_op()
        try:
            val: object = int(raw)
        except ValueError:
            try:
                val = float(raw)
            except ValueError:
                val = raw
        filtro = {field: val} if op == "$eq" else {field: {op: val}}
        try:
            return [ArbolDocumental.a_dict(r) for r in self.coleccion.find(filtro)]
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: ESTRUCTURA
    # ══════════════════════════════════════════════════════════════════

    def _v_structure(self) -> None:
        docs = self._docs()
        tk.Frame(self.content, bg=C["content"], height=20).pack()

        # Arbol card
        tc = self._card(pady=(0, 14))
        tk.Label(tc, text="Arbol Documental  —  NodoArbol",
            bg=C["card"], fg=C["text"], font=F.b(12)).pack(anchor="w", pady=(0, 10))

        tree_cv = tk.Canvas(tc, bg=C["card"], highlightthickness=0, height=310)
        tree_cv.pack(fill=tk.X)
        tree_cv.bind("<Configure>",
            lambda e, cv=tree_cv: self._draw_tree(cv, docs))

        leg = tk.Frame(tc, bg=C["card"])
        leg.pack(anchor="w", pady=(6, 0))
        for color, lbl in [(C["accent"], "Raiz"), (C["accent2"], "Nivel 1"),
                           (C["accent3"], "Nivel 2"), ("#85C4AA", "Nivel 3")]:
            tk.Label(leg, text="●", bg=C["card"], fg=color,
                font=F.r(13)).pack(side=tk.LEFT, padx=(0, 3))
            tk.Label(leg, text=lbl, bg=C["card"], fg=C["muted"],
                font=F.r(9)).pack(side=tk.LEFT, padx=(0, 14))
        tk.Label(leg, text="  ·  Haz clic en un nodo para ver su informacion",
            bg=C["card"], fg=C["dim"], font=F.r(9)).pack(side=tk.LEFT)

        # Lista enlazada card
        lc = self._card(pady=(0, 20))
        tk.Label(lc, text="Lista Enlazada  —  ListaDocumentos",
            bg=C["card"], fg=C["text"], font=F.b(12)).pack(anchor="w", pady=(0, 10))

        ll_wrap = tk.Frame(lc, bg=C["card"])
        ll_wrap.pack(fill=tk.X)
        ll_hsb = tk.Scrollbar(ll_wrap, orient="horizontal")
        ll_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        ll_cv = tk.Canvas(ll_wrap, bg=C["card"], highlightthickness=0,
            height=82, xscrollcommand=ll_hsb.set)
        ll_cv.pack(fill=tk.X)
        ll_hsb.config(command=ll_cv.xview)
        ll_cv.bind("<Configure>", lambda _, cv=ll_cv: self._draw_ll(cv, docs))

        info = tk.Frame(lc, bg=C["card"])
        info.pack(anchor="w", pady=(8, 0))
        tk.Label(info, text="cabeza  ->  NodoColeccion  ->  siguiente  ->  ...  ->  NULL",
            bg=C["card"], fg=C["muted"], font=F.m(9)).pack(side=tk.LEFT, padx=(0, 16))
        tk.Label(info,
            text=f"{len(docs)} nodos  —  insercion O(1) con puntero _cola",
            bg=C["card"], fg=C["badge_fg"], font=F.r(9)).pack(side=tk.LEFT)

    def _draw_tree(self, cv: tk.Canvas, docs: list[dict]) -> None:
        cv.delete("all")
        cv.update_idletasks()
        W = cv.winfo_width() or 700
        H = cv.winfo_height() or 310

        MAX_NODES = 31
        visible   = docs[:MAX_NODES]
        n         = len(visible)
        if n == 0:
            return

        # Nivel de cada nodo en árbol binario completo: nivel = bits(i+1) - 1
        def node_level(i: int) -> int:
            return (i + 1).bit_length() - 1

        levels = node_level(n - 1) + 1

        FILLS = [C["accent"], C["accent2"], C["accent3"], "#85C4AA", "#A8D4C8"]
        RADII = [26, 20, 15, 12, 9]

        y_top  = 32
        y_bot  = H - 16
        y_step = (y_bot - y_top) / max(levels - 1, 1)

        self._tree_node_data  = []
        self._tree_node_fills = {}
        self._tree_node_ovals = {}
        self._tree_hovered    = -1

        # Calcular posición (x, y) de cada nodo dinámicamente
        pos: dict[int, tuple] = {}
        for i in range(n):
            lv    = node_level(i)
            idx_in_lv = i - ((1 << lv) - 1)
            count = 1 << lv
            x     = W * (idx_in_lv + 0.5) / count
            y     = y_top + lv * y_step
            r     = RADII[min(lv, len(RADII) - 1)]
            fill  = FILLS[min(lv, len(FILLS) - 1)]
            pos[i] = (x, y, r, fill)

        # Aristas
        for i in range(1, n):
            px, py, pr, _ = pos[(i - 1) // 2]
            cx, cy, cr, _ = pos[i]
            dx, dy = cx - px, cy - py
            dist   = (dx**2 + dy**2) ** 0.5
            if dist:
                cv.create_line(
                    px + dx * pr / dist, py + dy * pr / dist,
                    cx - dx * cr / dist, cy - dy * cr / dist,
                    fill="#b2dfc8", width=1.2)

        # Nodos
        seen_levels: set[int] = set()
        for i, (x, y, r, fill) in pos.items():
            oid  = cv.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="")
            lbl  = visible[i].get("nombre", "?").split()[-1][:5]
            lv   = node_level(i)
            fs   = max(6, 9 - lv)
            cv.create_text(x, y, text=lbl, fill="#fff", font=F.m(fs))
            self._tree_node_ovals[i] = oid
            self._tree_node_data.append((x, y, r, i))
            self._tree_node_fills[i] = fill
            if lv not in seen_levels:
                cv.create_text(W - 4, y, text=f"N{lv}",
                    fill=C["dimmer"], font=F.m(8), anchor="e")
                seen_levels.add(lv)

        if len(docs) > MAX_NODES:
            cv.create_text(W / 2, H - 6, anchor="center",
                text=f"Mostrando {MAX_NODES} de {len(docs)} documentos",
                fill=C["dim"], font=F.r(8))

        cv.bind("<Button-1>", lambda e, d=docs: self._tree_click(cv, e.x, e.y, d))
        cv.bind("<Motion>",   lambda e: self._tree_motion(cv, e.x, e.y))

    def _draw_ll(self, cv: tk.Canvas, docs: list[dict]) -> None:
        cv.delete("all")
        cv.update_idletasks()
        BW, BH, GAP = 100, 54, 26
        n = len(docs)
        total_w = 10 + n * BW + max(n - 1, 0) * GAP + 60
        cv.config(scrollregion=(0, 0, total_w, BH + 24))
        sx = 10
        y = 10

        for i, d in enumerate(docs):
            x = sx + i * (BW + GAP)
            lname = d.get("nombre", "?").split()[-1][:8]

            cv.create_rectangle(x, y, x+BW, y+BH,
                fill=C["ll"], outline=C["ll_bdr"], width=1)
            cv.create_rectangle(x, y, x+BW, y+20,
                fill=C["accent2"], outline="")
            cv.create_text(x + BW/2, y+10,
                text=f"#{d.get('id', i+1):02d}",
                fill="#fff", font=F.mb(8))
            cv.create_text(x + BW/2, y+38,
                text=lname, fill=C["text"], font=F.m(9))

            if i < n - 1:
                cv.create_line(x+BW, y+BH/2, x+BW+GAP, y+BH/2,
                    fill=C["accent2"], width=2,
                    arrow=tk.LAST, arrowshape=(8, 10, 3))
            else:
                cv.create_line(x+BW, y+BH/2, x+BW+22, y+BH/2,
                    fill=C["err"], width=1.5)
                cv.create_text(x+BW+28, y+BH/2,
                    text="NULL", fill=C["err"], font=F.mb(8), anchor="w")

    # ── Tree interaction ───────────────────────────────────────────────────────

    def _tree_click(self, cv: tk.Canvas, mx: float, my: float,
                    docs: list[dict]) -> None:
        for x, y, r, idx in getattr(self, "_tree_node_data", []):
            if (mx - x) ** 2 + (my - y) ** 2 <= r ** 2:
                if idx < len(docs):
                    rx = cv.winfo_rootx() + int(mx)
                    ry = cv.winfo_rooty() + int(my)
                    self._show_tree_popup(rx, ry, docs[idx])
                return

    def _tree_motion(self, cv: tk.Canvas, mx: float, my: float) -> None:
        prev = getattr(self, "_tree_hovered", -1)
        hit  = -1
        for x, y, r, idx in getattr(self, "_tree_node_data", []):
            if (mx - x) ** 2 + (my - y) ** 2 <= r ** 2:
                hit = idx
                break
        if hit != prev:
            ovals = getattr(self, "_tree_node_ovals", {})
            fills = getattr(self, "_tree_node_fills", {})
            if prev >= 0 and prev in ovals:
                cv.itemconfig(ovals[prev], fill=fills.get(prev, C["accent"]))
            if hit >= 0 and hit in ovals:
                cv.itemconfig(ovals[hit],
                    fill=RoundedButton._shift(fills.get(hit, C["accent"]), 24))
            self._tree_hovered = hit

    def _show_tree_popup(self, x_root: int, y_root: int, doc: dict) -> None:
        pw, ph = 600, 430
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        px = max(0, min(x_root - pw // 2, sw - pw))
        py = max(0, min(y_root - ph // 2, sh - ph))

        popup = tk.Toplevel(self.root)
        popup.title("Arbol ⟷ JSON  —  Relacion bidireccional")
        popup.geometry(f"{pw}x{ph}+{px}+{py}")
        popup.configure(bg=C["card"])
        popup.resizable(True, True)
        popup.transient(self.root)
        popup.grab_set()

        # Header
        hdr = tk.Frame(popup, bg=C["accent"], padx=16, pady=10)
        hdr.pack(fill=tk.X)
        name = doc.get("nombre", "")
        tk.Label(hdr, text=name, bg=C["accent"], fg="#fff",
            font=F.b(13)).pack(side=tk.LEFT)
        tk.Label(hdr, text=f"    NodoArbol  ·  id: {doc.get('id', '')}",
            bg=C["accent"], fg="#c8f0e0", font=F.r(9)).pack(side=tk.LEFT)

        # Cuerpo: dos paneles con grid
        body = tk.Frame(popup, bg=C["card"], padx=10, pady=10)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(1, weight=1)

        # Panel izquierdo — árbol
        tk.Frame(body, bg=C["accent3"], padx=8, pady=4).grid(
            row=0, column=0, sticky="ew")
        tk.Label(body, text="Arbol Documental  (NodoArbol)",
            bg=C["accent3"], fg=C["text"], font=F.b(9),
            padx=8, pady=4).grid(row=0, column=0, sticky="ew")

        left_f = tk.Frame(body, bg=C["tbl_h"],
            highlightthickness=1, highlightbackground=C["border"])
        left_f.grid(row=1, column=0, sticky="nsew")
        left_sb = tk.Scrollbar(left_f, orient="vertical")
        left_sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree_txt = tk.Text(left_f, bg=C["tbl_h"], fg=C["text2"],
            font=F.m(9), relief=tk.FLAT, padx=8, pady=6,
            wrap=tk.NONE, highlightthickness=0,
            yscrollcommand=left_sb.set, width=24)
        tree_txt.pack(fill=tk.BOTH, expand=True)
        left_sb.config(command=tree_txt.yview)
        tree_txt.insert(tk.END, "● documento\n" + "\n".join(self._tree_repr(doc)))
        tree_txt.config(state=tk.DISABLED)

        # Flecha central
        ctr = tk.Frame(body, bg=C["card"], padx=6)
        ctr.grid(row=0, column=1, rowspan=2, sticky="ns")
        tk.Label(ctr, text="⟷", bg=C["card"], fg=C["accent"],
            font=F.b(22)).pack(expand=True)

        # Panel derecho — JSON
        tk.Label(body, text="JSON equivalente",
            bg=C["badge"], fg=C["badge_fg"], font=F.b(9),
            padx=8, pady=4).grid(row=0, column=2, sticky="ew")

        right_f = tk.Frame(body, bg=C["hint"],
            highlightthickness=1, highlightbackground=C["hint_bdr"])
        right_f.grid(row=1, column=2, sticky="nsew")
        right_sb = tk.Scrollbar(right_f, orient="vertical")
        right_sb.pack(side=tk.RIGHT, fill=tk.Y)
        json_txt = tk.Text(right_f, bg=C["hint"], fg=C["text3"],
            font=F.m(9), relief=tk.FLAT, padx=8, pady=6,
            wrap=tk.NONE, highlightthickness=0,
            yscrollcommand=right_sb.set, width=24)
        json_txt.pack(fill=tk.BOTH, expand=True)
        right_sb.config(command=json_txt.yview)
        json_txt.insert(tk.END, json.dumps(doc, indent=2, ensure_ascii=False))
        json_txt.config(state=tk.DISABLED)

        # Barra de info bidireccional
        info = tk.Frame(popup, bg=C["hint"], padx=14, pady=6)
        info.pack(fill=tk.X)
        tk.Label(info,
            text="JSON  →  NodoArbol  (cargar / insertar)     "
                 "NodoArbol  →  JSON  (consultar / exportar)",
            bg=C["hint"], fg=C["text3"], font=F.r(9)).pack()

        # Footer
        tk.Frame(popup, bg=C["border"], height=1).pack(fill=tk.X)
        foot = tk.Frame(popup, bg=C["card"], padx=16, pady=8)
        foot.pack(fill=tk.X)
        self._mk_btn(foot, "Descargar JSON", C["accent"], "#fff",
            lambda: self._download_json(doc),
            font=F.b(10), px=14, py=6).pack(side=tk.LEFT, padx=(0, 8))
        self._mk_btn(foot, "Descargar PDF", C["accent2"], "#fff",
            lambda: self._download_pdf(doc),
            font=F.b(10), px=14, py=6).pack(side=tk.LEFT)
        self._mk_btn(foot, "Cerrar", C["inp"], C["text3"],
            popup.destroy, font=F.r(10), px=14, py=6,
            border=C["inp_bdr"]).pack(side=tk.RIGHT)

    def _tree_repr(self, d: dict, prefix: str = "") -> list[str]:
        lines = []
        items = list(d.items())
        for idx, (k, v) in enumerate(items):
            last   = idx == len(items) - 1
            branch = "└─ " if last else "├─ "
            child  = prefix + ("   " if last else "│  ")
            if isinstance(v, dict):
                lines.append(f"{prefix}{branch}{k}")
                lines.extend(self._tree_repr(v, child))
            else:
                lines.append(f"{prefix}{branch}{k}:  {v}")
        return lines

    def _download_json(self, doc: dict) -> None:
        nombre = doc.get("nombre", "documento").replace(" ", "_")
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos los archivos", "*.*")],
            initialfile=f"{nombre}.json",
            title="Guardar documento como JSON")
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
            messagebox.showinfo("Guardado", f"Archivo guardado en:\n{path}")

    def _download_pdf(self, doc: dict) -> None:
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Dependencia faltante",
                "Instala fpdf2 para exportar PDF:\n\n  pip install fpdf2")
            return

        nombre = doc.get("nombre", "documento").replace(" ", "_")
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            initialfile=f"{nombre}.pdf",
            title="Guardar documento como PDF")
        if not path:
            return

        def tree_ascii(d: dict, prefix: str = "") -> list[str]:
            lines: list[str] = []
            items = list(d.items())
            for i, (k, v) in enumerate(items):
                last = i == len(items) - 1
                br   = "\\-- " if last else "+-- "
                ch   = prefix + ("    " if last else "|   ")
                if isinstance(v, dict):
                    lines.append(f"{prefix}{br}{k}")
                    lines.extend(tree_ascii(v, ch))
                else:
                    lines.append(f"{prefix}{br}{k}: {v}")
            return lines

        tree_lines = ["* documento"] + tree_ascii(doc)
        json_lines = json.dumps(doc, indent=2, ensure_ascii=False).split("\n")

        # Paleta (R, G, B)
        ACC   = (29,  158, 117)
        ACC2  = (93,  202, 165)
        ACC3  = (159, 225, 203)
        BADGE = (220, 242, 232)
        BFG   = (15,  110, 86)
        TBL   = (246, 250, 247)
        TBL2  = (249, 251, 249)
        HNT   = (240, 250, 244)
        HNT2  = (245, 252, 247)
        TXT   = (26,  46,  34)
        TXT2  = (42,  61,  48)
        TXT3  = (74,  110, 88)
        MUT   = (122, 171, 138)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15)
        W = pdf.w - 30

        # Encabezado principal
        pdf.set_fill_color(*ACC)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(W, 14, "DocuTree", fill=True, align="C",
            new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(W, 8,
            "Motor Documental  |  Arboles + Listas Enlazadas  |  Proyecto Academico",
            fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Banner del documento
        pdf.set_fill_color(*ACC2)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(W, 10,
            f"  {doc.get('nombre', '')}    id: {doc.get('id', '')}",
            fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Etiqueta bidireccional
        pdf.set_fill_color(*BADGE)
        pdf.set_text_color(*BFG)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(W, 7,
            "Relacion bidireccional:  JSON -> NodoArbol (insertar)"
            "   |   NodoArbol -> JSON (consultar)",
            fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Encabezados de columnas
        col_w = (W - 8) / 2
        pdf.set_fill_color(*ACC3)
        pdf.set_text_color(*TXT)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_w, 7, "  Arbol Documental  (NodoArbol)", fill=True, border=1)
        pdf.cell(8, 7, "", border=0)
        pdf.set_fill_color(*BADGE)
        pdf.set_text_color(*BFG)
        pdf.cell(col_w, 7, "  JSON equivalente", fill=True, border=1,
            new_x="LMARGIN", new_y="NEXT")

        # Filas de contenido
        max_rows = max(len(tree_lines), len(json_lines))
        row_h    = 5.2
        col1_x   = pdf.l_margin
        col2_x   = pdf.l_margin + col_w + 8
        pdf.set_font("Courier", "", 7)

        for i in range(max_rows):
            tl   = (tree_lines[i] if i < len(tree_lines) else "")[:60]
            jl   = (json_lines[i] if i < len(json_lines) else "")[:60]
            row_y = pdf.get_y()

            pdf.set_xy(col1_x, row_y)
            pdf.set_fill_color(*(TBL if i % 2 == 0 else TBL2))
            pdf.set_text_color(*TXT2)
            pdf.cell(col_w, row_h, f"  {tl}", fill=True, border="LR")

            pdf.set_xy(col2_x, row_y)
            pdf.set_fill_color(*(HNT if i % 2 == 0 else HNT2))
            pdf.set_text_color(*TXT3)
            pdf.cell(col_w, row_h, f"  {jl}", fill=True, border="LR",
                new_x="LMARGIN", new_y="NEXT")

        # Cerrar bordes inferiores
        end_y = pdf.get_y()
        pdf.set_xy(col1_x, end_y)
        pdf.cell(col_w, 0, "", border="B")
        pdf.set_xy(col2_x, end_y)
        pdf.cell(col_w, 0, "", border="B", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Pie de página
        pdf.set_fill_color(*TBL)
        pdf.set_text_color(*MUT)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(W, 7,
            "DocuTree  |  Proyecto Academico  |  Estructuras de Datos",
            fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.output(path)
        messagebox.showinfo("PDF guardado", f"Archivo guardado en:\n{path}")

    # ══════════════════════════════════════════════════════════════════
    #  VISTA: DETALLE
    # ══════════════════════════════════════════════════════════════════

    def _v_detail(self, doc_id) -> None:
        docs = self._docs()
        d = next((x for x in docs if x.get("id") == doc_id), None)
        if not d:
            self._switch_view("explorer")
            return

        tk.Frame(self.content, bg=C["content"], height=20).pack()
        card = self._card(pady=(0, 20))

        # Avatar + nombre
        hdr = tk.Frame(card, bg=C["card"])
        hdr.pack(fill=tk.X, pady=(0, 16))

        av = tk.Frame(hdr, bg=C["badge"], width=46, height=46)
        av.pack(side=tk.LEFT)
        av.pack_propagate(False)
        name = d.get("nombre", "")
        initials = "".join(w[0] for w in name.split()[:2]).upper()
        tk.Label(av, text=initials, bg=C["badge"], fg=C["badge_fg"],
            font=F.b(18)).place(relx=0.5, rely=0.5, anchor="center")

        nf = tk.Frame(hdr, bg=C["card"])
        nf.pack(side=tk.LEFT, padx=(14, 0))
        tk.Label(nf, text=name, bg=C["card"], fg=C["text"],
            font=F.b(16)).pack(anchor="w")
        idx = next((i for i, x in enumerate(docs) if x.get("id") == doc_id), 0)
        tk.Label(nf, text=f"coleccion[{idx}]  ->  NodoArbol(raiz)",
            bg=C["card"], fg=C["muted"], font=F.m(9)).pack(anchor="w", pady=(3, 0))

        # Campos
        direc = d.get("direccion", {})
        if not isinstance(direc, dict):
            direc = {}
        for lbl, val in [
            ("Edad",          str(d.get("edad", ""))),
            ("Ciudad",        d.get("ciudad", "")),
            ("Barrio",        direc.get("barrio", "")),
            ("Codigo postal", direc.get("codigo_postal", "")),
        ]:
            tk.Frame(card, bg=C["tbl"], height=1).pack(fill=tk.X)
            row = tk.Frame(card, bg=C["card"], pady=9)
            row.pack(fill=tk.X)
            tk.Label(row, text=lbl, bg=C["card"], fg=C["muted"],
                font=F.r(11), width=14, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=C["card"], fg=C["text2"],
                font=F.r(11)).pack(side=tk.LEFT)

        tk.Frame(card, bg=C["tbl"], height=1).pack(fill=tk.X)

        # JSON
        tk.Label(card, text="Representacion JSON del arbol:",
            bg=C["card"], fg=C["muted"],
            font=F.b(9), pady=10).pack(anchor="w")

        jf = tk.Frame(card, bg=C["tbl_h"],
            highlightthickness=1, highlightbackground=C["border"])
        jf.pack(fill=tk.X, pady=(0, 14))
        tk.Label(jf, text=json.dumps(d, indent=2, ensure_ascii=False),
            bg=C["tbl_h"], fg=C["text3"],
            font=F.m(10), justify=tk.LEFT,
            padx=12, pady=10).pack(anchor="w")

        bf = tk.Frame(card, bg=C["card"])
        bf.pack(anchor="w")
        self._mk_btn(bf, "Volver", C["inp"], C["muted"],
            lambda: self._switch_view("explorer"),
            font=F.r(10), px=16, py=7,
            border=C["inp_bdr"]).pack(side=tk.LEFT, padx=(0, 8))
        self._mk_btn(bf, "Eliminar", C["err_bg"], C["err"],
            lambda: self._delete_doc(doc_id),
            font=F.r(10), px=16, py=7,
            border="#f5c6b8").pack(side=tk.LEFT)

    # ── Eliminar ───────────────────────────────────────────────────────────────

    def _delete_doc(self, doc_id: int) -> None:
        if not messagebox.askyesno("Confirmar", f"Eliminar documento id={doc_id}?"):
            return
        nueva: ListaDocumentos = ListaDocumentos()
        nueva_roots = []
        for raiz in self.doc_roots:
            d = ArbolDocumental.a_dict(raiz)
            if d.get("id") != doc_id:
                nueva.agregar(raiz)
                nueva_roots.append(raiz)
        self.coleccion.documentos = nueva
        self.doc_roots = nueva_roots
        self._foot_docs.config(text=f"{len(self.doc_roots)} documentos")
        self._switch_view("explorer")


# ── Entrada ────────────────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    DocuTreeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
