import customtkinter as ctk
from tkinter import ttk

BG = "#111315"
PANEL = "#1B1E21"
PANEL2 = "#22262A"
BORDER = "#343A40"
TEXT = "#F3F4F6"
MUTED = "#9CA3AF"
BLUE = "#2584D6"
BLUE_HOVER = "#1F6FB7"
RED = "#C62828"
RED_HOVER = "#A91F1F"
GREEN = "#2E9B61"
ORANGE = "#D98A22"


def configure_treeview():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "LMS.Treeview",
        background="#171A1D",
        foreground=TEXT,
        fieldbackground="#171A1D",
        borderwidth=0,
        rowheight=34,
        font=("Segoe UI", 10),
    )
    style.configure(
        "LMS.Treeview.Heading",
        background=PANEL2,
        foreground=TEXT,
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 10, "bold"),
        padding=(8, 8),
    )
    style.map(
        "LMS.Treeview",
        background=[("selected", "#245B87")],
        foreground=[("selected", "white")],
    )
    style.map("LMS.Treeview.Heading", background=[("active", "#2A3035")])
    style.configure("LMS.Vertical.TScrollbar", troughcolor="#151719", background="#4B5563", arrowcolor=TEXT)
    style.configure("LMS.Horizontal.TScrollbar", troughcolor="#151719", background="#4B5563", arrowcolor=TEXT)


def make_table(parent, columns, widths=None, height=15):
    configure_treeview()
    frame = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=10)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, style="LMS.Treeview")
    widths = widths or [120] * len(columns)
    for i, col in enumerate(columns):
        tree.heading(col, text=col)
        tree.column(col, width=widths[i], minwidth=70, anchor="w", stretch=False)
    vs = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, style="LMS.Vertical.TScrollbar")
    hs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview, style="LMS.Horizontal.TScrollbar")
    tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vs.grid(row=0, column=1, sticky="ns")
    hs.grid(row=1, column=0, sticky="ew")
    return frame, tree


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, navigate, logout, active):
        super().__init__(master, width=220, corner_radius=0, fg_color="#181A1C")
        self.pack_propagate(False)
        ctk.CTkLabel(self, text="▣  LMS", font=ctk.CTkFont(size=30, weight="bold"), text_color=TEXT).pack(pady=(28, 35), padx=20, anchor="w")
        items = [
            ("Dashboard", "⌂"), ("Books", "▤"), ("Members", "♙"),
            ("Issue / Return", "⇄"), ("Reports", "▥"), ("CSV Import", "⇩"),
        ]
        for name, icon in items:
            ctk.CTkButton(
                self, text=f"{icon}   {name}", anchor="w", height=42, corner_radius=8,
                fg_color=PANEL2 if name == active else "transparent",
                hover_color="#2A3035", text_color=TEXT,
                command=lambda n=name: navigate(n),
            ).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(self, text="⇥   Logout", height=42, corner_radius=8, fg_color=RED, hover_color=RED_HOVER,
                      command=logout).pack(side="bottom", fill="x", padx=12, pady=22)


class Page(ctk.CTkFrame):
    def __init__(self, master, navigate, logout, active):
        super().__init__(master, fg_color=BG)
        self.navigate, self.logout = navigate, logout
        self.sidebar = Sidebar(self, navigate, logout, active)
        self.sidebar.pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def header(self, title, subtitle=""):
        top = ctk.CTkFrame(self.content, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(26, 14))
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=32, weight="bold"), text_color=TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(top, text=subtitle, font=ctk.CTkFont(size=14), text_color=MUTED).pack(anchor="w", pady=(4, 0))
        return top

    def button(self, parent, text, command, danger=False, width=130):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=38, corner_radius=8,
                             fg_color=RED if danger else BLUE, hover_color=RED_HOVER if danger else BLUE_HOVER)
