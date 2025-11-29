import math
import tkinter
import customtkinter as ctk

# Вспомогательные функции
def _bbox_union(canvas, items):
    #Общий bbox группы canvas-элементов: (x0,y0,x1,y1) или None
    if not items:
        return None
    try:
        return canvas.bbox(*items)
    except Exception:
        boxes = [canvas.bbox(i) for i in items if canvas.type(i) is not None]
        boxes = [b for b in boxes if b]
        if not boxes:
            return None
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        return (x0, y0, x1, y1)

# Примитивы на Canvas
def draw_hex_block(canvas, x, y, data_bytes: bytes | None,
                   rows=None, cols=None, cell=20, title="block"):
    #Гекс-«табличка» размера под данные
    items = []

    if data_bytes is None:
        total = 16
        cols_eff = cols or 4
        rows_eff = rows or 4
    else:
        total = len(data_bytes)
        cols_eff = cols or (16 if total > 16 else 4)
        rows_eff = rows or math.ceil(total / cols_eff)

    # рамка
    rect = canvas.create_rectangle(x, y, x + 10, y + 10, fill="#0e1016", outline="#2b3243")
    items.append(rect)
    title_id = canvas.create_text(x + 6, y + 6, anchor="nw", fill="#9fb3c8",
                                  font=("Consolas", 10, "bold"), text=title)
    items.append(title_id)
    # ячейки
    # внутренние отступы
    ox = x + 6
    oy = y + 16
    for r in range(rows_eff):
        for c in range(cols_eff):
            i = r * cols_eff + c
            rx0 = ox + c * cell
            ry0 = oy + r * cell
            items.append(canvas.create_rectangle(rx0, ry0, rx0 + cell - 4, ry0 + cell - 4,
                                                 fill="#151923", outline="#2b3243"))
            if data_bytes is not None and i < total:
                txt = f"{data_bytes[i]:02x}"
            else:
                txt = "  "
            items.append(canvas.create_text(rx0 + 3, ry0 + 2, anchor="nw", fill="#e6edf3",
                                            font=("Consolas", 9), text=txt))

    # финальный размер по bbox
    bx = _bbox_union(canvas, items)
    if bx:
        pad = 8
        canvas.coords(rect, bx[0] - 2, bx[1] - 2, bx[2] + pad, bx[3] + pad)

    return items

def draw_tag(canvas, x, y, label, value_hex_full: str):
    #Плашка с заголовком
    items = []
    rect = canvas.create_rectangle(x, y, x + 10, y + 10, fill="#10141d", outline="#2b3243")
    items.append(rect)
    lbl_id = canvas.create_text(x + 8, y + 6, anchor="nw", fill="#8fbaff",
                                font=("Consolas", 10, "bold"), text=label)
    items.append(lbl_id)
    val_id = canvas.create_text(x + 8, y + 26, anchor="nw", fill="#b9c2cf",
                                font=("Consolas", 9), text=value_hex_full)
    items.append(val_id)

    # подобрать ширину/высоту рамки по bbox текста
    bx = _bbox_union(canvas, [lbl_id, val_id])
    if bx:
        min_w = 220
        min_h = 52
        pad_w = 12
        pad_h = 10
        w = max(min_w, (bx[2] - x) + pad_w)
        h = max(min_h, (bx[3] - y) + pad_h)
        canvas.coords(rect, x, y, x + w, y + h)

    return items

def draw_badge(canvas, x, y, text):
    items = []
    rect = canvas.create_rectangle(x, y, x + 10, y + 10, fill="#1b2130", outline="#2b3243")
    items.append(rect)
    txt_id = canvas.create_text(x + 6, y + 6, anchor="nw", fill="#e6edf3",
                                font=("Consolas", 10, "bold"), text=text)
    items.append(txt_id)

    bx = _bbox_union(canvas, [txt_id])
    if bx:
        pad_w = 12
        pad_h = 10
        w = (bx[2] - x) + pad_w
        h = (bx[3] - y) + pad_h
        canvas.coords(rect, x, y, x + w, y + h)
    return items

def draw_arrow(canvas, x0, y0, x1, y1, text_mid=""):
    items = []
    items.append(canvas.create_line(x0, y0, x1, y1, fill="#7ea2ff", width=2, arrow=tkinter.LAST))
    if text_mid:
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        items.append(canvas.create_text(mx, my - 12, fill="#9fb3c8", font=("Consolas", 9), text=text_mid))
    return items


