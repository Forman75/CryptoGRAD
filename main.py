import customtkinter
import customtkinter as ctk
from tkinter import messagebox
import tkinter
import threading
import sys
import os
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA1

# ----------------------------------------------------------------------------------------
# ТЕМА/МАСШТАБ
# ----------------------------------------------------------------------------------------

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

customtkinter.set_default_color_theme("dark-blue")

# ----------------------------------------------------------------------------------------
# TOOLTIP
# ----------------------------------------------------------------------------------------
class Tooltip:
    def __init__(self, widget, text: str, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._tip = None
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)

    def _enter(self, _):
        self._schedule()

    def _leave(self, _):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
        self._id = None

    def _show(self):
        if self._tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self._tip = tkinter.Toplevel(self.widget)
        self._tip.wm_overrideredirect(1)
        try:
            self._tip.attributes("-topmost", True)
        except Exception:
            pass
        label = tkinter.Label(
            self._tip, text=self.text, justify="left",
            background="#2b2b2b", foreground="white",
            relief="solid", borderwidth=1, padx=6, pady=4, font=("Consolas", 10)
        )
        label.pack()
        self._tip.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

# ----------------------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ УТИЛИТЫ
# ----------------------------------------------------------------------------------------
def copy_to_clipboard(widget, text: str):
    widget.clipboard_clear()
    widget.clipboard_append(text)
    try:
        messagebox.showinfo("Скопировано", "Текст скопирован в буфер обмена.")
    except tkinter.TclError:
        pass

def _show_result_window(self, title: str, content: str):
    win = ctk.CTkToplevel(self)
    win.title(title)
    win.geometry("720x420")
    frame = ctk.CTkFrame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    txt = ctk.CTkTextbox(frame, wrap="word")
    txt.pack(fill="both", expand=True)
    txt.insert("1.0", str(content))
    txt.configure(state="disabled")
    ctk.CTkButton(frame, text="Закрыть", command=win.destroy).pack(pady=8)

