import customtkinter as ctk
from tkinter import messagebox
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from utils import pkcs7_pad, pkcs7_unpad, copy_to_clipboard
from animations import FullscreenTimelineWindow, draw_hex_block, draw_tag, draw_arrow, draw_badge

class AESTab:
    def __init__(self, app, parent, set_status):
        self.app=app; self.set_status=set_status
        frame = ctk.CTkFrame(parent); frame.pack(padx=10, pady=10, fill="both", expand=True)
        ctk.CTkLabel(frame,
            text="AES — симметричный блочный шифр. Режимы ECB/CBC/CTR/GCM. Анимация запускается в полноэкранном окне.",
            font=ctk.CTkFont(size=14, weight="bold"), justify="left").pack(pady=8)

        # Настройки
        keyrow = ctk.CTkFrame(frame); keyrow.pack(pady=5, fill="x")
        ctk.CTkLabel(keyrow, text="Длина ключа:").pack(side="left")
        self.key_size = ctk.CTkComboBox(keyrow, values=["16 (128-bit)", "24 (192-bit)", "32 (256-bit)"], width=140)
        self.key_size.set("16 (128-bit)"); self.key_size.pack(side="left", padx=6)
        ctk.CTkLabel(keyrow, text="Ключ (HEX):").pack(side="left", padx=6)
        self.key_entry = ctk.CTkEntry(keyrow, width=360); self.key_entry.pack(side="left", padx=6)
        ctk.CTkButton(keyrow, text="Сгенерировать ключ", command=self._gen_key).pack(side="left", padx=6)

        moderow = ctk.CTkFrame(frame); moderow.pack(pady=5, fill="x")
        ctk.CTkLabel(moderow, text="Режим:").pack(side="left", padx=6)
        self.mode_var = ctk.StringVar(value="ECB")
        self.mode_box = ctk.CTkComboBox(moderow, values=["ECB","CBC","CTR","GCM"], variable=self.mode_var, width=120)
        self.mode_box.pack(side="left", padx=6)

        ivrow = ctk.CTkFrame(frame); ivrow.pack(pady=5, fill="x")
        self.iv_label = ctk.CTkLabel(ivrow, text="IV/Nonce (HEX):"); self.iv_label.pack(side="left", padx=6)
        self.iv_entry = ctk.CTkEntry(ivrow, width=360, placeholder_text="Если пусто — сгенерируется (при шифровании)")
        self.iv_entry.pack(side="left", padx=6)

        tagrow = ctk.CTkFrame(frame); tagrow.pack(pady=5, fill="x")
        ctk.CTkLabel(tagrow, text="Tag (HEX, для GCM-расшифрования):").pack(side="left", padx=6)
        self.tag_entry = ctk.CTkEntry(tagrow, width=360, placeholder_text="Введите Tag при анимации расшифрования GCM")
        self.tag_entry.pack(side="left", padx=6)

        # Данные
        ctk.CTkLabel(frame, text="Данные (для шифрования) или шифртекст HEX (для расшифрования):").pack(anchor="w", pady=(6,0))
        trow = ctk.CTkFrame(frame); trow.pack(fill="x")
        self.text = ctk.CTkTextbox(trow, width=1000, height=100); self.text.pack(side="left", padx=6)
        ctk.CTkButton(trow, text="Копировать", command=lambda: copy_to_clipboard(self.app, self.text.get("0.0","end"))).pack(side="left", padx=6)

        # Кнопки анимации
        bro = ctk.CTkFrame(frame); bro.pack(pady=6)
        ctk.CTkButton(bro, text="Анимация шифрования (полноэкранно)", command=self._anim_encrypt_full).pack(side="left", padx=6)
        ctk.CTkButton(bro, text="Анимация расшифрования (полноэкранно)", command=self._anim_decrypt_full).pack(side="left", padx=6)

        # Вывод
        self.out  = ctk.CTkTextbox(frame, height=140); self.out.pack(fill="both", expand=False, pady=(6,0))

    # helpers
    def _gen_key(self):
        sz = {"16 (128-bit)":16,"24 (192-bit)":24,"32 (256-bit)":32}[self.key_size.get()]
        key = get_random_bytes(sz)
        self.key_entry.delete(0,"end"); self.key_entry.insert(0, key.hex())

    def _get_key(self):
        key_hex = self.key_entry.get().strip()
        if not key_hex: return None, "Введите ключ (HEX)!"
        try: key = bytes.fromhex(key_hex)
        except ValueError: return None, "Ключ должен быть HEX!"
        need = int(self.key_size.get().split()[0])
        if len(key)!=need: return None, f"Нужно {need} байт ключа."
        return key, None

    def _get_iv(self, mode: str, for_decrypt: bool):
        iv_hex = self.iv_entry.get().strip()
        if mode=="ECB": return None, None, "—"
        need = {"CBC":16,"CTR":8,"GCM":12}[mode]
        label = "IV" if mode=="CBC" else "Nonce"
        if not iv_hex and not for_decrypt:
            iv = get_random_bytes(need); return iv, None, f"{label}={iv.hex()}"
        if not iv_hex and for_decrypt:
            return None, f"Для {mode} нужен {label} ({need} байт).", ""
        try: iv = bytes.fromhex(iv_hex)
        except ValueError: return None, "IV/Nonce должен быть HEX.", ""
        if len(iv)!=need: return None, f"Для {mode} нужен {label} {need} байт.", ""
        return iv, None, f"{label}={iv.hex()}"

    # анимации
    def _anim_encrypt_full(self):
        mode = self.mode_box.get()
        key, err = self._get_key()
        if err: messagebox.showerror("Ошибка", err); return
        iv, iverr, ivlabel = self._get_iv(mode, for_decrypt=False)
        if iverr: messagebox.showerror("Ошибка IV/Nonce", iverr); return
        data = self.text.get("0.0","end").rstrip("\n")
        if not data: messagebox.showerror("Ошибка","Введите данные."); return
        m = data.encode("utf-8")

        title = f"AES-{mode} — анимация шифрования"
        wnd = FullscreenTimelineWindow(self.app, title=title)

        # визуализации для каждого режима
        if mode=="ECB":
            p = pkcs7_pad(m)
            blocks = [p[i:i+16] for i in range(0,len(p),16)]
            cipher = AES.new(key, AES.MODE_ECB)
            out_blocks = [cipher.encrypt(b) for b in blocks]
            c_hex = b"".join(out_blocks).hex()

            def draw_independence(canvas, x, y):
                # Три первых блока → три независимых «ветки» к E_k
                items=[]
                bx = x-160
                for i in range(min(3, len(blocks))):
                    items += draw_hex_block(canvas, bx+i*60, y, blocks[i], title=f"P{i+1}")
                    items += draw_arrow(canvas, bx+18+i*60, y+102, bx+18+i*60, y+140, "")
                    items += draw_badge(canvas, bx-8+i*60, y+144, "E_k")
                return items

            steps = [
                {"title":"Исходные данные", "text": data,
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, m[:16], title="plain")},
                {"title":"PKCS#7", "text":"Выравнивание до 16 байт."},
                {"title":"Разбиение на блоки", "text": f"Блоков: {len(blocks)}",
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, blocks[0] if blocks else None, title="P1")},
                {"title":"Независимое шифрование (ECB)", "text":"Каждый блок шифруется отдельно тем же ключом.",
                 "draw": draw_independence},
                {"title":"Результат", "text": c_hex[:120]+"…" if len(c_hex)>122 else c_hex,
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "|C| байт", str(len(b''.join(out_blocks))))},
            ]
            wnd.set_steps(steps)
            wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-ECB]\nCiphertext (HEX): {c_hex}\n")
            self.set_status("AES ECB: шифрование выполнено")

        elif mode=="CBC":
            p = pkcs7_pad(m)
            blocks = [p[i:i+16] for i in range(0,len(p),16)]
            ecb = AES.new(key, AES.MODE_ECB)
            out_blocks=[]; prev=iv
            chain_preview = []
            for i,b in enumerate(blocks):
                x = bytes(a^b_ for a,b_ in zip(b, prev))
                c = ecb.encrypt(x)
                out_blocks.append(c)
                chain_preview.append((b, prev, x, c))
                prev=c
            c_hex = b"".join(out_blocks).hex()

            def draw_cbc(canvas, x, y):
                items=[]
                shown = min(3, len(chain_preview))
                bx = x-220
                for i in range(shown):
                    P, PREV, X, C = chain_preview[i]
                    # P_i
                    items += draw_hex_block(canvas, bx, y, P, title=f"P{i+1}")
                    # prev (IV или C_{i-1})
                    items += draw_hex_block(canvas, bx+120, y, PREV, title=("IV" if i==0 else f"C{i}"))
                    # XOR
                    items += draw_badge(canvas, bx+240, y+36, "⊕")
                    items += draw_arrow(canvas, bx+96, y+48, bx+240, y+48, "")
                    items += draw_arrow(canvas, bx+216, y+48, bx+240, y+48, "")
                    # результат XOR
                    items += draw_hex_block(canvas, bx+280, y, X, title="XOR")
                    # E_k
                    items += draw_arrow(canvas, bx+360, y+48, bx+402, y+48, "")
                    items += draw_badge(canvas, bx+404, y+36, "E_k")
                    # C_i
                    items += draw_hex_block(canvas, bx+460, y, C, title=f"C{i+1}")
                    y += 100
                return items

            steps = [
                {"title":"Исходные данные", "text": data,
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, m[:16], title="plain")},
                {"title":"PKCS#7", "text":"Выравнивание до 16 байт."},
                {"title":"Начальный вектор (IV)", "text": ivlabel,
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "IV", iv.hex())},
                {"title":"Цепочка CBC", "text":"P_i ⊕ (IV/C_{i-1}) → E_k → C_i",
                 "draw": draw_cbc},
                {"title":"Результат", "text": f"IV={iv.hex()}\nC={c_hex[:120]}…" if len(c_hex)>122 else f"IV={iv.hex()}\nC={c_hex}",
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "|C| байт", str(len(b''.join(out_blocks))))},
            ]
            wnd.set_steps(steps)
            wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-CBC]\nIV (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\n")
            self.set_status("AES CBC: шифрование выполнено")

        elif mode=="CTR":
            blocks = [m[i:i+16] for i in range(0,len(m),16)]
            ecb = AES.new(key, AES.MODE_ECB)
            out=[]; ks_list=[]
            for i,b in enumerate(blocks):
                ctr = i.to_bytes(8, "big")
                ke = ecb.encrypt(iv + ctr)
                ks = ke[:len(b)]
                ks_list.append((ctr, ks))
                out.append(bytes(a^b_ for a,b_ in zip(b, ks)))
            c_hex = b"".join(out).hex()

            def draw_ctr(canvas, x, y):
                items=[]
                bx = x-280
                for i in range(min(3, len(blocks))):
                    ctr_i, ks_i = ks_list[i]
                    items += draw_tag(canvas, bx, y, "Nonce", iv.hex())
                    items += draw_badge(canvas, bx+190, y+8, f"ctr={i}")
                    items += draw_arrow(canvas, bx+170, y+28, bx+240, y+28, "")
                    items += draw_badge(canvas, bx+250, y+8, "E_k")   # шифрование счетчика
                    items += draw_arrow(canvas, bx+310, y+28, bx+356, y+28, "ke")
                    items += draw_tag(canvas, bx+360, y, "KS", ks_i.hex()[:32] + ("…" if len(ks_i)>16 else ""))
                    items += draw_hex_block(canvas, bx+520, y-8, blocks[i], title=f"P{i+1}")
                    items += draw_badge(canvas, bx+640, y+8, "⊕")
                    items += draw_arrow(canvas, bx+612, y+28, bx+640, y+28, "")
                    items += draw_arrow(canvas, bx+600, y+28, bx+520, y+28, "")
                    y += 96
                return items

            steps = [
                {"title":"Исходные данные", "text": data,
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, m[:16], title="plain")},
                {"title":"Nonce/Счётчик", "text": f"Nonce={iv.hex()}"},
                {"title":"Keystream (CTR)", "text":"E_k(Nonce||ctr) → KS; C = P ⊕ KS",
                 "draw": draw_ctr},
                {"title":"Результат", "text": f"Nonce={iv.hex()}\nC={c_hex[:120]}…" if len(c_hex)>122 else f"Nonce={iv.hex()}\nC={c_hex}"},
            ]
            wnd.set_steps(steps)
            wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-CTR]\nNonce (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\n")
            self.set_status("AES CTR: шифрование выполнено")

        else:  # GCM
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            c_bytes, tag = cipher.encrypt_and_digest(m)
            c_hex = c_bytes.hex()

            def draw_gcm(canvas, x, y):
                items=[]
                bx = x-280
                # CTR часть
                items += draw_tag(canvas, bx, y, "Nonce", iv.hex())
                items += draw_badge(canvas, bx+190, y+8, "ctr")
                items += draw_arrow(canvas, bx+170, y+28, bx+240, y+28, "")
                items += draw_badge(canvas, bx+250, y+8, "E_k")
                items += draw_arrow(canvas, bx+310, y+28, bx+356, y+28, "ke")
                items += draw_tag(canvas, bx+360, y, "KS", "…")
                items += draw_hex_block(canvas, bx+520, y-8, m[:16], title="P")
                items += draw_badge(canvas, bx+640, y+8, "⊕")
                # GHASH/Tag
                items += draw_arrow(canvas, bx+700, y+28, bx+760, y+28, "")
                items += draw_badge(canvas, bx+762, y+8, "GHASH")
                items += draw_arrow(canvas, bx+820, y+28, bx+880, y+28, "")
                items += draw_tag(canvas, bx+882, y, "TAG", "Galois auth")
                return items

            steps = [
                {"title":"Исходные данные", "text": data,
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, m[:16], title="plain")},
                {"title":"Nonce", "text": f"Nonce={iv.hex()}",
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "Nonce", iv.hex())},
                {"title":"CTR + GHASH", "text":"Шифрование в CTR + аутентификация в поле Галуа.",
                 "draw": draw_gcm},
                {"title":"Тег аутентичности", "text": tag.hex(),
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "Tag", tag.hex())},
                {"title":"Результат", "text": f"C={c_hex[:120]}…" if len(c_hex)>122 else f"C={c_hex}"},
            ]
            wnd.set_steps(steps)
            wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end",
                f"[AES-GCM]\nNonce (HEX): {iv.hex()}\nCiphertext (HEX): {c_hex}\nTag (HEX): {tag.hex()}\n")
            self.set_status("AES GCM: шифрование выполнено")

    def _anim_decrypt_full(self):
        mode = self.mode_box.get()
        key, err = self._get_key()
        if err: messagebox.showerror("Ошибка", err); return
        c_hex = self.text.get("0.0","end").strip()
        if not c_hex: messagebox.showerror("Ошибка","Введите шифртекст HEX."); return
        try: c_bytes = bytes.fromhex(c_hex)
        except ValueError: messagebox.showerror("Ошибка","Неверный HEX."); return
        iv, iverr, ivlabel = self._get_iv(mode, for_decrypt=True)
        if iverr: messagebox.showerror("Ошибка IV/Nonce", iverr); return

        title = f"AES-{mode} — анимация расшифрования"
        wnd = FullscreenTimelineWindow(self.app, title=title)

        if mode=="ECB":
            cipher = AES.new(key, AES.MODE_ECB); p = cipher.decrypt(c_bytes)
            try: p=pkcs7_unpad(p); plain=p.decode("utf-8", errors="replace")
            except Exception as e: plain=f"(ошибка паддинга/декодирования: {e})"

            steps = [
                {"title":"Входной шифртекст", "text": c_hex[:160]+"…" if len(c_hex)>162 else c_hex,
                 "draw": lambda cv,xx,yy: draw_tag(cv, xx-160, yy, "|C| байт", str(len(c_bytes)))},
                {"title":"D_k блоков", "text":"Расшифрование каждого блока отдельно."},
                {"title":"Удаление PKCS#7", "text":"Снимаем выравнивание."},
                {"title":"Получение текста", "text": plain,
                 "draw": lambda cv,xx,yy: draw_hex_block(cv, xx-80, yy, p[:16] if isinstance(p, (bytes, bytearray)) else None, title="plain")},
            ]
            wnd.set_steps(steps); wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-ECB]\nPlaintext: {plain}\n")
            self.set_status("AES ECB: расшифрование выполнено")

        elif mode=="CBC":
            ecb = AES.new(key, AES.MODE_ECB)
            blocks = [c_bytes[i:i+16] for i in range(0,len(c_bytes),16)]
            p_all=b""; prev=iv; demo=[]
            for i,b in enumerate(blocks):
                x = ecb.decrypt(b)
                pblk = bytes(a^b_ for a,b_ in zip(x,prev))
                demo.append((b, x, prev, pblk))
                p_all += pblk; prev=b
            try: p = pkcs7_unpad(p_all); plain = p.decode("utf-8", errors="replace")
            except Exception as e: plain=f"(ошибка паддинга/декодирования: {e})"

            def draw_cbc_dec(canvas, x, y):
                items=[]; bx=x-240
                for i in range(min(3, len(demo))):
                    C, X, PREV, P = demo[i]
                    items += draw_hex_block(canvas, bx, y, C, title=f"C{i+1}")
                    items += draw_badge(canvas, bx+120, y+36, "D_k")
                    items += draw_arrow(canvas, bx+100, y+48, bx+140, y+48, "")
                    items += draw_hex_block(canvas, bx+170, y, X, title="Dk(C)")
                    items += draw_badge(canvas, bx+290, y+36, "⊕")
                    items += draw_hex_block(canvas, bx+330, y, PREV, title=("IV" if i==0 else f"C{i}"))
                    items += draw_arrow(canvas, bx+270, y+48, bx+290, y+48, "")
                    items += draw_arrow(canvas, bx+310, y+48, bx+290, y+48, "")
                    items += draw_hex_block(canvas, bx+380, y, P, title=f"P{i+1}")
                    y += 100
                return items

            steps = [
                {"title":"Входной шифртекст", "text": c_hex[:160]+"…" if len(c_hex)>162 else c_hex},
                {"title":"D_k + XOR", "text":"D_k(C_i) ⊕ (IV/C_{i-1}) → P_i",
                 "draw": draw_cbc_dec},
                {"title":"Удаление PKCS#7", "text":"Снимаем выравнивание."},
                {"title":"Получение текста", "text": plain},
            ]
            wnd.set_steps(steps); wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-CBC]\nPlaintext: {plain}\n")
            self.set_status("AES CBC: расшифрование выполнено")

        elif mode=="CTR":
            ecb = AES.new(key, AES.MODE_ECB)
            blocks = [c_bytes[i:i+16] for i in range(0,len(c_bytes),16)]
            p_all=b""; view=[]
            for i,b in enumerate(blocks):
                ctr = i.to_bytes(8,"big"); ke = ecb.encrypt(iv+ctr); ks=ke[:len(b)]
                pblk = bytes(a^b_ for a,b_ in zip(b,ks))
                view.append((ctr, ks, b, pblk))
                p_all += pblk
            plain = p_all.decode("utf-8", errors="replace")

            def draw_ctr_dec(canvas, x, y):
                items=[]; bx=x-300
                for i in range(min(3, len(view))):
                    ctr_i, ks_i, C, P = view[i]
                    items += draw_tag(canvas, bx, y, "Nonce", iv.hex())
                    items += draw_badge(canvas, bx+190, y+8, f"ctr={i}")
                    items += draw_badge(canvas, bx+250, y+8, "E_k")
                    items += draw_tag(canvas, bx+360, y, "KS", ks_i.hex()[:32] + ("…" if len(ks_i)>16 else ""))
                    items += draw_hex_block(canvas, bx+520, y-8, C, title=f"C{i+1}")
                    items += draw_badge(canvas, bx+640, y+8, "⊕")
                    items += draw_hex_block(canvas, bx+680, y-8, P, title=f"P{i+1}")
                    y += 96
                return items

            steps = [
                {"title":"Nonce/ctr/KS", "text": f"Nonce={iv.hex()}"},
                {"title":"P = C ⊕ KS", "text":"Тот же KS, что на шифровании.", "draw": draw_ctr_dec},
                {"title":"Получение текста", "text": plain},
            ]
            wnd.set_steps(steps); wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-CTR]\nPlaintext: {plain}\n")
            self.set_status("AES CTR: расшифрование выполнено")

        else:  # GCM
            tag_hex = self.tag_entry.get().strip()
            if not tag_hex: messagebox.showerror("Ошибка","Укажите Tag (HEX)."); return
            try: tag = bytes.fromhex(tag_hex)
            except ValueError: messagebox.showerror("Ошибка","Некорректный Tag."); return
            try:
                cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
                p_bytes = cipher.decrypt_and_verify(c_bytes, tag)
                plain = p_bytes.decode("utf-8", errors="replace")
                ok = True
            except Exception as e:
                plain = f"(не удалось проверить тег: {e})"
                ok = False

            def draw_gcm_dec(canvas, x, y):
                items=[]
                bx=x-260
                items += draw_tag(canvas, bx, y, "Nonce", iv.hex())
                items += draw_tag(canvas, bx+200, y, "Tag", tag.hex()[:32]+"…")
                items += draw_badge(canvas, bx+400, y+8, "verify" if ok else "error")
                items += draw_arrow(canvas, bx+450, y+28, bx+520, y+28, "")
                items += draw_hex_block(canvas, bx+520, y-8, p_bytes[:16] if ok else None, title="P")
                return items

            steps = [
                {"title":"Nonce и TAG", "text": f"{ivlabel}\nTag={tag.hex()} (проверка)"},
                {"title":"Расшифрование + проверка", "text": "CTR поток + GHASH верификация.", "draw": draw_gcm_dec},
                {"title":"Результат", "text": plain},
            ]
            wnd.set_steps(steps); wnd.play()
            self.out.delete("0.0","end"); self.out.insert("end", f"[AES-GCM]\nPlaintext: {plain}\n")
            self.set_status("AES GCM: расшифрование выполнено")
