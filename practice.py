import random, tkinter
import customtkinter as ctk

class PracticeTab:
    def __init__(self, app, parent, set_status, caesar_fn):
        self.app=app; self.set_status=set_status; self.caesar_cipher=caesar_fn
        frame = ctk.CTkFrame(parent); frame.pack(padx=10, pady=10, fill="both", expand=True)
        ctk.CTkLabel(frame, text="Полигон", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0,6))

        # Полигон
        cz = ctk.CTkFrame(frame); cz.pack(fill="x", pady=8)
        ctk.CTkLabel(cz, text="Криптоанализ перехваченного сообщения", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.task_lbl = ctk.CTkLabel(cz, text="Нажмите «Новая задача»"); self.task_lbl.pack(anchor="w", padx=6)
        row = ctk.CTkFrame(cz); row.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(row, text="Новая задача", command=self._new).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Показать все сдвиги", command=self._bruteforce).pack(side="left", padx=4)
        inrow = ctk.CTkFrame(cz); inrow.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(inrow, text="Ваш сдвиг:").pack(side="left")
        self.shift = tkinter.IntVar(value=0)
        ctk.CTkEntry(inrow, width=60, textvariable=self.shift).pack(side="left", padx=4)
        ctk.CTkLabel(inrow, text="Ваша расшифровка:").pack(side="left", padx=8)
        self.answer = ctk.CTkEntry(inrow, width=500, placeholder_text="Введите предполагаемый текст")
        self.answer.pack(side="left", padx=4)
        ctk.CTkButton(inrow, text="Проверить", command=self._check).pack(side="left", padx=6)
        self.feedback = ctk.CTkLabel(cz, text=""); self.feedback.pack(anchor="w", padx=6, pady=(0,6))

        # Мини-викторины AES и RSA
        aes_box = ctk.CTkFrame(frame); aes_box.pack(fill="x", pady=8)
        ctk.CTkLabel(aes_box, text="Задание: распознай режим AES по подсказке",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.hint = ctk.CTkLabel(aes_box, text="Подсказка: повторяющиеся блоки видны в шифртексте. Какой режим?")
        self.hint.pack(anchor="w", padx=6)
        self.mode_var = tkinter.StringVar(value="")
        for m in ["ECB","CBC","CTR","GCM"]:
            ctk.CTkRadioButton(aes_box, text=m, variable=self.mode_var, value=m).pack(side="left", padx=6)
        ctk.CTkButton(aes_box, text="Проверить", command=self._check_aes).pack(anchor="w", padx=6, pady=6)
        self.aes_out = ctk.CTkLabel(aes_box, text=""); self.aes_out.pack(anchor="w", padx=6, pady=(0,6))

        rsa_box = ctk.CTkFrame(frame); rsa_box.pack(fill="x", pady=8)
        ctk.CTkLabel(rsa_box, text="Мини-викторина по RSA (True/False)",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=6, pady=(6,2))
        self.q_vars=[]
        questions=[
            ("Открытый ключ шифрует, закрытый — расшифровывает.", True),
            ("OAEP — схема паддинга, повышающая стойкость.", True),
            ("Повтор Nonce в GCM безопасен из-за тега.", False),
        ]
        for i,(q,ans) in enumerate(questions,1):
            row = ctk.CTkFrame(rsa_box); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{i}. {q}").pack(side="left")
            var = tkinter.StringVar(value="Нет ответа"); self.q_vars.append((var, ans))
            ctk.CTkRadioButton(row, text="True", variable=var, value="True").pack(side="left", padx=4)
            ctk.CTkRadioButton(row, text="False", variable=var, value="False").pack(side="left", padx=4)
        ctk.CTkButton(rsa_box, text="Проверить ответы", command=self._check_quiz).pack(anchor="w", padx=6, pady=6)
        self.quiz_out = ctk.CTkLabel(rsa_box, text=""); self.quiz_out.pack(anchor="w")

        self._secret=""; self._shift_secret=0

    # Цезарь
    def _new(self):
        samples = [
            "CRYPTOGRAPHY IS FUN", "SECURITY THROUGH OBSCURITY", "HELLO WORLD",
            "КРИПТОГРАФИЯ ЭТО ИНТЕРЕСНО", "ЛЮБЛЮ ПРОГРАММИРОВАТЬ", "ПРИВЕТ МИР"
        ]
        plain = random.choice(samples); shift = random.randint(1, 25)
        self._secret=plain; self._shift_secret=shift
        cipher = self.caesar_cipher(plain, shift)
        self.task_lbl.configure(text=f"Шифртекст: {cipher}")
        self.feedback.configure(text="Задача создана. Укажите сдвиг и/или расшифровку.")

    def _bruteforce(self):
        ct = self.task_lbl.cget("text").replace("Шифртекст: ","").strip()
        if not ct:
            from tkinter import messagebox; messagebox.showinfo("Брутфорс","Сначала создайте задачу."); return
        lines=[f"{s:2d}: {self.caesar_cipher(ct,-s)}" for s in range(0,33)]
        self.feedback.configure(text="Возможные варианты:\n" + "\n".join(lines[:33]))

    def _check(self):
        if not self._secret:
            from tkinter import messagebox; messagebox.showinfo("Проверка","Сначала создайте задачу."); return
        user_shift = self.shift.get(); user_answer = self.answer.get().strip()
        ok_shift = (user_shift % 33) == (self._shift_secret % 33)
        ok_text  = (user_answer.upper()==self._secret.upper()) if user_answer else False
        if ok_shift and ok_text:
            self.feedback.configure(text="✅ Верификация успешна. Параметры совпадают.")
        elif ok_shift:
            self.feedback.configure(text="🟡 Сдвиг верный, но текст не совпал.")
        elif ok_text:
            self.feedback.configure(text="🟡 Текст верный, но сдвиг неверный.")
        else:
            self.feedback.configure(text="❌ Ошибка валидации данных!")

    # Викторины
    def _check_aes(self):
        val = self.mode_var.get()
        if not val: self.aes_out.configure(text="Выберите вариант."); return
        self.aes_out.configure(text="✅ Верно!" if val=="ECB" else "❌ Неверно. Правильный ответ: ECB")

    def _check_quiz(self):
        correct=0; total=len(self.q_vars); details=[]
        for i,(var,ans) in enumerate(self.q_vars,1):
            val=var.get()
            if val=="Нет ответа": details.append(f"{i}) пропущено")
            else:
                ok = (val=="True")==ans; details.append(f"{i}) {'✅' if ok else '❌'}")
                if ok: correct+=1
        self.quiz_out.configure(text=f"Результат: {correct}/{total}\n" + " ".join(details))
