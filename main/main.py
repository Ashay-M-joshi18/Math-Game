import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import time
import math
from PIL.ImageChops import screen
from dotenv import load_dotenv
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
load_dotenv()
import sys
import random
import csv
import cv2
from db import init_db
from ui_analytics import DetailedAnalyticsWindow
try:
    from qt_splash import run_qt_splash
except Exception:
    run_qt_splash = None
try:
    from qt_portal import run_qt_portal
except Exception:
    run_qt_portal = None
from models import (
    create_student_user,
    login_user,
    ensure_default_admin,
    get_admin_user,
    get_student,
    update_admin_credentials,
    get_all_students,
    get_student_progress,
    update_student_details,
    delete_student_account,
    save_attempt as save_student_attempt,
    save_t20_attempt,
    upload_file,
    get_all_files,
    get_file_by_id,
    soft_delete_file,
    hard_delete_file,
    get_detailed_analytics
)
import re

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

APP_TITLE_COLOR = "#F6FAFF"
APP_BG_COLOR = "#07111F"
APP_ACCENT_COLOR = "#FF8A2B"
APP_SURFACE_COLOR = "#0E1B2D"
APP_TEXT_COLOR = "#F4F8FF"
SPLASH_BG_COLOR = "#07111F"

FONT_FAMILY_DISPLAY = "Impact"
FONT_FAMILY_UI = "Segoe UI"
FONT_FAMILY_TEXT = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

BACK_BUTTON_FONT = (FONT_FAMILY_UI, 12, "bold")
BACK_BUTTON_BG = "#13253C"
BACK_BUTTON_FG = "#F4F7FF"
BACK_BUTTON_ACTIVE_BG = "#1C3655"
BACK_BUTTON_ACTIVE_FG = "#FFFFFF"

GLOSSY_BUTTON_THEMES = {
    "green": {
        "edge": "#A7EEFF",
        "top": "#4BBBE7",
        "bottom": "#176C9B",
        "text": "#F4FCFF",
    },
    "lime": {
        "edge": "#9AB6D7",
        "top": "#345472",
        "bottom": "#16283B",
        "text": "#F4F8FF",
    },
    "amber": {
        "edge": "#FFD08A",
        "top": "#FF9A3D",
        "bottom": "#C75A12",
        "text": "#FFF7ED",
    },
    "red": {
        "edge": "#FFB299",
        "top": "#F96B45",
        "bottom": "#B63A23",
        "text": "#FFF5F1",
    },
    "blue": {
        "edge": "#7FD2FF",
        "top": "#2E7CFF",
        "bottom": "#1445A6",
        "text": "#F4FAFF",
    },
}
NAV_BACK_GLOSSY_VARIANT = "lime"


def _hex_to_rgb(hex_color):
    color = hex_color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _scale_color(color, factor):
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def _rgb_to_hex(rgb_color):
    return "#{:02X}{:02X}{:02X}".format(*rgb_color)


def _blend_hex(color_a, color_b, t):
    t = max(0.0, min(1.0, t))
    return _rgb_to_hex(_lerp_color(_hex_to_rgb(color_a), _hex_to_rgb(color_b), t))