# Полноэкранное окно-аниматор (динамическая вёрстка карточек)
class FullscreenTimelineWindow(ctk.CTkToplevel):
    def __init__(self, app, title="Анимация", min_card_width=1600):
        super().__init__(app)
        self.title(title)
        self.min_card_width = int(min_card_width)
        self._is_fullscreen = False

        # поверх
        try: self.transient(app)
        except Exception: pass
        try: self.attributes("-topmost", True)
        except Exception: pass
        self.lift()
        try: self.focus_force()
        except Exception: pass
        self.bind("<FocusOut>", lambda e: (self.lift(), self.after(0, lambda: self.attributes("-topmost", True))))

        # окно максимум
        try: self.state("zoomed")
        except Exception: pass

        # клавиши
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F11>", self._toggle_fullscreen)

        # верхняя панель
        top = ctk.CTkFrame(self); top.pack(fill="x")
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=8)

        self.fs_btn    = ctk.CTkButton(top, text="⛶ Во весь экран (F11)", width=170, command=self._toggle_fullscreen)
        self.play_btn  = ctk.CTkButton(top, text="▶ Пуск", width=90, command=self.play)
        self.pause_btn = ctk.CTkButton(top, text="⏸ Пауза", width=90, command=self.pause, state="disabled")
        self.reset_btn = ctk.CTkButton(top, text="⟲ Сброс", width=90, command=self.reset)
        self.close_btn = ctk.CTkButton(top, text="✕ Закрыть (Esc)", width=140, command=self.destroy)
        self.progress  = ctk.CTkProgressBar(top, width=420)

        self.close_btn.pack(side="right", padx=8)
        self.progress.pack(side="right", padx=8); self.progress.set(0)
        self.reset_btn.pack(side="right", padx=4)
        self.pause_btn.pack(side="right", padx=4)
        self.play_btn.pack(side="right", padx=8)
        self.fs_btn.pack(side="right", padx=8)

        # центр: canvas + 2 скроллбара
        self.center = ctk.CTkFrame(self)
        self.center.pack(fill="both", expand=True, padx=0, pady=0)

        self.canvas = tkinter.Canvas(self.center, bg="#0f1115", highlightthickness=0)
        self.vsb = tkinter.Scrollbar(self.center, orient="vertical", command=self.canvas.yview)
        self.hsb = tkinter.Scrollbar(self.center, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.center.grid_rowconfigure(0, weight=1)
        self.center.grid_columnconfigure(0, weight=1)

        # прокрутка
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)           # Win/mac
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_wheel)
        self.bind("<Left>",  lambda e: self.canvas.xview_scroll(-6, "units"))
        self.bind("<Right>", lambda e: self.canvas.xview_scroll( 6, "units"))
        self.bind("<Prior>", lambda e: self.canvas.yview_scroll(-6, "pages"))
        self.bind("<Next>",  lambda e: self.canvas.yview_scroll( 6, "pages"))

        # нижний лог
        self.log = ctk.CTkTextbox(self, height=160, wrap="word")
        self.log.pack(fill="x", padx=0, pady=(6, 6))
        self.log.configure(state="disabled")

        # состояние
        self.steps = []
        self._idx = 0; self._running = False; self._job = None
        self._y_cursor = 24
        self._min_card_height = 120
        self._cards = []

        self.update_idletasks()
        self._update_scrollregion()

    # полноэкранный тумблер
    def _toggle_fullscreen(self, *_):
        self._is_fullscreen = not self._is_fullscreen
        try:
            self.attributes("-fullscreen", self._is_fullscreen)
        except Exception:
            try: self.state("zoomed")
            except Exception: pass
        self.fs_btn.configure(text="❐ Окно (F11)" if self._is_fullscreen else "⛶ Во весь экран (F11)")
        self.lift()

    # прокрутка
    def _on_mousewheel(self, event):
        step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step * 3, "units")

    def _on_shift_wheel(self, event):
        step = -1 if event.delta > 0 else 1
        self.canvas.xview_scroll(step * 6, "units")

    # публичный API
    def set_steps(self, steps):
        self.reset()
        self.steps = steps

    def play(self):
        if not self.steps: return
        self._running = True
        self.play_btn.configure(state="disabled"); self.pause_btn.configure(state="normal")
        self._tick()

    def pause(self):
        self._running = False
        self.play_btn.configure(state="normal"); self.pause_btn.configure(state="disabled")
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None

    def reset(self):
        self.pause()
        self.canvas.delete("all"); self._cards.clear()
        self._idx = 0; self._y_cursor = 24; self.progress.set(0)
        self._set_log("", append=False)
        self._update_scrollregion()

    # внутренняя логика
    def _set_log(self, text, append=True):
        self.log.configure(state="normal")
        if not append: self.log.delete("1.0", "end")
        if text: self.log.insert("end", text)
        self.log.configure(state="disabled")

    def _card_rect(self, x, y, w, h):
        return self.canvas.create_rectangle(x, y, x + w, y + h, fill="#151923", outline="#2b3243", width=1)

    def _tick(self):
        if not self._running: return
        if self._idx >= len(self.steps):
            self.pause(); self.progress.set(1.0); return

        step = self.steps[self._idx]

        pad_x = 16
        gap = 24
        view_w = self.canvas.winfo_width() or self.winfo_width() or 1600
        # начальная ширина карточки
        card_w = max(self.min_card_width, int(view_w * 0.9))
        x0_target = 28
        x0 = -card_w - 60
        y0 = self._y_cursor

        # минимальная ширина области для текста
        body_w = max(520, min(900, int(card_w * 0.55)))

        # базовые элементы
        rect = self._card_rect(x0, y0, card_w, self._min_card_height)
        title = self.canvas.create_text(x0 + pad_x, y0 + 16, anchor="w", fill="#e6edf3",
                                        font=("Consolas", 14, "bold"),
                                        text=f"Шаг {self._idx + 1}: {step['title']}")
        body = self.canvas.create_text(x0 + pad_x, y0 + 44, anchor="nw", fill="#b9c2cf",
                                       font=("Consolas", 11), width=body_w,
                                       text=step.get("text", ""))

        # визуальная часть
        vis_group = []
        vis_bbox = None
        if step.get("draw"):
            vis_group = step["draw"](self.canvas, x0 + pad_x + body_w + gap, y0 + 12)
            vis_bbox = _bbox_union(self.canvas, vis_group)

        body_bbox = self.canvas.bbox(body) or (0, 0, 0, 0)
        title_bbox = self.canvas.bbox(title) or (0, 0, 0, 0)

        body_h = body_bbox[3] - body_bbox[1]
        title_h = title_bbox[3] - title_bbox[1]
        vis_w = (vis_bbox[2] - vis_bbox[0]) if vis_bbox else 0
        vis_h = (vis_bbox[3] - vis_bbox[1]) if vis_bbox else 0
        needed_w = pad_x + body_w + (gap + vis_w if vis_w > 0 else 0) + pad_x
        if needed_w > card_w:
            card_w = needed_w

        if vis_group:
            final_x = x0 + pad_x + body_w + gap
            dx = final_x - (vis_bbox[0] if vis_bbox else final_x)
            for it in vis_group:
                self.canvas.move(it, dx, 0)
            vis_bbox = _bbox_union(self.canvas, vis_group)  # обновить bbox
            vis_w = (vis_bbox[2] - vis_bbox[0]) if vis_bbox else 0
            vis_h = (vis_bbox[3] - vis_bbox[1]) if vis_bbox else 0

        all_items = [title, body] + (vis_group or [])
        all_bbox = _bbox_union(self.canvas, all_items)
        if all_bbox:
            content_h = (all_bbox[3] - y0)
        else:
            content_h = max(self._min_card_height, title_h + body_h + 40)

        card_h = max(self._min_card_height, content_h + 12)
        self.canvas.coords(rect, x0, y0, x0 + card_w, y0 + card_h)
        self._cards.append((rect, title, body, *(vis_group or [])))

        # анимация въезда
        frames = 14
        def animate_slide(i=0):
            if i >= frames:
                self._y_cursor += card_h + 14
                add = f"[{step['title']}]\n{step.get('text','')}\n\n"
                self._set_log(add, append=True)
                self._idx += 1
                self.progress.set(self._idx / max(1, len(self.steps)))
                self._update_scrollregion()
                self._job = self.after(520, self._tick)
                return
            dx = (x0_target - x0) / frames
            for item in (rect, title, body, *(vis_group or [])):
                self.canvas.move(item, dx, 0)
            self._job = self.after(18, lambda: animate_slide(i + 1))
        animate_slide()

    def _update_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
