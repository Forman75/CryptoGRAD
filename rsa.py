# rsa.py
import threading
import customtkinter as ctk
from tkinter import messagebox
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA1
from utils import copy_to_clipboard
from animations import FullscreenTimelineWindow, draw_hex_block, draw_tag, draw_arrow, draw_badge


class RSATab:
    def __init__(self, app, parent, set_status):
        self.app = app
        self.set_status = set_status

        frame = ctk.CTkFrame(parent)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="RSA — асимметричный алгоритм (OAEP/SHA-1). Анимация открывается в полноэкранном окне и показывает все байты БЕЗ сокращений.",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="left"
        ).pack(pady=8, anchor="w")

        # Прогресс-бар генерации
        self.progress = ctk.CTkProgressBar(frame, width=500)
        self.progress.pack(pady=6)
        self.progress.set(0.0)

        # Кнопки
        bro = ctk.CTkFrame(frame); bro.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(bro, text="Сгенерировать ключи (RSA-2048)", command=self._gen_keys).pack(side="left", padx=6)

        # Публичный ключ
        ctk.CTkLabel(frame, text="Открытый ключ (PEM):").pack(anchor="w")
        prow = ctk.CTkFrame(frame); prow.pack(fill="x", pady=(0, 6))
        self.pub_text = ctk.CTkTextbox(prow, height=80, width=900)
        self.pub_text.pack(side="left", padx=6, fill="x", expand=True)
        ctk.CTkButton(prow, text="Копировать", command=lambda: copy_to_clipboard(self.app, self.pub_text.get("0.0", "end"))).pack(side="left", padx=6)

        # Приватный ключ
        ctk.CTkLabel(frame, text="Закрытый ключ (PEM):").pack(anchor="w")
        rrow = ctk.CTkFrame(frame); rrow.pack(fill="x", pady=(0, 6))
        self.priv_text = ctk.CTkTextbox(rrow, height=80, width=900)
        self.priv_text.pack(side="left", padx=6, fill="x", expand=True)
        ctk.CTkButton(rrow, text="Копировать", command=lambda: copy_to_clipboard(self.app, self.priv_text.get("0.0", "end"))).pack(side="left", padx=6)

        # Сообщение/шифртекст
        ctk.CTkLabel(frame, text="Введите сообщение (для шифрования) или HEX-шифртекст (для расшифрования):").pack(anchor="w", pady=(4, 0))
        mrow = ctk.CTkFrame(frame); mrow.pack(fill="x", pady=(0, 6))
        self.msg = ctk.CTkTextbox(mrow, height=60, width=900)
        self.msg.pack(side="left", padx=6, fill="x", expand=True)
        ctk.CTkButton(mrow, text="Копировать", command=lambda: copy_to_clipboard(self.app, self.msg.get("0.0", "end"))).pack(side="left", padx=6)

        # Кнопки анимации
        arow = ctk.CTkFrame(frame); arow.pack(pady=6)
        ctk.CTkButton(arow, text="Анимация шифрования (полноэкранно)", command=self._anim_encrypt_full).pack(side="left", padx=6)
        ctk.CTkButton(arow, text="Анимация расшифрования (полноэкранно)", command=self._anim_decrypt_full).pack(side="left", padx=6)

        # Вывод результата/подсказок
        self.out = ctk.CTkTextbox(frame, height=160)
        self.out.pack(fill="both", expand=False, pady=(6, 0))

        # состояние
        self._keypair = None
        self._gen_job = None
        self._gen_inflight = False

    # ключи
    def _gen_keys(self):
        if self._gen_inflight:
            return
        self._gen_inflight = True
        self.progress.set(0.0)
        self._pulse()

        def worker():
            try:
                key = RSA.generate(2048)
            except Exception as e:
                self.app.after(0, lambda: self._finish_gen(error=e))
                return
            self.app.after(0, lambda: self._finish_gen(key))

        threading.Thread(target=worker, daemon=True).start()

    def _pulse(self):
        if not self._gen_inflight:
            return
        val = getattr(self, "_p", 0.0) + 0.03
        if val >= 1.0: val = 0.0
        self._p = val
        self.progress.set(val)
        self._gen_job = self.app.after(60, self._pulse)

    def _finish_gen(self, key=None, error=None):
        self._gen_inflight = False
        if self._gen_job:
            try: self.app.after_cancel(self._gen_job)
            except Exception: pass
            self._gen_job = None
        if error:
            self.progress.set(0.0)
            messagebox.showerror("Ошибка генерации", str(error))
            return
        self._keypair = key
        self.progress.set(1.0)
        self.priv_text.delete("0.0", "end"); self.priv_text.insert("end", key.export_key().decode())
        self.pub_text.delete("0.0", "end");  self.pub_text.insert("end", key.publickey().export_key().decode())
        self.set_status("RSA: ключи сгенерированы")

    # загрузка ключей
    def _load_pub(self):
        txt = self.pub_text.get("0.0", "end").strip()
        if not txt and self._keypair:
            return self._keypair.publickey()
        if not txt:
            return None
        try:
            return RSA.import_key(txt)
        except Exception:
            return None

    def _load_priv(self):
        txt = self.priv_text.get("0.0", "end").strip()
        if not txt and self._keypair:
            return self._keypair
        if not txt:
            return None
        try:
            return RSA.import_key(txt)
        except Exception:
            return None

    # вспомогательное
    @staticmethod
    def _mgf1(seed: bytes, length: int) -> bytes:
        out = b""
        counter = 0
        while len(out) < length:
            c = counter.to_bytes(4, "big")
            h = SHA1.new(seed + c).digest()
            out += h
            counter += 1
        return out[:length]

    @staticmethod
    def _oaep_max_plain_len(pubkey: RSA.RsaKey, hash_len=20) -> int:
        k = pubkey.size_in_bytes()
        return max(0, k - 2 * hash_len - 2)

    # анимации
    def _anim_encrypt_full(self):
        pub = self._load_pub()
        if not pub:
            messagebox.showerror("Ошибка", "Нужен открытый ключ (PEM).")
            return

        text = self.msg.get("0.0", "end").strip()
        if not text:
            messagebox.showerror("Ошибка", "Введите сообщение для шифрования.")
            return

        # Подготовка OAEP (SHA-1)
        k = pub.size_in_bytes()
        hlen = 20
        m = text.encode("utf-8")
        maxlen = self._oaep_max_plain_len(pub, hash_len=hlen)
        if len(m) > maxlen:
            messagebox.showerror("Ошибка", f"Сообщение слишком длинное для RSA-OAEP. Максимум {maxlen} байт.")
            return

        lHash = SHA1.new(b"").digest()
        ps_len = k - len(m) - 2 * hlen - 2
        PS = b"\x00" * ps_len
        DB = lHash + PS + b"\x01" + m
        seed = get_random_bytes(hlen)
        dbMask = self._mgf1(seed, k - hlen - 1)
        maskedDB = bytes(a ^ b for a, b in zip(DB, dbMask))
        seedMask = self._mgf1(maskedDB, hlen)
        maskedSeed = bytes(a ^ b for a, b in zip(seed, seedMask))
        EM = b"\x00" + maskedSeed + maskedDB

        # Контрольное шифрование тем же seed
        cipher = PKCS1_OAEP.new(pub, hashAlgo=SHA1, randfunc=lambda n: seed)
        c_bytes = cipher.encrypt(m)
        c_hex = c_bytes.hex()

        # полноэкранное окно
        wnd = FullscreenTimelineWindow(self.app, title="RSA — шифрование (OAEP/SHA-1)")

        # Рисовалки для шагов
        def draw_bytes_block(label, data):
            def _draw(cv, x, y):
                items = []
                # полная гекс-плашка
                items += draw_tag(cv, x, y, f"{label} (hex)", data.hex())
                items += draw_hex_block(cv, x, y + 70, data, title=label)
                return items
            return _draw

        def draw_two_tags(pairs):
            def _draw(cv, x, y):
                items = []
                yoff = 0
                for name, value in pairs:
                    items += draw_tag(cv, x, y + yoff, name, value if isinstance(value, str) else value.hex())
                    yoff += 70
                return items
            return _draw

        # Полные тексты шагов
        steps = [
            {
                "title": "Исходный текст",
                "text": f"m (UTF-8, hex): {m.hex()}",
                "draw": draw_bytes_block("m", m),
            },
            {
                "title": "Параметры OAEP",
                "text": f"k = {k} байт, hLen = {hlen} (SHA-1), max mLen = {maxlen}",
                "draw": draw_two_tags([
                    ("k (bytes)", str(k)),
                    ("hLen", str(hlen)),
                    ("max mLen", str(maxlen)),
                ])
            },
            {
                "title": "Формируем DB = lHash || PS || 0x01 || m",
                "text": (
                    f"lHash: {lHash.hex()}\n"
                    f"PS  (|PS|={ps_len}): {'00'*ps_len}\n"
                    f"DB: {DB.hex()}"
                ),
                "draw": draw_two_tags([
                    ("lHash", lHash),
                    ("PS", "00" * ps_len),
                ])
            },
            {
                "title": "Генерируем seed",
                "text": f"seed: {seed.hex()}",
                "draw": draw_bytes_block("seed", seed),
            },
            {
                "title": "Вычисляем маски (MGF1)",
                "text": (
                    f"dbMask  = MGF1(seed, k-hLen-1): {dbMask.hex()}\n"
                    f"seedMask= MGF1(maskedDB, hLen) (после маскирования DB): будет на следующем шаге"
                ),
                "draw": draw_two_tags([
                    ("dbMask", dbMask),
                ])
            },
            {
                "title": "Маскирование DB и seed",
                "text": (
                    f"maskedDB  = DB ⊕ dbMask: {maskedDB.hex()}\n"
                    f"seedMask  = MGF1(maskedDB, hLen): {seedMask.hex()}\n"
                    f"maskedSeed= seed ⊕ seedMask: {maskedSeed.hex()}"
                ),
                "draw": draw_two_tags([
                    ("maskedDB", maskedDB),
                    ("seedMask", seedMask),
                    ("maskedSeed", maskedSeed),
                ])
            },
            {
                "title": "Строим EM",
                "text": f"EM = 0x00 || maskedSeed || maskedDB:\n{EM.hex()}",
                "draw": draw_bytes_block("EM", EM),
            },
            {
                "title": "RSA-операция",
                "text": f"c = EM^e mod n (быстрая модульная экспонентация)\nРазмер n = {pub.size_in_bits()} бит, e = {pub.e}",
                "draw": draw_two_tags([
                    ("modulus bits", str(pub.size_in_bits())),
                    ("public exponent e", str(pub.e)),
                ])
            },
            {
                "title": "Результат шифрования",
                "text": f"Ciphertext (hex):\n{c_hex}",
                "draw": draw_bytes_block("ciphertext", c_bytes),
            },
        ]

        wnd.set_steps(steps)
        wnd.play()
        self._write_out(
            "[RSA-OAEP/SHA-1 — ШИФРОВАНИЕ]\n"
            f"m: {m.hex()}\n"
            f"lHash: {lHash.hex()}\n"
            f"PS({ps_len}): {'00'*ps_len}\n"
            f"DB: {DB.hex()}\n"
            f"seed: {seed.hex()}\n"
            f"dbMask: {dbMask.hex()}\n"
            f"seedMask: {seedMask.hex()}\n"
            f"maskedDB: {maskedDB.hex()}\n"
            f"maskedSeed: {maskedSeed.hex()}\n"
            f"EM: {EM.hex()}\n"
            f"ciphertext: {c_hex}\n"
        )
        self.set_status("RSA: шифрование (анимация) выполнено")

    def _anim_decrypt_full(self):
        priv = self._load_priv()
        if not priv:
            messagebox.showerror("Ошибка", "Нужен закрытый ключ (PEM).")
            return

        c_hex_in = self.msg.get("0.0", "end").strip()
        if not c_hex_in:
            messagebox.showerror("Ошибка", "Введите HEX-шифртекст для расшифрования.")
            return
        try:
            c_bytes = bytes.fromhex(c_hex_in)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный HEX шифртекста.")
            return

        k = priv.size_in_bytes()
        hlen = 20

        # Низкоуровневая RSA операция
        c_int = int.from_bytes(c_bytes, "big")
        m_int = pow(c_int, priv.d, priv.n)
        EM = m_int.to_bytes(k, "big")

        # OAEP распаковка
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
            messagebox.showerror("Ошибка", "Неверный формат EM для OAEP.")
            return

        maskedSeed = EM[1:1 + hlen]
        maskedDB = EM[1 + hlen:]
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
        PS = rest[:idx]
        M = rest[idx + 1:]
        warn = "" if lHash_ == lHash else "Внимание: lHash не совпал (учебная демонстрация продолжена)."
        m_text = M.decode("utf-8", errors="replace")

        # полноэкранное окно
        wnd = FullscreenTimelineWindow(self.app, title="RSA — расшифрование (OAEP/SHA-1)")

        def draw_pair(name_val):
            def _draw(cv, x, y):
                items = []
                yoff = 0
                for name, val in name_val:
                    items += draw_tag(cv, x, y + yoff, name, val if isinstance(val, str) else val.hex())
                    yoff += 70
                return items
            return _draw

        steps = [
            {
                "title": "Входной шифртекст",
                "text": f"c (hex): {c_hex_in}",
                "draw": (lambda cv, x, y: draw_hex_block(cv, x, y, c_bytes, title="ciphertext")),
            },
            {
                "title": "RSA-операция",
                "text": f"EM = c^d mod n (k={k}):\n{EM.hex()}",
                "draw": (lambda cv, x, y: draw_hex_block(cv, x, y, EM, title="EM")),
            },
            {
                "title": "Разделяем EM",
                "text": f"maskedSeed: {maskedSeed.hex()}\nmaskedDB: {maskedDB.hex()}",
                "draw": draw_pair([
                    ("maskedSeed", maskedSeed),
                    ("maskedDB", maskedDB),
                ])
            },
            {
                "title": "Вычисляем маски и снимаем их",
                "text": (
                    f"seedMask = MGF1(maskedDB, hLen): {seedMask.hex()}\n"
                    f"seed = maskedSeed ⊕ seedMask: {seed.hex()}\n"
                    f"dbMask = MGF1(seed, k-hLen-1): {dbMask.hex()}\n"
                    f"DB = maskedDB ⊕ dbMask: {DB.hex()}"
                ),
                "draw": draw_pair([
                    ("seedMask", seedMask),
                    ("seed", seed),
                    ("dbMask", dbMask),
                    ("DB", DB),
                ])
            },
            {
                "title": "OAEP⁻¹ (lHash || PS || 0x01 || M)",
                "text": (
                    f"lHash: {lHash.hex()}\n"
                    f"lHash': {lHash_.hex()}\n"
                    f"{('OK: lHash совпал.' if not warn else warn)}\n"
                    f"PS (|PS|={len(PS)}): {'00'*len(PS)}\n"
                    f"M (hex): {M.hex()}"
                ),
                "draw": draw_pair([
                    ("lHash", lHash),
                    ("lHash'", lHash_),
                    ("PS", "00" * len(PS)),
                    ("M", M),
                ])
            },
            {
                "title": "Получение открытого текста",
                "text": f"Plaintext (UTF-8): {m_text}",
                "draw": (lambda cv, x, y: draw_tag(cv, x, y, "plaintext (utf-8)", m_text.encode('utf-8', 'replace').hex())),
            },
        ]

        wnd.set_steps(steps)
        wnd.play()
        self._write_out(
            "[RSA-OAEP — РАСШИФРОВАНИЕ]\n"
            f"EM: {EM.hex()}\n"
            f"maskedSeed: {maskedSeed.hex()}\n"
            f"maskedDB: {maskedDB.hex()}\n"
            f"seedMask: {seedMask.hex()}\n"
            f"seed: {seed.hex()}\n"
            f"dbMask: {dbMask.hex()}\n"
            f"DB: {DB.hex()}\n"
            f"PS({len(PS)}): {'00'*len(PS)}\n"
            f"M: {M.hex()}\n"
            f"Plaintext: {m_text}\n"
        )
        self.set_status("RSA: расшифрование (анимация) выполнено")

    # вывод
    def _write_out(self, text: str):
        self.out.configure(state="normal")
        self.out.delete("0.0", "end")
        self.out.insert("end", text)
        self.out.configure(state="disabled")