def _render_glossy_button_surface(width_px, height_px, theme, pressed=False):
    width_px = max(96, int(width_px))
    height_px = max(38, int(height_px))
    supersample = 2
    w = width_px * supersample
    h = height_px * supersample
    radius = max(16, h // 2)
    inset = 4 * supersample
    inner_radius = max(12, radius - inset)

    edge = _hex_to_rgb(theme["edge"])
    top = _hex_to_rgb(theme["top"])
    bottom = _hex_to_rgb(theme["bottom"])
    if pressed:
        top = _scale_color(top, 0.88)
        bottom = _scale_color(bottom, 0.82)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer capsule ring
    draw.rounded_rectangle(
        (0, 0, w - 1, h - 1),
        radius=radius,
        fill=_lerp_color(edge, bottom, 0.18) + (255,),
        outline=_scale_color(edge, 0.70) + (255,),
        width=max(2, supersample * 2),
    )

    inner_x1, inner_y1 = inset, inset
    inner_x2, inner_y2 = w - inset - 1, h - inset - 1
    inner_w = inner_x2 - inner_x1 + 1
    inner_h = inner_y2 - inner_y1 + 1

    # Main vertical gradient fill
    gradient = Image.new("RGBA", (inner_w, inner_h), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    for y in range(inner_h):
        t = y / max(1, inner_h - 1)
        col = _lerp_color(top, bottom, t)
        grad_draw.line((0, y, inner_w - 1, y), fill=col + (255,))

    grad_mask = Image.new("L", (inner_w, inner_h), 0)
    ImageDraw.Draw(grad_mask).rounded_rectangle(
        (0, 0, inner_w - 1, inner_h - 1),
        radius=inner_radius,
        fill=255,
    )
    img.paste(gradient, (inner_x1, inner_y1), grad_mask)

    # Top gloss strip
    gloss = Image.new("RGBA", (inner_w, inner_h), (0, 0, 0, 0))
    gloss_draw = ImageDraw.Draw(gloss)
    gloss_alpha = 78 if not pressed else 38
    gloss_draw.rounded_rectangle(
        (
            2 * supersample,
            2 * supersample,
            inner_w - (3 * supersample),
            max(10 * supersample, int(inner_h * 0.46)),
        ),
        radius=max(8, inner_radius - (3 * supersample)),
        fill=(255, 255, 255, gloss_alpha),
    )
    img.paste(gloss, (inner_x1, inner_y1), gloss)

    # Small light sparkles near top-left for the reference look.
    if not pressed:
        draw.ellipse(
            (
                inner_x1 + int(inner_w * 0.05),
                inner_y1 + 3 * supersample,
                inner_x1 + int(inner_w * 0.15),
                inner_y1 + int(inner_h * 0.33),
            ),
            fill=(255, 255, 255, 130),
        )
        draw.ellipse(
            (
                inner_x1 + int(inner_w * 0.18),
                inner_y1 + 7 * supersample,
                inner_x1 + int(inner_w * 0.25),
                inner_y1 + int(inner_h * 0.29),
            ),
            fill=(255, 255, 255, 84),
        )

    # Crisp inner highlight ring.
    draw.rounded_rectangle(
        (inner_x1 + 1, inner_y1 + 1, inner_x2 - 1, inner_y2 - 1),
        radius=max(8, inner_radius - 1),
        outline=(255, 255, 255, 62),
        width=max(1, supersample),
    )

    resampling = getattr(Image, "Resampling", Image)
    return img.resize((width_px, height_px), resampling.LANCZOS)


def _pick_font_family(root, candidates):
    available = {family.lower() for family in tkfont.families(root)}
    for name in candidates:
        if name.lower() in available:
            return name
    return candidates[-1]


def configure_app_typography(root):
    """Pick preferred families when installed, else fall back safely."""
    global FONT_FAMILY_DISPLAY, FONT_FAMILY_UI, FONT_FAMILY_TEXT, FONT_FAMILY_MONO, BACK_BUTTON_FONT

    FONT_FAMILY_DISPLAY = _pick_font_family(
        root,
        ("Orbitron", "Bungee", "Eurostile", "Impact", "Segoe UI Black", "Arial Black"),
    )
    FONT_FAMILY_UI = _pick_font_family(
        root,
        ("Rajdhani", "Exo 2", "Segoe UI Semibold", "Segoe UI", "Arial"),
    )
    FONT_FAMILY_TEXT = _pick_font_family(
        root,
        ("Exo 2", "Rajdhani", "Segoe UI", "Calibri", "Arial"),
    )
    FONT_FAMILY_MONO = _pick_font_family(
        root,
        ("JetBrains Mono", "Cascadia Mono", "Consolas", "Courier New"),
    )

    BACK_BUTTON_FONT = (FONT_FAMILY_UI, 12, "bold")

    # Keep Tk default widgets in the new typography where explicit fonts are not set.
    for named_font in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(named_font).configure(family=FONT_FAMILY_TEXT)
        except tk.TclError:
            continue

    root.option_add("*Font", (FONT_FAMILY_TEXT, 10))
    root.option_add("*Label.Font", (FONT_FAMILY_TEXT, 10))
    root.option_add("*Entry.Font", (FONT_FAMILY_TEXT, 10))
    root.option_add("*Listbox.Font", (FONT_FAMILY_TEXT, 10))
    root.option_add("*Button.Font", (FONT_FAMILY_UI, 10, "bold"))


def create_back_button(parent, text, command, width=16, font=None):
    """Create a consistent Back button style across the app."""
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=font or BACK_BUTTON_FONT,
        width=width,
        bg=BACK_BUTTON_BG,
        fg=BACK_BUTTON_FG,
        activebackground=BACK_BUTTON_ACTIVE_BG,
        activeforeground=BACK_BUTTON_ACTIVE_FG,
        relief="raised",
        bd=2,
        padx=6,
        pady=4,
        cursor="hand2",
        highlightthickness=0,
    )

#to adjust the path for importing the MathFactory and backend from the backend folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.MathFactory import MathFactory
from sound_manager import sound_manager


class AsteroidMathGame:
    def __init__(self, root):
        self.root = root
        configure_app_typography(self.root)
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 30)
        self.root.title("Math Game")
        self.root.geometry("600x800")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass
        self._start_screen_resize_job = None
        self._start_screen_widgets = {}
        self.splash_animation_job = None
        self.splash_finish_job = None
        self.splash_started_at = None
        self.splash_starfield = []
        self.splash_starfield_size = None
        self.game_start_countdown_job = None
        self.game_start_countdown_canvas = None
        self.game_start_countdown_photo = None
        self.countdown_character_cache = {}
        self._glossy_button_cache = {}
        self.gameplay_canvas_tag = "gameplay_layer"
        self.ui_question_count = None
        self.screen_shake_job = None
        self.screen_shake_canvas = None
        self.screen_shake_offset_x = 0
        self.screen_shake_offset_y = 0
        # Sound + effects
        self.is_sound_muted = False
        self.mute_button = None
        self.bg_image_raw = None
        for bg_name in ("Asteroids.jpeg", "asteroids.jpeg", "darkimage.jpeg"):
            bg_path = os.path.join(PROJECT_ROOT, "assets", bg_name)
            if os.path.exists(bg_path):
                try:
                    self.bg_image_raw = Image.open(bg_path).convert("RGBA")
                    break
                except Exception:
                    continue
        
        self._bg_cache_size = None
        self._bg_cache_photo = None

        self.canvas = tk.Canvas(root, width=600, height=800, highlightthickness=0, bg=SPLASH_BG_COLOR)
        self.canvas.pack()

        # Game State
        self.asteroids = []
        self.questions_attempted = 0
        self.score = 0
        self.time_left = 180  # 3 minutes in seconds
        self.game_active = False
        self.session_game_count = 0  # tracks games played this session for running avg_speed

        # Mode flags
        self.is_t20_mode = False

        # Advanced maths (MCQ quiz) state
        self.advanced_questions = []
        self.current_advanced_index = 0
        self.advanced_score = 0
        self.timer_running = False
        self.quiz_start_time = None
        self.timer_label = None
        self.advanced_quiz_timer_job = None
        self.advanced_option_buttons = []
        self.advanced_back_button = None
        self.advanced_screen_ready = False
        self.advanced_question_item = None
        self.advanced_question_counter_item = None
        self.advanced_score_item = None
        self.advanced_progress_fill_item = None
        self.advanced_feedback_item = None
        self.advanced_feedback_y = 580
        self.advanced_back_y = 620
        self.t20_break_clock_id = None
        self.t20_break_screen_ready = False
        self.t20_break_countdown_item = None
        self.t20_total_score = 0
        self.t20_total_questions_answered = 0
        self.t20_session_mode = "guest"
        self.t20_round_started_at = None
        self.advanced_questions_file = os.path.join(PROJECT_ROOT, "assets", "advanced_questions.txt")
        self.load_default_advanced_questions()
        
        self.show_start_screen()

    # -------- Advanced Maths questions loading helpers --------

    def load_default_advanced_questions(self):
        """Load bundled advanced questions, if the file exists."""
        if os.path.exists(self.advanced_questions_file):
            self.load_advanced_questions_from_file(self.advanced_questions_file)

    def _record_student_attempt(self, topic: str, level, speed: str, score: int, total_q: int):
        """Save student attempt if a student is logged in."""
        if not self.current_user or self.current_user["role"] != "student":
            return

        # Accept either an int sub-level directly or legacy "Level X" strings
        if isinstance(level, int):
            level_num = level
        elif isinstance(level, str) and level.strip().lstrip('-').isdigit():
            level_num = int(level)
        elif level and " " in level:
            try:
                level_num = int(level.split(" ")[-1])
            except ValueError:
                level_num = 0
        else:
            level_num = 0

        # Convert speed from "X s" (or similar) to just numeric.
        speed_num = 0.0
        if speed:
            try:
                if isinstance(speed, (int, float)):
                    speed_num = float(speed)
                else:
                    # strip any non-numeric characters (e.g. trailing 's')
                    speed_num = float(re.sub(r"[^0-9.]", "", str(speed)))
            except Exception:
                speed_num = 0.0

        # Determine section based on topic
        section = (
            "Advanced"
            if topic in ("Squares", "Cubes", "Square Root", "Cube Root", "Word Problems", "Advanced Quiz")
            else "Basic"
        )

        try:
            save_student_attempt(
    student_id=self.current_user["student_id"],
    section=section,
    operation=topic,
    level=level_num,
    score=score,
    total_q=total_q,
    avg_speed=speed_num
)
        except Exception as e:
            print(f"Error saving attempt: {e}")

    def load_advanced_questions_from_file(self, file_path):
        """Read questions from a text file: Question?|opt1|opt2|opt3|opt4 per line.
        Assumes the first option is the correct answer.
        """
        questions = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 5:
                    continue  # skip malformed lines
                q_text = parts[0]
                options = parts[1:5]
                # First option is the correct one, but we'll randomise later
                questions.append({
                    "question": q_text,
                    "options": options,
                    "correct_answer": options[0],
                    "correct_index": 0,
                })

        self.advanced_questions = questions

    def clear_screen(self):
        self._cancel_splash_animation()
        self._cancel_game_start_countdown()
        self._cancel_screen_shake()
        if self._start_screen_resize_job is not None:
            self.root.after_cancel(self._start_screen_resize_job)
            self._start_screen_resize_job = None
        self._start_screen_widgets = {}
        for widget in self.root.winfo_children():
            widget.destroy()
        self.canvas = tk.Canvas(self.root, width=600, height=800, highlightthickness=0, bg=APP_BG_COLOR)
        self.canvas.pack(fill="both", expand=True)

    # -------- Button sound effect wrappers --------

    def _play_button_and_execute(self, callback):
        """Play button sound and execute callback."""
        sound_manager.play_button_sound()
        callback()

    def _create_back_button(self, text, callback, width=16, font=None, parent=None):
        target_parent = parent or self.root
        return create_back_button(
            target_parent,
            text=text,
            command=lambda: self._play_button_and_execute(callback),
            width=width,
            font=font,
        )

    def _get_glossy_button_images(self, width_px, height_px, variant):
        key = (int(width_px), int(height_px), variant)
        if key not in self._glossy_button_cache:
            theme = GLOSSY_BUTTON_THEMES.get(variant, GLOSSY_BUTTON_THEMES["green"])
            normal_img = ImageTk.PhotoImage(
                _render_glossy_button_surface(width_px, height_px, theme, pressed=False)
            )
            active_img = ImageTk.PhotoImage(
                _render_glossy_button_surface(width_px, height_px, theme, pressed=True)
            )
            self._glossy_button_cache[key] = (normal_img, active_img)
        return self._glossy_button_cache[key]

    def _create_glossy_button(self, text, callback, width=16, font=None, parent=None, variant="green"):
        target_parent = parent or self.root
        button_font = font or (FONT_FAMILY_UI, 16, "bold")
        measure_font = tkfont.Font(root=self.root, font=button_font)
        char_w = max(7, measure_font.measure("0"))
        text_w = measure_font.measure(text)
        width_px = max(int(width * char_w + 18), text_w + 62)
        height_px = max(50, measure_font.metrics("linespace") + 22)
        theme = GLOSSY_BUTTON_THEMES.get(variant, GLOSSY_BUTTON_THEMES["green"])
        base_kwargs = dict(
            text=text,
            command=lambda: self._play_button_and_execute(callback),
            font=button_font,
            fg=theme["text"],
            activeforeground=theme["text"],
            disabledforeground="#C6D3E5",
            cursor="hand2",
        )
        fallback_style = dict(
            bg=theme["top"],
            activebackground=theme["bottom"],
            relief="raised",
            bd=2,
            highlightthickness=0,
            padx=12,
            pady=8,
        )

        try:
            normal_img, active_img = self._get_glossy_button_images(width_px, height_px, variant)
            btn = tk.Button(
                target_parent,
                image=normal_img,
                compound="center",
                bg=theme["top"],
                activebackground=theme["bottom"],
                relief="flat",
                bd=0,
                highlightthickness=0,
                padx=0,
                pady=0,
                **base_kwargs,
            )
            # Keep refs and geometry metadata on the widget so it can be resized later
            # without falling back to Tk's character-based button sizing.
            btn._glossy_images = (normal_img, active_img)
            btn._glossy_is_pressed = False
            btn._glossy_variant = variant
            btn._glossy_font = button_font
            btn._glossy_width_units = width
            btn._glossy_uses_image = True
            btn.config(width=width_px, height=height_px)

            def _show_normal(_event=None):
                if btn.winfo_exists() and getattr(btn, "_glossy_images", None):
                    btn.config(image=btn._glossy_images[0])

            def _show_active(_event=None):
                if btn.winfo_exists() and getattr(btn, "_glossy_images", None):
                    btn.config(image=btn._glossy_images[1])

            def _on_press(_event):
                btn._glossy_is_pressed = True
                _show_active()

            def _on_release(event):
                btn._glossy_is_pressed = False
                inside = 0 <= event.x < btn.winfo_width() and 0 <= event.y < btn.winfo_height()
                if inside:
                    _show_active()
                else:
                    _show_normal()

            def _on_enter(_event):
                if not btn._glossy_is_pressed:
                    _show_active()

            def _on_leave(_event):
                if not btn._glossy_is_pressed:
                    _show_normal()

            btn.bind("<ButtonPress-1>", _on_press, add="+")
            btn.bind("<ButtonRelease-1>", _on_release, add="+")
            btn.bind("<Enter>", _on_enter, add="+")
            btn.bind("<Leave>", _on_leave, add="+")
            return btn
        except Exception:
            # Safe fallback: still visible even if image rendering fails.
            btn = tk.Button(target_parent, width=width, **base_kwargs, **fallback_style)
            btn._glossy_uses_image = False
            return btn

    def _resize_glossy_button(self, btn, width=16, font=None):
        if not btn or not btn.winfo_exists():
            return

        button_font = font or getattr(btn, "_glossy_font", (FONT_FAMILY_UI, 16, "bold"))
        if not getattr(btn, "_glossy_uses_image", False):
            btn.configure(font=button_font, width=width, padx=12, pady=8)
            return

        text = btn.cget("text")
        variant = getattr(btn, "_glossy_variant", "green")
        measure_font = tkfont.Font(root=self.root, font=button_font)
        char_w = max(7, measure_font.measure("0"))
        text_w = measure_font.measure(text)
        width_px = max(int(width * char_w + 18), text_w + 62)
        height_px = max(50, measure_font.metrics("linespace") + 22)
        normal_img, active_img = self._get_glossy_button_images(width_px, height_px, variant)
        btn._glossy_images = (normal_img, active_img)
        btn._glossy_font = button_font
        btn._glossy_width_units = width
        btn.configure(
            font=button_font,
            image=active_img if getattr(btn, "_glossy_is_pressed", False) else normal_img,
            width=width_px,
            height=height_px,
        )

    def _canvas_offset_x(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return 0
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            return 0
        return max(0, (canvas_width - 600) // 2)

    def _sx(self, x):
        return int(self._canvas_offset_x() + x)

    def _canvas_scale_y(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return 1.0
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:
            return 1.0
        return canvas_height / 800.0

    def _sy(self, y):
        return int(y * self._canvas_scale_y())

    def _create_round_rectangle(self, x1, y1, x2, y2, radius=24, **kwargs):
        """Draw a rounded rectangle on the active canvas."""
        radius = max(0, int(radius))
        max_radius = int(min((x2 - x1) / 2, (y2 - y1) / 2))
        radius = min(radius, max_radius)

        points = [
            x1 + radius, y1,
            x1 + radius, y1,
            x2 - radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            **kwargs,
        )

    def draw_bg(self, width=None, height=None):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        if width is None or height is None:
            self.root.update_idletasks()
            if width is None:
                width = self.canvas.winfo_width()
            if height is None:
                height = self.canvas.winfo_height()
            width = 600 if width <= 1 else width
            height = 800 if height <= 1 else height

        target_size = (max(1, int(width)), max(1, int(height)))
        if self._bg_cache_size != target_size:
            bg_img = Image.new("RGBA", target_size, "#110A2E")

            gradient = Image.new("RGBA", target_size, (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient)
            max_height = max(1, target_size[1] - 1)
            for y in range(target_size[1]):
                blend = y / max_height
                r = int(24 + ((5 - 24) * blend))
                g = int(16 + ((14 - 16) * blend))
                b = int(68 + ((36 - 68) * blend))
                gradient_draw.line(
                    (0, y, target_size[0], y),
                    fill=(r, g, b, 255),
                )
            bg_img = Image.alpha_composite(bg_img, gradient)

            glow_overlay = Image.new("RGBA", target_size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_overlay)
            glow_specs = [
                ((-120, 10, int(target_size[0] * 0.38), int(target_size[1] * 0.36)), (87, 47, 196)),
                ((int(target_size[0] * 0.62), 40, target_size[0] + 110, int(target_size[1] * 0.34)), (31, 84, 198)),
                ((int(target_size[0] * 0.22), int(target_size[1] * 0.62), int(target_size[0] * 0.72), target_size[1] + 140), (12, 126, 196)),
            ]
            for bounds, color in glow_specs:
                for step in range(6):
                    inset = step * 18
                    alpha = max(10, 58 - (step * 8))
                    x0 = bounds[0] + inset
                    y0 = bounds[1] + inset
                    x1 = bounds[2] - inset
                    y1 = bounds[3] - inset
                    if x1 < x0:
                        x0, x1 = x1, x0
                    if y1 < y0:
                        y0, y1 = y1, y0
                    glow_draw.ellipse(
                        (x0, y0, x1, y1),
                        fill=color + (alpha,),
                    )
            bg_img = Image.alpha_composite(bg_img, glow_overlay)

            star_draw = ImageDraw.Draw(bg_img)
            star_count = max(45, (target_size[0] * target_size[1]) // 18000)
            for _ in range(star_count):
                x = random.randint(0, target_size[0] - 1)
                y = random.randint(0, target_size[1] - 1)
                r = random.randint(1, 2)
                alpha = random.randint(90, 180)
                color = random.choice(
                    (
                        (198, 227, 255, alpha),
                        (255, 240, 214, alpha),
                        (164, 214, 255, alpha),
                    )
                )
                star_draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

            self._bg_cache_photo = ImageTk.PhotoImage(bg_img)
            self._bg_cache_size = target_size

        if self._bg_cache_photo:
            self.canvas.create_image(0, 0, image=self._bg_cache_photo, anchor="nw")
        else:
            self.canvas.config(bg="#0B0D17")

    def _schedule_start_screen_layout(self, _event=None):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        if self._start_screen_resize_job is not None:
            self.root.after_cancel(self._start_screen_resize_job)
        self._start_screen_resize_job = self.root.after(30, self._layout_start_screen)

    def _layout_start_screen(self):
        self._start_screen_resize_job = None
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        admin_btn = self._start_screen_widgets.get("admin_btn")
        student_btn = self._start_screen_widgets.get("student_btn")
        guest_btn = self._start_screen_widgets.get("guest_btn")
        if not all([admin_btn, student_btn, guest_btn]):
            return

        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        center_x = canvas_width / 2
        min_side = min(canvas_width, canvas_height)

        def _clamp(value, low, high):
            return max(low, min(high, value))

        palette = {
            "glow_left": "#251652",
            "glow_right": "#123C88",
            "panel_shadow": "#050819",
            "panel_fill": "#0E4B78",
            "panel_outline": "#38D1FF",
            "panel_inner": "#1F77AF",
            "panel_line": "#47D7FF",
            "hero_badge_fill": "#173C73",
            "hero_badge_outline": "#58E1FF",
            "hero_badge_text": "#B9F7FF",
            "title_shadow": "#0A2566",
            "title_fill": "#5BCBFF",
            "hero_line": "#F7FBFF",
            "hero_body": "#D5EAFF",
            "moon_fill": "#EAF38A",
            "moon_crater": "#B6DE5D",
            "orbit": "#59D8FF",
            "spark": "#FFF3A7",
            "chip_text": "#F2FAFF",
            "portal_card_fill": "#0D5B84",
            "portal_card_outline": "#38D1FF",
            "portal_text": "#F6FBFF",
            "portal_body": "#DAECFF",
            "caption": "#AFD0F0",
            "footer": "#C7DDF3",
            "footer_small": "#89A9CA",
        }

        eyebrow_size = int(_clamp(min_side * 0.019, 10, 14))
        title_size = int(_clamp(min_side * 0.080, 30, 64))
        hero_size = int(_clamp(min_side * 0.035, 14, 24))
        subtitle_size = int(_clamp(min_side * 0.024, 10, 17))
        portal_heading_size = int(_clamp(min_side * 0.030, 14, 20))
        portal_title_size = int(_clamp(min_side * 0.025, 11, 17))
        footer_size = int(_clamp(min_side * 0.020, 9, 14))
        footer_small_size = int(_clamp(min_side * 0.017, 8, 12))
        button_size = int(_clamp(min_side * 0.034, 12, 20))
        button_width_chars = int(_clamp(canvas_width / 70, 14, 20))

        footer_y = canvas_height - int(_clamp(canvas_height * 0.055, 38, 58))
        footer_small_y = canvas_height - int(_clamp(canvas_height * 0.030, 20, 34))

        button_font = (FONT_FAMILY_UI, button_size, "bold")
        for btn in (admin_btn, student_btn, guest_btn):
            self._resize_glossy_button(
                btn,
                width=button_width_chars,
                font=button_font,
            )

        self.canvas.delete("all")
        self.draw_bg(width=canvas_width, height=canvas_height)

        panel_width = int(min(canvas_width * 0.88, 1120))
        panel_height = int(min(canvas_height * 0.72, 650))
        panel_x1 = int(center_x - (panel_width / 2))
        panel_y1 = int(max(self._sy(56), canvas_height * 0.10))
        panel_x2 = int(center_x + (panel_width / 2))
        panel_y2 = int(min(canvas_height - self._sy(104), panel_y1 + panel_height))
        panel_height = panel_y2 - panel_y1

        wide_layout = panel_width >= 920
        panel_pad_x = int(_clamp(panel_width * 0.055, 28, 56))
        panel_pad_y = int(_clamp(panel_height * 0.085, 28, 50))
        panel_pad_bottom = int(_clamp(panel_height * 0.085, 30, 54))
        section_gap_sm = int(_clamp(panel_height * 0.022, 10, 16))
        section_gap_md = int(_clamp(panel_height * 0.036, 16, 24))
        section_gap_lg = int(_clamp(panel_height * 0.058, 24, 36))
        column_gap = int(_clamp(panel_width * 0.034, 22, 38))

        hero_left = panel_x1 + panel_pad_x
        hero_top = panel_y1 + panel_pad_y
        hero_width = int(panel_width * 0.46) if wide_layout else int(panel_width - (panel_pad_x * 2))
        hero_right = hero_left + hero_width

        if wide_layout:
            portal_x1 = hero_right + column_gap
            portal_x2 = panel_x2 - panel_pad_x
            portal_width = portal_x2 - portal_x1
            portal_top = hero_top + 2
        else:
            portal_x1 = panel_x1 + panel_pad_x
            portal_x2 = panel_x2 - panel_pad_x
            portal_width = portal_x2 - portal_x1
            portal_top = hero_top + int(_clamp(panel_height * 0.34, 170, 230))
        portal_x2 = portal_x1 + portal_width

        card_gap = int(_clamp(panel_height * 0.022, 12, 18))
        card_height = int(_clamp(panel_height * (0.19 if wide_layout else 0.13), 84, 126))
        portal_title_block_y = portal_top
        cards_start_y = portal_title_block_y + int(_clamp(panel_height * 0.14, 78, 96))

        # Soft glows behind the main card for a playful space-console feel.
        self.canvas.create_oval(
            panel_x1 - int(panel_width * 0.10),
            panel_y1 - int(panel_height * 0.10),
            panel_x1 + int(panel_width * 0.30),
            panel_y1 + int(panel_height * 0.36),
            fill=palette["glow_left"],
            outline="",
        )
        self.canvas.create_oval(
            panel_x2 - int(panel_width * 0.28),
            panel_y1 + int(panel_height * 0.04),
            panel_x2 + int(panel_width * 0.10),
            panel_y1 + int(panel_height * 0.38),
            fill=palette["glow_right"],
            outline="",
        )

        self._create_round_rectangle(
            panel_x1 + 12,
            panel_y1 + 16,
            panel_x2 + 12,
            panel_y2 + 16,
            radius=38,
            fill=palette["panel_shadow"],
            outline="",
        )
        self._create_round_rectangle(
            panel_x1,
            panel_y1,
            panel_x2,
            panel_y2,
            radius=38,
            fill=palette["panel_fill"],
            outline=palette["panel_outline"],
            width=2,
        )
        self._create_round_rectangle(
            panel_x1 + 18,
            panel_y1 + 18,
            panel_x2 - 18,
            panel_y2 - 18,
            radius=30,
            fill="",
            outline=palette["panel_inner"],
            width=1,
        )
        self.canvas.create_line(
            panel_x1 + 42,
            panel_y1 + 28,
            panel_x2 - 42,
            panel_y1 + 28,
            fill=palette["panel_line"],
            width=5,
        )

        if not wide_layout:
            compact_center_x = center_x
            compact_title_y = hero_top + int(_clamp(panel_height * 0.10, 58, 72))
            compact_subtitle_y = compact_title_y + title_size + section_gap_sm
            compact_chip_y = compact_subtitle_y + section_gap_lg
            compact_portal_y = compact_chip_y + section_gap_lg
            compact_cards_top = compact_portal_y + section_gap_md + 8
            compact_card_gap = int(_clamp(panel_height * 0.022, 10, 14))
            compact_card_height = int(
                max(
                    82,
                    min(
                        94,
                        ((panel_y2 - panel_pad_bottom) - compact_cards_top - (2 * compact_card_gap)) / 3,
                    ),
                )
            )

            planet_radius = int(_clamp(min_side * 0.055, 28, 44))
            compact_planet_x = panel_x2 - int(_clamp(panel_width * 0.16, 62, 86))
            compact_planet_y = hero_top + int(_clamp(panel_height * 0.03, 8, 18))
            self.canvas.create_oval(
                compact_planet_x - planet_radius,
                compact_planet_y - planet_radius,
                compact_planet_x + planet_radius,
                compact_planet_y + planet_radius,
                fill=palette["moon_fill"],
                outline="",
            )
            self.canvas.create_arc(
                compact_planet_x - int(planet_radius * 1.45),
                compact_planet_y - int(planet_radius * 0.75),
                compact_planet_x + int(planet_radius * 1.45),
                compact_planet_y + int(planet_radius * 0.75),
                start=20,
                extent=300,
                style="arc",
                outline=palette["orbit"],
                width=3,
            )

            eyebrow_text = "SPACE MISSION HQ"
            eyebrow_width = max(160, int(len(eyebrow_text) * eyebrow_size * 0.90))
            self._create_round_rectangle(
                compact_center_x - (eyebrow_width / 2),
                hero_top - 16,
                compact_center_x + (eyebrow_width / 2),
                hero_top + 16,
                radius=16,
                fill=palette["hero_badge_fill"],
                outline=palette["hero_badge_outline"],
                width=1,
            )
            self.canvas.create_text(
                compact_center_x,
                hero_top,
                text=eyebrow_text,
                font=(FONT_FAMILY_UI, eyebrow_size, "bold"),
                fill=palette["hero_badge_text"],
            )
            self.canvas.create_text(
                compact_center_x + 4,
                compact_title_y + 4,
                text="Math Game",
                font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
                fill=palette["title_shadow"],
                width=int(panel_width * 0.84),
            )
            self.canvas.create_text(
                compact_center_x,
                compact_title_y,
                text="Math Game",
                font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
                fill=palette["title_fill"],
                width=int(panel_width * 0.84),
            )
            self.canvas.create_text(
                compact_center_x,
                compact_subtitle_y,
                text="Pick a bright portal and launch into quick, playful space maths.",
                font=(FONT_FAMILY_TEXT, subtitle_size),
                fill=palette["hero_body"],
                width=int(panel_width * 0.78),
            )

            chip_specs = [
                ("Quick Play", "#102A43", "#56B6FF"),
                ("Track Scores", "#16233B", "#FF9A3D"),
                ("T20", "#112E3B", "#5CD6C5"),
            ]
            chip_gap = 10
            chip_height = 30
            chip_widths = [
                max(84, int(len(text) * max(7.0, subtitle_size * 0.72)) + 24)
                for text, _, _ in chip_specs
            ]
            total_chip_width = sum(chip_widths) + (chip_gap * (len(chip_specs) - 1))
            chip_x = compact_center_x - (total_chip_width / 2)
            for (chip_text, chip_fill, chip_outline), chip_width in zip(chip_specs, chip_widths):
                self._create_round_rectangle(
                    chip_x,
                    compact_chip_y - (chip_height / 2),
                    chip_x + chip_width,
                    compact_chip_y + (chip_height / 2),
                    radius=int(chip_height / 2),
                    fill=chip_fill,
                    outline=chip_outline,
                    width=1,
                )
                self.canvas.create_text(
                    chip_x + (chip_width / 2),
                    compact_chip_y,
                    text=chip_text,
                    font=(FONT_FAMILY_UI, max(9, subtitle_size - 1), "bold"),
                    fill=palette["chip_text"],
                )
                chip_x += chip_width + chip_gap

            self.canvas.create_text(
                compact_center_x,
                compact_portal_y,
                text="Choose your portal",
                font=(FONT_FAMILY_UI, portal_heading_size, "bold"),
                fill=palette["portal_text"],
                width=int(panel_width * 0.82),
            )

            compact_portals = [
                (admin_btn, "Teacher tools and student setup", "#5BB2FF"),
                (student_btn, "Cadet practice and profile tracking", "#7CD8FF"),
                (guest_btn, "Fast T20 sprint for instant play", "#FFB15C"),
            ]
            for index, (button, caption, accent_color) in enumerate(compact_portals):
                card_y1 = compact_cards_top + (index * (compact_card_height + compact_card_gap))
                card_y2 = card_y1 + compact_card_height
                button_y = card_y1 + int(compact_card_height * 0.42)
                self._create_round_rectangle(
                    portal_x1,
                    card_y1,
                    portal_x2,
                    card_y2,
                    radius=24,
                    fill=palette["portal_card_fill"],
                    outline=palette["portal_card_outline"],
                    width=2,
                )
                self.canvas.create_rectangle(
                    portal_x1 + 4,
                    card_y1 + 14,
                    portal_x1 + 10,
                    card_y2 - 14,
                    fill=accent_color,
                    outline="",
                )
                self.canvas.create_window(compact_center_x, button_y, window=button)
                self.canvas.create_text(
                    compact_center_x,
                    card_y2 - 18,
                    text=caption,
                    font=(FONT_FAMILY_TEXT, max(9, subtitle_size - 1)),
                    fill=palette["caption"],
                    width=max(180, int(portal_width * 0.80)),
                )

            self.canvas.create_text(
                center_x,
                footer_y,
                text="Built for playful practice, classroom demos, and progress-driven space adventures.",
                font=(FONT_FAMILY_UI, footer_size),
                fill=palette["footer"],
                width=int(canvas_width * 0.95),
            )
            self.canvas.create_text(
                center_x,
                footer_small_y,
                text="© 2026 SynCraft Solution",
                font=(FONT_FAMILY_UI, footer_small_size),
                fill=palette["footer_small"],
                width=int(canvas_width * 0.95),
            )
            return

        # Decorative hero art.
        hero_art_x = hero_right - int(_clamp(hero_width * 0.09, 28, 44))
        hero_art_y = hero_top + int(_clamp(panel_height * 0.04, 28, 40))
        planet_radius = int(_clamp(min_side * 0.044, 26, 42))
        self.canvas.create_oval(
            hero_art_x - planet_radius,
            hero_art_y - planet_radius,
            hero_art_x + planet_radius,
            hero_art_y + planet_radius,
            fill=palette["moon_fill"],
            outline="",
        )
        self.canvas.create_oval(
            hero_art_x - int(planet_radius * 0.68),
            hero_art_y - int(planet_radius * 0.52),
            hero_art_x + int(planet_radius * 0.42),
            hero_art_y + int(planet_radius * 0.58),
            fill=palette["moon_crater"],
            outline="",
        )
        self.canvas.create_arc(
            hero_art_x - int(planet_radius * 1.5),
            hero_art_y - int(planet_radius * 0.8),
            hero_art_x + int(planet_radius * 1.5),
            hero_art_y + int(planet_radius * 0.8),
            start=20,
            extent=300,
            style="arc",
            outline=palette["orbit"],
            width=4,
        )
        self.canvas.create_oval(
            hero_art_x + int(planet_radius * 0.85),
            hero_art_y - int(planet_radius * 1.05),
            hero_art_x + int(planet_radius * 1.18),
            hero_art_y - int(planet_radius * 0.72),
            fill=palette["spark"],
            outline="",
        )
        self.canvas.create_line(
            hero_art_x - int(planet_radius * 1.65),
            hero_art_y + int(planet_radius * 1.28),
            hero_art_x - int(planet_radius * 0.80),
            hero_art_y + int(planet_radius * 0.52),
            fill=palette["orbit"],
            width=3,
        )
        self.canvas.create_line(
            hero_art_x - int(planet_radius * 1.80),
            hero_art_y + int(planet_radius * 1.44),
            hero_art_x - int(planet_radius * 1.58),
            hero_art_y + int(planet_radius * 1.23),
            fill=palette["spark"],
            width=2,
        )

        eyebrow_x = hero_left
        eyebrow_y = hero_top
        eyebrow_text = "SPACE MISSION HQ"
        eyebrow_width = max(170, int(len(eyebrow_text) * eyebrow_size * 0.86))
        self._create_round_rectangle(
            eyebrow_x,
            eyebrow_y - 16,
            eyebrow_x + eyebrow_width,
            eyebrow_y + 16,
            radius=16,
            fill=palette["hero_badge_fill"],
            outline=palette["hero_badge_outline"],
            width=1,
        )
        self.canvas.create_text(
            eyebrow_x + (eyebrow_width / 2),
            eyebrow_y,
            text=eyebrow_text,
            font=(FONT_FAMILY_UI, eyebrow_size, "bold"),
            fill=palette["hero_badge_text"],
        )

        title_y = eyebrow_y + section_gap_lg + int(title_size * 0.42)
        hero_line_y = title_y + int(title_size * 1.08)
        subtitle_y = hero_line_y + int(hero_size * 1.45) + section_gap_sm
        hero_copy_width = int(hero_width * 0.88)
        hero_line_font_size = max(14, hero_size - 2)
        hero_body_font_size = max(10, subtitle_size - 1)
        hero_line_text = (
            "Playful number missions for young space explorers"
            if wide_layout
            else "A bright space mission for quick math wins"
        )
        hero_body_text = (
            "Jump into bright space portals, practise arithmetic with meteor rounds, and build confidence through quick wins and progress tracking."
            if wide_layout
            else "Pick a portal and launch straight into colourful arithmetic practice."
        )

        self.canvas.create_text(
            hero_left + 4,
            title_y + 4,
            anchor="w",
            text="Math Game",
            font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
            fill=palette["title_shadow"],
            width=hero_copy_width,
        )
        self.canvas.create_text(
            hero_left,
            title_y,
            anchor="w",
            text="Math Game",
            font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
            fill=palette["title_fill"],
            width=hero_copy_width,
        )
        self.canvas.create_text(
            hero_left,
            hero_line_y,
            anchor="w",
            text=hero_line_text,
            font=(FONT_FAMILY_UI, hero_line_font_size, "bold"),
            fill=palette["hero_line"],
            width=hero_copy_width,
        )
        self.canvas.create_text(
            hero_left,
            subtitle_y,
            anchor="w",
            text=hero_body_text,
            font=(FONT_FAMILY_TEXT, hero_body_font_size),
            fill=palette["hero_body"],
            width=hero_copy_width,
        )

        chip_font = (FONT_FAMILY_UI, max(9, subtitle_size - 1), "bold")
        chip_y = subtitle_y + section_gap_lg + 4
        chip_height = int(_clamp(panel_height * 0.07, 28, 38))
        chip_specs = (
            [
                ("Quick Drills", "#102A43", "#56B6FF"),
                ("Progress Reports", "#16233B", "#FF9A3D"),
                ("T20 Speed Arena", "#112E3B", "#5CD6C5"),
            ]
            if wide_layout
            else [
                ("Quick Play", "#102A43", "#56B6FF"),
                ("Track Scores", "#16233B", "#FF9A3D"),
                ("T20", "#112E3B", "#5CD6C5"),
            ]
        )
        chip_x = hero_left
        chip_gap = int(_clamp(panel_width * 0.012, 8, 12))
        for chip_text, chip_fill, chip_outline in chip_specs:
            chip_width = max(118, int(len(chip_text) * max(7.2, subtitle_size * 0.74)) + 28)
            self._create_round_rectangle(
                chip_x,
                chip_y - (chip_height / 2),
                chip_x + chip_width,
                chip_y + (chip_height / 2),
                radius=int(chip_height / 2),
                fill=chip_fill,
                outline=chip_outline,
                width=1,
            )
            self.canvas.create_text(
                chip_x + (chip_width / 2),
                chip_y,
                text=chip_text,
                font=chip_font,
                fill=palette["chip_text"],
            )
            chip_x += chip_width + chip_gap
            if chip_x > (hero_right - 130):
                chip_x = hero_left
                chip_y += chip_height + chip_gap

        note_y = chip_y + chip_height + section_gap_md
        self.canvas.create_text(
            hero_left,
            note_y,
            anchor="w",
            text="Choose a portal to launch the same game systems with a brighter, more kid-friendly mission control look.",
            font=(FONT_FAMILY_TEXT, max(10, subtitle_size - 1)),
            fill=palette["caption"],
            width=hero_copy_width,
        )

        portal_title_block_y = hero_top + 2
        portal_desc_y = portal_title_block_y + portal_heading_size + section_gap_sm
        cards_start_y = portal_desc_y + int(_clamp(panel_height * 0.08, 34, 46))
        available_cards_height = max(300, (panel_y2 - panel_pad_bottom) - cards_start_y)
        card_height = int(max(122, min(152, (available_cards_height - (2 * card_gap)) / 3)))

        self.canvas.create_text(
            portal_x1,
            portal_title_block_y,
            anchor="nw",
            text="Choose your portal",
            font=(FONT_FAMILY_UI, portal_heading_size, "bold"),
            fill=palette["portal_text"],
            width=portal_width,
        )
        self.canvas.create_text(
            portal_x1,
            portal_desc_y,
            anchor="nw",
            text="Each route keeps the same game logic. Only the mission entry point changes.",
            font=(FONT_FAMILY_TEXT, max(10, subtitle_size - 1)),
            fill=palette["caption"],
            width=portal_width,
        )

        def draw_portal_card(y1, accent_color, badge_text, title_text, body_text, button):
            y2 = y1 + card_height
            card_pad_x = 20
            card_pad_y = 18
            badge_size = 36
            badge_center_y = y1 + card_pad_y + int(badge_size / 2)
            badge_left = portal_x1 + card_pad_x
            badge_top = badge_center_y - int(badge_size / 2)
            badge_right = badge_left + badge_size
            badge_bottom = badge_top + badge_size
            title_x = badge_right + 14
            title_y = y1 + card_pad_y + 2
            body_y = title_y + 28
            body_width = max(160, portal_width - (title_x - portal_x1) - card_pad_x)
            button_y = y2 - 26

            self._create_round_rectangle(
                portal_x1,
                y1,
                portal_x2,
                y2,
                radius=26,
                fill=palette["portal_card_fill"],
                outline=palette["portal_card_outline"],
                width=2,
            )
            self.canvas.create_rectangle(
                portal_x1 + 2,
                y1 + 16,
                portal_x1 + 8,
                y2 - 16,
                fill=accent_color,
                outline="",
            )
            self.canvas.create_oval(
                badge_left,
                badge_top,
                badge_right,
                badge_bottom,
                fill=accent_color,
                outline="",
            )
            self.canvas.create_text(
                (badge_left + badge_right) / 2,
                (badge_top + badge_bottom) / 2,
                text=badge_text,
                font=(FONT_FAMILY_UI, max(9, portal_title_size - 2), "bold"),
                fill="#102033",
            )
            self.canvas.create_text(
                badge_right + 14,
                title_y,
                anchor="w",
                text=title_text,
                font=(FONT_FAMILY_UI, portal_title_size, "bold"),
                fill=palette["portal_text"],
                width=body_width,
            )
            self.canvas.create_text(
                badge_right + 14,
                body_y,
                anchor="w",
                text=body_text,
                font=(FONT_FAMILY_TEXT, max(9, subtitle_size - 1)),
                fill=palette["portal_body"],
                width=body_width,
            )
            self.canvas.create_window(
                (portal_x1 + portal_x2) / 2,
                button_y,
                window=button,
            )

        portal_cards = [
            (
                "#4AA7FF",
                "A",
                "Admin Login",
                "Create student access, upload quiz banks, and review progress.",
                admin_btn,
            ),
            (
                "#74D1FF",
                "S",
                "Student Login",
                "Play missions, track profile history, and practise by level.",
                student_btn,
            ),
            (
                "#FFAA54",
                "T20",
                "Guest Login (T20)",
                "Jump straight into a fast T20 classroom sprint mode.",
                guest_btn,
            ),
        ]
        for index, (accent_color, badge_text, title_text, body_text, button) in enumerate(portal_cards):
            draw_portal_card(
                cards_start_y + (index * (card_height + card_gap)),
                accent_color,
                badge_text,
                title_text,
                body_text,
                button,
            )

        self.canvas.create_text(
            center_x,
            footer_y,
            text="Built for playful practice, classroom demos, and progress-driven space adventures.",
            font=(FONT_FAMILY_UI, footer_size),
            fill=palette["footer"],
            width=int(canvas_width * 0.95),
        )
        self.canvas.create_text(
            center_x,
            footer_small_y,
            text="© 2026 SynCraft Solution",
            font=(FONT_FAMILY_UI, footer_small_size),
            fill=palette["footer_small"],
            width=int(canvas_width * 0.95),
        )

    # -------- Start Screen : Admin Login , Student Login , Guest Login , Footer With Credits --------

    def _cancel_splash_animation(self):
        if self.splash_animation_job is not None:
            try:
                self.root.after_cancel(self.splash_animation_job)
            except tk.TclError:
                pass
            self.splash_animation_job = None
        if self.splash_finish_job is not None:
            try:
                self.root.after_cancel(self.splash_finish_job)
            except tk.TclError:
                pass
            self.splash_finish_job = None
        self.splash_started_at = None

    def _ease_out_cubic(self, value):
        value = max(0.0, min(1.0, value))
        return 1 - ((1 - value) ** 3)

    def _ease_in_out(self, value):
        value = max(0.0, min(1.0, value))
        return (3 * (value ** 2)) - (2 * (value ** 3))

    def _ensure_splash_starfield(self, width, height):
        target_size = (max(1, int(width)), max(1, int(height)))
        if self.splash_starfield_size == target_size:
            return

        splash_rng = random.Random(42)
        stars = []
        star_count = max(36, (target_size[0] * target_size[1]) // 24000)
        x_min = min(24, max(0, target_size[0] // 4))
        x_max = max(x_min, target_size[0] - x_min)
        y_min = min(24, max(0, target_size[1] // 4))
        y_max = max(y_min, target_size[1] - y_min)
        for _ in range(star_count):
            stars.append(
                {
                    "x": splash_rng.randint(x_min, x_max),
                    "y": splash_rng.randint(y_min, y_max),
                    "size": splash_rng.choice((2, 2, 3, 4)),
                    "phase": splash_rng.uniform(0.0, math.tau),
                    "speed": splash_rng.uniform(0.8, 1.9),
                }
            )
        self.splash_starfield = stars
        self.splash_starfield_size = target_size

    def _draw_splash_star(self, x, y, size, brightness):
        sparkle = max(1, int(size * brightness))
        self.canvas.create_line(x - sparkle, y, x + sparkle, y, fill="#FFFFFF", width=2)
        self.canvas.create_line(x, y - sparkle, x, y + sparkle, fill="#FFFFFF", width=2)
        if sparkle >= 3:
            self.canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="#FFFFFF", outline="")

    def _draw_splash_rocket(self, x, y, scale, flame_scale):
        body_w = int(46 * scale)
        body_h = int(112 * scale)
        nose_h = int(28 * scale)
        fin_w = int(20 * scale)
        fin_h = int(28 * scale)
        booster_w = int(14 * scale)
        booster_h = int(18 * scale)
        window_r = max(7, int(9 * scale))

        left = x - (body_w // 2)
        right = x + (body_w // 2)
        top = y - (body_h // 2)
        bottom = y + (body_h // 2)
        body_top = top + int(body_h * 0.10)
        body_bottom = bottom - int(body_h * 0.18)
        skirt_top = body_bottom - int(body_h * 0.06)

        # smoke trail behind the rocket
        smoke_h = int(54 * scale * max(0.45, flame_scale))
        smoke_w = int(18 * scale)
        if smoke_h > 10:
            self.canvas.create_polygon(
                x - smoke_w,
                bottom - 4,
                x - int(smoke_w * 0.55),
                bottom + int(smoke_h * 0.35),
                x - int(smoke_w * 0.35),
                bottom + smoke_h,
                x + int(smoke_w * 0.35),
                bottom + smoke_h,
                x + int(smoke_w * 0.55),
                bottom + int(smoke_h * 0.35),
                x + smoke_w,
                bottom - 4,
                fill="#D7D4E3",
                outline="",
                smooth=True,
            )

        # rocket body
        self.canvas.create_polygon(
            x,
            top - nose_h,
            right - int(body_w * 0.10),
            body_top,
            left + int(body_w * 0.10),
            body_top,
            fill="#B993E6",
            outline="#4B3567",
            width=2,
            smooth=True,
        )
        self._create_round_rectangle(
            left,
            body_top,
            right,
            body_bottom,
            radius=max(14, int(16 * scale)),
            fill="#9A7ACC",
            outline="#4B3567",
            width=2,
        )
        self.canvas.create_polygon(
            left + int(body_w * 0.10),
            body_top + int(body_h * 0.02),
            x - int(body_w * 0.04),
            body_top + int(body_h * 0.10),
            x - int(body_w * 0.02),
            body_bottom - int(body_h * 0.02),
            left + int(body_w * 0.08),
            body_bottom - int(body_h * 0.04),
            fill="#7D62AD",
            outline="",
            smooth=True,
        )
        self.canvas.create_polygon(
            x + int(body_w * 0.04),
            body_top + int(body_h * 0.02),
            right - int(body_w * 0.08),
            body_top + int(body_h * 0.08),
            right - int(body_w * 0.06),
            body_bottom - int(body_h * 0.04),
            x + int(body_w * 0.02),
            body_bottom - int(body_h * 0.02),
            fill="#C8ACEF",
            outline="",
            smooth=True,
        )

        # side fins
        self.canvas.create_polygon(
            left + int(body_w * 0.08),
            body_bottom - int(body_h * 0.10),
            left - fin_w,
            bottom + fin_h,
            x - int(body_w * 0.10),
            skirt_top,
            fill="#7A58B0",
            outline="#4B3567",
            width=2,
            smooth=True,
        )
        self.canvas.create_polygon(
            right - int(body_w * 0.08),
            body_bottom - int(body_h * 0.10),
            right + fin_w,
            bottom + fin_h,
            x + int(body_w * 0.10),
            skirt_top,
            fill="#7A58B0",
            outline="#4B3567",
            width=2,
            smooth=True,
        )

        # engine/booster
        self._create_round_rectangle(
            x - (booster_w // 2),
            skirt_top,
            x + (booster_w // 2),
            skirt_top + booster_h,
            radius=max(4, int(5 * scale)),
            fill="#52465F",
            outline="#3B3245",
            width=2,
        )

        # window
        window_cy = body_top + int(body_h * 0.26)
        self.canvas.create_oval(
            x - (window_r + 5),
            window_cy - (window_r + 5),
            x + (window_r + 5),
            window_cy + (window_r + 5),
            fill="#5A447A",
            outline="",
        )
        self.canvas.create_oval(
            x - window_r,
            window_cy - window_r,
            x + window_r,
            window_cy + window_r,
            fill="#FFF8FF",
            outline="",
        )

        # flame
        flame_h = int(34 * scale * flame_scale)
        if flame_h > 6:
            flame_top = skirt_top + booster_h - 2
            self.canvas.create_polygon(
                x,
                flame_top + flame_h,
                x - int(10 * scale),
                flame_top + int(flame_h * 0.30),
                x,
                flame_top,
                x + int(10 * scale),
                flame_top + int(flame_h * 0.30),
                fill="#F1F0F5",
                outline="",
                smooth=True,
            )

    def _render_splash_frame(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists() or self.splash_started_at is None:
            return

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        elapsed = max(0.0, time.time() - self.splash_started_at)
        self._ensure_splash_starfield(width, height)

        self.canvas.delete("all")
        self.canvas.configure(bg="#12091F")
        self.canvas.create_rectangle(0, 0, width, height, fill="#15101F", outline="")
        self.canvas.create_oval(
            -int(width * 0.12),
            int(height * 0.04),
            int(width * 0.34),
            int(height * 0.40),
            fill="#26174F",
            outline="",
        )
        self.canvas.create_oval(
            int(width * 0.62),
            int(height * 0.10),
            int(width * 1.08),
            int(height * 0.44),
            fill="#143675",
            outline="",
        )

        for star in self.splash_starfield:
            twinkle = 0.55 + (0.45 * abs(math.sin((elapsed * star["speed"]) + star["phase"])))
            self._draw_splash_star(star["x"], star["y"], star["size"], twinkle)

        center_x = width / 2
        moon_y = height * 0.44
        moon_radius = min(width, height) * 0.18
        moon_pop = self._ease_out_cubic(min(1.0, elapsed / 1.0))
        moon_r = moon_radius * (0.85 + (0.15 * moon_pop))
        self.canvas.create_oval(
            center_x - moon_r,
            moon_y - moon_r,
            center_x + moon_r,
            moon_y + moon_r,
            fill="#F7EFD0",
            outline="",
        )
        crater_specs = (
            (-0.58, -0.22, 0.12),
            (-0.44, 0.34, 0.09),
            (0.46, -0.18, 0.10),
            (0.57, 0.03, 0.12),
            (0.42, 0.26, 0.08),
        )
        for dx, dy, radius_ratio in crater_specs:
            crater_r = moon_r * radius_ratio
            cx = center_x + (moon_r * dx)
            cy = moon_y + (moon_r * dy)
            self.canvas.create_oval(
                cx - crater_r,
                cy - crater_r,
                cx + crater_r,
                cy + crater_r,
                fill="#DCCEA0",
                outline="",
            )

        rocket_progress = min(1.0, elapsed / 1.35)
        rocket_eased = self._ease_out_cubic(rocket_progress)
        rocket_start_x = width * 0.46
        rocket_end_x = width * 0.50
        rocket_x = rocket_start_x + ((rocket_end_x - rocket_start_x) * rocket_eased)
        rocket_x += math.sin(rocket_progress * math.pi) * (width * 0.018)
        rocket_start_y = height + 140
        rocket_end_y = (moon_y + moon_r) - (height * 0.02)
        rocket_y = rocket_start_y - ((rocket_start_y - rocket_end_y) * rocket_eased)
        rocket_scale = 0.75 + (0.20 * rocket_eased)
        flame_scale = max(0.0, 1.0 - (rocket_progress * 0.60))
        self._draw_splash_rocket(rocket_x, rocket_y, rocket_scale, flame_scale)

        orbit_progress = self._ease_in_out(max(0.0, min(1.0, (elapsed - 0.9) / 0.9)))
        if orbit_progress > 0:
            orbit_extent = 260 * orbit_progress
            self.canvas.create_arc(
                center_x - (moon_r * 1.28),
                moon_y - (moon_r * 0.34),
                center_x + (moon_r * 1.28),
                moon_y + (moon_r * 0.98),
                start=210,
                extent=orbit_extent,
                style="arc",
                outline="#FFFFFF",
                width=6,
            )

        title_progress = self._ease_out_cubic(max(0.0, min(1.0, (elapsed - 0.95) / 0.9)))
        if title_progress > 0:
            title_size = int(max(34, min(88, (min(width, height) * 0.078) * (0.72 + (0.28 * title_progress)))))
            shadow_offset = max(3, int(title_size * 0.07))
            title_y = moon_y - (moon_r * 0.05)
            self.canvas.create_text(
                center_x - shadow_offset,
                title_y + shadow_offset,
                text="Math\nGame",
                font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
                fill="#FFFFFF",
                justify="center",
            )
            self.canvas.create_text(
                center_x,
                title_y,
                text="Math\nGame",
                font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
                fill="#2E2C37",
                justify="center",
            )
            subtitle_size = max(12, int(title_size * 0.26))
            self.canvas.create_text(
                center_x,
                moon_y + (moon_r * 0.82),
                text="Ready for launch",
                font=(FONT_FAMILY_UI, subtitle_size, "bold"),
                fill="#FFF8DD",
            )

        self.canvas.create_text(
            center_x,
            height - 46,
            text="SynCraft Solution",
            font=(FONT_FAMILY_UI, 11, "bold"),
            fill="#D4D8F7",
        )

        if elapsed < 2.7:
            self.splash_animation_job = self.root.after(33, self._render_splash_frame)
        else:
            self.splash_animation_job = None

    def show_splash_screen(self):
        self._cancel_splash_animation()
        for widget in self.root.winfo_children():
            widget.destroy()

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=SPLASH_BG_COLOR)
        self.canvas.pack(fill="both", expand=True)
        self.splash_started_at = time.time()
        self.splash_starfield = []
        self.splash_starfield_size = None
        self._render_splash_frame()
        self.splash_finish_job = self.root.after(2800, self.show_start_screen)

    def play_video_frame(self):
        ret, frame = self.video_cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            
            canvas_width = max(self.canvas.winfo_width(), 1)
            canvas_height = max(self.canvas.winfo_height(), 1)

            frame_w, frame_h = img.size
            scale = min(canvas_width / frame_w, canvas_height / frame_h)
            target_w = max(1, int(frame_w * scale))
            target_h = max(1, int(frame_h * scale))
            img_resized = img.resize((target_w, target_h), Image.Resampling.BILINEAR)
            self.video_photo = ImageTk.PhotoImage(image=img_resized)
            
            self.canvas.delete("all")
            self.canvas.configure(bg=SPLASH_BG_COLOR)
            self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.video_photo, anchor="center")
            
            self.root.after(self.video_delay, self.play_video_frame)
        else:
            self.video_cap.release()
            self.show_start_screen()

    def _show_legacy_start_screen(self):
        self._cancel_splash_animation()
        self.game_active = False
        # Reset any special mode flags when returning home
        self.is_t20_mode = False
        if self._start_screen_resize_job is not None:
            self.root.after_cancel(self._start_screen_resize_job)
            self._start_screen_resize_job = None
        # Destroy everything in root before rebuilding the start screen.
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create a fresh, resize-aware canvas for the start screen.
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self._bg_cache_size = None
        self._bg_cache_photo = None

        self._start_screen_widgets = {
            "admin_btn": self._create_glossy_button(
                text="Admin Login",
                callback=self.admin_login,
                width=19,
                font=(FONT_FAMILY_UI, 16, "bold"),
                parent=self.root,
                variant="amber",
            ),
            "student_btn": self._create_glossy_button(
                text="Student Login",
                callback=self.student_login,
                width=19,
                font=(FONT_FAMILY_UI, 16, "bold"),
                parent=self.root,
                variant="amber",
            ),
            "guest_btn": self._create_glossy_button(
                text="Guest Login (T20)",
                callback=self.start_t20_flow,
                width=19,
                font=(FONT_FAMILY_UI, 16, "bold"),
                parent=self.root,
                variant="amber",
            ),
        }

        self.canvas.bind("<Configure>", self._schedule_start_screen_layout)
        self._layout_start_screen()

    def show_start_screen(self):
        self._cancel_splash_animation()
        self.game_active = False
        self.is_t20_mode = False

        if callable(run_qt_portal):
            try:
                self.root.withdraw()
                selected_action = run_qt_portal()
            except Exception:
                selected_action = "__fallback__"
            finally:
                if self.root.winfo_exists():
                    self.root.deiconify()
                    try:
                        self.root.lift()
                        self.root.focus_force()
                    except tk.TclError:
                        pass

            if selected_action == "admin":
                self.admin_login()
                return
            if selected_action == "student":
                self.student_login()
                return
            if selected_action == "guest":
                self.start_t20_flow()
                return
            if selected_action is None:
                self.root.destroy()
                return

        self._show_legacy_start_screen()

    # ------- Admin Login Flow --------

    def admin_login(self) -> None:
        """Switches to the formal LoginScreen UI specifically for Admin access"""
        self.canvas.destroy()
        # Call the class you already have to render that dark-themed card
        LoginScreen(
            self.root,
            on_login_success=self.handle_admin_auth_success,
            on_back=self.show_start_screen,
            heading_text="Admin Login",
        )

    def handle_admin_auth_success(self, user):
        if user["role"] == "admin":
            show_admin_panel(
            self.root,
            user,
            handle_logout=lambda: self.show_login_screen(),
            handle_upload=self.upload_advanced_questions
            )
        else:
            messagebox.showerror(
            "Access Denied",
            "This portal is restricted to Administrators."
            )
    

    def show_login_screen(self):
        clear_root(self.root)
        LoginScreen(
        self.root,
        on_login_success=self.handle_admin_auth_success,
        on_back=self.show_start_screen,
        heading_text="Admin Login",
        )

    def student_login(self):
        clear_root(self.root)
        LoginScreen(
            self.root,
            on_login_success=self.handle_student_auth_success,
            on_back=self.show_start_screen,
            heading_text="Student Login",
        )

    def open_my_profile(self):
        """
        Allows the logged-in student to view their own mastery metrics.
        """
        
        # 1. Get current student info from the session
        # Assuming self.current_user stores the dict returned by login_user()
        student_id = self.current_user.get("student_id")
        
        if not student_id:
            print("Error: No student session found.")
            return

        # 2. Fetch data (This is the same logic the Admin uses)
        analytics_data = get_detailed_analytics(student_id)
        
        # 3. Package identity info for the UI header
        # We can pull the name from the current_user or a greeting label
        student_info = {
            "id": student_id,
            "name": getattr(self, "student_name", "Student"), 
            "login_id": getattr(self, "student_login_id", "N/A")
        }
        
        # 4. Open the window (Reusing the class we built!)
        DetailedAnalyticsWindow(self.root, student_info, analytics_data, viewer_mode="student")

    def add_profile_icon(self):
        """Adds the profile button to the header"""
        profile_btn = tk.Button(
            self.student_header_frame, 
            text="My Progress", 
            command=self.open_my_profile, # The function we wrote earlier
            font=("Segoe UI", 10, "bold"),
            bg="#34495e",
            fg="white",
            activebackground="#1abc9c",
            cursor="hand2",
            relief="flat",
            padx=15
        )
        profile_btn.pack(side="right", padx=20, pady=10)

    def handle_student_auth_success(self, user):
        if user["role"] == "student":
            self.current_user = user
            student_id = user.get("student_id")
            
            # Fetch the row from the students table
            student_row = get_student(student_id) if student_id else None
            
            # --- FIX START ---
            if student_row:
                # Access by key name 'name' instead of index [1]
                # student_row is likely a sqlite3.Row or a dict now
                try:
                    self.student_name = student_row['name']
                except (KeyError, TypeError):
                    # Fallback if it's a standard tuple
                    self.student_name = student_row[1] if len(student_row) > 1 else "Student"
            else:
                self.student_name = "Student"
            # --- FIX END ---

            self.student_login_id = user.get("login_id", "N/A")
            self.show_operation_screen()
        else:
            messagebox.showerror(
                "Access Denied",
                "This portal is restricted to Students."
            )

#------- Operation Selection Screen --------
    def _create_operation_page(self, page_num):
        self.clear_screen()
        self.draw_bg()
        center_x = self._sx(300)
        profile_btn = self._create_back_button(
        text="My Progress",
        callback=self.open_my_profile,
        width=16,
        font=(FONT_FAMILY_UI, 10, "bold")
    )
    # Positioning in the top-right corner of your canvas
        self.canvas.create_window(self._sx(520), 40, window=profile_btn)
        chevron_font_family = _pick_font_family(
            self.root,
            ("Segoe UI Symbol", "Arial Unicode MS", FONT_FAMILY_UI, "Arial"),
        )
        self.canvas.create_text(center_x, 100, text="Select Math Operation", font=(FONT_FAMILY_UI, 20, "bold"), fill="white")

        all_ops = [
            "Addition", "Subtraction", "Multiplication", "Division", "Mixed",
            "Squares", "Cubes", "Square Root", "Cube Root", "T20 Test", "Advance Maths Quiz"
        ]
        
        if page_num == 0:
            start_index = 0
            end_index = 5
        else:
            start_index = page_num * 5
            end_index = start_index + 6

        ops_to_display = all_ops[start_index:end_index]

        start_y = 170
        spacing = 70
        
        # Keep track of the last y position for the home button
        last_y = start_y 

        for i, op in enumerate(ops_to_display):
            y_pos = start_y + (i * spacing)
            if op == "Advance Maths Quiz":
                btn = self._create_glossy_button(
                    text="Advance Maths Quiz",
                    callback=self.start_advanced_quiz,
                    width=20,
                    font=(FONT_FAMILY_UI, 14, "bold"),
                    variant="blue",
                )
            elif op == "T20 Test":
                btn = self._create_glossy_button(
                    text="T20 Test",
                    callback=self.start_student_t20_flow,
                    width=20,
                    font=(FONT_FAMILY_UI, 14, "bold"),
                    variant="blue",
                )
            else:
                btn = self._create_glossy_button(
                    text=op,
                    callback=lambda o=op: self.select_op(o),
                    width=20,
                    font=(FONT_FAMILY_UI, 14, "bold"),
                    variant="blue",
                )
            self.canvas.create_window(center_x, y_pos, window=btn)
            last_y = y_pos

        # Navigation arrows
        if page_num > 0:
            prev_btn = self._create_glossy_button(
                text="\u276E",
                callback=lambda: self._create_operation_page(page_num - 1),
                width=3,
                font=(chevron_font_family, 20, "bold"),
                variant="blue",
            )
            self.canvas.create_window(self._sx(50), 400, window=prev_btn)

        if end_index < len(all_ops):
            next_btn = self._create_glossy_button(
                text="\u276F",
                callback=lambda: self._create_operation_page(page_num + 1),
                width=3,
                font=(chevron_font_family, 20, "bold"),
                variant="blue",
            )
            self.canvas.create_window(self._sx(550), 400, window=next_btn)
        
        # Back to Home button
        home_btn = self._create_glossy_button(
            text="Back to Home",
            callback=self.show_start_screen,
            width=20,
            font=(FONT_FAMILY_UI, 14, "bold"),
            variant=NAV_BACK_GLOSSY_VARIANT,
        )
        self.canvas.create_window(center_x, last_y + spacing + 20, window=home_btn)




    def show_operation_screen(self):
        self.clear_screen()
        
        # 1. Initialize the missing attribute!
        self.student_header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        self.student_header_frame.pack(fill="x", side="top")
        self.student_header_frame.pack_propagate(False) # Keep fixed height

        # 2. Add the Student Name/Greeting on the left
        tk.Label(
            self.student_header_frame, 
            text=f"Welcome, {getattr(self, 'student_name', 'Student')}", 
            fg="white", bg="#2c3e50", font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=20, pady=15)

        # 3. NOW add the profile button
        self.add_profile_icon()

        # 4. Continue with your existing page logic
        self._create_operation_page(0)


    # -------- Admin: upload questions --------

    def upload_advanced_questions(self):
        """Simple admin UI to manage advanced question files stored in the DB.

        - Shows last uploaded TXT files (from the files table).
        - Lets admin upload one or more new TXT files.
        - Lets admin delete a file from the DB (soft delete).
        - Lets admin set any uploaded file as the active questions file.
        """

        manage_window = tk.Toplevel(self.root)
        manage_window.title("Manage Advanced Question Files")
        manage_window.geometry("900x560")
        manage_window.minsize(760, 500)
        manage_window.resizable(True, True)
        manage_window.transient(self.root)
        manage_window.grab_set()
        color_bg = "#EEF3F9"
        color_surface = "#FFFFFF"
        color_surface_soft = "#F6F9FD"
        color_text = "#13253F"
        color_muted = "#5C6F8A"
        color_border = "#D7E1EF"
        color_primary = "#2F6FB4"
        color_primary_active = "#285F99"
        color_success = APP_ACCENT_COLOR
        color_success_active = "#439A46"
        color_danger = "#C64A4A"
        color_danger_active = "#A23D3D"
        color_neutral = "#4E607A"
        color_neutral_active = "#44556D"
        manage_window.configure(bg=color_bg)

        wrapper = tk.Frame(manage_window, bg=color_bg, padx=16, pady=14)
        wrapper.pack(fill="both", expand=True)

        tk.Label(
            wrapper,
            text="Manage Advanced Question Files",
            font=(FONT_FAMILY_TEXT, 16, "bold"),
            bg=color_bg,
            fg=color_text,
        ).pack(anchor="w")
        tk.Label(
            wrapper,
            text="Upload TXT files and choose which one to use for the advanced quiz.",
            fg=color_muted,
            bg=color_bg,
            font=(FONT_FAMILY_TEXT, 10),
        ).pack(anchor="w", pady=(2, 12))

        card = tk.Frame(
            wrapper,
            bg=color_surface,
            bd=0,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_border,
        )
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        list_frame = tk.Frame(card, bg=color_surface)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        db_list = tk.Listbox(
            list_frame,
            exportselection=False,
            activestyle="none",
            font=(FONT_FAMILY_TEXT, 11),
            bg=color_surface_soft,
            fg=color_text,
            selectbackground=color_primary,
            selectforeground="white",
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_primary,
            relief="flat",
        )
        db_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=db_list.yview)
        db_list.configure(yscrollcommand=db_scroll.set)
        db_list.grid(row=0, column=0, sticky="nsew")
        db_scroll.grid(row=0, column=1, sticky="ns", padx=(8, 0))

        status_label = tk.Label(card, text="", fg=color_muted, bg=color_surface, font=(FONT_FAMILY_TEXT, 10))
        status_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        def create_manage_button(parent, text, command, *, tone="neutral", width=12):
            palette = {
                "primary": (color_primary, color_primary_active),
                "success": (color_success, color_success_active),
                "danger": (color_danger, color_danger_active),
                "neutral": (color_neutral, color_neutral_active),
            }
            bg, active_bg = palette.get(tone, palette["neutral"])
            return tk.Button(
                parent,
                text=text,
                command=lambda: (sound_manager.play_button_sound(), command()),
                width=width,
                font=(FONT_FAMILY_UI, 10, "bold"),
                bg=bg,
                fg="white",
                activebackground=active_bg,
                activeforeground="white",
                relief="raised",
                bd=1,
                padx=10,
                pady=7,
                cursor="hand2",
                highlightthickness=0,
            )

        db_files = []  # cache of dict rows

        def refresh_db_files():
            nonlocal db_files
            db_list.delete(0, tk.END)
            try:
                db_files = get_all_files()
            except Exception as exc:
                db_files = []
                status_label.config(text=f"Error loading DB files: {exc}", fg=color_danger)
                return

            if not db_files:
                status_label.config(text="No uploaded files yet. Use 'Upload TXT...' to add one.", fg=color_muted)
                return

            for row in db_files:
                label = row.get("filename") or row.get("id")
                db_list.insert(tk.END, label)

            status_label.config(text=f"Loaded {len(db_files)} file(s) from database.", fg=color_primary)

        def current_db_row():
            sel = db_list.curselection()
            if not sel:
                return None
            idx = sel[0]
            return db_files[idx] if 0 <= idx < len(db_files) else None

        def handle_set_active_from_db():
            row = current_db_row()
            if not row:
                messagebox.showerror("Select File", "Please select a file from the list.", parent=manage_window)
                return
            try:
                full_row = get_file_by_id(row["id"])
                if not full_row:
                    messagebox.showerror("Error", "File not found in database.", parent=manage_window)
                    return

                # Save content to a temp TXT file in assets so we can
                # reuse the existing load_advanced_questions_from_file logic.
                tmp_dir = os.path.join(PROJECT_ROOT, "assets")
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_path = os.path.join(tmp_dir, full_row["filename"])
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(full_row["file_content"])

                self.load_advanced_questions_from_file(tmp_path)
                self.advanced_questions_file = tmp_path
                status_label.config(text=f"Active questions file set from DB: {full_row['filename']}", fg=color_primary)
                messagebox.showinfo("Active File Updated", f"Now using: {full_row['filename']}", parent=manage_window)
            except Exception as exc:
                messagebox.showerror("Error", f"Could not load DB file.\n{exc}", parent=manage_window)

        def handle_multi_upload():
            file_paths = filedialog.askopenfilenames(
                parent=manage_window,
                title="Select TXT file(s) to upload",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            )
            if not file_paths:
                return

            uploaded = 0
            failed = 0
            for path in file_paths:
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    filename = os.path.basename(path)
                    upload_file(filename, content, file_type="questions", description=None)
                    uploaded += 1
                except Exception as exc:
                    print(f"Error uploading {path}: {exc}")
                    failed += 1

            refresh_db_files()
            status_label.config(
                text=f"Uploaded {uploaded} file(s); {failed} failed.",
                fg=color_primary if failed == 0 else color_danger,
            )

        def handle_delete_db_file():
            row = current_db_row()
            if not row:
                messagebox.showerror("Select File", "Select a file to delete.", parent=manage_window)
                return

            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Soft-delete this file from DB?\n\n{row.get('filename') or row.get('id')}",
                parent=manage_window,
            )
            if not confirm:
                return

            try:
                ok = soft_delete_file(row["id"])
            except Exception as exc:
                messagebox.showerror("Error", f"Could not delete file.\n{exc}", parent=manage_window)
                return

            if not ok:
                messagebox.showerror("Error", "File not found or already deleted.", parent=manage_window)
                return

            refresh_db_files()
            status_label.config(text="File soft-deleted from DB.", fg=color_primary)

        # Buttons row
        buttons = tk.Frame(card, bg=color_surface)
        buttons.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        buttons.columnconfigure(3, weight=1)

        create_manage_button(buttons, "Use Selected", handle_set_active_from_db, tone="primary", width=14).grid(
            row=0, column=0, sticky="w"
        )
        create_manage_button(buttons, "Upload TXT...", handle_multi_upload, tone="success", width=14).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        create_manage_button(buttons, "Delete", handle_delete_db_file, tone="danger", width=10).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        create_manage_button(buttons, "Close", manage_window.destroy, tone="neutral", width=10).grid(
            row=0, column=4, sticky="e"
        )

        refresh_db_files()

    # -------- Advanced Maths quiz (MCQ) flow --------

    def _stop_advanced_quiz_timer(self):
        self.timer_running = False
        if self.advanced_quiz_timer_job is not None:
            try:
                self.root.after_cancel(self.advanced_quiz_timer_job)
            except tk.TclError:
                pass
            self.advanced_quiz_timer_job = None

    def exit_advanced_quiz(self):
        self._stop_advanced_quiz_timer()
        self.advanced_screen_ready = False
        self.show_operation_screen()

    def advance_math_quiz_timer(self):
        if not getattr(self, "timer_running", False):
            self.advanced_quiz_timer_job = None
            return

        elapsed_time = int(time.time() - self.quiz_start_time)

        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        formatted = f"{minutes:02}:{seconds:02}"

        timer_label = getattr(self, "timer_label", None)
        if timer_label is not None:
            try:
                # Support both Tk widgets and canvas text items for timer UI.
                if isinstance(timer_label, int):
                    self.canvas.itemconfig(timer_label, text=formatted)
                elif timer_label.winfo_exists():
                    timer_label.config(text=formatted)
            except tk.TclError:
                pass

        self.advanced_quiz_timer_job = self.root.after(1000, self.advance_math_quiz_timer)

    def start_advanced_quiz(self):
        """Entry point for students when they click Advance Maths."""

        self._cancel_game_start_countdown()
        self._stop_advanced_quiz_timer()
        self.timer_label = None
        self.advanced_screen_ready = False
        self.advanced_question_item = None
        self.advanced_question_counter_item = None
        self.advanced_score_item = None
        self.advanced_progress_fill_item = None
        self.advanced_feedback_item = None
        self.advanced_option_buttons = []
        self.advanced_back_button = None

        # Make sure bubble game is not running
        self.game_active = False

        if not self.advanced_questions:
            messagebox.showinfo(
                "No Questions",
                "No advanced questions available. Please ask admin to upload the TXT file.",
            )
            return

        # Reset quiz state
        self.timer_running = False
        self.quiz_start_time = None
        self.current_advanced_index = 0
        self.advanced_score = 0

        self.attempted_questions = len(self.advanced_questions)

        self.clear_screen()
        self.draw_bg()
        self.canvas.create_text(
            self._sx(300),
            self._sy(140),
            text="Advanced Maths Quiz",
            font=(FONT_FAMILY_UI, 24, "bold"),
            fill="white",
        )
        self.canvas.create_text(
            self._sx(300),
            self._sy(185),
            text="Get ready...",
            font=(FONT_FAMILY_UI, 14),
            fill="#AFC6DC",
        )
        self._show_pre_game_countdown(on_complete=self._launch_advanced_quiz_round)

    def _launch_advanced_quiz_round(self):
        self.timer_running = True
        self.quiz_start_time = time.time()
        self.show_advanced_question()
        self.advance_math_quiz_timer()

    def show_advanced_question(self):
        # Keep static HUD and background persistent to avoid flash between questions.
        for btn in getattr(self, "advanced_option_buttons", []):
            if btn is not None:
                try:
                    if btn.winfo_exists():
                        btn.destroy()
                except tk.TclError:
                    pass
        self.advanced_option_buttons = []

        if hasattr(self, "canvas") and self.canvas.winfo_exists() and self.advanced_screen_ready:
            self.canvas.delete("advanced_dynamic")
        else:
            self.clear_screen()
            self.draw_bg()
            self.advanced_screen_ready = True

        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        if canvas_w <= 1:
            canvas_w = 600
        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 1:
            canvas_h = 800
        center_x = self._sx(300)

        if self.timer_label is None:
            elapsed_time = int(time.time() - self.quiz_start_time) if self.quiz_start_time else 0
            timer_mins, timer_secs = divmod(elapsed_time, 60)
            timer_text = f"{timer_mins:02}:{timer_secs:02}"
            timer_center_x = self._sx(520)
            timer_center_y = 60
            timer_box_w = max(130, int(150 * self._canvas_scale_y()))
            timer_box_h = max(44, int(54 * self._canvas_scale_y()))
            box_x1 = timer_center_x - (timer_box_w // 2)
            box_y1 = timer_center_y - (timer_box_h // 2)
            box_x2 = timer_center_x + (timer_box_w // 2)
            box_y2 = timer_center_y + (timer_box_h // 2)
            self.canvas.create_rectangle(
                box_x1,
                box_y1,
                box_x2,
                box_y2,
                fill="#050608",
                outline="#1D232C",
                width=2,
                tags=("advanced_static",),
            )
            timer_font_family = _pick_font_family(
                self.root,
                ("DS-Digital", "Digital-7", "Digital-7 Mono", FONT_FAMILY_MONO, "Courier New"),
            )
            timer_font_size = max(20, self._sy(26))
            self.timer_label = self.canvas.create_text(
                timer_center_x,
                timer_center_y,
                text=timer_text,
                font=(timer_font_family, timer_font_size, "bold"),
                fill="#FF2B2B",
                anchor="center",
                justify="center",
                tags=("advanced_static",),
            )

            # Static header/HUD gets created once.
            self.canvas.create_text(
                center_x,
                60,
                text="Advance Maths Quiz",
                font=(FONT_FAMILY_UI, 22, "bold"),
                fill="white",
                tags=("advanced_static",),
            )
            self.advanced_question_counter_item = self.canvas.create_text(
                center_x,
                100,
                text="",
                font=(FONT_FAMILY_UI, 14),
                fill="#E0E0E0",
                tags=("advanced_static",),
            )
            self.advanced_score_item = self.canvas.create_text(
                center_x,
                130,
                text="",
                font=(FONT_FAMILY_UI, 14),
                fill="#E0E0E0",
                tags=("advanced_static",),
            )

            bar_x1, bar_y1, bar_x2, bar_y2 = self._sx(100), 150, self._sx(500), 170
            self.canvas.create_rectangle(
                bar_x1,
                bar_y1,
                bar_x2,
                bar_y2,
                fill="#263238",
                outline="",
                tags=("advanced_static",),
            )
            self.advanced_progress_fill_item = self.canvas.create_rectangle(
                bar_x1,
                bar_y1,
                bar_x1,
                bar_y2,
                fill="#4CAF50",
                outline="",
                tags=("advanced_static",),
            )

            back_btn = self._create_back_button(
                text="Back to Operations",
                callback=self.exit_advanced_quiz,
                width=18,
            )
            self.advanced_back_button = back_btn
            self.advanced_back_y = min(640, canvas_h - 45)
            self.canvas.create_window(
                center_x,
                self.advanced_back_y,
                window=back_btn,
                tags=("advanced_static",),
            )

        total = len(self.advanced_questions)
        q_data = self.advanced_questions[self.current_advanced_index]

        # Randomise options for this question while remembering the correct one
        options = q_data["options"][:]
        correct_answer = q_data.get("correct_answer", options[q_data.get("correct_index", 0)])
        random.shuffle(options)
        q_data["options"] = options
        q_data["correct_index"] = options.index(correct_answer)

        # Update progress and score in-place.
        self.canvas.itemconfig(
            self.advanced_question_counter_item,
            text=f"Question {self.current_advanced_index + 1} of {total}",
        )
        self.canvas.itemconfig(
            self.advanced_score_item,
            text=f"Score: {self.advanced_score}",
        )

        progress = (self.current_advanced_index + 1) / total
        bar_x1, bar_y1, bar_x2, bar_y2 = self._sx(100), 150, self._sx(500), 170
        self.canvas.coords(
            self.advanced_progress_fill_item,
            bar_x1,
            bar_y1,
            bar_x1 + int((bar_x2 - bar_x1) * progress),
            bar_y2,
        )

        # Dynamic question layout: long questions get more vertical room automatically.
        question_wrap = max(360, min(560, int(canvas_w * 0.72)))
        self.advanced_question_item = self.canvas.create_text(
            center_x,
            200,
            text=q_data["question"],
            font=(FONT_FAMILY_UI, 16, "bold"),
            fill="white",
            width=question_wrap,
            anchor="n",
            tags=("advanced_dynamic",),
        )
        bbox = self.canvas.bbox(self.advanced_question_item)
        q_bottom = bbox[3] if bbox else 250
        option_start_y = max(290, q_bottom + 24)
        back_y = min(self.advanced_back_y, canvas_h - 45)

        option_count = len(q_data["options"])
        option_button_height = 50
        available_span = max(200, int((back_y - 35) - option_start_y))
        option_step = max(option_button_height + 10, available_span // max(1, option_count))

        option_font_size = 14 if len(q_data["question"]) < 120 else 13
        option_width_chars = max(24, min(34, int((canvas_w * 0.62) / 10)))
        option_wrap = max(280, min(460, int(canvas_w * 0.62)))
        first_option_center_y = option_start_y + (option_button_height // 2)
        options_bottom = first_option_center_y + ((option_count - 1) * option_step) + (option_button_height // 2)
        self.advanced_feedback_y = min(back_y - 35, options_bottom + 28)

        # Options as MCQ buttons
        for idx, opt in enumerate(q_data["options"]):
                btn = tk.Button(
                    self.root,
                    text=opt,
                    font=(FONT_FAMILY_UI, option_font_size),
                    width=option_width_chars,
                    bg="#263238",
                    fg="white",
                    command=lambda i=idx: (sound_manager.play_pop_sound(), self.answer_advanced_question(i)),
                    activebackground="#455A64",
                    activeforeground="white",
                    relief="raised",
                    bd=2,
                    wraplength=option_wrap,
                    justify="center",
                    padx=6,
                    pady=8,
                )
                option_y = first_option_center_y + (idx * option_step)
                self.canvas.create_window(center_x, option_y, window=btn, tags=("advanced_dynamic",))
                self.advanced_option_buttons.append(btn)

        self.advanced_feedback_item = None
        
    def answer_advanced_question(self, selected_index):
        q_data = self.advanced_questions[self.current_advanced_index]
        correct_index = q_data["correct_index"]

        if self.advanced_feedback_item is not None:
            try:
                self.canvas.delete(self.advanced_feedback_item)
            except tk.TclError:
                pass
            self.advanced_feedback_item = None
        
        # Disable further clicks while we show feedback
        for btn in getattr(self, "advanced_option_buttons", []):
            btn.config(state="disabled")

        # Fun inline feedback instead of popups
        if selected_index == correct_index:
            self.advanced_score += 1
            self.advanced_option_buttons[selected_index].config(bg="#2ecc71")
            feedback_text = "Correct! 🎉 Great job!"
            feedback_color = "#2ecc71"
        else:
            self.advanced_option_buttons[selected_index].config(bg="#e74c3c")
            self.advanced_option_buttons[correct_index].config(bg="#2ecc71")
            correct_text = q_data["options"][correct_index]
            feedback_text = f"Nice try! ✅ Correct: {correct_text}"
            feedback_color = "#e74c3c"

        self.advanced_feedback_item = self.canvas.create_text(
            self._sx(300),
            self.advanced_feedback_y,
            text=feedback_text,
            font=(FONT_FAMILY_UI, 14, "bold"),
            fill=feedback_color,
            tags=("advanced_dynamic",),
        )

        # Move to next question or show results after a short pause
        self.current_advanced_index += 1

        def go_next():
            if self.current_advanced_index < len(self.advanced_questions):
                self.show_advanced_question()
            else:
                self.show_advanced_results()

        self.root.after(1200, go_next)

    def show_advanced_results(self):
        # Save quiz result for logged-in students so admins can track progress.
        self._stop_advanced_quiz_timer()
        self.advanced_screen_ready = False

        total = len(self.advanced_questions)

        if hasattr(self, "quiz_start_time") and self.quiz_start_time:
            total_time = time.time() - self.quiz_start_time
        else:
            total_time = 0

        # Calculate average speed
        avg_speed = total_time / total if total > 0 else 0

        minutes = int(total_time) // 60
        seconds = int(total_time) % 60
        formatted_time = f"{minutes:02}:{seconds:02}"

        self._record_student_attempt(
            topic="Advanced Quiz",
            level="MCQ",
            speed=round(avg_speed, 2),
            score=self.advanced_score,
            total_q=total,
        )

        self.clear_screen()
        self.draw_bg()
        canvas = self.canvas
        self.root.update_idletasks()
        canvas_w = max(canvas.winfo_width(), 600)
        canvas_h = max(canvas.winfo_height(), 800)
        center_x = canvas_w // 2

        total = len(self.advanced_questions)
        ratio = (self.advanced_score / total) if total > 0 else 0
        accuracy = ratio * 100

        if ratio == 1:
            summary = "Perfect score! You are a maths pro!"
            accent = "#FFD54F"
            accent_dim = "#F9A825"
            title_color = "#FFF8D6"
        elif ratio >= 0.7:
            summary = "Awesome! Keep it up! You're doing great!"
            accent = "#66BB6A"
            accent_dim = "#2E7D32"
            title_color = "#F1FFF3"
        elif ratio >= 0.4:
            summary = "Good effort! A bit more practice and you'll nail it."
            accent = "#4FC3F7"
            accent_dim = "#1E88E5"
            title_color = "#EAF8FF"
        else:
            summary = "Don't give up! Every question makes you stronger."
            accent = "#FFA726"
            accent_dim = "#EF6C00"
            title_color = "#FFF4E6"

        card_w = max(430, min(580, int(canvas_w * 0.43)))
        card_h = max(520, min(640, int(canvas_h * 0.66)))
        card_x1 = center_x - (card_w // 2)
        card_x2 = center_x + (card_w // 2)
        card_y1 = max(30, ((canvas_h - card_h) // 2) - 20)
        card_y2 = card_y1 + card_h

        # Soft decorative shapes to make the result card less flat.
        canvas.create_oval(
            card_x1 - 70,
            card_y1 - 58,
            card_x1 + 120,
            card_y1 + 118,
            fill="#0C2037",
            outline="",
        )
        canvas.create_oval(
            card_x2 - 120,
            card_y2 - 118,
            card_x2 + 70,
            card_y2 + 58,
            fill="#0A1D31",
            outline="",
        )

        outer_frame = canvas.create_rectangle(
            card_x1 - 6,
            card_y1 - 6,
            card_x2 + 6,
            card_y2 + 6,
            fill="#091221",
            outline=accent_dim,
            width=2,
        )
        canvas.create_rectangle(
            card_x1,
            card_y1,
            card_x2,
            card_y2,
            fill="#101A2B",
            outline="#1A2B43",
            width=2,
        )
        accent_bar = canvas.create_rectangle(
            card_x1 + 24,
            card_y1 + 22,
            card_x2 - 24,
            card_y1 + 32,
            fill=accent,
            outline="",
        )

        title_size = max(24, min(34, int(card_h * 0.060)))
        score_size = max(19, min(28, int(card_h * 0.048)))
        body_size = max(14, min(20, int(card_h * 0.036)))
        meta_size = max(13, min(18, int(card_h * 0.030)))
        summary_width = max(280, card_w - 110)

        subtitle_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.13),
            text="Session Summary",
            font=(FONT_FAMILY_UI, body_size - 1, "bold"),
            fill="#9AB6D6",
            state="hidden",
        )

        title_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.27),
            text="Advanced Maths\nQuiz Completed!",
            font=(FONT_FAMILY_UI, title_size, "bold"),
            fill=title_color,
            width=summary_width + 20,
            justify="center",
            state="hidden",
        )
        score_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.46),
            text=f"Your Score: 0 / {total}",
            font=(FONT_FAMILY_UI, score_size, "bold"),
            fill="white",
            state="hidden",
        )
        summary_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.56),
            text=summary,
            font=(FONT_FAMILY_UI, body_size, "bold"),
            fill="#D7E3FC",
            width=summary_width,
            justify="center",
            state="hidden",
        )
        accuracy_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.66),
            text=f"Accuracy: {accuracy:.0f}%",
            font=(FONT_FAMILY_UI, body_size),
            fill=accent,
            state="hidden",
        )

        stats_x1 = card_x1 + 36
        stats_x2 = card_x2 - 36
        stats_y1 = card_y1 + int(card_h * 0.73)
        stats_y2 = card_y1 + int(card_h * 0.87)
        stats_panel = canvas.create_rectangle(
            stats_x1,
            stats_y1,
            stats_x2,
            stats_y2,
            fill="#0E233D",
            outline="#1F3C64",
            width=1,
            state="hidden",
        )
        time_item = canvas.create_text(
            center_x,
            stats_y1 + int((stats_y2 - stats_y1) * 0.34),
            text=f"Time Taken: {formatted_time}",
            font=(FONT_FAMILY_UI, meta_size),
            fill="#E0E0E0",
            width=summary_width,
            justify="center",
            state="hidden",
        )
        speed_item = canvas.create_text(
            center_x,
            stats_y1 + int((stats_y2 - stats_y1) * 0.72),
            text=f"Average Speed: {avg_speed:.2f} sec/question",
            font=(FONT_FAMILY_UI, meta_size),
            fill="#E0E0E0",
            width=summary_width,
            justify="center",
            state="hidden",
        )

        btn_width = 22
        back_ops_btn = self._create_back_button(
            text="Back to Operations",
            callback=self.show_operation_screen,
            width=btn_width,
            font=(FONT_FAMILY_UI, 12, "bold"),
        )
        back_ops_btn.configure(
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            bg="#2A3B57",
            fg="#E6EDFF",
            activebackground="#3A5378",
            activeforeground="white",
            cursor="hand2",
        )

        back_btn_item = canvas.create_window(
            center_x,
            card_y1 + int(card_h * 0.93),
            window=back_ops_btn,
            state="hidden",
        )

        if ratio >= 0.7:
            self._launch_confetti_burst(center_x, card_y1 + 70)

        reveal_items = [
            subtitle_item,
            title_item,
            score_item,
            summary_item,
            accuracy_item,
            stats_panel,
            time_item,
            speed_item,
            back_btn_item,
        ]

        def animate_score(step=0, total_steps=18):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return
            current_score = round((self.advanced_score * step) / total_steps)
            canvas.itemconfig(score_item, text=f"Your Score: {current_score} / {total}")
            if step < total_steps:
                self.root.after(35, lambda: animate_score(step + 1, total_steps))

        def pop_in(item_id, dy=12, steps=6):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return
            coords = canvas.coords(item_id)
            if len(coords) == 2:
                x, y = coords
                canvas.coords(item_id, x, y + dy)
            else:
                canvas.move(item_id, 0, dy)

            def lift(step=0):
                if canvas is not self.canvas or not canvas.winfo_exists():
                    return
                if step >= steps:
                    return
                canvas.move(item_id, 0, -dy / steps)
                self.root.after(18, lambda: lift(step + 1))

            lift()

        def reveal_next(index=0):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return
            if index >= len(reveal_items):
                return

            item_id = reveal_items[index]
            canvas.itemconfigure(item_id, state="normal")
            pop_in(item_id)

            if item_id == score_item:
                animate_score()

            self.root.after(115, lambda: reveal_next(index + 1))

        def pulse_accent(tick=0):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return
            pulse_colors = (accent, accent_dim, accent)
            frame_colors = (accent_dim, accent, accent_dim)
            canvas.itemconfig(accent_bar, fill=pulse_colors[tick % len(pulse_colors)])
            canvas.itemconfig(outer_frame, outline=frame_colors[tick % len(frame_colors)])
            self.root.after(230, lambda: pulse_accent(tick + 1))

        reveal_next()
        pulse_accent()

    def select_op(self, op):
        self.selected_op = op
        self.show_level_screen()

    # --- SCREEN 3: LEVELS ---
    def show_level_screen(self):
        self.clear_screen()
        self.draw_bg()
        self._glossy_button_cache.clear()
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        if canvas_w <= 1:
            canvas_w = 600
        center_x = canvas_w // 2
        self.canvas.create_text(center_x, 100, text="Select Challenge Mode", font=(FONT_FAMILY_UI, 25, "bold"), fill="white")

        levels = [("Easy", "green"), ("Intermediate", "amber"), ("Expert", "blue")]
        start_y = 250
        spacing = 100
        for i, (lvl, variant) in enumerate(levels):
            btn = self._create_glossy_button(
                text=lvl,
                callback=lambda l=lvl: self.select_level(l),
                width=16,
                font=(FONT_FAMILY_UI, 18, "bold"),
                variant=variant,
            )
            self.canvas.create_window(center_x, start_y + (i * spacing), window=btn)

        # Back button to go to previous (operations) screen
        back_btn = self._create_glossy_button(
            text="Back",
            callback=self.show_operation_screen,
            width=14,
            font=(FONT_FAMILY_UI, 16, "bold"),
            variant=NAV_BACK_GLOSSY_VARIANT,
        )
        last_level_y = start_y + ((len(levels) - 1) * spacing)
        self.canvas.create_window(center_x, last_level_y + 90, window=back_btn)

    def select_level(self, lvl):
        self.selected_level = lvl
        self.show_mode_screen()

    # --- SCREEN 4: TIME CONTROL MODES ---
    def show_mode_screen(self):
        self.clear_screen()
        self.draw_bg()
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        if canvas_w <= 1:
            canvas_w = 600
        center_x = canvas_w // 2
        self.canvas.create_text(center_x, 100, text="Select Time Control", font=(FONT_FAMILY_UI, 25, "bold"), fill="white")

        # 1. Define the time mapping based on your new requirements
        time_data = {
            "Easy": {"Rapid": "26s", "Blitz": "13s", "Bullet": "7s"},
            "Intermediate": {"Rapid": "21s", "Blitz": "10s", "Bullet": "5s"},
            "Expert": {"Rapid": "16s", "Blitz": "7s", "Bullet": "3s"}
        }

        # 2. Get the specific times for the level the user just picked
        level_times = time_data.get(self.selected_level, time_data["Easy"])

        # 3. Create the dynamic labels
        modes = [
            (f"Rapid ({level_times['Rapid']})", "Rapid"),
            (f"Blitz ({level_times['Blitz']})", "Blitz"),
            (f"Bullet ({level_times['Bullet']})", "Bullet")
        ]

        start_y = 250
        spacing = 100
        for i, (label, mode_val) in enumerate(modes):
            btn = self._create_glossy_button(
                text=label,
                callback=lambda m=mode_val: self.start_actual_game(m),
                width=15,
                font=(FONT_FAMILY_UI, 16, "bold"),
                variant="blue",
            )
            self.canvas.create_window(center_x, start_y + (i * spacing), window=btn)

        # Back button
        back_btn = self._create_glossy_button(
            text="Back",
            callback=self.show_level_screen,
            width=15,
            font=(FONT_FAMILY_UI, 16, "bold"),
            variant=NAV_BACK_GLOSSY_VARIANT,
        )
        last_mode_y = start_y + ((len(modes) - 1) * spacing)
        self.canvas.create_window(center_x, last_mode_y + 90, window=back_btn)


    def select_level(self, lvl):
        self.selected_level = lvl
        self.show_sub_level_screen() # New screen for 1-8

    def show_sub_level_screen(self):
        self.clear_screen()
        self.draw_bg()
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        if canvas_w <= 1:
            canvas_w = 600
        center_x = canvas_w // 2
        self.canvas.create_text(center_x, 80, text=f"{self.selected_level}: Select Level", font=(FONT_FAMILY_UI, 25, "bold"), fill="white")

        # Define sub-levels based on your mapping
        if self.selected_op in ["Addition", "Subtraction"]:
            if self.selected_level == "Easy":
                sub_levels = [1, 2, 3, 4]
            elif self.selected_level == "Intermediate":
                sub_levels = [5, 6]
            else:
                sub_levels = [7, 8]  # Expert
        elif self.selected_op in ["Multiplication", "Division" , "Mixed"]:
            if self.selected_level == "Easy":
                sub_levels = [1, 2]
            elif self.selected_level == "Intermediate":
                sub_levels = [3]
            else:
                sub_levels = [4]  # Expert
        else:
            #  Squares, Cubes, Square Root, Cube Root
            sub_levels = [1, 2, 3, 4]

        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 1:
            canvas_h = 800

        level_buttons = []
        for sl in sub_levels:
            btn = self._create_glossy_button(
                text=f"Level {sl}",
                callback=lambda s=sl: self.select_sub_level(s),
                width=15,
                font=(FONT_FAMILY_UI, 16, "bold"),
                variant="blue",
            )
            level_buttons.append(btn)

        button_height = max((btn.winfo_reqheight() for btn in level_buttons), default=self._sy(58))
        button_gap = max(self._sy(18), 14)
        spacing_y = button_height + button_gap
        start_y = self._sy(200)

        if len(level_buttons) > 1:
            max_last_level_y = canvas_h - self._sy(180)
            needed_last_level_y = start_y + ((len(level_buttons) - 1) * spacing_y)
            if needed_last_level_y > max_last_level_y:
                available_span = max_last_level_y - start_y
                spacing_y = max(button_height + 8, available_span // (len(level_buttons) - 1))

        for i, btn in enumerate(level_buttons):
            self.canvas.create_window(center_x, start_y + (i * spacing_y), window=btn)

        back_btn = self._create_glossy_button(
            text="Back",
            callback=self.show_level_screen,
            width=15,
            font=(FONT_FAMILY_UI, 16, "bold"),
            variant=NAV_BACK_GLOSSY_VARIANT,
        )
        last_level_y = start_y + ((len(level_buttons) - 1) * spacing_y)
        back_gap = max(self._sy(95), button_height + button_gap + 12)
        back_y = min(last_level_y + back_gap, canvas_h - self._sy(70))
        self.canvas.create_window(center_x, back_y, window=back_btn)

    def select_sub_level(self, sl):
        self.selected_sub_level = sl
        self.show_mode_screen() # Now move to time control screen

    def _cancel_game_start_countdown(self):
        if self.game_start_countdown_job is not None:
            try:
                self.root.after_cancel(self.game_start_countdown_job)
            except tk.TclError:
                pass
            self.game_start_countdown_job = None
        self.game_start_countdown_canvas = None
        self.game_start_countdown_photo = None
    def _get_countdown_character_photo(self, token, scale=1.0):
        token = str(token).upper()
        target = max(120, int(220 * scale))
        key = (token, int(target))
        cached = self.countdown_character_cache.get(key)
        if cached is not None:
            return cached

        supersample = 3
        canvas_size = int(target * 1.2)
        img_size = canvas_size * supersample
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        def load_font(px_size):
            font_paths = (
                r"C:\Windows\Fonts\comicbd.ttf",
                r"C:\Windows\Fonts\seguisb.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\impact.ttf",
            )
            for path in font_paths:
                try:
                    return ImageFont.truetype(path, px_size)
                except OSError:
                    continue
            return ImageFont.load_default()

        palette = {
            "3": ("#1F58D6", "#122E77"),
            "2": ("#8FEA72", "#3C8C2A"),
            "1": ("#F3F5F7", "#2B2F36"),
            "GO!": ("#59B9EC", "#133E57"),
        }
        fill_color, stroke_color = palette.get(token, ("#59B9EC", "#133E57"))
        text_scale = 0.92 if token in {"1", "2", "3"} else 0.56
        font = load_font(max(48, int(target * text_scale * supersample)))
        stroke_width = max(3, int(4 * supersample))

        bbox = draw.textbbox((0, 0), token, font=font, stroke_width=stroke_width)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (img_size - text_w) // 2 - bbox[0]
        text_y = (img_size - text_h) // 2 - bbox[1]

        draw.text(
            (text_x, text_y),
            token,
            font=font,
            fill=fill_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )

        # Eyes/mouth for digit characters to give the "number character" look.
        if token in {"1", "2", "3"}:
            eye_radius = max(6, int(target * 0.10 * supersample))
            eye_gap = int(eye_radius * 2.2)
            eye_y = int(text_y + text_h * 0.48)
            left_eye_x = (img_size // 2) - (eye_gap // 2)
            right_eye_x = (img_size // 2) + (eye_gap // 2)
            outline_w = max(2, int(2 * supersample))

            for eye_x in (left_eye_x, right_eye_x):
                draw.ellipse(
                    (
                        eye_x - eye_radius,
                        eye_y - eye_radius,
                        eye_x + eye_radius,
                        eye_y + eye_radius,
                    ),
                    fill="#FFFFFF",
                    outline="#111111",
                    width=outline_w,
                )

            pupil_radius = max(3, int(eye_radius * 0.42))
            pupil_offset = {
                "3": (0.22, 0.10),
                "2": (0.08, 0.18),
                "1": (-0.05, 0.12),
            }.get(token, (0.0, 0.12))
            dx = int(pupil_offset[0] * eye_radius)
            dy = int(pupil_offset[1] * eye_radius)
            for eye_x in (left_eye_x, right_eye_x):
                draw.ellipse(
                    (
                        eye_x - pupil_radius + dx,
                        eye_y - pupil_radius + dy,
                        eye_x + pupil_radius + dx,
                        eye_y + pupil_radius + dy,
                    ),
                    fill="#111111",
                )

            mouth_y = eye_y + int(eye_radius * 1.45)
            if token == "3":
                draw.arc(
                    (
                        (img_size // 2) - int(eye_radius * 1.6),
                        mouth_y - int(eye_radius * 0.8),
                        (img_size // 2) + int(eye_radius * 1.6),
                        mouth_y + int(eye_radius * 0.9),
                    ),
                    start=10,
                    end=170,
                    fill="#111111",
                    width=outline_w,
                )
                tongue_w = int(eye_radius * 1.0)
                tongue_h = int(eye_radius * 0.9)
                draw.ellipse(
                    (
                        (img_size // 2) - (tongue_w // 2),
                        mouth_y - int(eye_radius * 0.1),
                        (img_size // 2) + (tongue_w // 2),
                        mouth_y - int(eye_radius * 0.1) + tongue_h,
                    ),
                    fill="#FF6FB2",
                    outline="#111111",
                    width=max(1, outline_w - 1),
                )
            elif token == "2":
                draw.arc(
                    (
                        (img_size // 2) - int(eye_radius * 1.7),
                        mouth_y - int(eye_radius * 0.7),
                        (img_size // 2) + int(eye_radius * 1.7),
                        mouth_y + int(eye_radius * 0.8),
                    ),
                    start=20,
                    end=165,
                    fill="#111111",
                    width=outline_w,
                )
            else:
                draw.arc(
                    (
                        (img_size // 2) - int(eye_radius * 1.1),
                        mouth_y - int(eye_radius * 0.7),
                        (img_size // 2) + int(eye_radius * 1.1),
                        mouth_y + int(eye_radius * 0.3),
                    ),
                    start=200,
                    end=350,
                    fill="#111111",
                    width=outline_w,
                )

        resampling = getattr(Image, "Resampling", Image)
        img = img.resize((canvas_size, canvas_size), resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.countdown_character_cache[key] = photo
        return photo

    def _start_main_game_loop(self):
        if self.game_active:
            return
        self.game_active = True
        self.spawn_asteroid(self.current_sub_level)
        self.update_animation()
        self.update_game_clock()

    def _show_pre_game_countdown(self, on_complete=None):
        self._cancel_game_start_countdown()
        canvas = self.canvas
        if not canvas.winfo_exists():
            return

        self.root.update_idletasks()
        canvas_w = max(canvas.winfo_width(), 600)
        canvas_h = max(canvas.winfo_height(), 800)
        center_x = canvas_w // 2
        center_y = (canvas_h // 2) - 40

        glow = canvas.create_oval(
            center_x - 108,
            center_y - 106,
            center_x + 108,
            center_y + 110,
            fill="#14273D",
            outline="",
        )
        character_icon = canvas.create_image(center_x, center_y + 15, image="")

        # Stronger zoom-in/zoom-out pulse per number.
        scale_steps = (0.58, 0.74, 0.92, 1.12, 1.30, 1.12, 0.90)
        frames = []
        for value in ("3", "2", "1"):
            for scale in scale_steps:
                frames.append((value, scale))
        for scale in (0.88, 1.08, 1.28, 1.08, 0.94):
            frames.append(("GO!", scale))

        countdown_items = (glow, character_icon)
        self.game_start_countdown_canvas = canvas
        frame_index = 0

        def animate():
            nonlocal frame_index
            if self.game_start_countdown_canvas is not canvas or canvas is not self.canvas or not canvas.winfo_exists():
                self._cancel_game_start_countdown()
                return

            if frame_index >= len(frames):
                for item_id in countdown_items:
                    try:
                        canvas.delete(item_id)
                    except tk.TclError:
                        pass
                self._cancel_game_start_countdown()
                if callable(on_complete):
                    on_complete()
                else:
                    self._start_main_game_loop()
                return

            value, scale = frames[frame_index]
            photo = self._get_countdown_character_photo(value, scale)
            self.game_start_countdown_photo = photo

            glow_radius = int(96 * scale)
            canvas.coords(
                glow,
                center_x - glow_radius,
                center_y - glow_radius,
                center_x + glow_radius,
                center_y + glow_radius,
            )
            canvas.itemconfig(character_icon, image=photo)
            frame_index += 1
            self.game_start_countdown_job = self.root.after(120, animate)

        animate()

    # --- UPDATED START GAME ---
    def start_actual_game(self, mode):
        self._cancel_game_start_countdown()
        self.game_active = False
        self.score = 0
        self.time_left = 180
        self.asteroids = []
        self.questions_attempted = 0
        
        # 1. Get difficulty timing from MathFactory (NO physics here)
        _, seconds_allowed = MathFactory.get_level_settings(self.selected_level, mode)

        # Clear and redraw screen
        self.clear_screen()
        self.draw_bg()
        self.canvas.addtag_all(self.gameplay_canvas_tag)

        # Ensure geometry is updated
        self.root.update_idletasks()

        # Get real-time canvas size (no hardcoding 600x800)
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w <= 1:
            canvas_w = 600

        # Safety fallback if window hasn't fully rendered yet
        if canvas_h <= 1:
            canvas_h = 800

        # 2. Calculate physics dynamically (30 FPS assumption)
        self.y_speed = canvas_h / (seconds_allowed * (1000 / 30))
        self.spawn_time = seconds_allowed * 1000

        # UI positioning only: keep the HUD in the side gutters when space is available.
        hud_y = self._sy(58)
        hud_edge_pad = max(18, int(canvas_w * 0.02))
        hud_gap = max(14, int(canvas_w * 0.012))

        # Exit button
        exit_btn = self._create_back_button(
            text="Exit",
            callback=self.exit_to_operation_screen,
            width=8,
            font=(FONT_FAMILY_UI, 12, "bold"),
        )
        exit_w = max(exit_btn.winfo_reqwidth(), 84)
        self.canvas.create_window(
            hud_edge_pad,
            hud_y,
            window=exit_btn,
            anchor="w",
            tags=(self.gameplay_canvas_tag,),
        )
        
        # UI: Simple digital timer and score (no gameplay logic changes)
        timer_box_w = max(170, int(190 * self._canvas_scale_y()))
        timer_box_h = max(58, int(68 * self._canvas_scale_y()))
        timer_center_x = hud_edge_pad + exit_w + hud_gap + (timer_box_w // 2)
        timer_center_y = hud_y + 2
        timer_font_family = _pick_font_family(
            self.root,
            ("DS-Digital", "Digital-7", "Digital-7 Mono", FONT_FAMILY_MONO, "Courier New"),
        )
        timer_font_size = max(24, self._sy(34))

        box_x1 = timer_center_x - (timer_box_w // 2)
        box_y1 = timer_center_y - (timer_box_h // 2)
        box_x2 = timer_center_x + (timer_box_w // 2)
        box_y2 = timer_center_y + (timer_box_h // 2)
        self.canvas.create_rectangle(
            box_x1,
            box_y1,
            box_x2,
            box_y2,
            fill="#050608",
            outline="#1D232C",
            width=2,
            tags=(self.gameplay_canvas_tag,),
        )

        self.ui_timer = self.canvas.create_text(
            timer_center_x,
            timer_center_y,
            text="03:00",
            font=(timer_font_family, timer_font_size, "bold"),
            fill="#FF2B2B",
            anchor="center",
            justify="center",
            tags=(self.gameplay_canvas_tag,),
        )
        self.ui_score = self.canvas.create_text(
            canvas_w - hud_edge_pad - 56,
            hud_y + 2,
            text="Score: 0",
            font=(FONT_FAMILY_MONO, 17, "bold"),
            fill="white",
            anchor="e",
            tags=(self.gameplay_canvas_tag,),
        )
        self.ui_question_count = self.canvas.create_text(
            canvas_w - hud_edge_pad - 56,
            hud_y + 26,
            text="Q: 0",
            font=(FONT_FAMILY_MONO, 13, "bold"),
            fill="#C9D6E8",
            anchor="e",
            tags=(self.gameplay_canvas_tag,),
        )

        # Sound mute/unmute toggle button with icons
        def _toggle_sound():
            new_state = sound_manager.toggle_mute()
            self.is_sound_muted = new_state
            icon = "🔇" if new_state else "🔊"
            try:
                self.mute_button.config(text=icon)
            except Exception:
                pass

        self.mute_button = tk.Button(
            self.root,
            text="🔊",
            font=(FONT_FAMILY_UI, 12, "bold"),
            width=3,
            bg="#1F2933",
            fg="#E5E9F0",
            activebackground="#323F4B",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=_toggle_sound,
        )
        mute_w = max(self.mute_button.winfo_reqwidth(), 48)
        self.canvas.coords(self.ui_score, canvas_w - hud_edge_pad - mute_w - hud_gap, hud_y + 2)
        self.canvas.coords(self.ui_question_count, canvas_w - hud_edge_pad - mute_w - hud_gap, hud_y + 26)
        self.canvas.create_window(
            canvas_w - hud_edge_pad,
            hud_y + 2,
            window=self.mute_button,
            anchor="e",
            tags=(self.gameplay_canvas_tag,),
        )
        
        # Buttons
        answer_y = int(max(self._sy(560), min(self._sy(720), canvas_h - self._sy(70))))
        self.answer_y = answer_y
        self.asteroid_miss_y = max(self._sy(650), answer_y - self._sy(40))
        self.answer_btn_normal_bg = "#273A5A"
        self.answer_btn_hover_bg = "#36598A"
        self.answer_btn_disabled_bg = "#1B2740"
        self.buttons = []

        def _set_answer_hover_state(event, is_hovered):
            btn = event.widget
            if str(btn.cget("state")) != "normal":
                return
            btn.config(bg=self.answer_btn_hover_bg if is_hovered else self.answer_btn_normal_bg)

        for i in range(4):
            btn = tk.Button(
                self.root,
                text="-",
                font=(FONT_FAMILY_UI, 15, "bold"),
                width=8,
                bg=self.answer_btn_normal_bg,
                fg="#F4F8FF",
                activebackground=self.answer_btn_hover_bg,
                activeforeground="#FFFFFF",
                disabledforeground="#7E95BA",
                relief="raised",
                bd=2,
                padx=8,
                pady=6,
                cursor="hand2",
                highlightthickness=0,
                command=lambda idx=i: self.process_answer(idx),
            )
            btn.bind("<Enter>", lambda event: _set_answer_hover_state(event, True))
            btn.bind("<Leave>", lambda event: _set_answer_hover_state(event, False))
            self.canvas.create_window(
                self._sx(100 + (i * 130)),
                answer_y,
                window=btn,
                tags=(self.gameplay_canvas_tag,),
            )
            self.buttons.append(btn)
        self.update_buttons()
        
        # 2. Store the sub_level instead of num_range
        # This ensures the digit-based math (1d+1d, 2d*2d) is used
        self.current_sub_level = getattr(self, 'selected_sub_level', 1) 
        self.current_mode = mode
            
        # 3. Show animated countdown, then start the game loop
        self._show_pre_game_countdown()

    def exit_to_operation_screen(self):
        self._cancel_game_start_countdown()
        # 1. Pause the game loops
        self.game_active = False 
        
        # 2. Create the popup window
        popup = tk.Toplevel(self.root)
        popup.title("Quit Game?")
        
        # 3. SET SIZE: Make it bigger (e.g., 400x200)
        width, height = 400, 200
        
        # 4. ALIGN CENTER: Calculate position relative to the main window
        # Get main window position
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        
        # Calculate center
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        pos_x = main_x + (main_w // 2) - (width // 2)
        pos_y = main_y + (main_h // 2) - (height // 2)
        
        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        
        # 5. UI Elements inside the popup
        popup.configure(bg="#2c3e50") # Match your theme
        popup.transient(self.root)

        def close_popup():
            if not popup.winfo_exists():
                return
            try:
                popup.grab_release()
            except tk.TclError:
                pass
            popup.destroy()

        def play_again():
            sound_manager.play_button_sound()
            # Reset burst sound mute & icon for the new run
            try:
                sound_manager.set_muted(False)
            except Exception:
                pass
            self.is_sound_muted = False
            if self.mute_button is not None:
                try:
                    self.mute_button.config(text="🔊")
                except Exception:
                    pass
            close_popup()
            self.start_actual_game(self.current_mode)

        def back_to_menu():
            close_popup()
            self._back_to_menu_after_game()

        def cancel_quit(play_sound=False):
            if play_sound:
                sound_manager.play_button_sound()
            close_popup()
            self.resume_game()

        popup.protocol("WM_DELETE_WINDOW", cancel_quit)
        
        tk.Label(popup, text="Do you wanna Quit?", font=(FONT_FAMILY_UI, 16, "bold"), 
                 bg="#2c3e50", fg="white", pady=10).pack()
        
        tk.Label(popup, text="Game progress will not be saved.", font=(FONT_FAMILY_UI, 12), 
                 bg="#2c3e50", fg="#bdc3c7").pack(pady=5)
        
        # Button Container
        btn_frame = tk.Frame(popup, bg="#2c3e50")
        btn_frame.pack(pady=20)
        
        # Play Again Button
        tk.Button(btn_frame, text="Play Again", width=10, bg="#3ce76d", fg="white", 
                  command=play_again).pack(side="left", padx=10)
        
        # Back To Menu Button
        self._create_back_button(
            text="Back To Menu",
            callback=back_to_menu,
            width=12,
            parent=btn_frame,
        ).pack(side="left", padx=10)
        
        # Cancel Button (Resumes the game)
        tk.Button(btn_frame, text="Cancel", width=10, 
                  command=lambda: cancel_quit(play_sound=True)).pack(side="left", padx=10)

        # Force focus to the popup
        popup.grab_set()
        popup.focus_set()

    def resume_game(self):
        """Helper to restart the loops after canceling a quit."""
        self._cancel_game_start_countdown()
        self._start_main_game_loop()

    def _back_to_menu_after_game(self):
        """Return to the appropriate menu after a game.

                - If we're in T20 mode, always go back to the home screen
                    regardless of any logged-in student.
                - Otherwise, for logged-in students, go back to the operation
                    selection screen (Addition, Subtraction, etc.). For all other
                    cases, go to the main start screen.
        """                
        # Reset burst sound mute state when leaving the game
        try:
            sound_manager.set_muted(False)
        except Exception:
            pass
        self.is_sound_muted = False
        if self.mute_button is not None:
            try:
                self.mute_button.config(text="🔊")
            except Exception:
                pass
        if getattr(self, "is_t20_mode", False):
                        self.is_t20_mode = False
                        self.show_start_screen()
                        return

        user = getattr(self, "current_user", None)
        if user and user.get("role") == "student":
            self.show_operation_screen()
        else:
            self.show_start_screen()

    def update_game_clock(self):
        if self.time_left > 0 and self.game_active:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.canvas.itemconfig(self.ui_timer, text=f"{mins:02d}:{secs:02d}")
            self.root.after(1000, self.update_game_clock) # Update every 1 second
        elif self.time_left <= 0:
            self.end_game()

    def _cancel_screen_shake(self):
        if self.screen_shake_job is not None:
            try:
                self.root.after_cancel(self.screen_shake_job)
            except tk.TclError:
                pass
            self.screen_shake_job = None

        if (
            self.screen_shake_canvas is not None
            and self.screen_shake_canvas.winfo_exists()
            and (self.screen_shake_offset_x or self.screen_shake_offset_y)
        ):
            try:
                self.screen_shake_canvas.move(
                    self.gameplay_canvas_tag,
                    -self.screen_shake_offset_x,
                    -self.screen_shake_offset_y,
                )
            except tk.TclError:
                pass

        self.screen_shake_canvas = None
        self.screen_shake_offset_x = 0
        self.screen_shake_offset_y = 0

    def _trigger_screen_shake(self):
        # Screen shake disabled based on user preference.
        return

    def _create_asteroid_visual(self, center_x, center_y, question_text):
        start_scale = 0.72
        font_family = FONT_FAMILY_MONO
        font_base_size = 18
        min_font_size = 14
        target_inner_width = 120

        measure_font = tkfont.Font(root=self.root, family=font_family, size=font_base_size, weight="bold")
        text_width = measure_font.measure(question_text)
        text_height = measure_font.metrics("linespace")

        while text_width > target_inner_width and font_base_size > min_font_size:
            font_base_size -= 1
            measure_font.configure(size=font_base_size)
            text_width = measure_font.measure(question_text)
            text_height = measure_font.metrics("linespace")

        base_radius = max(
            40,
            int(round((text_width / 2) + 18)),
            int(round((text_height / 2) + 18)),
        )

        glow_radius = int(base_radius * 1.22)
        scaled_radius = base_radius * start_scale
        scaled_glow_radius = glow_radius * start_scale
        start_font_size = max(min_font_size, int(font_base_size * start_scale))

        asteroid_themes = [
            {
                "trail_outer_start": "#311204",
                "trail_outer_end": "#FF7A22",
                "trail_inner_start": "#7D2403",
                "trail_inner_end": "#FFD08C",
                "glow_start": "#5B2200",
                "glow_end": "#FF8F32",
                "fill_start": "#363C48",
                "fill_end": "#616977",
                "outline_start": "#8D97A8",
                "outline_end": "#D5DBE4",
                "highlight_start": "#BCC7D7",
                "highlight_end": "#F6F9FF",
                "lava_start": "#AC2200",
                "lava_end": "#FFBF2C",
                "crater_start": "#1C2230",
                "crater_end": "#394152",
                "txt_back_start": "#08131E",
                "txt_back_end": "#112336",
                "txt_back_outline_start": "#4A657F",
                "txt_back_outline_end": "#87A7C6",
                "txt_shadow_start": "#040A12",
                "txt_shadow_end": "#101B27",
                "txt_start": "#F8FBFF",
                "txt_end": "#FFFFFF",
            },
            {
                "trail_outer_start": "#25120A",
                "trail_outer_end": "#FF9448",
                "trail_inner_start": "#5F2208",
                "trail_inner_end": "#FFE0AA",
                "glow_start": "#6A2D08",
                "glow_end": "#FFB05A",
                "fill_start": "#404550",
                "fill_end": "#727986",
                "outline_start": "#9EA6B4",
                "outline_end": "#E3E8EF",
                "highlight_start": "#CBD4E1",
                "highlight_end": "#FFFFFF",
                "lava_start": "#C23A06",
                "lava_end": "#FFD24A",
                "crater_start": "#242A35",
                "crater_end": "#404958",
                "txt_back_start": "#0A1624",
                "txt_back_end": "#142B40",
                "txt_back_outline_start": "#58728E",
                "txt_back_outline_end": "#9CC0E0",
                "txt_shadow_start": "#050B14",
                "txt_shadow_end": "#122031",
                "txt_start": "#F4F8FF",
                "txt_end": "#FFFFFF",
            },
        ]
        theme = random.choice(asteroid_themes)

        trail_outer = self.canvas.create_oval(
            center_x - (scaled_radius * 0.92),
            center_y - (scaled_radius * 2.1),
            center_x + (scaled_radius * 0.92),
            center_y - (scaled_radius * 0.15),
            fill=theme["trail_outer_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        trail_inner = self.canvas.create_oval(
            center_x - (scaled_radius * 0.48),
            center_y - (scaled_radius * 1.72),
            center_x + (scaled_radius * 0.48),
            center_y - (scaled_radius * 0.22),
            fill=theme["trail_inner_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )

        glow = self.canvas.create_oval(
            center_x - scaled_glow_radius,
            center_y - scaled_glow_radius,
            center_x + scaled_glow_radius,
            center_y + scaled_glow_radius,
            outline=theme["glow_start"],
            width=3,
            tags=(self.gameplay_canvas_tag,),
        )
        asteroid = self.canvas.create_oval(
            center_x - scaled_radius,
            center_y - scaled_radius,
            center_x + scaled_radius,
            center_y + scaled_radius,
            fill=theme["fill_start"],
            outline=theme["outline_start"],
            width=3,
            tags=(self.gameplay_canvas_tag,),
        )
        lava = self.canvas.create_oval(
            center_x - (scaled_radius * 0.54),
            center_y + (scaled_radius * 0.12),
            center_x + (scaled_radius * 0.50),
            center_y + (scaled_radius * 0.80),
            fill=theme["lava_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        highlight = self.canvas.create_oval(
            center_x - (scaled_radius * 0.36),
            center_y - (scaled_radius * 0.42),
            center_x - (scaled_radius * 0.02),
            center_y - (scaled_radius * 0.08),
            fill=theme["highlight_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        crater_a = self.canvas.create_oval(
            center_x + (scaled_radius * 0.05),
            center_y - (scaled_radius * 0.18),
            center_x + (scaled_radius * 0.34),
            center_y + (scaled_radius * 0.08),
            fill=theme["crater_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        crater_b = self.canvas.create_oval(
            center_x - (scaled_radius * 0.22),
            center_y + (scaled_radius * 0.02),
            center_x,
            center_y + (scaled_radius * 0.24),
            fill=theme["crater_start"],
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        label_plate_half_w = max(18, (text_width * start_scale * 0.56))
        label_plate_half_h = max(10, (text_height * start_scale * 0.72))
        label_backdrop = self.canvas.create_oval(
            center_x - label_plate_half_w,
            center_y - label_plate_half_h,
            center_x + label_plate_half_w,
            center_y + label_plate_half_h,
            fill=theme["txt_back_start"],
            outline=theme["txt_back_outline_start"],
            width=1,
            tags=(self.gameplay_canvas_tag,),
        )
        label_shadow = self.canvas.create_text(
            center_x + 1,
            center_y + 1,
            text=question_text,
            fill=theme["txt_shadow_start"],
            font=(font_family, start_font_size, "bold"),
            anchor="center",
            justify="center",
            tags=(self.gameplay_canvas_tag,),
        )
        label = self.canvas.create_text(
            center_x,
            center_y,
            text=question_text,
            fill=theme["txt_start"],
            font=(font_family, start_font_size, "bold"),
            anchor="center",
            justify="center",
            tags=(self.gameplay_canvas_tag,),
        )

        self.canvas.tag_raise(label_backdrop)
        self.canvas.tag_raise(label_shadow)
        self.canvas.tag_raise(label)

        asteroid_item = {
            "trail_outer": trail_outer,
            "trail_inner": trail_inner,
            "obj": asteroid,
            "lava": lava,
            "crater_a": crater_a,
            "crater_b": crater_b,
            "txt_backdrop": label_backdrop,
            "txt_shadow": label_shadow,
            "txt": label,
            "glow": glow,
            "highlight": highlight,
            "center_x": center_x,
            "center_y": center_y,
            "spawn_progress": 0.0,
            "current_scale": start_scale,
            "spawn_start_scale": start_scale,
            "font_base_size": font_base_size,
            "font_family": font_family,
            "logic_miss_offset": 40,
            "theme": theme,
        }
        if self.screen_shake_canvas is self.canvas and (self.screen_shake_offset_x or self.screen_shake_offset_y):
            for key in (
                "trail_outer",
                "trail_inner",
                "glow",
                "obj",
                "lava",
                "highlight",
                "crater_a",
                "crater_b",
                "txt_backdrop",
                "txt_shadow",
                "txt",
            ):
                self.canvas.move(
                    asteroid_item[key],
                    self.screen_shake_offset_x,
                    self.screen_shake_offset_y,
                )
        self._update_asteroid_spawn_visual(asteroid_item, advance=False)
        return asteroid_item

    def _update_asteroid_spawn_visual(self, asteroid_item, advance=True):
        if not asteroid_item:
            return

        canvas = getattr(self, "canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return

        progress = asteroid_item.get("spawn_progress", 0.0)
        if advance and progress < 1.0:
            progress = min(1.0, progress + 0.18)
            asteroid_item["spawn_progress"] = progress
        progress = asteroid_item.get("spawn_progress", 1.0)
        eased_progress = 1.0 - ((1.0 - progress) ** 2)

        new_scale = asteroid_item["spawn_start_scale"] + (
            (1.0 - asteroid_item["spawn_start_scale"]) * eased_progress
        )
        current_scale = max(asteroid_item.get("current_scale", new_scale), 0.01)
        scale_ratio = new_scale / current_scale

        if abs(scale_ratio - 1.0) > 0.0001:
            for key in (
                "trail_outer",
                "trail_inner",
                "glow",
                "obj",
                "lava",
                "highlight",
                "crater_a",
                "crater_b",
                "txt_backdrop",
            ):
                canvas.scale(
                    asteroid_item[key],
                    asteroid_item["center_x"],
                    asteroid_item["center_y"],
                    scale_ratio,
                    scale_ratio,
                )
            asteroid_item["current_scale"] = new_scale

        font_base_size = asteroid_item.get("font_base_size", 16)
        font_family = asteroid_item.get("font_family", FONT_FAMILY_MONO)
        start_font_size = max(10, int(font_base_size * asteroid_item.get("spawn_start_scale", 0.72)))
        current_font_size = max(
            start_font_size,
            int(round(start_font_size + ((font_base_size - start_font_size) * eased_progress))),
        )

        theme = asteroid_item.get("theme") or {
            "trail_outer_start": "#311204",
            "trail_outer_end": "#FF7A22",
            "trail_inner_start": "#7D2403",
            "trail_inner_end": "#FFD08C",
            "glow_start": "#5B2200",
            "glow_end": "#FF8F32",
            "fill_start": "#363C48",
            "fill_end": "#616977",
            "outline_start": "#8D97A8",
            "outline_end": "#D5DBE4",
            "highlight_start": "#BCC7D7",
            "highlight_end": "#F6F9FF",
            "lava_start": "#AC2200",
            "lava_end": "#FFBF2C",
            "crater_start": "#1C2230",
            "crater_end": "#394152",
            "txt_back_start": "#08131E",
            "txt_back_end": "#112336",
            "txt_back_outline_start": "#4A657F",
            "txt_back_outline_end": "#87A7C6",
            "txt_shadow_start": "#040A12",
            "txt_shadow_end": "#101B27",
            "txt_start": "#F8FBFF",
            "txt_end": "#FFFFFF",
        }

        canvas.itemconfig(
            asteroid_item["trail_outer"],
            fill=_blend_hex(theme["trail_outer_start"], theme["trail_outer_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["trail_inner"],
            fill=_blend_hex(theme["trail_inner_start"], theme["trail_inner_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["obj"],
            fill=_blend_hex(theme["fill_start"], theme["fill_end"], eased_progress),
            outline=_blend_hex(theme["outline_start"], theme["outline_end"], eased_progress),
            width=max(2, int(round(2 + eased_progress))),
        )
        canvas.itemconfig(
            asteroid_item["glow"],
            outline=_blend_hex(theme["glow_start"], theme["glow_end"], eased_progress),
            width=max(3, int(round(3 + (4 * eased_progress)))),
        )
        canvas.itemconfig(
            asteroid_item["lava"],
            fill=_blend_hex(theme["lava_start"], theme["lava_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["highlight"],
            fill=_blend_hex(theme["highlight_start"], theme["highlight_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["crater_a"],
            fill=_blend_hex(theme["crater_start"], theme["crater_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["crater_b"],
            fill=_blend_hex(theme["crater_start"], theme["crater_end"], eased_progress),
        )
        canvas.itemconfig(
            asteroid_item["txt_backdrop"],
            fill=_blend_hex(theme["txt_back_start"], theme["txt_back_end"], eased_progress),
            outline=_blend_hex(theme["txt_back_outline_start"], theme["txt_back_outline_end"], eased_progress),
            width=1,
        )
        canvas.itemconfig(
            asteroid_item["txt_shadow"],
            fill=_blend_hex(theme["txt_shadow_start"], theme["txt_shadow_end"], eased_progress),
            font=(font_family, current_font_size, "bold"),
        )
        canvas.itemconfig(
            asteroid_item["txt"],
            fill=_blend_hex(theme["txt_start"], theme["txt_end"], eased_progress),
            font=(font_family, current_font_size, "bold"),
        )

        canvas.tag_raise(asteroid_item["txt_backdrop"])
        canvas.tag_raise(asteroid_item["txt_shadow"])
        canvas.tag_raise(asteroid_item["txt"])

    def _delete_asteroid_visual(self, asteroid_item):
        if not asteroid_item:
            return

        canvas = getattr(self, "canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return

        for key in (
            "trail_outer",
            "trail_inner",
            "glow",
            "obj",
            "lava",
            "highlight",
            "crater_a",
            "crater_b",
            "txt_backdrop",
            "txt_shadow",
            "txt",
        ):
            item_id = asteroid_item.get(key)
            if not item_id:
                continue
            try:
                canvas.delete(item_id)
            except tk.TclError:
                pass
            asteroid_item[key] = None

    def _launch_asteroid_hit_effect(self, center_x, center_y, flash_color="#FFFFFF", debris_colors=None):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        canvas = self.canvas
        # If caller didn't specify a palette, pick a fresh color scheme
        # each time so the burst isn't always the same yellow/white.
        if debris_colors is None:
            debris_colors = ("#FFD36B", "#FFB347", "#FF7A1A", "#FFE9B5")
            flash_color = "#FF9E3D"

        flash = canvas.create_oval(
            center_x - 14,
            center_y - 14,
            center_x + 14,
            center_y + 14,
            fill=flash_color,
            outline="",
            tags=(self.gameplay_canvas_tag,),
        )
        ring = canvas.create_oval(
            center_x - 18,
            center_y - 18,
            center_x + 18,
            center_y + 18,
            outline=flash_color,
            width=2,
            tags=(self.gameplay_canvas_tag,),
        )

        debris = []
        for _ in range(random.randint(5, 8)):
            size = random.randint(4, 7)
            piece_id = canvas.create_polygon(
                center_x,
                center_y - size,
                center_x + size,
                center_y,
                center_x,
                center_y + size,
                center_x - size,
                center_y,
                fill=random.choice(debris_colors),
                outline="",
                tags=(self.gameplay_canvas_tag,),
            )
            debris.append(
                {
                    "id": piece_id,
                    "dx": random.uniform(-6.0, 6.0),
                    "dy": random.uniform(-6.5, -2.0),
                }
            )

        flash_scales = (1.0, 1.45, 1.85, 2.2, 2.55, 2.8)
        current_scale = 1.0
        self._trigger_screen_shake()

        def animate(step=0):
            nonlocal current_scale
            if canvas is not self.canvas or not canvas.winfo_exists():
                return

            target_scale = flash_scales[min(step, len(flash_scales) - 1)]
            scale_ratio = target_scale / max(current_scale, 0.01)
            canvas.scale(flash, center_x, center_y, scale_ratio, scale_ratio)
            canvas.scale(ring, center_x, center_y, scale_ratio, scale_ratio)
            current_scale = target_scale

            fade_progress = step / max(1, len(flash_scales) - 1)
            canvas.itemconfig(flash, fill=_blend_hex(flash_color, "#CBD5E1", fade_progress))
            canvas.itemconfig(ring, outline=_blend_hex(flash_color, "#6D7B8D", fade_progress))

            active_debris = []
            for piece in debris:
                piece["dy"] += 0.42
                piece["dx"] *= 0.97
                canvas.move(piece["id"], piece["dx"], piece["dy"])
                coords = canvas.coords(piece["id"])
                if coords:
                    active_debris.append(piece)
                else:
                    canvas.delete(piece["id"])
            debris[:] = active_debris

            if step < len(flash_scales) - 1:
                self.root.after(28, lambda: animate(step + 1))
            else:
                try:
                    canvas.delete(flash)
                    canvas.delete(ring)
                except tk.TclError:
                    pass
                for piece in debris:
                    try:
                        canvas.delete(piece["id"])
                    except tk.TclError:
                        pass

        animate()

    def _launch_asteroid_miss_effect(self, center_x, center_y):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        canvas = self.canvas
        ring = canvas.create_oval(
            center_x - 18,
            center_y - 10,
            center_x + 18,
            center_y + 10,
            outline="#D8E2EF",
            width=2,
            tags=(self.gameplay_canvas_tag,),
        )

        dust = []
        for _ in range(6):
            size = random.randint(5, 9)
            offset_x = random.randint(-26, 26)
            piece_id = canvas.create_oval(
                center_x + offset_x - size,
                center_y - size,
                center_x + offset_x + size,
                center_y + size,
                fill=random.choice(("#9099A6", "#B7C1CE", "#7C8795")),
                outline="",
                tags=(self.gameplay_canvas_tag,),
            )
            dust.append(
                {
                    "id": piece_id,
                    "dx": random.uniform(-2.8, 2.8),
                    "dy": random.uniform(-3.2, -0.6),
                }
            )

        def animate(step=0):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return

            expand_x = 18 + (step * 9)
            expand_y = 10 + (step * 2)
            canvas.coords(
                ring,
                center_x - expand_x,
                center_y - expand_y,
                center_x + expand_x,
                center_y + expand_y,
            )
            canvas.itemconfig(ring, outline=_blend_hex("#D8E2EF", "#465363", step / 6))

            active_dust = []
            for piece in dust:
                piece["dy"] += 0.36
                piece["dx"] *= 0.94
                canvas.move(piece["id"], piece["dx"], piece["dy"])
                coords = canvas.coords(piece["id"])
                if coords:
                    active_dust.append(piece)
                else:
                    canvas.delete(piece["id"])
            dust[:] = active_dust

            if step < 6:
                self.root.after(30, lambda: animate(step + 1))
            else:
                try:
                    canvas.delete(ring)
                except tk.TclError:
                    pass
                for piece in dust:
                    try:
                        canvas.delete(piece["id"])
                    except tk.TclError:
                        pass

        animate()

    # Asteroid spawning logic with dynamic difficulty based on level and mode
    def spawn_asteroid(self, num_range):
        if not self.game_active: return
        
        # Prevent more than, say, 3 asteroids on screen at once
        if len(self.asteroids) >= 1:
            return
        self.questions_attempted = getattr(self, "questions_attempted", 0) + 1
        if getattr(self, "ui_question_count", None) is not None:
            try:
                self.canvas.itemconfig(self.ui_question_count, text=f"Q: {self.questions_attempted}")
            except Exception:
                pass
        q_text, ans, opts = MathFactory.generate_question(self.selected_op, num_range)
        x_pos = random.randint(self._sx(50), self._sx(500))
        center_x = x_pos + 40
        center_y = -20

        asteroid_item = self._create_asteroid_visual(center_x, center_y, q_text)
        asteroid_item.update({"ans": ans, "opts": opts})
        self.asteroids.append(asteroid_item)
        self.update_buttons()
        
        # Keep the background timer as a safety net
        self.root.after(self.spawn_time, lambda: self.spawn_asteroid(num_range))

    def update_animation(self):
        """Update the game animation by moving the asteroids and
        their text labels downwards. If an asteroid has moved off
        the screen, remove it from the list and update the
        buttons. If the game is not active, do nothing."""
        if not self.game_active: return
        miss_y = getattr(self, "asteroid_miss_y", self._sy(650))
        
        for item in self.asteroids[:]:
            for key in ("glow", "obj", "highlight", "txt_backdrop", "txt_shadow", "txt"):
                self.canvas.move(item[key], 0, self.y_speed)
            item["center_y"] += self.y_speed
            self._update_asteroid_spawn_visual(item)

            if item["center_y"] > (miss_y + item.get("logic_miss_offset", 40)): # Boundary check
                center_x = item.get("center_x", 0)
                center_y = item.get("center_y", 0)
                self._delete_asteroid_visual(item)
                self.asteroids.remove(item)
                self._launch_asteroid_miss_effect(center_x, center_y)
                self.update_buttons()
                
        self.root.after(30, self.update_animation)

    def update_buttons(self):
        if self.asteroids:
            target = self.asteroids[0]
            for i, btn in enumerate(self.buttons):
                btn.config(
                    text=str(target['opts'][i]),
                    state="normal",
                    bg=getattr(self, "answer_btn_normal_bg", "#273A5A"),
                )
        else:
            for btn in self.buttons:
                btn.config(
                    text="-",
                    state="disabled",
                    bg=getattr(self, "answer_btn_disabled_bg", "#1B2740"),
                )


    def process_answer(self, idx):
        if not self.asteroids or not self.game_active: 
            return

        selected = int(self.buttons[idx].cget("text"))
        target = self.asteroids[0]

        if selected == target['ans']:
            # --- CORRECT ANSWER LOGIC ---
            self.score += 1
            self.canvas.itemconfig(self.ui_score, text=f"Score: {self.score}")
            
            # Laser effect
            laser_start_y = max(self.canvas.winfo_height(), self._sy(800))
            center_x = target.get("center_x", self._sx(300))
            center_y = target.get("center_y", self._sy(300))
            laser = self.canvas.create_line(
                self._sx(300),
                laser_start_y,
                center_x,
                center_y,
                fill="cyan",
                width=3,
                tags=(self.gameplay_canvas_tag,),
            )
            self.root.after(100, lambda: self.canvas.delete(laser))
            
            # Remove asteroid (bubble pop) and play pop sound
            item = self.asteroids.pop(0)
            self._delete_asteroid_visual(item)
            self._launch_asteroid_hit_effect(center_x, center_y)
            sound_manager.play_pop_sound()
            
            # REPLACEMENT: Use current_sub_level (1-8)
            self.spawn_asteroid(self.current_sub_level) 
            
            self.update_buttons()
        else:
            # --- WRONG ANSWER PENALTY ---
            self.score = max(0, self.score - 1) 
            self.canvas.itemconfig(self.ui_score, text=f"Score: {self.score}")
            center_x = target.get("center_x", self._sx(300))
            center_y = target.get("center_y", self._sy(300))
            
            item = self.asteroids.pop(0)
            self._delete_asteroid_visual(item)
            self._launch_asteroid_hit_effect(
                center_x,
                center_y,
                flash_color="#FFD8D0",
                debris_colors=("#FFD8D0", "#FFAB91", "#FFE0B2", "#DADCE0"),
            )
            sound_manager.play_pop_sound()
            
            # REPLACEMENT: Use current_sub_level even on wrong answer
            self.spawn_asteroid(self.current_sub_level)
            
            self.update_buttons()


    def end_game(self):
        self.game_active = False
        # Ensure burst sounds are re-enabled for the next session
        try:
            sound_manager.set_muted(False)
        except Exception:
            pass
        self.is_sound_muted = False

        # Compute average seconds-per-question from the game timer
        elapsed = 180 - getattr(self, "time_left", 0)
        q_done = getattr(self, "questions_attempted", 0)
        avg_speed_current = round(elapsed / q_done, 2) if q_done > 0 else 0.0
        self.session_game_count += 1
        count = self.session_game_count
        avg_speed_val = (self.avg_speed_val * (count - 1) + avg_speed_current) / count if hasattr(self, "avg_speed_val") else avg_speed_current
        self.avg_speed_val = avg_speed_val

        self._record_student_attempt(
    topic=getattr(self, "selected_op", "Unknown"),
    level=getattr(self, "current_sub_level", 1),
    speed=avg_speed_val,
    score=self.score,
    total_q=q_done,
)

        self.clear_screen()
        self.draw_bg()
        center_x = self._sx(300)
        title_size = max(32, self._sy(44))
        score_size = max(22, self._sy(30))
        note_size = max(13, self._sy(18))
        motivation_line = self._get_score_motivation_line(self.score)
        badge_text, badge_color = self._get_score_badge(self.score)

        self._launch_confetti_burst(center_x, self._sy(230))
        self.canvas.create_text(
            center_x,
            self._sy(270),
            text="Challenge Complete!",
            font=(FONT_FAMILY_DISPLAY, title_size, "bold"),
            fill="#FFD54F",
        )
        self.canvas.create_text(
            center_x,
            self._sy(345),
            text=f"Final Score: {self.score}",
            font=(FONT_FAMILY_UI, score_size, "bold"),
            fill="white",
        )
        self.canvas.create_text(
            center_x,
            self._sy(400),
            text=motivation_line,
            font=(FONT_FAMILY_UI, note_size, "bold"),
            fill="#A7FFD9",
        )
        self._draw_congrats_character(center_x, self._sy(500), badge_text, badge_color)
        
        exit_btn = self._create_back_button(
            text="Back to Menu",
            callback=self._back_to_menu_after_game,
            width=15,
        )
        self.canvas.create_window(center_x, self._sy(640), window=exit_btn)

    def _get_score_motivation_line(self, score):
        if score >= 45:
            return "Phenomenal run - your focus and speed were unstoppable!"
        if score >= 30:
            return "Excellent work - your rhythm stayed strong to the end!"
        if score >= 18:
            return "Great push - your maths confidence is rising fast!"
        if score >= 8:
            return "Solid effort - every round is making you sharper!"
        if score >= 3:
            return "Good start - keep practicing and your speed will jump quickly!"
        if score > 0:
            return "You can do better! don't worry about the score, just keep playing and you'll see your skills improve!"
        return "No score yet - take a breath and attack the next round!"

    def _get_score_badge(self, score):
        if score >= 30:
            return "Excellent!", "#2E7D32"
        if score >= 12:
            return "Good Effort!", "#43A047"
        if score >= 1:
            return "Keep Going!", "#6FBF73"
        return "Try Again!", "#546E7A"

    def _draw_congrats_character(self, center_x, center_y, badge_text="Great Job!", badge_color="#4CAF50"):
        head_r = max(26, self._sy(34))
        eye_r = max(2, head_r // 8)
        body_w = 90
        body_h = max(40, self._sy(60))
        body_top = center_y + head_r + self._sy(10)

        # Cheerful mascot so the end screen feels warm and celebratory.
        self.canvas.create_oval(
            center_x - head_r,
            center_y - head_r,
            center_x + head_r,
            center_y + head_r,
            fill="#FFE082",
            outline="#FFC107",
            width=3,
        )
        eye_y = center_y - (head_r // 4)
        left_eye_x = center_x - (head_r // 3)
        right_eye_x = center_x + (head_r // 3)
        self.canvas.create_oval(left_eye_x - eye_r, eye_y - eye_r, left_eye_x + eye_r, eye_y + eye_r, fill="#1E2A39", outline="")
        self.canvas.create_oval(right_eye_x - eye_r, eye_y - eye_r, right_eye_x + eye_r, eye_y + eye_r, fill="#1E2A39", outline="")
        self.canvas.create_arc(
            center_x - (head_r // 2),
            center_y - (head_r // 8),
            center_x + (head_r // 2),
            center_y + (head_r // 2),
            start=200,
            extent=140,
            style="arc",
            outline="#1E2A39",
            width=3,
        )

        self.canvas.create_oval(
            center_x - (body_w // 2),
            body_top,
            center_x + (body_w // 2),
            body_top + body_h,
            fill=badge_color,
            outline="#2E7D32",
            width=3,
        )
        self.canvas.create_line(
            center_x - (body_w // 2),
            body_top + (body_h // 3),
            center_x - (body_w // 2) - 26,
            body_top + (body_h // 3) - self._sy(24),
            fill="#FFE082",
            width=4,
        )
        self.canvas.create_line(
            center_x + (body_w // 2),
            body_top + (body_h // 3),
            center_x + (body_w // 2) + 26,
            body_top + (body_h // 3) - self._sy(24),
            fill="#FFE082",
            width=4,
        )
        self.canvas.create_text(
            center_x,
            body_top + (body_h // 2),
            text=badge_text,
            font=(FONT_FAMILY_UI, max(12, self._sy(16)), "bold"),
            fill="white",
        )

    def _launch_confetti_burst(self, center_x, center_y):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        canvas = self.canvas
        canvas_h = max(canvas.winfo_height(), 800)
        colors = ("#FFD54F", "#FF6B6B", "#4FC3F7", "#81C784", "#BA68C8", "#FF8A65")
        pieces = []

        for _ in range(56):
            size = random.randint(4, 8)
            start_x = center_x + random.randint(-46, 46)
            start_y = center_y + random.randint(-10, 10)
            piece_id = canvas.create_rectangle(
                start_x,
                start_y,
                start_x + size,
                start_y + size,
                fill=random.choice(colors),
                outline="",
            )
            pieces.append(
                {
                    "id": piece_id,
                    "dx": random.uniform(-7.5, 7.5),
                    "dy": random.uniform(-11.0, -4.0),
                }
            )

        def animate(step=0):
            if canvas is not self.canvas or not canvas.winfo_exists():
                return

            active = []
            for piece in pieces:
                piece["dy"] += 0.45
                piece["dx"] *= 0.99
                canvas.move(piece["id"], piece["dx"], piece["dy"])
                coords = canvas.coords(piece["id"])
                if coords and coords[1] <= canvas_h + 20:
                    active.append(piece)
                else:
                    canvas.delete(piece["id"])

            pieces[:] = active
            if pieces and step < 55:
                self.root.after(30, lambda: animate(step + 1))
            else:
                for piece in pieces:
                    canvas.delete(piece["id"])

        animate()
    
    def start_t20_flow(self):
        """Initializes the T20 Test session"""
        self.is_t20_mode = True
        self.t20_session_mode = "guest"
        self.show_t20_instruction_manual()

    def start_student_t20_flow(self):
        """Student-only T20 entry point (separate from guest flow)."""
        user = getattr(self, "current_user", None)
        if not user or user.get("role") != "student":
            messagebox.showerror("Access Denied", "T20 student mode requires student login.")
            return
        self.is_t20_mode = True
        self.t20_session_mode = "student"
        self.show_t20_instruction_student()

    def show_t20_instruction_student(self):
        """Show instructions before student T20 mode starts."""
        self.show_t20_instruction_manual()

    def show_t20_instruction_manual(self):
        """Show a simple guest-friendly guide before T20 starts."""
        self.clear_screen()
        self.draw_bg()
        self.root.update_idletasks()
        is_student_t20 = getattr(self, "t20_session_mode", "guest") == "student"

        canvas = self.canvas
        canvas_w = max(canvas.winfo_width(), 600)
        canvas_h = max(canvas.winfo_height(), 800)
        center_x = canvas_w // 2

        card_w = max(500, min(780, int(canvas_w * 0.70)))
        card_h = max(500, min(620, int(canvas_h * 0.68)))
        card_x1 = center_x - (card_w // 2)
        card_x2 = center_x + (card_w // 2)
        card_y1 = max(40, (canvas_h - card_h) // 2)
        card_y2 = card_y1 + card_h

        canvas.create_rectangle(
            card_x1 - 5,
            card_y1 - 5,
            card_x2 + 5,
            card_y2 + 5,
            fill="#0A1A2B",
            outline="#2D89D3",
            width=2,
        )
        canvas.create_rectangle(
            card_x1,
            card_y1,
            card_x2,
            card_y2,
            fill="#10243A",
            outline="#1D3C60",
            width=2,
        )
        canvas.create_rectangle(
            card_x1 + 22,
            card_y1 + 20,
            card_x2 - 22,
            card_y1 + 30,
            fill="#59B9EC",
            outline="",
        )

        heading_size = max(20, min(34, int(card_h * 0.060)))
        subheading_size = max(14, min(19, int(card_h * 0.034)))
        body_size = max(11, min(15, int(card_h * 0.026)))

        canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.10),
            text="T20 Student Challenge" if is_student_t20 else "T20 Guest Challenge",
            font=(FONT_FAMILY_DISPLAY, heading_size, "bold"),
            fill="white",
        )
        canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.16),
            text="How it works",
            font=(FONT_FAMILY_UI, subheading_size, "bold"),
            fill="#9CC6E8",
        )

        instructions_text = (
            "1. You will play 4 rounds: Addition, Subtraction, Multiplication, Division.\n"
            "2. Each round has its own 3:30 timer (210 seconds).\n"
            "3. Choose difficulty:\n"
            "   Easy: 28 questions per round\n"
            "   Hard: 56 questions per round\n"
            "4. Score rule: +1 for correct, -1 for wrong.\n"
            "   Score never goes below 0.\n"
            "5. After each round, you get a 20-second break before the next one.\n"
            "6. Use Exit anytime. If you exit, current T20 progress is not saved.\n"
            "7. Final screen shows your score for each round."
        )

        text_x = card_x1 + 46
        start_y = card_y1 + int(card_h * 0.24)
        canvas.create_text(
            text_x,
            start_y,
            text=instructions_text,
            font=(FONT_FAMILY_UI, body_size),
            fill="#E2ECF7",
            anchor="nw",
            width=card_w - 92,
            justify="left",
        )

        canvas.create_line(
            card_x1 + 26,
            card_y2 - 120,
            card_x2 - 26,
            card_y2 - 120,
            fill="#244A72",
            width=1,
        )

        btn_frame = tk.Frame(self.root, bg="#10243A")

        begin_btn = tk.Button(
            btn_frame,
            text="Start T20",
            font=(FONT_FAMILY_UI, 14, "bold"),
            width=15,
            bg="#3FAE4D",
            fg="white",
            activebackground="#2E8B3A",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=lambda: self._play_button_and_execute(self.show_t20_difficulty_selection),
        )
        begin_btn.pack(side="left", padx=(0, 10))

        back_btn = self._create_back_button(
            text="Back",
            callback=self.show_operation_screen if is_student_t20 else self.show_start_screen,
            width=15,
            font=(FONT_FAMILY_UI, 14, "bold"),
            parent=btn_frame,
        )
        back_btn.configure(
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            bg="#2A3B57",
            fg="#E6EDFF",
            activebackground="#3A5378",
            activeforeground="white",
            cursor="hand2",
        )
        back_btn.pack(side="left", padx=(10, 0))

        canvas.create_window(center_x, card_y2 - 78, window=btn_frame)

    def show_t20_difficulty_selection(self):
        self.clear_screen()
        self.draw_bg()
        center_x = self._sx(300)
        is_student_t20 = getattr(self, "t20_session_mode", "guest") == "student"
        level_callback = self.set_t20_level_student if is_student_t20 else self.set_t20_level_guest
        back_callback = self.show_operation_screen if is_student_t20 else self.show_start_screen
        
        self.canvas.create_text(center_x, 150, text="Select Challenge Mode", 
                                font=(FONT_FAMILY_DISPLAY, 36, "bold"), fill="white")
        
        # Easy Button
        easy_btn = tk.Button(self.root, text="EASY (28 Qs)", font=(FONT_FAMILY_UI, 18, "bold"),
                             width=15, height=2, bg="#4CAF50", fg="white",
                             command=lambda: self._play_button_and_execute(lambda: level_callback("easy")))
        self.canvas.create_window(center_x, 300, window=easy_btn)
        
        # Hard Button
        hard_btn = tk.Button(self.root, text="HARD (56 Qs)", font=(FONT_FAMILY_UI, 18, "bold"),
                             width=15, height=2, bg="#e74c3c", fg="white",
                             command=lambda: self._play_button_and_execute(lambda: level_callback("hard")))
        self.canvas.create_window(center_x, 420, window=hard_btn)
        
        # Back Button
        back_btn = self._create_back_button(
            text="Back",
            callback=back_callback,
            width=12,
            font=(FONT_FAMILY_TEXT, 13, "bold"),
        )
        self.canvas.create_window(center_x, 550, window=back_btn)

    def set_t20_level_guest(self, level):
        self.t20_session_mode = "guest"
        self.set_t20_level(level)

    def set_t20_level_student(self, level):
        self.t20_session_mode = "student"
        self.set_t20_level(level)

    def set_t20_level(self, level):
        self.t20_level = level
        self.t20_ops = ["Addition", "Subtraction", "Multiplication", "Division"]
        self.t20_current_op_idx = 0
        self.t20_scores = {}
        self.t20_total_score = 0
        self.t20_total_questions_answered = 0
        per_round_q = 28 if level == "easy" else 56
        self.t20_total_questions_planned = per_round_q * len(self.t20_ops)
        self.start_t20_operation()

    def _cancel_t20_break_clock(self):
        if getattr(self, "t20_break_clock_id", None) is not None:
            try:
                self.root.after_cancel(self.t20_break_clock_id)
            except Exception:
                pass
            self.t20_break_clock_id = None

    def _reset_t20_break_ui_state(self):
        self.t20_break_screen_ready = False
        self.t20_break_countdown_item = None

    def start_t20_operation(self):
        """Initializes a specific math challenge within the T20 Test"""
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        self.current_op = self.t20_ops[self.t20_current_op_idx]
        self.t20_q_count = 0
        self.t20_current_score = 0
        self.t20_round_started_at = time.time()
        self._t20_screen_ready = False
        self.t20_option_buttons = []
        self.t20_ui_progress = None
        
        # RESET: Ensure each of the 4 operations gets its own 3:30
        self.t20_time_left = 210  
        
        self.show_t20_test_screen()
        
        # Stop any existing clock before starting a new one to prevent 'double speed'
        if hasattr(self, 't20_clock_id'):
            self.root.after_cancel(self.t20_clock_id)
        self.update_t20_clock()

    def show_t20_test_screen(self):
        center_x = self._sx(300)
        max_q = 28 if getattr(self, "t20_level", "easy") == "easy" else 56
        next_q = min(getattr(self, "t20_q_count", 0) + 1, max_q)

        if not getattr(self, "_t20_screen_ready", False):
            self.clear_screen()
            self.draw_bg()

            self.canvas.create_text(
                center_x,
                30,
                text=f"T20 Test: {self.current_op}",
                font=(FONT_FAMILY_UI, 22, "bold"),
                fill="white",
                tags=("t20_static",),
            )

            exit_btn = self._create_back_button(
                text="Exit",
                callback=self.show_t20_exit_popup,
                width=8,
                font=(FONT_FAMILY_UI, 12, "bold"),
            )
            self.canvas.create_window(self._sx(60), 30, window=exit_btn, tags=("t20_static",))

            mins, secs = divmod(self.t20_time_left, 60)
            self.t20_ui_timer = self.canvas.create_text(
                self._sx(80),
                70,
                text=f"{mins}:{secs:02d}",
                font=(FONT_FAMILY_MONO, 16, "bold"),
                fill="red",
                tags=("t20_static",),
            )

            self.t20_ui_score = self.canvas.create_text(
                center_x,
                100,
                text=f"Round Score: {self.t20_current_score}",
                font=(FONT_FAMILY_MONO, 20, "bold"),
                fill="gold",
                tags=("t20_static",),
            )
            self._t20_screen_ready = True

        progress_text = f"Q: {next_q}/{max_q}"
        try:
            if not getattr(self, "t20_ui_progress", None):
                raise tk.TclError("missing progress label")
            self.canvas.itemconfig(self.t20_ui_progress, text=progress_text)
        except Exception:
            self.t20_ui_progress = self.canvas.create_text(
                self._sx(510),
                70,
                text=progress_text,
                font=(FONT_FAMILY_MONO, 16, "bold"),
                fill="white",
                anchor="e",
                tags=("t20_static",),
            )

        self._clear_t20_dynamic_widgets()

        # Question text
        diff_config = self.adjust_t20_difficulty(self.t20_q_count)
        # Use the NEW dedicated function for T20
        q_text, self.t20_correct_ans, opts = MathFactory.generate_t20_question(diff_config)
        self.canvas.create_text(
            center_x,
            180,
            text=q_text,
            font=(FONT_FAMILY_UI, 26, "bold"),
            fill="white",
            width=500,
            tags=("t20_dynamic",),
        )

        # MCQ Buttons (aligned as per your 2nd image)
        for i, opt in enumerate(opts):
            btn = tk.Button(self.root, text=str(opt), font=(FONT_FAMILY_UI, 14), width=35,
                            bg="#263238", fg="white", activebackground="#455A64",
                            command=lambda o=opt: (sound_manager.play_pop_sound(), self.process_t20_answer(o)))
            self.t20_option_buttons.append(btn)
            self.canvas.create_window(center_x, 280 + (i * 70), window=btn, tags=("t20_dynamic",))

    def _clear_t20_dynamic_widgets(self):
        for btn in getattr(self, "t20_option_buttons", []):
            try:
                btn.destroy()
            except Exception:
                pass
        self.t20_option_buttons = []
        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            self.canvas.delete("t20_dynamic")

    def show_t20_exit_popup(self):
        """Ask for confirmation before exiting the T20 guest test."""
        if not getattr(self, "is_t20_mode", False):
            return

        popup = tk.Toplevel(self.root)
        popup.title("Quit T20 Test?")

        width, height = 400, 200
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        pos_x = main_x + (main_w // 2) - (width // 2)
        pos_y = main_y + (main_h // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        popup.configure(bg="#2c3e50")
        popup.transient(self.root)

        def close_popup():
            if not popup.winfo_exists():
                return
            try:
                popup.grab_release()
            except tk.TclError:
                pass
            popup.destroy()

        def confirm_exit():
            sound_manager.play_button_sound()
            close_popup()
            self.exit_t20_flow()

        def cancel_exit(play_sound=False):
            if play_sound:
                sound_manager.play_button_sound()
            close_popup()

        popup.protocol("WM_DELETE_WINDOW", cancel_exit)

        tk.Label(
            popup,
            text="Do you want to exit the T20 Test?",
            font=(FONT_FAMILY_UI, 14, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10,
        ).pack()

        tk.Label(
            popup,
            text="Your current T20 progress will not be saved.",
            font=(FONT_FAMILY_UI, 11),
            bg="#2c3e50",
            fg="#bdc3c7",
        ).pack(pady=5)

        btn_frame = tk.Frame(popup, bg="#2c3e50")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Yes, Exit",
            width=10,
            bg="#e74c3c",
            fg="white",
            command=confirm_exit,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            width=10,
            command=lambda: cancel_exit(play_sound=True),
        ).pack(side="left", padx=10)

        popup.grab_set()
        popup.focus_set()

    def exit_t20_flow(self):
        """Exit handler for the guest T20 flow.

        Cancels the T20 timer and returns to the difficulty selection screen.
        """
        self._clear_t20_dynamic_widgets()
        self._t20_screen_ready = False
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        # Stop the T20 clock if it's running
        if hasattr(self, "t20_clock_id"):
            try:
                self.root.after_cancel(self.t20_clock_id)
            except Exception:
                pass
            del self.t20_clock_id

        if getattr(self, "t20_session_mode", "guest") == "student":
            self.show_operation_screen()
        else:
            self.show_t20_difficulty_selection()

    def _record_student_t20_round(self):
        """Save one T20 operation result for logged-in students only."""
        if getattr(self, "t20_session_mode", "guest") != "student":
            return
        user = getattr(self, "current_user", None)
        if not user or user.get("role") != "student":
            return

        q_done = int(getattr(self, "t20_q_count", 0) or 0)
        elapsed = max(0, 210 - int(getattr(self, "t20_time_left", 0) or 0))
        avg_speed = round(elapsed / q_done, 2) if q_done > 0 else 0.0

        save_t20_attempt(
            student_id=user.get("student_id"),
            student_name=getattr(self, "student_name", "Student"),
            operation=str(getattr(self, "current_op", "T20")),
            difficulty=str(getattr(self, "t20_level", "easy")),
            score=int(getattr(self, "t20_current_score", 0) or 0),
            total_q=q_done,
            avg_speed=avg_speed,
        )

    def adjust_t20_difficulty(self, count):
        """
        count : current question index (0-based)
        Uses self.t20_level -> 'easy' or 'hard'
        Uses self.current_op
        """

        # ---------------- SET TOTAL QUESTIONS ----------------
        if self.t20_level == "easy":
            total_q = 28
        else:  # hard
            total_q = 56
        
        # Check if we passed the question limit for the current level
        if count >= total_q:
            # We are done with this operation, return None to signal end
            return None

        block = total_q // 4  # Divide questions into 4 blocks for progressive difficulty
        op = self.current_op.lower()

        # ---------------- ADDITION / SUBTRACTION ----------------
        if op in ["add", "addition"]:
            return {"type": "add", "a_digits": 2, "b_digits": 2}

        if op in ["sub", "subtraction"]:
            return {"type": "sub", "a_digits": 2, "b_digits": 2}

        # ---------------- MULTIPLICATION ----------------
        if op in ["mul", "multiply", "multiplication"]:
            block = 7 

            if count <= block:
                return {"type": "mul", "a_digits": 1, "b_digits": 1}

            elif count <= block * 2:
                return {"type": "mul", "a_digits": 2, "b_digits": 1}

            elif count <= block * 3:
                return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (11, 19)
                }
            elif count <= block * 4:
                 return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (21, 29)
                }
            elif count <= block * 5:
                 return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (31, 39)
                }
            elif count <= block * 6:
                 return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (41, 49)
                }
            elif count <= block * 7:
                 return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (51, 59)
                }

            else:
                return {
                    "type": "mul",
                    "a_digits": 2,
                    "b_digits": 2,
                    "range": (61, 69)
                }

        # ---------------- DIVISION ----------------
        if op in ["div", "divide", "division"]:

            if count <= block:
                return {"type": "div", "num_digits": 2, "den_digits": 1}

            elif count <= block * 2:
                return {"type": "div", "num_digits": 3, "den_digits": 1}

            elif count <= block * 3:
                return {"type": "div", "num_digits": 3, "den_digits": 2}

            else:
                return {"type": "div", "num_digits": 4, "den_digits": 2}

    def process_t20_answer(self, selected):
        try:
            is_correct = int(selected) == int(self.t20_correct_ans)
        except Exception:
            is_correct = str(selected).strip() == str(self.t20_correct_ans).strip()

        if is_correct:
            self.t20_current_score += 1
            self.t20_total_score += 1
        else:
            self.t20_current_score = max(0, self.t20_current_score - 1)
        
        # Update the score visibility on the screen
        if hasattr(self, 't20_ui_score'):
            self.canvas.itemconfig(self.t20_ui_score, text=f"Round Score: {self.t20_current_score}")
        
        self.t20_q_count += 1
        self.t20_total_questions_answered += 1
        
        # Check if we should end based on question count for the level
        max_q = 28 if getattr(self, "t20_level", "easy") == "easy" else 56
        
        if self.t20_q_count < max_q and self.t20_time_left > 0:
            self.show_t20_test_screen()
        else:
            self.end_t20_operation()

    def end_t20_operation(self):
        """Saves score and handles the 20-second gap"""
        self._clear_t20_dynamic_widgets()
        self._t20_screen_ready = False
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        # Cancel the clock immediately
        if hasattr(self, 't20_clock_id'):
            self.root.after_cancel(self.t20_clock_id)
            
        # Store the result for the summary screen
        self.t20_scores[self.current_op] = self.t20_current_score
        self._record_student_t20_round()
        self.t20_current_op_idx += 1
        
        if self.t20_current_op_idx < len(self.t20_ops):
            # Start the 20-second Rest Period
            self.break_timer = 20
            self.update_break_clock()
        else:
            self.show_t20_final_results()

    def show_t20_break_screen(self):
        self._reset_t20_break_ui_state()
        self.break_timer = 20
        self.update_break_clock()

    def _continue_t20_from_break(self):
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        self.start_t20_operation()

    def _restart_t20_from_break(self):
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        self.t20_current_op_idx = 0
        self.t20_scores = {}
        self.t20_total_score = 0
        self.t20_total_questions_answered = 0
        self.start_t20_operation()

    def show_t20_final_results(self):
        self._cancel_t20_break_clock()
        self._reset_t20_break_ui_state()
        self.clear_screen()
        self.draw_bg()
        center_x = self._sx(300)
        self.canvas.create_text(center_x, 150, text="T20 Test Results", font=(FONT_FAMILY_DISPLAY, 32), fill="gold")
        
        max_q = 28 if getattr(self, "t20_level", "easy") == "easy" else 56
        
        for i, (op, score) in enumerate(self.t20_scores.items()):
            txt = f"Challenge {i+1} ({op}): {score}/{max_q}"
            self.canvas.create_text(center_x, 250 + (i * 50), text=txt, font=(FONT_FAMILY_UI, 18), fill="white")
            
        final_back_cb = self.show_operation_screen if getattr(self, "t20_session_mode", "guest") == "student" else self.show_start_screen
        back_btn = self._create_back_button(
            text="Back to Menu",
            callback=final_back_cb,
            width=15,
        )
        self.canvas.create_window(center_x, 600, window=back_btn)
    
    def update_t20_clock(self):
        """Manages the 3:30 countdown for T20 operations"""
        if self.t20_time_left > 0 and hasattr(self, 't20_ui_timer'):
            self.t20_time_left -= 1
            mins, secs = divmod(self.t20_time_left, 60)
            # Update the specific T20 UI element, but guard against stale/invalid items
            try:
                self.canvas.itemconfig(self.t20_ui_timer, text=f"{mins}:{secs:02d}")
            except Exception:
                return
            self.t20_clock_id = self.root.after(1000, self.update_t20_clock)
        elif self.t20_time_left <= 0:
            self.end_t20_operation()
    

    def update_break_clock(self):
        """Manages the 20-second transition between challenges"""
        if self.break_timer <= 0:
            self._cancel_t20_break_clock()
            self._reset_t20_break_ui_state()
            # Automatically move to the next operation
            self.start_t20_operation()
            return

        if not getattr(self, "t20_break_screen_ready", False):
            self.clear_screen()
            self.draw_bg()
            self.canvas.create_text(
                self._sx(300),
                250,
                text=f"Great Job! Next: {self.t20_ops[self.t20_current_op_idx]}",
                font=(FONT_FAMILY_UI, 20),
                fill="white",
            )
            self.canvas.create_text(
                self._sx(300),
                200,
                text="Rest Your Eyes!",
                font=(FONT_FAMILY_UI, 20, "bold"),
                fill="white",
            )
            self.t20_break_countdown_item = self.canvas.create_text(
                self._sx(300),
                350,
                text="",
                font=(FONT_FAMILY_DISPLAY, 45),
                fill="gold",
            )
            self.canvas.create_text(
                self._sx(300),
                405,
                text=f"Score Of Last Round: {self.t20_current_score}",
                font=(FONT_FAMILY_UI, 15, "bold"),
                fill="#D8E2EF",
            )

            btn_row = tk.Frame(self.root, bg="#0F1728")

            continue_btn = tk.Button(
                btn_row,
                text="Continue Now",
                command=lambda: self._play_button_and_execute(self._continue_t20_from_break),
                font=(FONT_FAMILY_UI, 13, "bold"),
                width=14,
                bg="#2E9F44",
                fg="white",
                activebackground="#257F36",
                activeforeground="white",
                relief="raised",
                bd=2,
                padx=8,
                pady=8,
                cursor="hand2",
            )
            restart_btn = tk.Button(
                btn_row,
                text="Restart T20",
                command=lambda: self._play_button_and_execute(self._restart_t20_from_break),
                font=(FONT_FAMILY_UI, 13, "bold"),
                width=12,
                bg="#D9A11A",
                fg="#1C1C1C",
                activebackground="#BD8A15",
                activeforeground="#111111",
                relief="raised",
                bd=2,
                padx=8,
                pady=8,
                cursor="hand2",
            )
            exit_btn = tk.Button(
                btn_row,
                text="Exit",
                command=lambda: self._play_button_and_execute(self.exit_t20_flow),
                font=(FONT_FAMILY_UI, 13, "bold"),
                width=9,
                bg="#C84A42",
                fg="white",
                activebackground="#A93C35",
                activeforeground="white",
                relief="raised",
                bd=2,
                padx=8,
                pady=8,
                cursor="hand2",
            )

            continue_btn.pack(side="left", padx=(0, 10))
            restart_btn.pack(side="left", padx=(0, 10))
            exit_btn.pack(side="left")
            self.canvas.create_window(self._sx(300), 470, window=btn_row)
            self.t20_break_screen_ready = True

        if getattr(self, "t20_break_countdown_item", None) is not None:
            try:
                self.canvas.itemconfig(
                    self.t20_break_countdown_item,
                    text=f"Next Challenge in: {self.break_timer}",
                )
            except Exception:
                return

        self.break_timer -= 1
        self.t20_break_clock_id = self.root.after(1000, self.update_break_clock)
    
# ----------------------------
# Admin Panel 
# ----------------------------
# This section provides the admin interface for managing student accounts and uploading questions for the advanced quiz. It includes form validation, dynamic display of student information, and handling of file uploads for quiz questions.
def clear_root(root: tk.Tk):
    """Destroy all widgets in root (screen switch helper)."""
    for w in root.winfo_children():
        w.destroy()

#  SAFETY: destroy old canvas if it exists
def show_admin_panel(root, user, handle_logout, handle_upload):
    clear_root(root)

    panel_wrap = tk.Frame(root)
    panel_wrap.pack(fill="both", expand=True)

    panel_canvas = tk.Canvas(panel_wrap, highlightthickness=0)
    panel_scrollbar = ttk.Scrollbar(panel_wrap, orient="vertical", command=panel_canvas.yview)
    panel_canvas.configure(yscrollcommand=panel_scrollbar.set)

    panel_canvas.pack(side="left", fill="both", expand=True)
    panel_scrollbar.pack(side="right", fill="y")

    frame = tk.Frame(panel_canvas, padx=20, pady=20)
    panel_window = panel_canvas.create_window((0, 0), window=frame, anchor="nw")

    def _refresh_admin_scrollregion(_event=None):
        panel_canvas.configure(scrollregion=panel_canvas.bbox("all"))

    def _resize_admin_panel_width(event):
        panel_canvas.itemconfigure(panel_window, width=event.width)

    frame.bind("<Configure>", _refresh_admin_scrollregion)
    panel_canvas.bind("<Configure>", _resize_admin_panel_width)

    def _is_pointer_over_admin_canvas() -> bool:
        if not panel_canvas.winfo_exists():
            return False
        pointer_x = root.winfo_pointerx()
        pointer_y = root.winfo_pointery()
        x0 = panel_canvas.winfo_rootx()
        y0 = panel_canvas.winfo_rooty()
        x1 = x0 + panel_canvas.winfo_width()
        y1 = y0 + panel_canvas.winfo_height()
        return x0 <= pointer_x <= x1 and y0 <= pointer_y <= y1
# Windows and macOS use MouseWheel for mouse wheel events
    def _on_admin_mousewheel(event):
        if not _is_pointer_over_admin_canvas():
            return
        delta = event.delta
        if delta == 0:
            return "break"
        # Normalize wheel delta so one notch scrolls one unit on Windows/macOS.
        units = int(-delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        panel_canvas.yview_scroll(units, "units")
        return "break"
# Linux uses Button-4 and Button-5 for mouse wheel events, so we need a separate handler for that platform
    def _on_admin_mousewheel_linux(event):
        if not _is_pointer_over_admin_canvas():
            return
        if event.num == 4:
            panel_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            panel_canvas.yview_scroll(1, "units")
        return "break"

    wheel_bind_id = root.bind("<MouseWheel>", _on_admin_mousewheel, add="+")
    wheel_up_bind_id = root.bind("<Button-4>", _on_admin_mousewheel_linux, add="+")
    wheel_down_bind_id = root.bind("<Button-5>", _on_admin_mousewheel_linux, add="+")
# this will ensure that when the admin panel is closed/destroyed, we clean up the mouse wheel bindings to prevent them from affecting other parts of the app
    def _cleanup_admin_mousewheel_bindings(_event=None):
        if wheel_bind_id:
            root.unbind("<MouseWheel>", wheel_bind_id)
        if wheel_up_bind_id:
            root.unbind("<Button-4>", wheel_up_bind_id)
        if wheel_down_bind_id:
            root.unbind("<Button-5>", wheel_down_bind_id)

    panel_wrap.bind("<Destroy>", _cleanup_admin_mousewheel_bindings)


    def is_grade_input(value):
        return value == "" or (value.isdigit() and len(value) <= 2)
    
    def is_enrollment_input(value):
        return value == "" or value.isdigit()

    def normalize_student_row(row):
        if isinstance(row, dict) or hasattr(row, "keys"):
            row_data = dict(row)
            return {
                "id": row_data.get("id"),
                "name": row_data.get("name"),
                "grade": row_data.get("grade"),
                "batch": row_data.get("batch"),
                "enrollment_id": row_data.get("enrollment_id"),
                "login_id": row_data.get("login_id"),
            }

        sid, name, grade, batch, enrollment_id, login_id = row
        return {
            "id": sid,
            "name": name,
            "grade": grade,
            "batch": batch,
            "enrollment_id": enrollment_id,
            "login_id": login_id,
        }
# This function formats the student information into a readable label for display in the admin panel
    def format_student_label(student):
        batch = student["batch"] if student["batch"] else "-"
        enrollment = student["enrollment_id"] if student["enrollment_id"] is not None else "-"
        login = student["login_id"] if student["login_id"] else "-"
        return f"{student['name']} | Std {student['grade']} | Batch {batch} | Roll {enrollment} | Login {login}"

    color_bg = "#07111F"
    color_surface = "#0D1A2C"
    color_surface_soft = "#12243A"
    color_sidebar = "#081321"
    color_sidebar_surface = "#11253B"
    color_sidebar_border = "#1F3B59"
    color_sidebar_text = "#F4F8FF"
    color_sidebar_primary = "#2E7CFF"
    color_sidebar_primary_active = "#235FCA"
    color_sidebar_neutral = "#17314A"
    color_sidebar_neutral_active = "#214767"
    color_sidebar_logout = "#C65833"
    color_sidebar_logout_active = "#A34224"
    color_text = "#F4F8FF"
    color_muted = "#8EA6C1"
    color_border = "#1D3652"
    color_focus = "#73C9FF"
    color_primary = "#FF8A2B"
    color_primary_active = "#D96E14"
    color_success = "#43C0C6"
    color_success_active = "#2A9AA0"
    color_danger = "#C95D4A"
    color_danger_active = "#A44637"

    root.configure(bg=color_bg)
    panel_wrap.configure(bg=color_bg)
    panel_canvas.configure(bg=color_bg)
    frame.configure(bg=color_bg)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Admin.Vertical.TScrollbar",
        background="#16314B",
        troughcolor=color_bg,
        bordercolor=color_bg,
        arrowcolor="#8FB5DA",
        relief="flat",
    )
    panel_scrollbar.configure(style="Admin.Vertical.TScrollbar")

    def create_button(parent, text, command, *, kind="neutral", width=None):
        palette = {
            "primary": (color_primary, color_primary_active),
            "success": (color_success, color_success_active),
            "danger": (color_danger, color_danger_active),
            "neutral": ("#203650", "#294563"),
            "sidebar_primary": (color_sidebar_primary, color_sidebar_primary_active),
            "sidebar_neutral": (color_sidebar_neutral, color_sidebar_neutral_active),
            "sidebar_logout": (color_sidebar_logout, color_sidebar_logout_active),
        }
        bg, active_bg = palette.get(kind, palette["neutral"])
        is_sidebar_kind = kind.startswith("sidebar_")
        return tk.Button(
            parent,
            text=text,
            command=lambda: (sound_manager.play_button_sound(), command()),
            width=width,
            font=(FONT_FAMILY_UI, 10, "bold"),
            bg=bg,
            fg="white",
            activebackground=active_bg,
            activeforeground="white",
            relief="raised" if is_sidebar_kind else "flat",
            bd=1 if is_sidebar_kind else 0,
            padx=12,
            pady=9 if is_sidebar_kind else 8,
            cursor="hand2",
            highlightthickness=0,
        )

    def create_card(parent, title, *, bg=color_surface, fg=color_text, border=color_border, pady=(0, 10), padx=16):
        card = tk.Frame(
            parent,
            bg=bg,
            bd=0,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
        )
        card.pack(fill="x", pady=pady)
        tk.Frame(card, bg=border, height=2).pack(fill="x")
        tk.Label(
            card,
            text=title,
            font=(FONT_FAMILY_TEXT, 12, "bold"),
            fg=fg,
            bg=bg,
        ).pack(anchor="w", padx=padx, pady=(12, 8))
        body = tk.Frame(card, bg=bg)
        body.pack(fill="x", padx=padx, pady=(0, 14))
        return card, body

    def style_entry(entry: tk.Entry):
        entry.configure(
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_focus,
            bg=color_surface_soft,
            fg=color_text,
            insertbackground=color_text,
            font=(FONT_FAMILY_TEXT, 10),
        )

    welcome_name = "Admin"
    if isinstance(user, dict):
        welcome_name = user.get("login_id") or user.get("name") or "Admin"
    if welcome_name == "Admin":
        try:
            admin_info = get_admin_user()
            if admin_info and admin_info.get("login_id"):
                welcome_name = admin_info.get("login_id")
        except Exception:
            pass
    try:
        student_count = len(get_all_students())
    except Exception:
        student_count = 0

    header = tk.Frame(frame, bg=color_bg)
    header.pack(fill="x", pady=(0, 14))

    menu_toggle_btn = tk.Button(
        header,
        text="\u2630",
        font=("Segoe UI Symbol", 14, "bold"),
        bg=color_surface,
        fg=color_text,
        activebackground="#16314B",
        activeforeground=color_text,
        relief="flat",
        bd=0,
        padx=10,
        pady=2,
        cursor="hand2",
    )
    menu_toggle_btn.pack(side="left", padx=(0, 10))

    right_spacer = tk.Label(header, text=" ", bg=color_bg, width=4)
    right_spacer.pack(side="right")

    heading_block = tk.Frame(header, bg=color_bg)
    heading_block.pack(fill="x", expand=True)

    tk.Label(
        heading_block,
        text=f"Welcome {welcome_name}",
        fg="#73C9FF",
        bg=color_bg,
        font=(FONT_FAMILY_TEXT, 11, "bold"),
    ).pack(anchor="center")

    tk.Label(
        heading_block,
        text="Admin Panel",
        font=(FONT_FAMILY_DISPLAY, 26, "bold"),
        fg=color_text,
        bg=color_bg,
    ).pack(anchor="center")

    tk.Label(
        heading_block,
        text="Create credentials, manage student access, upload quiz banks, and review performance from one console.",
        fg=color_muted,
        bg=color_bg,
        font=(FONT_FAMILY_TEXT, 11),
    ).pack(anchor="center", pady=(2, 0))

    summary_row = tk.Frame(frame, bg=color_bg)
    summary_row.pack(fill="x", pady=(0, 16))

    summary_cards = [
        ("Students", str(student_count), "Active records in the roster"),
        ("Access", "Passwords On", "Student logins now use stored credentials"),
        ("Progress", "Live Tracking", "Basic, advanced, and T20 results"),
    ]
    for index, (label, value, hint) in enumerate(summary_cards):
        card = tk.Frame(
            summary_row,
            bg=color_surface,
            padx=16,
            pady=14,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_border,
        )
        card.grid(row=0, column=index, padx=(0, 12 if index < len(summary_cards) - 1 else 0), sticky="nsew")
        tk.Frame(card, bg="#FF8A2B" if index == 0 else "#73C9FF", height=3).pack(fill="x", pady=(0, 12))
        tk.Label(card, text=label, bg=color_surface, fg=color_muted, font=(FONT_FAMILY_UI, 9, "bold")).pack(anchor="w")
        tk.Label(card, text=value, bg=color_surface, fg=color_text, font=(FONT_FAMILY_UI, 18, "bold")).pack(anchor="w", pady=(8, 2))
        tk.Label(card, text=hint, bg=color_surface, fg=color_muted, font=(FONT_FAMILY_UI, 9)).pack(anchor="w")
    for index in range(len(summary_cards)):
        summary_row.grid_columnconfigure(index, weight=1)

    layout = tk.Frame(frame, bg=color_bg)
    layout.pack(fill="both", expand=True)

    sidebar = tk.Frame(
        layout,
        bg=color_sidebar,
        bd=0,
        highlightthickness=1,
        highlightbackground=color_sidebar_border,
        highlightcolor=color_sidebar_border,
        padx=14,
        pady=14,
        width=290,
    )
    sidebar.pack(side="left", fill="y", padx=(0, 12))
    sidebar.pack_propagate(False)

    main_content = tk.Frame(layout, bg=color_bg)
    main_content.pack(side="left", fill="both", expand=True)

    sidebar_visible = True

    def toggle_sidebar():
        nonlocal sidebar_visible
        if sidebar_visible:
            sidebar.pack_forget()
            sidebar_visible = False
        else:
            sidebar.pack(side="left", fill="y", padx=(0, 12), before=main_content)
            sidebar_visible = True

    menu_toggle_btn.configure(command=toggle_sidebar)

    _, student_actions = create_card(
        sidebar,
        "Actions",
        bg=color_sidebar_surface,
        fg=color_sidebar_text,
        border=color_sidebar_border,
        pady=(0, 12),
        padx=12,
    )

    _, form = create_card(
        main_content,
        "Add Student",
        bg=color_surface,
        fg=color_text,
        border=color_border,
        pady=(0, 10),
        padx=16,
    )
    form.columnconfigure(1, weight=1)

    tk.Label(form, text="Student Name", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=0, column=0, sticky="w", pady=6)
    name_entry = tk.Entry(form, width=36)
    style_entry(name_entry)
    name_entry.grid(row=0, column=1, pady=6, padx=10, sticky="ew")

    tk.Label(form, text="Standard (1-10)", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=1, column=0, sticky="w", pady=6)
    grade_entry = tk.Entry(form, width=12)
    style_entry(grade_entry)
    grade_validator = root.register(is_grade_input)
    grade_entry.config(validate="key", validatecommand=(grade_validator, "%P"))
    grade_entry.grid(row=1, column=1, sticky="w", pady=6, padx=10)

    tk.Label(form, text="Batch (optional)", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=2, column=0, sticky="w", pady=6)
    batch_entry = tk.Entry(form, width=36)
    style_entry(batch_entry)
    batch_entry.grid(row=2, column=1, pady=6, padx=10, sticky="ew")

    tk.Label(form, text="Enrollment/Roll No", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=3, column=0, sticky="w", pady=6)
    enroll_entry = tk.Entry(form, width=12)
    style_entry(enroll_entry)
    enroll_validator = root.register(is_enrollment_input)
    enroll_entry.config(validate="key", validatecommand=(enroll_validator, "%P"))
    enroll_entry.grid(row=3, column=1, sticky="w", pady=6, padx=10)

    _, output = create_card(
        main_content,
        "Generated Credentials",
        bg=color_surface,
        fg=color_text,
        border="#22405C",
        pady=(0, 10),
        padx=16,
    )

    cards = tk.Frame(output, bg=color_surface)
    cards.pack(fill="x")

    login_card = tk.Frame(
        cards,
        bg=color_surface_soft,
        bd=0,
        highlightthickness=1,
        highlightbackground="#294461",
        highlightcolor="#294461",
    )
    login_card.pack(fill="x", pady=(0, 6))
    login_lbl = tk.Label(login_card, text="Login ID: -", font=(FONT_FAMILY_MONO, 11, "bold"), bg=color_surface_soft, fg=color_text)
    login_lbl.pack(anchor="w", padx=10, pady=8)

    pass_card = tk.Frame(
        cards,
        bg=color_surface_soft,
        bd=0,
        highlightthickness=1,
        highlightbackground="#294461",
        highlightcolor="#294461",
    )
    pass_card.pack(fill="x")
    pass_lbl = tk.Label(pass_card, text="Password: -", font=(FONT_FAMILY_MONO, 11, "bold"), bg=color_surface_soft, fg=color_text)
    pass_lbl.pack(anchor="w", padx=10, pady=8)

    def copy_generated_credentials():
        login_text = login_lbl.cget("text")
        pass_text = pass_lbl.cget("text")

        login_value = login_text.split(":", 1)[1].strip() if ":" in login_text else "-"
        pass_value = pass_text.split(":", 1)[1].strip() if ":" in pass_text else "-"

        if login_value == "-" and pass_value == "-":
            messagebox.showinfo("Copy", "No generated credentials to copy yet.")
            return

        root.clipboard_clear()
        root.clipboard_append(f"Login ID: {login_value}\nPassword: {pass_value}")
        root.update_idletasks()
        messagebox.showinfo("Copied", "Generated credentials copied to clipboard.")

    copy_row = tk.Frame(output, bg=color_surface)
    copy_row.pack(fill="x", pady=(8, 0))
    copy_btn = tk.Button(
        copy_row,
        text="\U0001F4CB Copy",
        command=copy_generated_credentials,
        font=(FONT_FAMILY_TEXT, 9, "bold"),
        bg="#173149",
        fg=color_text,
        activebackground="#224560",
        activeforeground=color_text,
        relief="flat",
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    copy_btn.pack(anchor="e")

    _, admin_frame = create_card(
        main_content,
        "Admin Account",
        bg=color_surface,
        fg=color_text,
        border=color_border,
        pady=(0, 10),
        padx=16,
    )

    tk.Label(admin_frame, text="Admin Login ID", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=0, column=0, sticky="w", pady=6)
    admin_login_entry = tk.Entry(admin_frame, width=36)
    style_entry(admin_login_entry)
    admin_login_entry.grid(row=0, column=1, pady=6, padx=10, sticky="ew")

    tk.Label(admin_frame, text="New Password (leave blank to keep)", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(row=1, column=0, sticky="w", pady=6)
    admin_pass_entry = tk.Entry(admin_frame, width=36, show="*")
    style_entry(admin_pass_entry)
    admin_pass_entry.grid(row=1, column=1, pady=6, padx=10, sticky="ew")
    show_admin_pass_var = tk.BooleanVar(value=False)

    def toggle_admin_password_visibility():
        # Keep password masked by default; reveal only when explicitly requested.
        reveal = show_admin_pass_var.get()
        admin_pass_entry.configure(show="" if reveal else "*")
        show_admin_pass_btn.configure(text="Hide" if reveal else "Show")

    show_admin_pass_btn = tk.Button(
        admin_frame,
        text="Show",
        command=lambda: (sound_manager.play_button_sound(), show_admin_pass_var.set(not show_admin_pass_var.get()), toggle_admin_password_visibility()),
        font=(FONT_FAMILY_UI, 9, "bold"),
        bg="#173149",
        fg=color_text,
        activebackground="#224560",
        activeforeground=color_text,
        relief="flat",
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
    )
    show_admin_pass_btn.grid(row=1, column=2, padx=(0, 4), sticky="w")
    admin_frame.columnconfigure(1, weight=1)

    _, question_actions = create_card(
        sidebar,
        "Upload Questions",
        bg=color_sidebar_surface,
        fg=color_sidebar_text,
        border=color_sidebar_border,
        pady=(0, 0),
        padx=12,
    )
    sidebar_footer = tk.Frame(sidebar, bg=color_sidebar, pady=8)
    sidebar_footer.pack(side="bottom", fill="x")

    def reload_admin_info():
        try:
            admin = get_admin_user()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load admin info.\n{exc}")
            return

        if not admin:
            admin_login_entry.delete(0, tk.END)
            admin_pass_entry.delete(0, tk.END)
            return

        admin_login_entry.delete(0, tk.END)
        admin_login_entry.insert(0, admin.get("login_id") or "")
        admin_pass_entry.delete(0, tk.END)
        show_admin_pass_var.set(False)
        toggle_admin_password_visibility()
# This function handles the updating of the admin account credentials, including validation of inputs 
# and error handling for database operations. It allows the admin to change their login ID and/or password, with appropriate feedback messages.
    def update_admin_account():
        new_login = admin_login_entry.get().strip() or None
        new_pass = admin_pass_entry.get().strip() or None

        if new_login is None and new_pass is None:
            messagebox.showinfo("No Changes", "Nothing to update for admin account.")
            return

        # Basic validation for login
        if new_login is not None and len(new_login) < 3:
            messagebox.showerror("Validation Error", "Login ID must be at least 3 characters long.")
            return

        try:
            updated = update_admin_credentials(new_login=new_login, new_password=new_pass)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to update admin account.\n{exc}")
            return

        if not updated:
            messagebox.showerror("Error", "Admin account not found or no changes applied.")
            return

        messagebox.showinfo("Success", "Admin account updated successfully.")
        admin_pass_entry.delete(0, tk.END)
        show_admin_pass_var.set(False)
        toggle_admin_password_visibility()

    create_button(admin_frame, "Update Admin Account", update_admin_account, kind="primary", width=22).grid(
        row=2, column=0, columnspan=3, pady=(8, 0)
    )
    reload_admin_info()
    
# This function validates the form inputs and returns the cleaned data or shows errors
    def validate_student_form():
        name = name_entry.get().strip()
        grade_text = grade_entry.get().strip()
        batch = batch_entry.get().strip()
        enrollment_text = enroll_entry.get().strip()

        errors = []
        first_invalid_field = None

        if not name:
            errors.append("Student name is required.")
            first_invalid_field = name_entry
        elif len(name) > MAX_STUDENT_NAME_LENGTH:
            errors.append(f"Student name cannot exceed {MAX_STUDENT_NAME_LENGTH} characters.")
            first_invalid_field = name_entry
        elif not STUDENT_NAME_PATTERN.fullmatch(name):
            errors.append("Student name can contain only letters, spaces, apostrophe ('), dot (.) and hyphen (-).")
            first_invalid_field = name_entry

        if not grade_text:
            errors.append("Standard is required.")
            if first_invalid_field is None:
                first_invalid_field = grade_entry
        elif not grade_text.isdigit():
            errors.append("Standard must be a number between 1 and 10.")
            if first_invalid_field is None:
                first_invalid_field = grade_entry
        else:
            grade = int(grade_text)
            if grade < 1 or grade > 10:
                errors.append("Standard must be between 1 and 10.")
                if first_invalid_field is None:
                    first_invalid_field = grade_entry

        if batch:
            if len(batch) > MAX_BATCH_LENGTH:
                errors.append(f"Batch cannot exceed {MAX_BATCH_LENGTH} characters.")
                if first_invalid_field is None:
                    first_invalid_field = batch_entry
            elif not BATCH_PATTERN.fullmatch(batch):
                errors.append("Batch can contain only letters, numbers, spaces, slash (/), hyphen (-) and underscore (_).")
                if first_invalid_field is None:
                    first_invalid_field = batch_entry

        if not enrollment_text:
            errors.append("Enrollment/Roll number is required.")
            if first_invalid_field is None:
                first_invalid_field = enroll_entry
        elif not enrollment_text.isdigit():
            errors.append("Enrollment/Roll number must be numeric.")
            if first_invalid_field is None:
                first_invalid_field = enroll_entry

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            if first_invalid_field is not None:
                first_invalid_field.focus_set()
            return None

        grade = int(grade_text)
        enrollment_id = int(enrollment_text)
        return name, grade, batch, enrollment_id
# This function handles the creation of a new student account, including form validation,
# user creation, and updating the UI with the generated credentials
    def add_student():
        validated_form = validate_student_form()
        if not validated_form:
            return

        name, grade, batch, enrollment_id = validated_form

        try:
            login_id, temp_password = create_student_user(
                name=name,
                grade=grade,
                batch=batch if batch else "00",
                enrollment_id=enrollment_id
            )
            
            login_lbl.config(text=f"Login ID: {login_id}")
            pass_lbl.config(text=f"Password: {temp_password}")

            messagebox.showinfo("Student Created", f"Successfully created: {login_id}")

            name_entry.delete(0, tk.END)
            grade_entry.delete(0, tk.END)
            batch_entry.delete(0, tk.END)
            enroll_entry.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create student.\n{e}")
            
# This function opens a dialog for editing existing student information,
# allowing the admin to select a student and update their details with validation
    def open_edit_student_dialog():
        edit_window = tk.Toplevel(root)
        edit_window.title("Edit Student")
        edit_window.geometry("980x560")
        edit_window.minsize(900, 520)
        edit_window.resizable(True, True)
        edit_window.transient(root)
        edit_window.grab_set()
        edit_window.configure(bg=color_bg)

        dialog = tk.Frame(edit_window, bg=color_bg, padx=16, pady=14)
        dialog.pack(fill="both", expand=True)

        tk.Label(
            dialog,
            text="Edit Student",
            font=(FONT_FAMILY_TEXT, 16, "bold"),
            fg=color_text,
            bg=color_bg,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            dialog,
            text="Select a student from the left and update details on the right.",
            font=(FONT_FAMILY_TEXT, 10),
            fg=color_muted,
            bg=color_bg,
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        content = tk.Frame(dialog, bg=color_bg)
        content.grid(row=2, column=0, sticky="nsew")
        dialog.rowconfigure(2, weight=1)
        dialog.columnconfigure(0, weight=1)

        list_card = tk.Frame(
            content,
            bg=color_surface,
            bd=0,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_border,
        )
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(
            list_card,
            text="Select Student",
            font=(FONT_FAMILY_TEXT, 12, "bold"),
            fg=color_text,
            bg=color_surface,
        ).pack(anchor="w", padx=14, pady=(12, 8))

        list_wrap = tk.Frame(list_card, bg=color_surface)
        list_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        student_list = tk.Listbox(
            list_wrap,
            exportselection=False,
            activestyle="none",
            font=(FONT_FAMILY_TEXT, 10),
            bg=color_surface_soft,
            fg=color_text,
            selectbackground="#2F6FB4",
            selectforeground="white",
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_focus,
            relief="flat",
        )
        student_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=student_list.yview)
        student_list.configure(yscrollcommand=student_scroll.set)
        student_list.grid(row=0, column=0, sticky="nsew")
        student_scroll.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        list_wrap.rowconfigure(0, weight=1)
        list_wrap.columnconfigure(0, weight=1)

        form_card = tk.Frame(
            content,
            bg=color_surface,
            bd=0,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_border,
        )
        form_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            form_card,
            text="Student Details",
            font=(FONT_FAMILY_TEXT, 12, "bold"),
            fg=color_text,
            bg=color_surface,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 10))

        form = tk.Frame(form_card, bg=color_surface)
        form.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        form_card.rowconfigure(1, weight=1)
        form_card.columnconfigure(0, weight=1)

        tk.Label(form, text="Student Name", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        edit_name = tk.Entry(form, width=30)
        style_entry(edit_name)
        edit_name.grid(row=0, column=1, sticky="ew", pady=6)

        tk.Label(form, text="Standard (1-10)", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(
            row=1, column=0, sticky="w", pady=6
        )
        edit_grade = tk.Entry(form, width=10)
        style_entry(edit_grade)
        edit_grade.config(validate="key", validatecommand=(grade_validator, "%P"))
        edit_grade.grid(row=1, column=1, sticky="w", pady=6)

        tk.Label(form, text="Batch", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(
            row=2, column=0, sticky="w", pady=6
        )
        edit_batch = tk.Entry(form, width=30)
        style_entry(edit_batch)
        edit_batch.grid(row=2, column=1, sticky="ew", pady=6)

        tk.Label(form, text="Enrollment/Roll No", bg=color_surface, fg=color_text, font=(FONT_FAMILY_TEXT, 10)).grid(
            row=3, column=0, sticky="w", pady=6
        )
        edit_enroll = tk.Entry(form, width=10)
        style_entry(edit_enroll)
        edit_enroll.config(validate="key", validatecommand=(enroll_validator, "%P"))
        edit_enroll.grid(row=3, column=1, sticky="w", pady=6)

        status_label = tk.Label(
            form,
            text="Login ID: -",
            fg=color_primary,
            bg=color_surface,
            font=(FONT_FAMILY_TEXT, 11, "bold"),
        )
        status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 10))

        form.columnconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        students_cache = []


        def selected_student():
            selected_indices = student_list.curselection()
            if not selected_indices:
                return None
            return students_cache[selected_indices[0]]

        def load_selected_student(_event=None):
            student = selected_student()
            if not student:
                return

            edit_name.delete(0, tk.END)
            edit_name.insert(0, student["name"] or "")

            edit_grade.delete(0, tk.END)
            edit_grade.insert(0, str(student["grade"]))

            edit_batch.delete(0, tk.END)
            edit_batch.insert(0, student["batch"] or "")

            edit_enroll.delete(0, tk.END)
            if student["enrollment_id"] is not None:
                edit_enroll.insert(0, str(student["enrollment_id"]))

            status_label.config(text=f"Login ID: {student['login_id'] or '-'}", fg=color_primary)

        def reload_students(selected_id=None):
            nonlocal students_cache
            try:
                raw_students = get_all_students()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to load students.\n{exc}", parent=edit_window)
                edit_window.destroy()
                return

            students_cache = [normalize_student_row(row) for row in raw_students]
            student_list.delete(0, tk.END)

            if not students_cache:
                status_label.config(text="No students found.", fg=color_muted)
                edit_name.delete(0, tk.END)
                edit_grade.delete(0, tk.END)
                edit_batch.delete(0, tk.END)
                edit_enroll.delete(0, tk.END)
                return

            for student in students_cache:
                student_list.insert(tk.END, format_student_label(student))

            index_to_select = 0
            if selected_id:
                for index, student in enumerate(students_cache):
                    if student["id"] == selected_id:
                        index_to_select = index
                        break

            student_list.selection_clear(0, tk.END)
            student_list.selection_set(index_to_select)
            student_list.activate(index_to_select)
            load_selected_student()
# this function validates the edited student information and saves the changes to the database,
# updating the UI accordingly
        def save_student_changes():
            student = selected_student()
            if not student:
                messagebox.showerror("Validation Error", "Select a student first.", parent=edit_window)
                return

            name = edit_name.get().strip()
            grade_text = edit_grade.get().strip()
            batch = edit_batch.get().strip()
            enrollment_text = edit_enroll.get().strip()

            errors = []
            if not name:
                errors.append("Student name is required.")
            elif len(name) > MAX_STUDENT_NAME_LENGTH:
                errors.append(f"Student name cannot exceed {MAX_STUDENT_NAME_LENGTH} characters.")
            elif not STUDENT_NAME_PATTERN.fullmatch(name):
                errors.append("Student name can contain only letters, spaces, apostrophe ('), dot (.) and hyphen (-).")

            if not grade_text:
                errors.append("Standard is required.")
            elif not grade_text.isdigit() or not (1 <= int(grade_text) <= 10):
                errors.append("Standard must be between 1 and 10.")

            if batch:
                if len(batch) > MAX_BATCH_LENGTH:
                    errors.append(f"Batch cannot exceed {MAX_BATCH_LENGTH} characters.")
                elif not BATCH_PATTERN.fullmatch(batch):
                    errors.append("Batch can contain only letters, numbers, spaces, slash (/), hyphen (-) and underscore (_).")

            if enrollment_text and not enrollment_text.isdigit():
                errors.append("Enrollment/Roll number must be numeric.")

            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors), parent=edit_window)
                return

            grade = int(grade_text)
            enrollment_id = int(enrollment_text) if enrollment_text else student["enrollment_id"]

            try:
                updated = update_student_details(
                    student["id"],
                    name=name,
                    grade=grade,
                    batch=batch,
                    enrollment_id=enrollment_id,
                )
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to update student.\n{exc}", parent=edit_window)
                return

            if not updated:
                messagebox.showerror("Error", "Student not found or update failed.", parent=edit_window)
                return

            messagebox.showinfo("Updated", "Student details updated.", parent=edit_window)
            reload_students(selected_id=student["id"])
# this function deletes the selected student from the database
        def delete_selected_student():
            student = selected_student()
            if not student:
                messagebox.showerror("Validation Error", "Select a student first.", parent=edit_window)
                return

            login_value = student["login_id"] or "-"
            enrollment_value = student["enrollment_id"] if student["enrollment_id"] is not None else "-"
            confirmed = messagebox.askyesno(
                "Confirm Delete",
                (
                    "Delete this student account?\n\n"
                    f"Name: {student['name']}\n"
                    f"Standard: {student['grade']}\n"
                    f"Batch: {student['batch'] or '-'}\n"
                    f"Enrollment/Roll: {enrollment_value}\n"
                    f"Login ID: {login_value}\n\n"
                    "This will also delete the student's login and attempts data."
                ),
                parent=edit_window,
            )
            if not confirmed:
                return

            try:
                deleted = delete_student_account(student["id"])
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to delete student.\n{exc}", parent=edit_window)
                return

            if not deleted:
                messagebox.showerror("Error", "Student not found or already deleted.", parent=edit_window)
                reload_students()
                return

            messagebox.showinfo("Deleted", "Student account deleted successfully.", parent=edit_window)
            reload_students()

        student_list.bind("<<ListboxSelect>>", load_selected_student)

        action_row = tk.Frame(form, bg=color_surface)
        action_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        create_button(action_row, "Save Changes", save_student_changes, kind="success", width=15).pack(side="left")
        create_button(action_row, "Delete Student", delete_selected_student, kind="danger", width=15).pack(
            side="left", padx=(8, 0)
        )
        create_button(action_row, "Close", edit_window.destroy, kind="neutral", width=11).pack(side="right")

        reload_students()

    def open_progress_dialog():
        progress_window = tk.Toplevel(root)
        progress_window.title("Student Progress")
        progress_window.geometry("1160x600")
        progress_window.minsize(980, 520)
        progress_window.resizable(True, True)
        progress_window.transient(root)
        progress_window.grab_set()
        progress_window.configure(bg=color_bg)

        dialog = tk.Frame(progress_window, bg=color_bg, padx=16, pady=14)
        dialog.pack(fill="both", expand=True)

        tk.Label(
            dialog,
            text="Student Progress & Scores",
            font=(FONT_FAMILY_TEXT, 16, "bold"),
            fg=color_text,
            bg=color_bg,
        ).pack(anchor="w")
        tk.Label(
            dialog,
            text="Track attempts and export reports as CSV or Excel.",
            font=(FONT_FAMILY_TEXT, 10),
            fg=color_muted,
            bg=color_bg,
        ).pack(anchor="w", pady=(2, 12))

        table_card = tk.Frame(
            dialog,
            bg=color_surface,
            bd=0,
            highlightthickness=1,
            highlightbackground=color_border,
            highlightcolor=color_border,
        )
        table_card.pack(fill="both", expand=True)
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        table_wrap = tk.Frame(table_card, bg=color_surface)
        table_wrap.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))

        columns = (
            "name",
            "grade",
            "batch",
            "enrollment",
            "login",
            "attempts",
            "avg_score",
            "best_score",
            "last_score",
            "last_attempt",
        )
        style.configure(
            "Progress.Treeview",
            background=color_surface_soft,
            fieldbackground=color_surface_soft,
            foreground=color_text,
            bordercolor=color_border,
            rowheight=28,
            relief="flat",
        )
        style.map(
            "Progress.Treeview",
            background=[("selected", "#2E7CFF")],
            foreground=[("selected", "white")],
        )
        style.configure(
            "Progress.Treeview.Heading",
            background="#13253C",
            foreground=color_text,
            font=(FONT_FAMILY_UI, 10, "bold"),
            relief="flat",
            padding=(8, 7),
        )
        style.map("Progress.Treeview.Heading", background=[("active", "#173149")])

        tree = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            height=13,
            style="Progress.Treeview",
        )

        headings = {
            "name": "Student",
            "grade": "Std",
            "batch": "Batch",
            "enrollment": "Roll",
            "login": "Login ID",
            "attempts": "Attempts",
            "avg_score": "Avg Score",
            "best_score": "Best",
            "last_score": "Last",
            "last_attempt": "Last Attempt",
        }
        for key, title in headings.items():
            tree.heading(key, text=title)

        tree.column("name", width=180, anchor="w")
        tree.column("grade", width=60, anchor="center")
        tree.column("batch", width=90, anchor="center")
        tree.column("enrollment", width=80, anchor="center")
        tree.column("login", width=150, anchor="w")
        tree.column("attempts", width=80, anchor="center")
        tree.column("avg_score", width=80, anchor="center")
        tree.column("best_score", width=80, anchor="center")
        tree.column("last_score", width=80, anchor="center")
        tree.column("last_attempt", width=170, anchor="center")

        tree.tag_configure("even", background=color_surface_soft)
        tree.tag_configure("odd", background="#173149")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        table_wrap.columnconfigure(0, weight=1)
        table_wrap.rowconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        status_label = tk.Label(
            table_card,
            text="",
            fg=color_muted,
            bg=color_surface,
            font=(FONT_FAMILY_TEXT, 10),
        )
        status_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        def create_progress_button(parent, text, command, *, tone="neutral", width=12):
            palette = {
                "neutral": ("#4E607A", "#44556D"),
                "primary": ("#2F6FB4", "#285F99"),
                "success": (color_primary, color_primary_active),
            }
            bg, active_bg = palette.get(tone, palette["neutral"])
            return tk.Button(
                parent,
                text=text,
                command=lambda: (sound_manager.play_button_sound(), command()),
                width=width,
                font=(FONT_FAMILY_UI, 10, "bold"),
                bg=bg,
                fg="white",
                activebackground=active_bg,
                activeforeground="white",
                relief="raised",
                bd=1,
                padx=10,
                pady=7,
                cursor="hand2",
                highlightthickness=0,
            )
        progress_rows_cache = []
        export_headers = [
            "Student",
            "Std",
            "Batch",
            "Roll",
            "Login ID",
            "Attempts",
            "Avg Score",
            "Best",
            "Last",
            "Last Attempt",
        ]

        def format_attempt_time(raw_value):
            if not raw_value:
                return "-"
            if hasattr(raw_value, "strftime"):
                return raw_value.strftime("%Y-%m-%d %H:%M:%S")
            return str(raw_value).replace("T", " ")[:19]

        def build_row_values(row, placeholder="-"):
            attempts = int(row.get("attempts_count") or 0)
            avg_score = float(row.get("avg_score") or 0)
            best_score = int(row.get("best_score") or 0)
            last_score_raw = row.get("last_score")
            last_score = placeholder if last_score_raw is None else int(last_score_raw)

            return [
                row.get("name") or placeholder,
                row.get("grade") if row.get("grade") is not None else placeholder,
                row.get("batch") or placeholder,
                row.get("enrollment_id") if row.get("enrollment_id") is not None else placeholder,
                row.get("login_id") or placeholder,
                attempts,
                f"{avg_score:.2f}",
                best_score,
                last_score,
                format_attempt_time(row.get("last_attempt_at")),
            ]

        def load_progress():
            nonlocal progress_rows_cache
            for item in tree.get_children():
                tree.delete(item)

            try:
                progress_rows = get_student_progress()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to load progress.\n{exc}", parent=progress_window)
                return

            if not progress_rows:
                progress_rows_cache = []
                status_label.config(text="No student records found.", fg=color_muted)
                return

            progress_rows_cache = progress_rows
            for index, row in enumerate(progress_rows):
                row_tag = "even" if index % 2 == 0 else "odd"
                tree.insert(
                    "",
                    "end",
                    values=build_row_values(row, placeholder="-"),
                    tags=(row_tag,),
                )

            status_label.config(text=f"Loaded {len(progress_rows)} students.", fg=color_primary)

        def get_rows_for_export():
            if progress_rows_cache:
                return progress_rows_cache
            load_progress()
            return progress_rows_cache

        def export_progress_csv():
            rows = get_rows_for_export()
            if not rows:
                messagebox.showinfo("Export", "No student data available to export.", parent=progress_window)
                return

            file_path = filedialog.asksaveasfilename(
                parent=progress_window,
                title="Export Student Progress (CSV)",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="student_progress.csv",
            )
            if not file_path:
                return

            try:
                with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(export_headers)
                    for row in rows:
                        writer.writerow(build_row_values(row, placeholder=""))
                messagebox.showinfo("Export Success", f"CSV exported to:\n{file_path}", parent=progress_window)
            except Exception as exc:
                messagebox.showerror("Export Error", f"Could not export CSV.\n{exc}", parent=progress_window)

        def export_progress_excel():
            if Workbook is None:
                messagebox.showerror(
                    "Missing Dependency",
                    "Excel export requires openpyxl.\nInstall with: pip install openpyxl",
                    parent=progress_window,
                )
                return

            rows = get_rows_for_export()
            if not rows:
                messagebox.showinfo("Export", "No student data available to export.", parent=progress_window)
                return

            file_path = filedialog.asksaveasfilename(
                parent=progress_window,
                title="Export Student Progress (Excel)",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile="student_progress.xlsx",
            )
            if not file_path:
                return

            try:
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Student Progress"
                worksheet.append(export_headers)
                for row in rows:
                    worksheet.append(build_row_values(row, placeholder=""))

                worksheet.freeze_panes = "A2"
                worksheet.auto_filter.ref = f"A1:J{len(rows) + 1}"
                workbook.save(file_path)
                messagebox.showinfo("Export Success", f"Excel exported to:\n{file_path}", parent=progress_window)
            except Exception as exc:
                messagebox.showerror("Export Error", f"Could not export Excel.\n{exc}", parent=progress_window)

        def view_student_analytics():
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select a student from the table.", parent=progress_window)
                return
            
            selected_index = tree.index(selected_items[0])
            student_data = progress_rows_cache[selected_index]
            analytics_data = get_detailed_analytics(student_data['id'])
            DetailedAnalyticsWindow(
                progress_window,
                student_data,
                analytics_data,
                allow_reset=True,
                allow_export=True,
                on_reset=load_progress,
            )
        
        actions = tk.Frame(table_card, bg=color_surface)
        actions.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        actions.columnconfigure(3, weight=1)

        create_progress_button(actions, "Refresh", load_progress, tone="neutral", width=12).grid(
            row=0, column=0, sticky="w"
        )
        create_progress_button(actions, "View Analytics", view_student_analytics, tone="primary", width=14).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        create_progress_button(actions, "Export CSV", export_progress_csv, tone="primary", width=12).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        create_progress_button(actions, "Export Excel", export_progress_excel, tone="primary", width=12).grid(
            row=0, column=3, sticky="w", padx=(8, 0)
        )
        create_progress_button(actions, "Close", progress_window.destroy, tone="neutral", width=10).grid(
            row=0, column=4, sticky="e"
        )

        load_progress()

    create_button(form, "Create Student Login", add_student, kind="success", width=22).grid(
        row=4, column=1, sticky="w", pady=10, padx=10
    )

    create_button(student_actions, "Edit Student", open_edit_student_dialog, kind="sidebar_primary", width=18).pack(
        fill="x", pady=(0, 8)
    )
    create_button(student_actions, "View Progress", open_progress_dialog, kind="sidebar_neutral", width=18).pack(
        fill="x"
    )

    create_button(question_actions, "Upload Questions", handle_upload, kind="sidebar_primary", width=18).pack(
        fill="x"
    )
    create_button(sidebar_footer, "Logout", handle_logout, kind="sidebar_logout", width=18).pack(fill="x")
    
class LoginScreen(tk.Frame):
    def _handle_back(self):
        sound_manager.play_button_sound()
        self.destroy()
        self.on_back()

    def __init__(self, master, on_login_success, on_back, heading_text="Login"):
        super().__init__(master, bg=APP_BG_COLOR)
        self.on_login_success = on_login_success
        self.on_back = on_back
        self.heading_text = heading_text

        # Root frame should fill window but we'll center an inner column
        self.pack(fill="both", expand=True)

        create_back_button(
            self,
            text="Back to Home",
            command=self._handle_back,
            width=15,
        ).pack(anchor="w", padx=20, pady=10)

        # Center column that holds the title + card; expands so it stays centered
        content = tk.Frame(self, bg=APP_BG_COLOR)
        content.pack(fill="both", expand=True)

        center_column = tk.Frame(content, bg=APP_BG_COLOR)
        center_column.pack(expand=True)

        tk.Label(
            center_column,
            text="Math Game",
            font=(FONT_FAMILY_DISPLAY, 30, "bold"),
            fg=APP_TITLE_COLOR,
            bg=APP_BG_COLOR,
        ).pack(pady=(10, 4))
        tk.Label(
            center_column,
            text=self.heading_text,
            font=(FONT_FAMILY_TEXT, 15, "bold"),
            fg="#7CCBFF",
            bg=APP_BG_COLOR,
        ).pack(pady=(0, 8))
        tk.Label(
            center_column,
            text="Secure access to student play, admin controls, and progress insights.",
            font=(FONT_FAMILY_TEXT, 10),
            fg="#8FAAC6",
            bg=APP_BG_COLOR,
        ).pack(pady=(0, 22))

        # Compute a responsive target width so the card feels as wide
        # as the main menu column but still keeps side margins.
        self.update_idletasks()
        available_w = max(480, self.winfo_width() or 0)
        card_width = max(560, min(available_w - 180, 820))

        # Login card: wider & taller, centered within the column
        login_card = tk.Frame(
            center_column,
            bg=APP_SURFACE_COLOR,
            padx=34,
            pady=30,
            highlightthickness=1,
            highlightbackground="#27425E",
            width=card_width,
            height=420,
        )
        login_card.pack(padx=32, pady=(0, 64))
        # Respect the explicit width/height instead of shrinking to children
        login_card.pack_propagate(False)

        top_strip = tk.Frame(login_card, bg="#FF8A2B", height=6)
        top_strip.pack(fill="x", pady=(0, 18))

        status_row = tk.Frame(login_card, bg=APP_SURFACE_COLOR)
        status_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            status_row,
            text="AUTH PORTAL",
            font=(FONT_FAMILY_UI, 9, "bold"),
            fg="#74CFFF",
            bg=APP_SURFACE_COLOR,
        ).pack(side="left")
        tk.Label(
            status_row,
            text="LIVE",
            font=(FONT_FAMILY_UI, 9, "bold"),
            fg="#091726",
            bg="#7EE081",
            padx=10,
            pady=3,
        ).pack(side="right")

        tk.Label(
            login_card,
            text="Welcome Back",
            font=(FONT_FAMILY_TEXT, 22, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w")
        tk.Label(
            login_card,
            text="Sign in to continue your challenge in the space-console arena.",
            font=(FONT_FAMILY_TEXT, 10),
            fg="#A5BCD7",
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w", pady=(3, 20))

        tk.Label(
            login_card,
            text="Login ID",
            font=(FONT_FAMILY_TEXT, 10, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w")
        self.login_id = tk.Entry(
            login_card,
            font=(FONT_FAMILY_TEXT, 11),
            bg="#091726",
            fg=APP_TEXT_COLOR,
            insertbackground=APP_TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#21374F",
            highlightcolor="#74CFFF",
        )
        self.login_id.pack(fill="x", pady=(6, 14), ipady=8)

        tk.Label(
            login_card,
            text="Password",
            font=(FONT_FAMILY_TEXT, 10, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w")

        self.password_visible = False
        self.password_show_label = "\U0001F441 Show"
        self.password_hide_label = "\U0001F441 Hide"
        password_row = tk.Frame(
            login_card,
            bg="#091726",
            highlightthickness=1,
            highlightbackground="#21374F"
        )
        password_row.pack(fill="x", pady=(6, 18))

        self.password = tk.Entry(
            password_row,
            font=(FONT_FAMILY_TEXT, 11),
            show="*",
            bg="#091726",
            fg=APP_TEXT_COLOR,
            insertbackground=APP_TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        self.password.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=8, ipady=6)

        self.password_toggle_btn = tk.Button(
            password_row,
            text=self.password_show_label,
            command=self._toggle_password_visibility,
            font=("Segoe UI Emoji", 9, "bold"),
            bg="#173149",
            fg="#C9D7FF",
            activebackground="#23415E",
            activeforeground=APP_TEXT_COLOR,
            relief="flat",
            bd=0,
            width=8,
            takefocus=False,
            cursor="hand2"
        )
        self.password_toggle_btn.pack(side="right", padx=(0, 8), pady=8, ipady=6)
        self.password_toggle_btn.bind("<Enter>", lambda _: self.password_toggle_btn.config(bg="#23415E"))
        self.password_toggle_btn.bind("<Leave>", lambda _: self.password_toggle_btn.config(bg="#173149"))
        self._set_password_visibility(False)

        button_base = tk.Frame(login_card, bg=APP_SURFACE_COLOR)
        button_base.pack(fill="x")

        sign_in_btn = tk.Button(
            button_base,
            text="Sign In",
            command=self._submit,
            font=(FONT_FAMILY_TEXT, 11, "bold"),
            bg=APP_ACCENT_COLOR,
            fg="#07111F",
            activebackground="#FFAA54",
            activeforeground="#07111F",
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        sign_in_btn.pack(fill="x", ipady=11, pady=(2, 4))

        def raise_sign_in():
            sign_in_btn.pack_configure(pady=(0, 4))

        def press_sign_in():
            sign_in_btn.pack_configure(pady=(3, 1))

        sign_in_btn.bind("<Enter>", lambda _: sign_in_btn.config(bg="#FFAA54"))
        sign_in_btn.bind("<Leave>", lambda _: (raise_sign_in(), sign_in_btn.config(bg=APP_ACCENT_COLOR)))
        sign_in_btn.bind("<ButtonPress-1>", lambda _: (press_sign_in(), sign_in_btn.config(bg="#D96E14")))
        sign_in_btn.bind("<ButtonRelease-1>", lambda _: (raise_sign_in(), sign_in_btn.config(bg="#FFAA54")))

        self.login_id.bind("<Return>", lambda _: self.password.focus_set())
        self.password.bind("<Return>", lambda _: self._submit())
        self.login_id.focus_set()

# password visibility toggle helper
    def _set_password_visibility(self, is_visible: bool):
        self.password_visible = is_visible
        self.password.config(show="" if self.password_visible else "*")
        self.password_toggle_btn.config(
            text=self.password_hide_label if self.password_visible else self.password_show_label
        )
    def _toggle_password_visibility(self):
        sound_manager.play_button_sound()
        self._set_password_visibility(not self.password_visible)
        self.password.focus_set()
        self.password.icursor(tk.END)

    def _validate_login_form(self):
        login_id = self.login_id.get().strip()
        password = self.password.get()

        if not login_id:
            messagebox.showerror("Validation Error", "Login ID is required.")
            self.login_id.focus_set()
            return None

        if len(login_id) > MAX_LOGIN_ID_LENGTH:
            messagebox.showerror(
                "Validation Error",
                f"Login ID cannot exceed {MAX_LOGIN_ID_LENGTH} characters."
            )
            self.login_id.focus_set()
            return None

        if not LOGIN_ID_PATTERN.fullmatch(login_id):
            messagebox.showerror(
                "Validation Error",
                "Login ID can contain only letters, numbers, dot (.), underscore (_) and hyphen (-)."
            )
            self.login_id.focus_set()
            return None

        if not password:
            messagebox.showerror("Validation Error", "Password is required.")
            self.password.focus_set()
            return None

        if len(password) > MAX_PASSWORD_LENGTH:
            messagebox.showerror(
                "Validation Error",
                f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."
            )
            self.password.focus_set()
            return None

        if self.login_id.get() != login_id:
            self.login_id.delete(0, tk.END)
            self.login_id.insert(0, login_id)

        return login_id, password

    def _submit(self):
        sound_manager.play_button_sound()
        validated_form = self._validate_login_form()
        if not validated_form:
            return

        login_id, password = validated_form
        user = login_user(login_id, password)
        if not user:
            messagebox.showerror("Error", "Invalid credentials")
            return
        self.on_login_success(user)

LOGIN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
STUDENT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]*$")
BATCH_PATTERN = re.compile(r"^[A-Za-z0-9 _/-]+$")
MAX_LOGIN_ID_LENGTH = 50
MAX_PASSWORD_LENGTH = 128
MAX_STUDENT_NAME_LENGTH = 60
MAX_BATCH_LENGTH = 30


if __name__ == "__main__":
    init_db()
    ensure_default_admin()
    if callable(run_qt_splash):
        run_qt_splash()
    root = tk.Tk()
    root.withdraw()
    game = AsteroidMathGame(root)
    root.mainloop()
   
