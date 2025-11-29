import os, sys, tkinter
import customtkinter as ctk
from tkinter import messagebox

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Tooltip:
    def __init__(self, widget, text: str, delay=500):
        self.widget, self.text, self.delay = widget, text, delay
        self._id = None; self._tip = None
        widget.bind("<Enter>", self._enter); widget.bind("<Leave>", self._leave)

    def _enter(self, _): self._schedule()
    def _leave(self, _): self._unschedule(); self._hide()

    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._id:
            try: self.widget.after_cancel(self._id)
            except Exception: pass
        self._id = None

    def _show(self):
        if self._tip or not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self._tip = tkinter.Toplevel(self.widget)
        self._tip.wm_overrideredirect(1)
        try: self._tip.attributes("-topmost", True)
        except Exception: pass
        label = tkinter.Label(
            self._tip, text=self.text, justify="left",
            background="#2b2b2b", foreground="white",
            relief="solid", borderwidth=1, padx=6, pady=4, font=("Consolas", 10)
        )
        label.pack()
        self._tip.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self._tip is not None:
            try: self._tip.destroy()
            except Exception: pass
            self._tip = None

def copy_to_clipboard(widget, text: str):
    widget.clipboard_clear(); widget.clipboard_append(text)
    try: messagebox.showinfo("Скопировано", "Текст скопирован в буфер обмена.")
    except tkinter.TclError: pass

def pkcs7_pad(data: bytes, block_size=16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def pkcs7_unpad(data: bytes) -> bytes:
    if not data: raise ValueError("Данные пусты.")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > len(data): raise ValueError("Неверный padding.")
    if any(p != pad_len for p in data[-pad_len:]): raise ValueError("Неверный padding байт.")
    return data[:-pad_len]

def bind_context_menus(root):
    def add_menu(widget):
        menu = tkinter.Menu(widget, tearoff=0)
        def cut():
            try:
                sel = widget.selection_get()
                widget.clipboard_clear(); widget.clipboard_append(sel)
                widget.delete("sel.first", "sel.last")
            except tkinter.TclError: pass
        def copy():
            try:
                sel = widget.selection_get()
                widget.clipboard_clear(); widget.clipboard_append(sel)
            except tkinter.TclError: pass
        def paste():
            try:
                txt = widget.clipboard_get()
                widget.insert("insert", txt)
            except tkinter.TclError: pass
        menu.add_command(label="Вырезать", command=cut)
        menu.add_command(label="Копировать", command=copy)
        menu.add_command(label="Вставить", command=paste)
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def recurse(parent):
        for child in parent.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkTextbox)):
                add_menu(child)
            recurse(child)
    recurse(root)