def pkcs7_pad(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def pkcs7_unpad(data):
    if not data:
        raise ValueError("Данные пусты. Невозможно удалить PKCS#7 padding.")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > len(data):
        raise ValueError("Неверный padding.")
    if any(p != pad_len for p in data[-pad_len:]):
        raise ValueError("Неверный padding байт.")
    return data[:-pad_len]

# ----------------------------------------------------------------------------------------
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ----------------------------------------------------------------------------------------
class CryptoGRAD(ctk.CTk):

    def __init__(self, scale: float = 1.0):
        try:
            customtkinter.set_widget_scaling(scale)
        except Exception:
            pass
        super().__init__()
        self.title("КриптоГРАД — обучающий криптографический стенд")

        # Верхняя панель (заголовок/подсказка)
        topbar = ctk.CTkFrame(self)
        topbar.pack(fill="x")
        title_lbl = ctk.CTkLabel(topbar, text="🔐 КриптоГРАД — стенд для обучения криптографии",
                                 font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(side="left", padx=10, pady=6)
        self.tabview = ctk.CTkTabview(self, width=1280, height=760)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tab_caesar = self.tabview.add("Шифр Цезаря")
        self.tab_rsa = self.tabview.add("RSA")
        self.tab_aes = self.tabview.add("AES")
        self.tab_practice = self.tabview.add("Практика")
        self.tab_tutor = self.tabview.add("Учебник")

        # Вкладки
        self.init_caesar_tab()
        self.init_rsa_tab()
        self.init_aes_tab()
        self.init_practice_tab()
        self.init_tutor_tab()
        self._bind_context_menus()

        # Нижняя строка состояния
        self.status = ctk.CTkLabel(topbar, text="Программа готова к работе", anchor="e")
        self.status.pack(side="right", padx=10)
        self.after(0, self._safe_zoom)

    def _safe_zoom(self):
        try:
            self.state("zoomed")
        except tkinter.TclError:
            pass

    # ------------------------------------------------------------------------------------
    # УТИЛИТЫ ОКОН: модалка результата + окно с карточками шагов (для RSA/AES)
    # ------------------------------------------------------------------------------------
    def _show_modal_result(self, title: str, body_text: str):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("900x560")
        win.resizable(True, True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.lift()
        win.grab_set()
        header = ctk.CTkLabel(win, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(padx=10, pady=(10, 4), anchor="w")
        txt = ctk.CTkTextbox(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", body_text)
        txt.configure(state="disabled")
        btns = ctk.CTkFrame(win); btns.pack(fill="x")
        ctk.CTkButton(btns, text="Копировать", command=lambda: copy_to_clipboard(win, body_text)).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(btns, text="Закрыть", command=win.destroy).pack(side="right", padx=8, pady=8)

    def _open_steps_window(self, title: str, steps: list[tuple[str, str]]):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("1200x720")
        win.resizable(True, True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.lift()
        win.grab_set()

        # Верхняя панель
        top = ctk.CTkFrame(win); top.pack(fill="x")
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=10, pady=8)
        ctk.CTkButton(top, text="Закрыть", command=win.destroy).pack(side="right", padx=10, pady=8)

        # Скроллируемая центральная область
        center = ctk.CTkFrame(win)
        center.pack(fill="both", expand=True, padx=8, pady=8)
        canvas = tkinter.Canvas(center, bg="#0f1115", highlightthickness=0)
        vsb = tkinter.Scrollbar(center, orient="vertical", command=canvas.yview)
        hsb = tkinter.Scrollbar(center, orient="horizontal", command=canvas.xview)
        scroll_frame = ctk.CTkFrame(canvas)
        scroll_frame_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        def on_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def frame_width(_event=None):
            canvas.itemconfig(scroll_frame_id, width=canvas.winfo_width())

        scroll_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", frame_width)

        # Карточки шагов
        for idx, (head, body) in enumerate(steps, 1):
            card = ctk.CTkFrame(scroll_frame)
            card.pack(fill="x", padx=6, pady=8)
            ctk.CTkLabel(card, text=f"Шаг {idx}: {head}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
            box = ctk.CTkTextbox(card, wrap="word", height=160)
            box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            box.insert("1.0", body)
            box.configure(state="disabled")

        return win

    # ------------------------------------------------------------------------------------
    # ЦЕЗАРЬ (Только анимация)
    # ------------------------------------------------------------------------------------
    def init_caesar_tab(self):
        frame = ctk.CTkFrame(self.tab_caesar)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        info_label = ctk.CTkLabel(
            frame,
            text=(
                "Шифр Цезаря — поддерживаются русский и английский алфавиты.\n"
                "Шифрование и расшифрование доступны только через образовательную анимацию."
            ),
            justify="left",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        info_label.pack(pady=10)

        # Ввод/сдвиг
        in_frame = ctk.CTkFrame(frame)
        in_frame.pack(pady=5, fill="x")
        self.caesar_input_text = ctk.CTkEntry(in_frame, width=600, placeholder_text="Введите текст (рус./англ.)")
        self.caesar_input_text.pack(side="left", padx=5, pady=5)
        Tooltip(self.caesar_input_text, "Исходный текст для (де)шифрования")
        shift_frame = ctk.CTkFrame(in_frame)
        shift_frame.pack(side="left", padx=10)
        ctk.CTkLabel(shift_frame, text="Сдвиг:").pack(side="left", padx=5)
        self.caesar_shift_var = tkinter.IntVar(value=3)
        self.caesar_shift_entry = ctk.CTkEntry(shift_frame, width=50, textvariable=self.caesar_shift_var)
        self.caesar_shift_entry.pack(side="left")
        Tooltip(self.caesar_shift_entry, "Целое число (можно отрицательное)")

        # Кнопки (только анимация)
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(pady=5)
        ctk.CTkButton(button_frame, text="Анимация шифрования", command=lambda: self.animate_caesar_start(True)).pack(
            side="left", padx=10)
        ctk.CTkButton(button_frame, text="Анимация расшифрования",
                      command=lambda: self.animate_caesar_start(False)).pack(side="left", padx=10)

        # Алфавиты
        self.animation_container = ctk.CTkFrame(frame)
        self.animation_container.pack(pady=10, fill="x")
        self.rus_labels = []
        self.eng_labels = []
        self.create_alphabet_panels()

        # Вывод
        out_frame = ctk.CTkFrame(frame)
        out_frame.pack(pady=5, fill="both", expand=True)
        self.caesar_output = ctk.CTkTextbox(out_frame, height=150, wrap="word")
        self.caesar_output.pack(side="left", padx=5, fill="both", expand=True)
        btn_copy = ctk.CTkButton(out_frame, text="Копировать результат",
                                 command=lambda: copy_to_clipboard(self, self.caesar_output.get("0.0", "end").strip()))
        btn_copy.pack(side="left", padx=5)
        Tooltip(btn_copy, "Скопировать текст из поля справа")

        # Переменные анимации
        self.caesar_anim_index = 0
        self.caesar_anim_text = ""
        self.caesar_anim_result = ""
        self.caesar_anim_shift = 3
        self.caesar_is_animating = False
        self.current_char_highlight = None

    def animate_caesar_start(self, is_encrypt: bool):
        text = self.caesar_input_text.get()
        if not text:
            messagebox.showerror("Ошибка", "Введите текст для анимации.")
            return
        try:
            shift = int(self.caesar_shift_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Сдвиг должен быть целым числом!")
            return

        action = "Шифрование" if is_encrypt else "Расшифрование"
        if not is_encrypt:
            shift = -shift

        # Сбрасываем состояние
        self.caesar_anim_index = 0
        self.caesar_anim_text = text
        self.caesar_anim_result = ""
        self.caesar_anim_shift = shift
        self.caesar_is_animating = True
        self.current_char_highlight = None
        self.caesar_output.delete("0.0", "end")
        self.caesar_output.insert("end", f"Пошаговое {action.lower()}...\n")
        self.animate_caesar_step(action)

    def animate_caesar_step(self, action="Шифрование"):
        if not self.caesar_is_animating:
            return
        if self.current_char_highlight:
            for lbl in self.current_char_highlight:
                lbl.configure(fg_color="transparent")
        if self.caesar_anim_index >= len(self.caesar_anim_text):
            self.caesar_output.insert("end", f"\n{action} завершено.\n")
            self.caesar_is_animating = False
            self.status.configure(text=f"Цезарь: {action} завершено")
            return

        char = self.caesar_anim_text[self.caesar_anim_index]
        shifted_char = self.caesar_cipher(char, self.caesar_anim_shift)
        self.highlight_characters(char, shifted_char)
        self.caesar_anim_result += shifted_char
        self.caesar_output.delete("0.0", "end")
        self.caesar_output.insert(
            "end",
            f"Шаг {self.caesar_anim_index + 1}:\n"
            f"Исходный: '{char}' → Результат: '{shifted_char}'\n"
            f"Текущий результат: {self.caesar_anim_result}",
        )
        self.caesar_anim_index += 1
        self.after(600, lambda: self.animate_caesar_step(action))

    def create_alphabet_panels(self):
        for widget in self.animation_container.winfo_children():
            widget.destroy()

        # Русский
        rus_panel = ctk.CTkFrame(self.animation_container)
        rus_panel.pack(pady=10, fill="x")
        ctk.CTkLabel(rus_panel, text="Русский алфавит:", font=("Arial", 14, "bold")).pack(anchor="w")
        self.rus_labels, rus_frame = [], ctk.CTkFrame(rus_panel)
        rus_frame.pack()
        for i, ch in enumerate("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"):
            lbl = ctk.CTkLabel(rus_frame, text=ch, width=30, height=30, fg_color="transparent", corner_radius=5)
            lbl.grid(row=0, column=i, padx=2)
            self.rus_labels.append(lbl)

        # Английский
        eng_panel = ctk.CTkFrame(self.animation_container)
        eng_panel.pack(pady=10, fill="x")
        ctk.CTkLabel(eng_panel, text="Английский алфавит:", font=("Arial", 14, "bold")).pack(anchor="w")
        self.eng_labels, eng_frame = [], ctk.CTkFrame(eng_panel)
        eng_frame.pack()
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            lbl = ctk.CTkLabel(eng_frame, text=ch, width=30, height=30, fg_color="transparent", corner_radius=5)
            lbl.grid(row=0, column=i, padx=2)
            self.eng_labels.append(lbl)

    def highlight_characters(self, original, shifted):
        highlight_color = "#3B8ED0"
        shifted_color = "#2FA572"
        if original.upper() in "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ":
            original_idx = self.get_char_index(original, "rus")
            shifted_idx = self.get_char_index(shifted, "rus")
            if original_idx != -1 and shifted_idx != -1:
                self.rus_labels[original_idx].configure(fg_color=highlight_color)
                self.rus_labels[shifted_idx].configure(fg_color=shifted_color)
                self.current_char_highlight = [self.rus_labels[original_idx], self.rus_labels[shifted_idx]]
        elif original.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            original_idx = self.get_char_index(original, "eng")
            shifted_idx = self.get_char_index(shifted, "eng")
            if original_idx != -1 and shifted_idx != -1:
                self.eng_labels[original_idx].configure(fg_color=highlight_color)
                self.eng_labels[shifted_idx].configure(fg_color=shifted_color)
                self.current_char_highlight = [self.eng_labels[original_idx], self.eng_labels[shifted_idx]]

    def get_char_index(self, char: str, lang: str) -> int:
        alphabets = {
            "rus": ("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"),
            "eng": ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"),
        }
        upper, lower = alphabets[lang]
        if char in upper:
            return upper.index(char)
        if char in lower:
            return lower.index(char)
        return -1

    def caesar_cipher(self, text, shift):
        rus_upper = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        rus_lower = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        eng_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        eng_lower = "abcdefghijklmnopqrstuvwxyz"
        result = []
        for ch in text:
            if ch in rus_upper:
                idx = rus_upper.index(ch)
                result.append(rus_upper[(idx + shift) % len(rus_upper)])
            elif ch in rus_lower:
                idx = rus_lower.index(ch)
                result.append(rus_lower[(idx + shift) % len(rus_lower)])
            elif ch in eng_upper:
                idx = eng_upper.index(ch)
                result.append(eng_upper[(idx + shift) % len(eng_upper)])
            elif ch in eng_lower:
                idx = eng_lower.index(ch)
                result.append(eng_lower[(idx + shift) % len(eng_lower)])
            else:
                result.append(ch)
        return "".join(result)

    # ------------------------------------------------------------------------------------
    # RSA
    # ------------------------------------------------------------------------------------
    def init_rsa_tab(self):
        frame = ctk.CTkFrame(self.tab_rsa)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text=("RSA — асимметричный алгоритм. Шифрование/расшифрование выполняются только через образовательные анимации (OAEP)."),
            justify="left",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        # Прогресс
        self.rsa_progress = ctk.CTkProgressBar(frame, width=500)
        self.rsa_progress.pack(pady=5)
        self.rsa_progress.set(0)
        btns = ctk.CTkFrame(frame)
        btns.pack(fill="x", pady=5)
        ctk.CTkButton(btns, text="Сгенерировать ключи (RSA-2048)", command=self.generate_rsa_keys_thread).pack(side="left", padx=5)

        # Ключи
        ctk.CTkLabel(frame, text="Открытый ключ (PEM):").pack(anchor="w")
        pub_row = ctk.CTkFrame(frame); pub_row.pack(fill="x", pady=(0,5))
        self.pub_key_text = ctk.CTkTextbox(pub_row, width=900, height=70)
        self.pub_key_text.pack(side="left", padx=5)
        ctk.CTkButton(pub_row, text="Копировать", command=lambda: copy_to_clipboard(self, self.pub_key_text.get("0.0","end"))).pack(side="left", padx=5)
        ctk.CTkLabel(frame, text="Закрытый ключ (PEM):").pack(anchor="w")
        priv_row = ctk.CTkFrame(frame); priv_row.pack(fill="x", pady=(0,5))
        self.priv_key_text = ctk.CTkTextbox(priv_row, width=900, height=70)
        self.priv_key_text.pack(side="left", padx=5)
        ctk.CTkButton(priv_row, text="Копировать", command=lambda: copy_to_clipboard(self, self.priv_key_text.get("0.0","end"))).pack(side="left", padx=5)
        ctk.CTkLabel(frame, text="Введите сообщение (для анимации шифрования) или HEX-шифр (для анимации расшифрования):").pack(anchor="w")
        msg_row = ctk.CTkFrame(frame); msg_row.pack(fill="x", pady=(0,5))
        self.rsa_message_entry = ctk.CTkTextbox(msg_row, width=900, height=50)
        self.rsa_message_entry.pack(side="left", padx=5)
        ctk.CTkButton(msg_row, text="Копировать", command=lambda: copy_to_clipboard(self, self.rsa_message_entry.get("0.0","end"))).pack(side="left", padx=5)

        # Кнопки анимаций
        controls = ctk.CTkFrame(frame); controls.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(controls, text="Анимация шифрования (OAEP)", command=self.rsa_anim_encrypt_start).pack(side="left", padx=4)
        ctk.CTkButton(controls, text="Анимация расшифрования (OAEP)", command=self.rsa_anim_decrypt_start).pack(side="left", padx=4)

        # Вывод
        self.rsa_output = ctk.CTkTextbox(frame, width=900, height=160)
        self.rsa_output.pack(pady=5)
        self.rsa_private_key = None
        self.rsa_public_key = None
        self._rsa_generating = False
        self._rsa_pulse_job = None

    # Генерация ключей
    def generate_rsa_keys_thread(self):
        if self._rsa_generating:
            return
        self._rsa_generating = True
        self.rsa_output.delete("0.0", "end")
        self.rsa_progress.set(0.0)
        self._start_rsa_progress_pulse()

        def worker():
            try:
                key = RSA.generate(2048)
            except Exception as exc:
                self.after(0, lambda: self._finish_rsa_keygen(error=exc)); return
            self.after(0, lambda: self._finish_rsa_keygen(key=key))

        threading.Thread(target=worker, daemon=True).start()

    def _start_rsa_progress_pulse(self):
        def pulse():
            if not self._rsa_generating:
                return
            current = getattr(self, "_rsa_progress_value", 0.0) + 0.03
            if current > 1.0:
                current = 0.0
            self._rsa_progress_value = current
            self.rsa_progress.set(current)
            self._rsa_pulse_job = self.after(50, pulse)
        self._rsa_progress_value = 0.0
        pulse()

    def _stop_rsa_progress_pulse(self):
        if self._rsa_pulse_job is not None:
            try: self.after_cancel(self._rsa_pulse_job)
            except Exception: pass
            self._rsa_pulse_job = None

    def _finish_rsa_keygen(self, key: RSA.RsaKey | None = None, error: Exception | None = None):
        self._rsa_generating = False
        self._stop_rsa_progress_pulse()
        if error is not None:
            self.rsa_progress.set(0.0)
            messagebox.showerror("Ошибка", f"Генерация ключей: {error}")
            self.status.configure(text="RSA: ошибка генерации")
            return
        self.rsa_private_key = key
        self.rsa_public_key = key.publickey()
        self.priv_key_text.delete("0.0", "end")
        self.priv_key_text.insert("end", key.export_key().decode())
        self.pub_key_text.delete("0.0", "end")
        self.pub_key_text.insert("end", key.publickey().export_key().decode())
        self.rsa_progress.set(1.0)
        self.status.configure(text="RSA: ключи сгенерированы")

        def _on_rsa_key_text_changed(_evt=None):
            self.rsa_public_key = None
            self.rsa_private_key = None

        self.pub_key_text.bind("<KeyRelease>", _on_rsa_key_text_changed)
        self.priv_key_text.bind("<KeyRelease>", _on_rsa_key_text_changed)

    def _load_public_key(self):
        text = self.pub_key_text.get("0.0", "end").strip()
        if not text:
            return None
        try:
            return RSA.import_key(text)
        except Exception:
            return None

    def _load_private_key(self):
        text = self.priv_key_text.get("0.0", "end").strip()
        if not text:
            return None
        try:
            return RSA.import_key(text)
        except Exception:
            return None

    def _rsa_oaep_max_plain_len(self, pubkey: RSA.RsaKey, hash_len=20) -> int:
        k = pubkey.size_in_bytes()
        return max(0, k - 2 * hash_len - 2)

    # RSA: Анимация шифрования (OAEP)
    def rsa_anim_encrypt_start(self):
        pub = self._load_public_key() or self.rsa_public_key
        if not pub:
            messagebox.showerror("Ошибка", "Нужен открытый ключ.")
            return

        text = self.rsa_message_entry.get("0.0", "end").strip()
        if not text:
            messagebox.showerror("Ошибка", "Введите сообщение для шифрования (анимация).")
            return

        # Подготовка OAEP
        k = pub.size_in_bytes()
        hlen = 20  # SHA-1
        m = text.encode("utf-8")
        maxlen = self._rsa_oaep_max_plain_len(pub, hash_len=hlen)
        if len(m) > maxlen:
            messagebox.showerror("Ошибка", f"Сообщение слишком длинное (>{maxlen} байт) для OAEP.")
            return

        def mgf1(seed: bytes, length: int) -> bytes:
            out = b""
            counter = 0
            while len(out) < length:
                c = counter.to_bytes(4, "big")
                h = SHA1.new(seed + c).digest()
                out += h
                counter += 1
            return out[:length]

        lHash = SHA1.new(b"").digest()
        ps_len = k - len(m) - 2*hlen - 2
        PS = b"\x00" * ps_len
        DB = lHash + PS + b"\x01" + m
        seed = get_random_bytes(hlen)
        dbMask = mgf1(seed, k - hlen - 1)
        maskedDB = bytes(a ^ b for a, b in zip(DB, dbMask))
        seedMask = mgf1(maskedDB, hlen)
        maskedSeed = bytes(a ^ b for a, b in zip(seed, seedMask))
        EM = b"\x00" + maskedSeed + maskedDB

        # Контроль: шифрование тем же seed
        cipher = PKCS1_OAEP.new(pub, hashAlgo=SHA1, randfunc=lambda n: seed)
        c_bytes = cipher.encrypt(m)
        c_hex = c_bytes.hex()

        # Карточки шагов
        steps = [
            ("Исходный текст", f"{text}"),
            ("Преобразование в байты m", f"m (UTF-8, hex):\n{m.hex()}"),
            ("Формируем DB", f"DB = lHash || PS || 0x01 || m\n"
                             f"lHash: {lHash.hex()}\n"
                             f"|PS| = {len(PS)} байт, PS: {'00'*min(32, len(PS))}{'…' if len(PS)>32 else ''}\n"
                             f"m: {m.hex()}"),
            ("Генерируем seed", f"seed ({hlen} байт):\n{seed.hex()}"),
            ("Применяем MGF1", f"dbMask = MGF1(seed, k-hlen-1)\nseedMask = MGF1(maskedDB, hlen)\n"
                               f"dbMask: {dbMask.hex()}\nseedMask: {seedMask.hex()}"),
            ("Маскируем", f"maskedDB = DB ⊕ dbMask\nmaskedSeed = seed ⊕ seedMask\n"
                          f"maskedDB: {maskedDB.hex()}\nmaskedSeed: {maskedSeed.hex()}"),
            ("Строим EM", f"EM = 0x00 || maskedSeed || maskedDB\nEM (hex):\n{EM.hex()}"),
            ("Модульная экспонентация", "c = EM^e mod n (быстрая экспонентация по модулю)"),
            ("Результат шифрования", f"Шифртекст (HEX):\n{c_hex}"),
        ]

        # Окно с шагами
        self._open_steps_window("RSA — образовательная анимация шифрования (OAEP/SHA-1)", steps)

        # Вывод и отдельное окно результата
        body = [
            "[RSA-OAEP/SHA-1 — ШИФРОВАНИЕ]",
            f"m (hex): {m.hex()}",
            f"lHash: {lHash.hex()}",
            f"seed: {seed.hex()}",
            f"maskedSeed: {maskedSeed.hex()}",
            f"maskedDB: {maskedDB.hex()}",
            f"EM: {EM.hex()}",
            f"Ciphertext (HEX): {c_hex}",
        ]
        self.rsa_output.delete("0.0", "end")
        self.rsa_output.insert("end", "\n".join(body) + "\n")
        self._show_modal_result("RSA — результат шифрования", "\n".join(body))
        self.status.configure(text="RSA: шифрование (анимация) выполнено")

    # RSA: Анимация расшифрования (OAEP)
    def rsa_anim_decrypt_start(self):
        priv = self._load_private_key() or self.rsa_private_key
        if not priv:
            messagebox.showerror("Ошибка", "Нужен закрытый ключ.")
            return

        text = self.rsa_message_entry.get("0.0", "end").strip()
        if not text:
            messagebox.showerror("Ошибка", "Введите HEX-шифр для анимации расшифрования.")
            return

        try:
            c_bytes = bytes.fromhex(text)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный HEX шифртекста.")
            return

        k = priv.size_in_bytes()
        hlen = 20

        # RSA-расшифрование
        c_int = int.from_bytes(c_bytes, "big")
        m_int = pow(c_int, priv.d, priv.n)
        EM = m_int.to_bytes(k, "big")

        # OAEP: обратные шаги
        def mgf1(seed: bytes, length: int) -> bytes:
            out = b""
            counter = 0
            while len(out) < length:
                c = counter.to_bytes(4, "big")
                h = SHA1.new(seed + c).digest()
                out += h
                counter += 1
            return out[:length]

        if len(EM) != k or EM[0] != 0x00:
            messagebox.showerror("Ошибка", "Неверный формат EM (OAEP).")
            return
        maskedSeed = EM[1:1+hlen]
        maskedDB = EM[1+hlen:]

        seedMask = mgf1(maskedDB, hlen)
        seed = bytes(a ^ b for a, b in zip(maskedSeed, seedMask))
        dbMask = mgf1(seed, k - hlen - 1)
        DB = bytes(a ^ b for a, b in zip(maskedDB, dbMask))

        lHash = SHA1.new(b"").digest()
        lHash_, rest = DB[:hlen], DB[hlen:]
        try:
            idx = rest.index(b"\x01")
        except ValueError:
            messagebox.showerror("Ошибка", "OAEP: отсутствует разделитель 0x01.")
            return
        PS, M = rest[:idx], rest[idx+1:]
        if lHash_ != lHash:
            warn = "Предупреждение: lHash не совпал. Продолжаем учебную демонстрацию."
        else:
            warn = "lHash корректен."

        m_text = M.decode("utf-8", errors="replace")

        steps = [
            ("Входной шифртекст", f"c (HEX):\n{text}"),
            ("Модульная экспонентация", f"EM = c^d mod n\nEM (hex):\n{EM.hex()}"),
            ("Unmask seed", f"seedMask = MGF1(maskedDB)\nmaskedSeed: {maskedSeed.hex()}\nseed: {seed.hex()}"),
            ("Unmask DB", f"dbMask = MGF1(seed)\nmaskedDB: {maskedDB.hex()}\nDB: {DB.hex()}"),
            ("OAEP^-1", f"DB = lHash || PS || 0x01 || M\nlHash: {lHash.hex()}\n{warn}\n|PS|={len(PS)} байт"),
            ("Сообщение m (байты)", f"M (hex): {M.hex()}"),
            ("Декодирование текста", f"{m_text}"),
        ]

        self._open_steps_window("RSA — образовательная анимация расшифрования (OAEP)", steps)

        body = [
            "[RSA-OAEP — РАСШИФРОВАНИЕ]",
            f"EM: {EM.hex()}",
            f"maskedSeed: {maskedSeed.hex()}",
            f"maskedDB: {maskedDB.hex()}",
            f"seed: {seed.hex()}",
            f"DB: {DB.hex()}",
            f"M (hex): {M.hex()}",
            f"Plaintext: {m_text}",
        ]
        self.rsa_output.delete("0.0", "end")
        self.rsa_output.insert("end", "\n".join(body) + "\n")
        self._show_modal_result("RSA — результат расшифрования", "\n".join(body))
        self.status.configure(text="RSA: расшифрование (анимация) выполнено")

    # ------------------------------------------------------------------------------------
    # AES
    # ------------------------------------------------------------------------------------
    def init_aes_tab(self):
        frame = ctk.CTkFrame(self.tab_aes)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        info_label = ctk.CTkLabel(
            frame,
            text=("AES — симметричный блочный шифр. Доступны режимы ECB/CBC/CTR/GCM.\n"
                  "Шифрование/расшифрование выполняются только через образовательные анимации по вашим данным."),
            justify="left",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        info_label.pack(pady=10)
        self.aes_progress = ctk.CTkProgressBar(frame, width=500)
        self.aes_progress.pack(pady=5)
        self.aes_progress.set(0)

        # Настройки
        key_frame = ctk.CTkFrame(frame); key_frame.pack(pady=5, fill="x")
        key_size_frame = ctk.CTkFrame(key_frame); key_size_frame.pack(side="left", padx=5)
        ctk.CTkLabel(key_size_frame, text="Длина ключа:").pack(side="left")
        self.aes_key_size = ctk.CTkComboBox(key_size_frame, values=["16 (128-bit)", "24 (192-bit)", "32 (256-bit)"], width=140)
        self.aes_key_size.set("16 (128-bit)"); self.aes_key_size.pack(side="left")
        key_label = ctk.CTkLabel(key_frame, text="Ключ (HEX):"); key_label.pack(side="left", padx=5)
        self.aes_key_entry = ctk.CTkEntry(key_frame, width=360)
        self.aes_key_entry.pack(side="left", padx=5)
        ctk.CTkButton(key_frame, text="Сгенерировать ключ", command=self.generate_aes_key).pack(side="left", padx=5)
        mode_frame = ctk.CTkFrame(frame); mode_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(mode_frame, text="Режим:").pack(side="left", padx=5)
        self.aes_mode_var = tkinter.StringVar(value="ECB")
        self.aes_mode_box = ctk.CTkComboBox(mode_frame, values=["ECB", "CBC", "CTR", "GCM"], variable=self.aes_mode_var, width=120)
        self.aes_mode_box.pack(side="left", padx=5)
        iv_frame = ctk.CTkFrame(frame); iv_frame.pack(pady=5, fill="x")
        self.iv_nonce_label = ctk.CTkLabel(iv_frame, text="IV/Nonce (HEX):")
        self.iv_nonce_label.pack(side="left", padx=5)
        self.aes_iv_entry = ctk.CTkEntry(iv_frame, width=360, placeholder_text="Если пусто — будет сгенерирован (при шифровании)")
        self.aes_iv_entry.pack(side="left", padx=5)
        tag_frame = ctk.CTkFrame(frame); tag_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(tag_frame, text="Tag (HEX, для GCM-расшифрования):").pack(side="left", padx=5)
        self.aes_tag_entry = ctk.CTkEntry(tag_frame, width=360, placeholder_text="Введите Tag при анимации расшифрования GCM")
        self.aes_tag_entry.pack(side="left", padx=5)

        # Ввод данных
        ctk.CTkLabel(frame, text="Данные (для шифрования) или шифртекст HEX (для расшифрования):").pack(pady=5, anchor="w")
        text_row = ctk.CTkFrame(frame); text_row.pack(fill="x")
        self.aes_text_box = ctk.CTkTextbox(text_row, width=1000, height=100)
        self.aes_text_box.pack(side="left", padx=5)
        ctk.CTkButton(text_row, text="Копировать", command=lambda: copy_to_clipboard(self, self.aes_text_box.get("0.0","end"))).pack(side="left", padx=5)

        # Кнопки анимаций
        aes_button_frame = ctk.CTkFrame(frame); aes_button_frame.pack(pady=5)
        ctk.CTkButton(aes_button_frame, text="Анимация шифрования", command=self.animate_aes_encrypt_start).pack(side="left", padx=5)
        ctk.CTkButton(aes_button_frame, text="Анимация расшифрования", command=self.animate_aes_decrypt_start).pack(side="left", padx=5)

        # Вывод
        self.aes_output_box = ctk.CTkTextbox(frame, width=1000, height=200)
        self.aes_output_box.pack(pady=5)

    def generate_aes_key(self):
        try:
            size_map = {"16 (128-bit)": 16, "24 (192-bit)": 24, "32 (256-bit)": 32}
            key_length = size_map[self.aes_key_size.get()]
            random_key = get_random_bytes(key_length)
            self.aes_key_entry.delete(0, "end")
            self.aes_key_entry.insert(0, random_key.hex())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Генерация ключа: {e}")

    def _get_aes_key_checked(self):
        key_hex = self.aes_key_entry.get().strip()
        if not key_hex:
            return None, "Введите ключ (HEX)!"
        try:
            key = bytes.fromhex(key_hex)
        except ValueError:
            return None, "Ключ должен быть в HEX-формате!"
        expected_len = int(self.aes_key_size.get().split()[0])
        if len(key) != expected_len:
            return None, f"Ожидается {expected_len} байт для выбранной длины ключа!"
        return key, None

    def _get_iv_for_mode(self, mode: str, for_decrypt: bool):
        iv_hex = self.aes_iv_entry.get().strip()
        if mode == "ECB":
            return None, None, "—"
        if mode == "CBC":
            if not iv_hex and not for_decrypt:
                iv = get_random_bytes(16)
                return iv, None, f"IV={iv.hex()}"
            if not iv_hex and for_decrypt:
                return None, "Для CBC нужен IV (16 байт).", ""
            try:
                iv = bytes.fromhex(iv_hex)
            except ValueError:
                return None, "IV/Nonce должен быть в HEX-формате.", ""
            if len(iv) != 16:
                return None, "Для CBC нужен 16-байтовый IV.", ""
            return iv, None, f"IV={iv.hex()}"
        if mode == "CTR":
            if not iv_hex and not for_decrypt:
                iv = get_random_bytes(8)
                return iv, None, f"Nonce={iv.hex()}"
            if not iv_hex and for_decrypt:
                return None, "Для CTR нужен Nonce (8 байт).", ""
            try:
                iv = bytes.fromhex(iv_hex)
            except ValueError:
                return None, "IV/Nonce должен быть в HEX-формате.", ""
            if len(iv) != 8:
                return None, "Для CTR нужен Nonce 8 байт.", ""
            return iv, None, f"Nonce={iv.hex()}"
        # GCM
        if not iv_hex and not for_decrypt:
            iv = get_random_bytes(12)
            return iv, None, f"Nonce={iv.hex()}"
        if not iv_hex and for_decrypt:
            return None, "Для GCM нужен Nonce (12 байт) и Tag.", ""
        try:
            iv = bytes.fromhex(iv_hex)
        except ValueError:
            return None, "IV/Nonce должен быть в HEX-формате.", ""
        if len(iv) != 12:
            return None, "Для GCM нужен Nonce 12 байт.", ""
        return iv, None, f"Nonce={iv.hex()}"

    # AES: Анимация шифрования
    def animate_aes_encrypt_start(self):
        mode = self.aes_mode_box.get()
        key, err = self._get_aes_key_checked()
        if err: messagebox.showerror("Ошибка", err); return
        iv, iverr, iv_label = self._get_iv_for_mode(mode, for_decrypt=False)
        if iverr: messagebox.showerror("Ошибка IV/Nonce", iverr); return
        data = self.aes_text_box.get("0.0", "end").rstrip("\n")
        if not data: messagebox.showerror("Ошибка", "Введите данные для шифрования!"); return
        m = data.encode("utf-8")

        steps = []
        if mode == "ECB":
            p = pkcs7_pad(m)
            blocks = [p[i:i+16] for i in range(0, len(p), 16)]
            cipher = AES.new(key, AES.MODE_ECB)
            out_blocks = [cipher.encrypt(b) for b in blocks]
            c_hex = b"".join(out_blocks).hex()

            steps = [
                ("Исходные данные", f"{data}"),
                ("Преобразование в байты", f"m (hex): {m.hex()}"),
                ("PKCS#7", "Добавляем выравнивание, чтобы длина стала кратной 16."),
                ("Разбиение на блоки", f"Количество блоков: {len(blocks)}\nПервый блок (hex): {blocks[0].hex() if blocks else '—'}"),
                ("AES-ECB для каждого блока", "Шифрование каждого блока независимо (SubBytes→ShiftRows→MixColumns→AddRoundKey...)."),
                ("Результат шифрования", f"Ciphertext (HEX):\n{c_hex}"),
            ]
            self._open_steps_window(f"AES-ECB — образовательная анимация шифрования", steps)
            result_text = f"[AES-ECB]\nCiphertext (HEX): {c_hex}\n"

        elif mode == "CBC":
            p = pkcs7_pad(m)
            blocks = [p[i:i+16] for i in range(0, len(p), 16)]
            cipher_ecb = AES.new(key, AES.MODE_ECB)
            out_blocks = []
            prev = iv
            details = []
            for i, b in enumerate(blocks):
                x = bytes(a ^ b_ for a, b_ in zip(b, prev))
                c = cipher_ecb.encrypt(x)
                out_blocks.append(c)
                details.append(f"Блок {i+1}: Plain={b.hex()} XOR prev={prev.hex()} → {x.hex()} → E_k → C={c.hex()}")
                prev = c
            c_hex = b"".join(out_blocks).hex()
            steps = [
                ("Исходные данные", f"{data}"),
                ("Преобразование в байты", f"m (hex): {m.hex()}"),
                ("PKCS#7", "Добавляем выравнивание до кратности 16."),
                ("Начальный вектор", iv_label),
                ("XOR и шифрование блоков", "\n".join(details)),
                ("Результат шифрования", f"IV (HEX): {iv.hex()}\nCiphertext (HEX):\n{c_hex}"),
            ]
            self._open_steps_window(f"AES-CBC — образовательная анимация шифрования", steps)
            result_text = f"[AES-CBC]\nIV (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\n"

        elif mode == "CTR":
            blocks = [m[i:i+16] for i in range(0, len(m), 16)]
            cipher_ecb = AES.new(key, AES.MODE_ECB)
            out_blocks = []
            lines = []
            for i, b in enumerate(blocks):
                ctr = i.to_bytes(8, "big")
                ke = cipher_ecb.encrypt(iv + ctr)
                ks = ke[:len(b)]
                c = bytes(a ^ b_ for a, b_ in zip(b, ks))
                out_blocks.append(c)
                lines.append(f"Блок {i+1}: ctr={ctr.hex()} | KS={ks.hex()} | Plain={b.hex()} → C={c.hex()}")
            c_hex = b"".join(out_blocks).hex()
            steps = [
                ("Исходные данные", f"{data}"),
                ("Преобразование в байты", f"m (hex): {m.hex()}"),
                ("Nonce", iv_label),
                ("Формирование счётчика и Keystream", "\n".join(lines)),
                ("Результат шифрования", f"Nonce (HEX): {iv.hex()}\nCiphertext (HEX):\n{c_hex}"),
            ]
            self._open_steps_window(f"AES-CTR — образовательная анимация шифрования", steps)
            result_text = f"[AES-CTR]\nNonce (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\n"

        else:  # GCM
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            c_bytes, tag = cipher.encrypt_and_digest(m)
            c_hex = c_bytes.hex()
            steps = [
                ("Исходные данные", f"{data}"),
                ("Преобразование в байты", f"m (hex): {m.hex()}"),
                ("Nonce", f"Nonce={iv.hex()}"),
                ("CTR-поток + XOR", "GCM шифрует в CTR, параллельно считает MAC в поле Галуа."),
                ("Тег аутентичности", f"Tag (HEX): {tag.hex()}"),
                ("Результат шифрования", f"Nonce (HEX): {iv.hex()}\nCiphertext (HEX):\n{c_hex}\nTag (HEX): {tag.hex()}"),
            ]
            self._open_steps_window(f"AES-GCM — образовательная анимация шифрования", steps)
            result_text = f"[AES-GCM]\nNonce (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\nTag (HEX): {tag.hex()}\n"

        # Выводы и модалка
        self.aes_output_box.delete("0.0", "end")
        self.aes_output_box.insert("end", result_text)
        self._show_modal_result(f"AES — результат шифрования ({mode})", result_text)
        self.status.configure(text=f"AES {mode}: шифрование (анимация) выполнено")

    # AES: Анимация расшифрования
    def animate_aes_decrypt_start(self):
        mode = self.aes_mode_box.get()
        key, err = self._get_aes_key_checked()
        if err: messagebox.showerror("Ошибка", err); return
        c_hex = self.aes_text_box.get("0.0", "end").strip()
        if not c_hex: messagebox.showerror("Ошибка", "Введите шифртекст (HEX) для расшифрования!"); return
        try:
            c_bytes = bytes.fromhex(c_hex)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат шифртекста (HEX)!"); return

        iv, iverr, iv_label = self._get_iv_for_mode(mode, for_decrypt=True)
        if iverr: messagebox.showerror("Ошибка IV/Nonce", iverr); return
        steps = []
        if mode == "ECB":
            cipher = AES.new(key, AES.MODE_ECB)
            p = cipher.decrypt(c_bytes)
            try:
                p = pkcs7_unpad(p)
                plain = p.decode("utf-8", errors="replace")
            except Exception as e:
                plain = f"(ошибка паддинга/декодирования: {e})"
            steps = [
                ("Входной шифртекст", f"C (HEX): {c_hex}"),
                ("Расшифрование блоков", "D_k для каждого блока."),
                ("Удаление PKCS#7", "Снимаем выравнивание."),
                ("Получение текста", f"{plain}"),
            ]
            self._open_steps_window("AES-ECB — образовательная анимация расшифрования", steps)
            result_text = f"[AES-ECB]\nPlaintext: {plain}\n"

        elif mode == "CBC":
            cipher_ecb = AES.new(key, AES.MODE_ECB)
            blocks = [c_bytes[i:i+16] for i in range(0, len(c_bytes), 16)]
            p_all = b""
            details = []
            prev = iv
            for i, b in enumerate(blocks):
                x = cipher_ecb.decrypt(b)
                pblk = bytes(a ^ b_ for a, b_ in zip(x, prev))
                details.append(f"Блок {i+1}: D_k(C)={x.hex()} XOR prev={prev.hex()} → {pblk.hex()}")
                p_all += pblk
                prev = b
            try:
                p = pkcs7_unpad(p_all)
                plain = p.decode("utf-8", errors="replace")
            except Exception as e:
                plain = f"(ошибка паддинга/декодирования: {e})"
            steps = [
                ("Входной шифртекст", f"C (HEX): {c_hex}"),
                ("Расшифрование блоков", "\n".join(details)),
                ("Удаление PKCS#7", "Снимаем выравнивание."),
                ("Получение текста", f"{plain}"),
            ]
            self._open_steps_window("AES-CBC — образовательная анимация расшифрования", steps)
            result_text = f"[AES-CBC]\nPlaintext: {plain}\n"

        elif mode == "CTR":
            cipher_ecb = AES.new(key, AES.MODE_ECB)
            blocks = [c_bytes[i:i+16] for i in range(0, len(c_bytes), 16)]
            p_all = b""
            details = []
            for i, b in enumerate(blocks):
                ctr = i.to_bytes(8, "big")
                ke = cipher_ecb.encrypt(iv + ctr)
                ks = ke[:len(b)]
                pblk = bytes(a ^ b_ for a, b_ in zip(b, ks))
                details.append(f"Блок {i+1}: ctr={ctr.hex()} | KS={ks.hex()} | C={b.hex()} → P={pblk.hex()}")
                p_all += pblk
            plain = p_all.decode("utf-8", errors="replace")
            steps = [
                ("Nonce/Счётчик/Keystream", iv_label + "\n" + "\n".join(details)),
                ("Получение текста", f"{plain}"),
            ]
            self._open_steps_window("AES-CTR — образовательная анимация расшифрования", steps)
            result_text = f"[AES-CTR]\nPlaintext: {plain}\n"

        else:  # GCM
            tag_hex = self.aes_tag_entry.get().strip()
            if not tag_hex:
                messagebox.showerror("Ошибка", "Укажите Tag (HEX) для GCM расшифрования."); return
            try:
                tag = bytes.fromhex(tag_hex)
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный Tag (HEX)."); return
            try:
                cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
                p_bytes = cipher.decrypt_and_verify(c_bytes, tag)
                plain = p_bytes.decode("utf-8", errors="replace")
                steps = [
                    ("Nonce и TAG", f"{iv_label}\nTag={tag.hex()}\nПроверяем подлинность."),
                    ("CTR-поток + XOR", "После успешной проверки тега извлекаем текст."),
                    ("Получение текста", f"{plain}"),
                ]
            except Exception as e:
                plain = f"(не удалось проверить тег: {e})"
                steps = [
                    ("Nonce и TAG", f"{iv_label}\nTag={tag.hex()}"),
                    ("Ошибка аутентичности", str(e)),
                ]
            self._open_steps_window("AES-GCM — образовательная анимация расшифрования", steps)
            result_text = f"[AES-GCM]\nPlaintext: {plain}\n"

        self.aes_output_box.delete("0.0", "end")
        self.aes_output_box.insert("end", result_text)
        self._show_modal_result(f"AES — результат расшифрования ({mode})", result_text)
        self.status.configure(text=f"AES {mode}: расшифрование (анимация) выполнено")

    # ------------------------------------------------------------------------------------
    # ПРАКТИКА
    # ------------------------------------------------------------------------------------
    def init_practice_tab(self):
        frame = ctk.CTkFrame(self.tab_practice)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="Практические задания", font=ctk.CTkFont(size=15, weight="bold"))
        title.pack(pady=6, anchor="w")

        # Цезарь: испытание
        caesar_box = ctk.CTkFrame(frame); caesar_box.pack(fill="x", pady=8)
        ctk.CTkLabel(caesar_box, text="Цезарь: испытание", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.practice_caesar_task_lbl = ctk.CTkLabel(caesar_box, text="Нажмите «Новая задача»")
        self.practice_caesar_task_lbl.pack(anchor="w", padx=6)
        row = ctk.CTkFrame(caesar_box); row.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(row, text="Новая задача", command=self.practice_caesar_new).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Показать все сдвиги", command=self.practice_caesar_bruteforce).pack(side="left", padx=4)
        inrow = ctk.CTkFrame(caesar_box); inrow.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(inrow, text="Ваш сдвиг:").pack(side="left")
        self.practice_caesar_shift = ctk.IntVar(value=0)
        ctk.CTkEntry(inrow, width=60, textvariable=self.practice_caesar_shift).pack(side="left", padx=4)
        ctk.CTkLabel(inrow, text="Ваша расшифровка:").pack(side="left", padx=8)
        self.practice_caesar_answer = ctk.CTkEntry(inrow, width=500, placeholder_text="Введите предполагаемый открытый текст")
        self.practice_caesar_answer.pack(side="left", padx=4)
        ctk.CTkButton(inrow, text="Проверить", command=self.practice_caesar_check).pack(side="left", padx=6)
        self.practice_caesar_feedback = ctk.CTkLabel(caesar_box, text="")
        self.practice_caesar_feedback.pack(anchor="w", padx=6, pady=(0,6))

        # Новая мини-задача: Определи режим AES
        aes_box = ctk.CTkFrame(frame); aes_box.pack(fill="x", pady=8)
        ctk.CTkLabel(aes_box, text="Задание: распознай режим AES по подсказке", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.aes_quiz_hint = ctk.CTkLabel(aes_box, text="Подсказка: повторяющиеся блоки видны в шифртексте. Какой режим использован?")
        self.aes_quiz_hint.pack(anchor="w", padx=6)
        self.aes_mode_var_q = tkinter.StringVar(value="")
        modes = ["ECB", "CBC", "CTR", "GCM"]
        rowm = ctk.CTkFrame(aes_box); rowm.pack(anchor="w", padx=6, pady=6)
        for m in modes:
            ctk.CTkRadioButton(rowm, text=m, variable=self.aes_mode_var_q, value=m).pack(side="left", padx=4)
        ctk.CTkButton(aes_box, text="Проверить", command=self._check_aes_quiz).pack(anchor="w", padx=6, pady=6)
        self.aes_quiz_out = ctk.CTkLabel(aes_box, text="")
        self.aes_quiz_out.pack(anchor="w", padx=6, pady=(0,6))

        # Новая мини-задача: RSA-логика (True/False)
        rsa_box = ctk.CTkFrame(frame); rsa_box.pack(fill="x", pady=8)
        ctk.CTkLabel(rsa_box, text="Мини-викторина по RSA (True/False)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.q_vars = []
        questions = [
            ("В RSA открытый ключ используется для шифрования, закрытый — для расшифрования.", True),
            ("OAEP — это схема паддинга, повышающая стойкость к атакам на шифртекст.", True),
            ("Если Nonce в GCM повторить, это безопасно, ведь есть тег.", False),
        ]
        for i,(q,ans) in enumerate(questions, 1):
            row = ctk.CTkFrame(rsa_box); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{i}. {q}").pack(side="left")
            var = tkinter.StringVar(value="Нет ответа")
            self.q_vars.append((var, ans))
            ctk.CTkRadioButton(row, text="True", variable=var, value="True").pack(side="left", padx=4)
            ctk.CTkRadioButton(row, text="False", variable=var, value="False").pack(side="left", padx=4)
        ctk.CTkButton(rsa_box, text="Проверить ответы", command=self._check_quiz).pack(anchor="w", padx=6, pady=6)
        self.quiz_out = ctk.CTkLabel(rsa_box, text="")
        self.quiz_out.pack(anchor="w")
        self._practice_caesar_secret = ""
        self._practice_caesar_shift = 0

    def practice_caesar_new(self):
        samples = [
            "CRYPTOGRAPHY IS FUN", "SECURITY THROUGH OBSCURITY", "HELLO WORLD",
            "КРИПТОГРАФИЯ ЭТО ИНТЕРЕСНО", "ЛЮБЛЮ ПРОГРАММИРОВАТЬ", "ПРИВЕТ МИР"
        ]
        plain = random.choice(samples)
        shift = random.randint(1, 25)
        self._practice_caesar_secret = plain
        self._practice_caesar_shift = shift
        cipher = self.caesar_cipher(plain, shift)
        self.practice_caesar_task_lbl.configure(text=f"Шифртекст: {cipher}")
        self.practice_caesar_feedback.configure(text="Задача создана. Укажите сдвиг и/или расшифровку.")

    def practice_caesar_bruteforce(self):
        ct = self.practice_caesar_task_lbl.cget("text").replace("Шифртекст: ", "").strip()
        if not ct:
            messagebox.showinfo("Брутфорс", "Сначала создайте задачу.")
            return
        lines = []
        for s in range(0, 33):
            lines.append(f"{s:2d}: {self.caesar_cipher(ct, -s)}")
        self.practice_caesar_feedback.configure(text="Возможные варианты:\n" + "\n".join(lines[:33]))

    def practice_caesar_check(self):
        if not self._practice_caesar_secret:
            messagebox.showinfo("Проверка", "Сначала создайте задачу.")
            return
        user_shift = self.practice_caesar_shift.get()
        user_answer = self.practice_caesar_answer.get().strip()
        ok_shift = (user_shift % 33) == (self._practice_caesar_shift % 33)
        ok_text = (user_answer.strip().upper() == self._practice_caesar_secret.strip().upper()) if user_answer else False
        if ok_shift and ok_text:
            self.practice_caesar_feedback.configure(text="✅ Верно! Сдвиг и текст совпадают.")
        elif ok_shift:
            self.practice_caesar_feedback.configure(text="🟡 Сдвиг верный, но текст не совпал.")
        elif ok_text:
            self.practice_caesar_feedback.configure(text="🟡 Текст верный, но сдвиг указан неверно.")
        else:
            self.practice_caesar_feedback.configure(text="❌ Пока неверно. Попробуйте ещё!")

    def _check_aes_quiz(self):
        val = self.aes_mode_var_q.get()
        if not val:
            self.aes_quiz_out.configure(text="Выберите вариант.")
            return
        correct = "ECB"
        self.aes_quiz_out.configure(text="✅ Верно!" if val == correct else f"❌ Неверно. Правильный ответ: {correct}")

    def _check_quiz(self):
        correct = 0
        total = len(self.q_vars)
        details = []
        for i,(var, ans) in enumerate(self.q_vars, 1):
            val = var.get()
            if val == "Нет ответа":
                details.append(f"{i}) пропущено")
            else:
                ok = (val == "True") == ans
                details.append(f"{i}) {'✅' if ok else '❌'}")
                if ok: correct += 1
        self.quiz_out.configure(text=f"Результат: {correct}/{total}\n" + " ".join(details))

    # ------------------------------------------------------------------------------------
    # УЧЕБНИК
    # ------------------------------------------------------------------------------------
    def init_tutor_tab(self):
        frame = ctk.CTkFrame(self.tab_tutor)
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        header = ctk.CTkLabel(frame, text="📘 Интерактивный учебник", font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(anchor="w", padx=6, pady=(0, 6))
        # Контейнер под текст + полосы прокрутки
        container = ctk.CTkFrame(frame)
        container.pack(fill="both", expand=True, padx=6, pady=6)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.tutor_textbox = ctk.CTkTextbox(container, wrap="word")
        self.tutor_textbox.grid(row=0, column=0, sticky="nsew")
        vscroll = ctk.CTkScrollbar(container, command=self.tutor_textbox.yview)
        vscroll.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.tutor_textbox.configure(yscrollcommand=vscroll.set)

        tutor_text = (
            "🔐 Добро пожаловать в подробную справку программы!\n\n"
            "📚 Информация по работе программы:\n\n"
            "🔸 Шифр Цезаря:\n"
            "  Простой симметричный алгоритм, при котором символы заменяются на символы с фиксированным сдвигом.\n"
            "  Реализованы функции шифровки/расшифровки, а также возможность управлять сдвигом.\n"
            "  Реализована подробная алфавитная анимация для русского и английского языков.\n\n"
            "🔸 RSA:\n"
            "  Асимметричный алгоритм с открытым и закрытым ключом. Подходит для безопасной передачи данных и цифровой подписи.\n"
            "  Используется длина ключей 2048 бит.\n"
            "  Реализована функция шифровки/расшифровки.\n\n"
            "🔸 AES:\n"
            "  Современный симметричный блочный шифр с возможностью выбора режима работы: ECB, CBC, CTR, GCM.\n"
            "  Реализована генерация ключа (16/24/32 байта), IV или Nonce. В режиме GCM используется тег аутентификации (Tag).\n"
            "  Реализована функция шифровки/расшифровки.\n"
            "  Реализована подробная анимация для каждого из режима работы.\n\n"
            "==================================\n"
            "📖 Подробная теоретическая справка\n"
            "==================================\n\n"
            "🔹 1) Шифр Цезаря:\n"
            "Определение: метод, при котором каждый символ сдвигается по алфавиту на определённое количество позиций.\n"
            "Пример:\n"
            "- Оригинал: HELLO, Ключ: 3 → Зашифровано: KHOOR\n"
            "Преимущества: простота, подходит для обучения.\n"
            "Недостатки: легко взломать перебором.\n\n"
            "🔹 2) RSA:\n"
            "Определение: криптографический метод с использованием пары ключей (публичного и приватного).\n"
            "Цифровая подпись - подтверждает подлинность отправителя и неизменность данных.\n"
            "Преимущества: безопасность при передаче данных и наличии подписи.\n"
            "Недостатки: низкая производительность при больших объёмах данных.\n"
            "Размер ключей: 2048 бит.\n\n"
            "📌 Дополнительные определения:\n"
            "- 🔑 Ключ (Key) - набор байт, используемый для шифрования/расшифровки.\n"
            "- 🧊 IV (Initialization Vector) - начальное значение для режимов, таких как CBC. Должен быть уникальным.\n"
            "- 🔁 Nonce - уникальное число, аналог IV для CTR и GCM, но обычно короче.\n"
            "- 🧪 Tag (MAC) - цифровая подпись сообщения для проверки подлинности (используется в GCM).\n"
            "- 🧾 HEX-шифр - данные в шестнадцатеричном виде. Используются для представления зашифрованного текста.\n"
            "- ✖️ XOR - побитовая операция, используется для объединения блоков при шифровании (например, в CBC).\n\n"
            "🔹 3) AES — Режимы работы:\n"
            "- 🧱 ECB (Electronic Codebook):\n"
            "  Каждый блок шифруется независимо от других.\n"
            "  Преимущества: простая реализация.\n"
            "  Недостатки: небезопасен — повторяющиеся блоки остаются узнаваемыми.\n\n"
            "- 🔗 CBC (Cipher Block Chaining):\n"
            "  Каждый блок перед шифрованием объединяется с предыдущим с помощью XOR.\n"
            "  Преимущества: надёжнее, чем ECB.\n"
            "  Недостатки: требует IV и невозможность параллельной расшифровки.\n\n"
            "- 📊 CTR (Counter):\n"
            "  Потоковый режим, где каждый блок шифруется с помощью счётчика и Nonce.\n"
            "  Преимущества: высокая скорость, возможность параллельной обработки.\n"
            "  Недостатки: необходимо обеспечить уникальность Nonce.\n\n"
            "- 🔐 GCM (Galois/Counter Mode):\n"
            "  Совмещает CTR и проверку целостности с помощью тега (Tag).\n"
            "  Преимущества: высокая безопасность, аутентификация данных.\n"
            "  Недостатки: сложность реализации.\n\n"
            "📎 Примеры (в формате HEX):\n"
            "- Ключ AES-128: 00112233445566778899aabbccddeeff\n"
            "- IV (CBC/CTR): aabbccddeeff00112233445566778899\n"
            "- Nonce (GCM): aabbccddeeff001122334455\n"
            "- Tag (GCM): 112233445566778899aabbccddeeff00\n\n"
            "💡 Подсказка:\n "
            "- HEX-шифр вставляется в поле «Данные для шифрования/дешифрования». Не путайте с IV или Nonce.\n"
            " - Копирование/Вставка/Вырезка доступна по нажатию ПКМ.\n\n"
            "✨ Удачи в изучении криптографии и приятной работы!\n\n\n"
            "👨‍💻 Разработчик программы: Forman75 (https://github.com/Forman75)"
        )
        self.tutor_textbox.configure(state="normal")
        self.tutor_textbox.delete("1.0", "end")
        self.tutor_textbox.insert("1.0", tutor_text)
        self.tutor_textbox.configure(state="disabled")

    # ------------------------------------------------------------------------------------
    # КОНТЕКСТНОЕ МЕНЮ (ПКМ)
    # ------------------------------------------------------------------------------------
    def _bind_context_menus(self):
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

        recurse(self)
        self.after(0, lambda: self.state("zoomed"))

# ----------------------------------------------------------------------------------------
# ЗАПУСК ПРОГРАММЫ
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    app = CryptoGRAD(scale=1.0)
    app.mainloop()
