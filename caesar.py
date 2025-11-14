# caesar.py
import tkinter
import customtkinter as ctk
from utils import Tooltip, copy_to_clipboard

RUS_UP = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
RUS_LO = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
ENG_UP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ENG_LO = "abcdefghijklmnopqrstuvwxyz"

def caesar_cipher(text, shift):
    res=[]
    for ch in text:
        if ch in RUS_UP:  res.append(RUS_UP[(RUS_UP.index(ch)+shift)%len(RUS_UP)])
        elif ch in RUS_LO:res.append(RUS_LO[(RUS_LO.index(ch)+shift)%len(RUS_LO)])
        elif ch in ENG_UP:res.append(ENG_UP[(ENG_UP.index(ch)+shift)%len(ENG_UP)])
        elif ch in ENG_LO:res.append(ENG_LO[(ENG_LO.index(ch)+shift)%len(ENG_LO)])
        else: res.append(ch)
    return "".join(res)

class CaesarTab:
    def __init__(self, app, parent, set_status):
        self.app = app; self.set_status = set_status
        frame = ctk.CTkFrame(parent); frame.pack(padx=10, pady=10, fill="both", expand=True)
        ctk.CTkLabel(
            frame, text="Шифр Цезаря — поддерживаются русский и английский алфавиты.\nАнимация на алфавитных панелях.",
            font=ctk.CTkFont(size=14, weight="bold"), justify="left"
        ).pack(pady=10)

        inrow = ctk.CTkFrame(frame); inrow.pack(pady=5, fill="x")
        self.in_entry = ctk.CTkEntry(inrow, width=600, placeholder_text="Введите текст (рус./англ.)")
        self.in_entry.pack(side="left", padx=5)
        Tooltip(self.in_entry, "Исходный текст для (де)шифрования")
        ctk.CTkLabel(inrow, text="Сдвиг:").pack(side="left", padx=6)
        self.shift_var = tkinter.IntVar(value=3)
        ctk.CTkEntry(inrow, width=60, textvariable=self.shift_var).pack(side="left")

        btnrow = ctk.CTkFrame(frame); btnrow.pack(pady=4)
        ctk.CTkButton(btnrow, text="Анимация шифрования", command=lambda: self._start(True)).pack(side="left", padx=6)
        ctk.CTkButton(btnrow, text="Анимация расшифрования", command=lambda: self._start(False)).pack(side="left", padx=6)

        self.anim_area = ctk.CTkFrame(frame); self.anim_area.pack(fill="x", pady=8)
        self.rus_labels=[]; self.eng_labels=[]
        self._build_alphabet_panels()

        outrow = ctk.CTkFrame(frame); outrow.pack(fill="both", expand=True, pady=6)
        self.out = ctk.CTkTextbox(outrow, height=150, wrap="word"); self.out.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkButton(outrow, text="Копировать", command=lambda: copy_to_clipboard(self.app, self.out.get("0.0","end").strip())).pack(side="left", padx=6)

        # анимационные переменные
        self._idx=0; self._text=""; self._res=""; self._shift=3; self._running=False; self._hl=None

    def _build_alphabet_panels(self):
        for w in self.anim_area.winfo_children(): w.destroy()
        rus = ctk.CTkFrame(self.anim_area); rus.pack(pady=8, fill="x")
        ctk.CTkLabel(rus, text="Русский алфавит:", font=("Arial", 14, "bold")).pack(anchor="w")
        fr = ctk.CTkFrame(rus); fr.pack()
        self.rus_labels=[]
        for i,ch in enumerate(RUS_UP):
            lbl = ctk.CTkLabel(fr, text=ch, width=30, height=30, fg_color="transparent", corner_radius=5)
            lbl.grid(row=0, column=i, padx=2); self.rus_labels.append(lbl)

        eng = ctk.CTkFrame(self.anim_area); eng.pack(pady=8, fill="x")
        ctk.CTkLabel(eng, text="Английский алфавит:", font=("Arial", 14, "bold")).pack(anchor="w")
        fe = ctk.CTkFrame(eng); fe.pack()
        self.eng_labels=[]
        for i,ch in enumerate(ENG_UP):
            lbl = ctk.CTkLabel(fe, text=ch, width=30, height=30, fg_color="transparent", corner_radius=5)
            lbl.grid(row=0, column=i, padx=2); self.eng_labels.append(lbl)

    def caesar_cipher(self, text, shift):  # прокидка наружу для practice
        return caesar_cipher(text, shift)

    def _start(self, enc: bool):
        text = self.in_entry.get()
        if not text:
            from tkinter import messagebox; messagebox.showerror("Ошибка","Введите текст для анимации."); return
        try: shift = int(self.shift_var.get())
        except ValueError:
            from tkinter import messagebox; messagebox.showerror("Ошибка","Сдвиг — целое число."); return
        if not enc: shift = -shift
        self._idx=0; self._text=text; self._res=""; self._shift=shift; self._running=True; self._hl=None
        self.out.delete("0.0","end"); self._step("Шифрование" if enc else "Расшифрование")

    def _get_idx(self, ch, lang):
        upper, lower = (RUS_UP, RUS_LO) if lang=="rus" else (ENG_UP, ENG_LO)
        if ch in upper: return upper.index(ch)
        if ch in lower: return lower.index(ch)
        return -1

    def _highlight(self, orig, sh):
        if self._hl:
            for lbl in self._hl: lbl.configure(fg_color="transparent")
        color1="#3B8ED0"; color2="#2FA572"
        if orig.upper() in RUS_UP:
            i1=self._get_idx(orig,"rus"); i2=self._get_idx(sh,"rus")
            if i1!=-1 and i2!=-1:
                self.rus_labels[i1].configure(fg_color=color1)
                self.rus_labels[i2].configure(fg_color=color2)
                self._hl=[self.rus_labels[i1], self.rus_labels[i2]]
        elif orig.upper() in ENG_UP:
            i1=self._get_idx(orig,"eng"); i2=self._get_idx(sh,"eng")
            if i1!=-1 and i2!=-1:
                self.eng_labels[i1].configure(fg_color=color1)
                self.eng_labels[i2].configure(fg_color=color2)
                self._hl=[self.eng_labels[i1], self.eng_labels[i2]]

    def _step(self, action="Шифрование"):
        if not self._running: return
        if self._idx >= len(self._text):
            self.out.insert("end", f"\n{action} завершено.\n"); self._running=False
            self.set_status(f"Цезарь: {action} завершено"); return
        ch = self._text[self._idx]; sh = caesar_cipher(ch, self._shift)
        self._highlight(ch, sh)
        self._res += sh
        self.out.delete("0.0","end")
        self.out.insert("end", f"Шаг {self._idx+1}:\nИсходный: '{ch}' → '{sh}'\nТекущий результат: {self._res}")
        self._idx += 1
        self.app.after(600, lambda: self._step(action))
