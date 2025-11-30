import customtkinter as ctk
import tkinter
from utils import resource_path, bind_context_menus
from caesar import CaesarTab
from rsa import RSATab
from aes import AESTab
from practice import PracticeTab
from tutor import TutorTab

ctk.set_default_color_theme("dark-blue")

class CryptoGRAD(ctk.CTk):
    def __init__(self, scale: float = 1.0):
        try:
            ctk.set_widget_scaling(scale)
        except Exception:
            pass
        super().__init__()
        self.title("CryptoGRAD - Environment for Cryptographic Modeling")

        # Верхняя панель
        topbar = ctk.CTkFrame(self); topbar.pack(fill="x")
        ctk.CTkLabel(
            topbar,
            text="🔐 CryptoGRAD - Environment for Cryptographic Modeling",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10, pady=6)
        self.status = ctk.CTkLabel(topbar, text="Программа готова к работе", anchor="e")
        self.status.pack(side="right", padx=10)

        # Табы
        self.tabview = ctk.CTkTabview(self, width=1280, height=760)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tab_caesar = self.tabview.add("Шифр Цезаря")
        self.tab_rsa    = self.tabview.add("RSA")
        self.tab_aes    = self.tabview.add("AES")
        self.tab_prac   = self.tabview.add("Симуляция")
        self.tab_tutor  = self.tabview.add("База знаний")

        # Внедрение вкладок
        self.caesar = CaesarTab(self, self.tab_caesar, self.set_status)
        self.rsa    = RSATab(self, self.tab_rsa,    self.set_status)
        self.aes    = AESTab(self, self.tab_aes,    self.set_status)
        self.practice = PracticeTab(self, self.tab_prac, self.set_status, self.caesar.caesar_cipher)
        self.tutor    = TutorTab(self, self.tab_tutor)
        bind_context_menus(self)
        self.after(0, self._safe_zoom)

    def _safe_zoom(self):
        try:
            self.state("zoomed")
        except tkinter.TclError:
            pass

    def set_status(self, text: str):
        self.status.configure(text=text)

if __name__ == "__main__":
    app = CryptoGRAD(scale=1.0)
    app.mainloop()
