"""Shared desktop palette and ttk styles; no additional dependencies."""

from tkinter import ttk

BG = "#0C111B"
PANEL = "#141D2B"
FIELD = "#0E1623"
TEXT = "#E6EDF7"
MUTED = "#9AAFC7"
ACCENT = "#68B5FF"
BORDER = "#28374B"


def configure(root):
    family = "Helvetica Neue" if root.tk.call("tk", "windowingsystem") == "aqua" else "DejaVu Sans"
    root.configure(background=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=TEXT, font=(family, 10),
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    troughcolor=FIELD, selectbackground="#264D72", selectforeground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Title.TLabel", font=(family, 24, "bold"))
    style.configure("Section.TLabel", font=(family, 14, "bold"))
    style.configure("Card.TFrame", background=PANEL)
    style.configure("Card.TLabel", background=PANEL)
    style.configure("CardMuted.TLabel", background=PANEL, foreground=MUTED)
    style.configure("CardTitle.TLabel", background=PANEL, font=(family, 15, "bold"))
    style.configure("Metric.TLabel", background=PANEL, foreground=ACCENT, font=(family, 17, "bold"))
    style.configure("TButton", background="#213147", foreground=TEXT, padding=(14, 9), borderwidth=0)
    style.map("TButton", background=[("active", "#304A68"), ("pressed", "#3B5879")],
              foreground=[("disabled", "#6E8199")])
    style.configure("Accent.TButton", background=ACCENT, foreground="#071321", font=(family, 10, "bold"))
    style.map("Accent.TButton", background=[("active", "#93CCFF"), ("pressed", "#4496DF")])
    style.configure("Danger.TButton", background="#40252D", foreground="#FFB6B6")
    style.map("Danger.TButton", background=[("active", "#653340")])
    style.configure("Nav.TButton", background=BG, foreground=MUTED, anchor="w", padding=(16, 13))
    style.map("Nav.TButton", background=[("active", PANEL)], foreground=[("active", TEXT)])
    style.configure("Selected.Nav.TButton", background="#1C3550", foreground=ACCENT)
    style.map("Selected.Nav.TButton", background=[("active", "#264561")])
    style.configure("TEntry", fieldbackground=FIELD, foreground=TEXT, insertcolor=TEXT, padding=8)
    style.configure("TCombobox", fieldbackground=FIELD, background=PANEL, foreground=TEXT, padding=7,
                    arrowcolor=ACCENT)
    style.map("TCombobox", fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", TEXT)])
    root.option_add("*TCombobox*Listbox.background", FIELD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    style.configure("TCheckbutton", background=BG, foreground=MUTED, padding=4)
    style.map("TCheckbutton", background=[("active", BG)], foreground=[("active", TEXT)])
    style.configure("TLabelframe", background=BG, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG, foreground=MUTED)
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    rowheight=36, borderwidth=0)
    style.map("Treeview", background=[("selected", "#264D72")], foreground=[("selected", "#FFFFFF")])
    style.configure("Treeview.Heading", background="#1C293B", foreground=MUTED,
                    padding=(12, 10), font=(family, 10, "bold"), relief="flat")
    style.map("Treeview.Heading", background=[("active", "#283A51")])
    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
    style.layout("TNotebook.Tab", [])
    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=FIELD,
                    borderwidth=0, thickness=5)
    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                    arrowcolor=MUTED, borderwidth=0)


DARK = dict(BG=BG, PANEL=PANEL, FIELD=FIELD, TEXT=TEXT, MUTED=MUTED,
            ACCENT=ACCENT, BORDER=BORDER)
LIGHT = dict(BG="#F1F5FA", PANEL="#FFFFFF", FIELD="#FFFFFF", TEXT="#16243A",
             MUTED="#475D77", ACCENT="#005BAA", BORDER="#B8C8DA")
STYLE_NAMES = (".", "TFrame", "TLabel", "Muted.TLabel", "Title.TLabel", "Section.TLabel",
               "Card.TFrame", "Card.TLabel", "CardMuted.TLabel", "CardTitle.TLabel", "Metric.TLabel",
               "TButton", "Accent.TButton", "Danger.TButton", "Nav.TButton", "Selected.Nav.TButton",
               "TEntry", "TCombobox", "TCheckbutton", "TLabelframe", "TLabelframe.Label", "Treeview",
               "Treeview.Heading", "TNotebook", "Horizontal.TProgressbar", "Vertical.TScrollbar")
EXTRA_LIGHT = {"#264D72": "#D7E8FA", "#213147": "#DDE7F2", "#304A68": "#C7D9EC",
               "#3B5879": "#B4CCE5", "#6E8199": "#687A90", "#071321": "#FFFFFF",
               "#93CCFF": "#004C90", "#4496DF": "#003E78", "#40252D": "#FFE8E8",
               "#FFB6B6": "#9B2020", "#653340": "#FFD4D4", "#1C3550": "#D7E8FA",
               "#264561": "#C3DCF5", "#1C293B": "#DFE8F2", "#283A51": "#D0DEEE",
               "#EBC389": "#855200"}


def switch(root, mode):
    """Restyle existing widgets without rebuilding stateful vehicle workspaces."""
    if mode not in ("dark", "light"):
        raise ValueError("Unknown theme")
    old = {name: globals()[name] for name in DARK}
    palette = DARK if mode == "dark" else LIGHT
    globals().update(palette)
    configure(root)
    style = ttk.Style(root)
    if mode == "light":
        for name in STYLE_NAMES:
            for option, value in style.configure(name).items():
                replacement = EXTRA_LIGHT.get(str(value).upper())
                if replacement:
                    style.configure(name, **{option: replacement})
            for option, states in style.map(name).items():
                style.map(name, **{option: [(*state[:-1], EXTRA_LIGHT.get(str(state[-1]).upper(), state[-1]))
                                           for state in states]})
        style.map("Treeview", foreground=[("selected", LIGHT["TEXT"])])
    colors = {old[name].upper(): palette[name] for name in DARK}
    for color, replacement in (EXTRA_LIGHT if mode == "light" else {v.upper(): k for k, v in EXTRA_LIGHT.items()}).items():
        colors.setdefault(color, replacement)

    def visit(widget):
        if widget.winfo_class() == "Canvas":
            widget.configure(background=PANEL)
        for option in ("background", "foreground", "insertbackground", "highlightbackground"):
            if option in widget.keys():
                value = str(widget.cget(option)).upper()
                if value in colors:
                    widget.configure(**{option: colors[value]})
        for child in widget.winfo_children():
            visit(child)
    visit(root)
