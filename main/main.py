import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import time
import math
from PIL.ImageChops import screen
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
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
try:
    from PySide6.QtCore import QRectF, Qt, QTimer
    from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QDialog,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception:
    QAbstractItemView = None
    QApplication = None
    QDialog = None
    QFileDialog = None
    QRectF = None
    Qt = None
    QTimer = None
    QColor = None
    QLinearGradient = None
    QPainter = None
    QPainterPath = None
    QPen = None
    QRadialGradient = None
    QFrame = None
    QGridLayout = None
    QHBoxLayout = None
    QHeaderView = None
    QLabel = None
    QLineEdit = None
    QMessageBox = None
    QPushButton = None
    QScrollArea = None
    QSizePolicy = None
    QTableWidget = None
    QTableWidgetItem = None
    QVBoxLayout = None
    QWidget = None
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
    get_detailed_analytics,
    reset_student_analytics,
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
        self._ensure_root_viewport()
        self.root.bind("<F11>", self._toggle_window_viewport, add="+")
        self.root.bind("<Escape>", self._exit_viewport_cover, add="+")
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

        self.canvas = tk.Canvas(root, highlightthickness=0, bg=SPLASH_BG_COLOR)
        self.canvas.pack(fill="both", expand=True)

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

    def _ensure_root_viewport(self):
        """Use maximized viewport mode (not true fullscreen) across transitions."""
        if not self.root or not self.root.winfo_exists():
            return
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

    def _toggle_window_viewport(self, _event=None):
        """Toggle between normal window and maximized viewport mode."""
        if not self.root or not self.root.winfo_exists():
            return "break"
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            current_state = str(self.root.state())
            self.root.state("normal" if current_state == "zoomed" else "zoomed")
        except tk.TclError:
            pass
        return "break"

    def _exit_viewport_cover(self, _event=None):
        """Ensure users can always leave covered-screen mode quickly."""
        if not self.root or not self.root.winfo_exists():
            return "break"
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            self.root.state("normal")
        except tk.TclError:
            pass
        return "break"

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
        self._ensure_root_viewport()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=APP_BG_COLOR)
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

    # -------- Start Screen : Splash screen, Admin Login , Student Login , Guest Login , Footer With Credits --------
    
# Splash screen with animated rocket and starfield, shown on app launch and when returning to start screen after visiting portals.
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
        sparkle = max(2, int(size * (1.0 + (brightness * 0.9))))
        vertical_reach = max(3, int(sparkle * 1.7))
        horizontal_reach = max(2, int(sparkle * 1.2))
        inner_notch = max(1, int(sparkle * 0.42))
        points = [
            x,
            y - vertical_reach,
            x + inner_notch,
            y - inner_notch,
            x + horizontal_reach,
            y,
            x + inner_notch,
            y + inner_notch,
            x,
            y + vertical_reach,
            x - inner_notch,
            y + inner_notch,
            x - horizontal_reach,
            y,
            x - inner_notch,
            y - inner_notch,
        ]
        self.canvas.create_polygon(points, fill="#FFFFFF", outline="", smooth=True)
        center_r = max(1, sparkle // 4)
        self.canvas.create_oval(
            x - center_r,
            y - center_r,
            x + center_r,
            y + center_r,
            fill="#FFFFFF",
            outline="",
        )
#Rocket drawing adapted from original by SynCraft Solution's lead designer, using a custom approach to create a playful, stylized rocket with a dynamic flame effect that scales with the animation progress.
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
            orbit_extent = 238 * orbit_progress
            self.canvas.create_arc(
                center_x - (moon_r * 1.32),
                moon_y - (moon_r * 0.10),
                center_x + (moon_r * 1.32),
                moon_y + (moon_r * 1.18),
                start=196,
                extent=orbit_extent,
                style="arc",
                outline="#FFFFFF",
                width=5,
            )

        title_progress = self._ease_out_cubic(max(0.0, min(1.0, (elapsed - 0.95) / 0.9)))
        if title_progress > 0:
            title_size = int(max(34, min(88, (min(width, height) * 0.078) * (0.72 + (0.28 * title_progress)))))
            shadow_offset = max(3, int(title_size * 0.07))
            title_y = moon_y - (moon_r * 0.18)
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
                moon_y + (moon_r * 0.42),
                text="Ready for launch",
                font=(FONT_FAMILY_UI, subtitle_size, "bold"),
                fill="#2E2C37",
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
        self.is_t20_mode = False
        for widget in self.root.winfo_children():
            widget.destroy()

        container = tk.Frame(self.root, bg=APP_BG_COLOR)
        container.pack(fill="both", expand=True)

        content = tk.Frame(
            container,
            bg=APP_SURFACE_COLOR,
            highlightbackground="#38D1FF",
            highlightthickness=2,
            bd=0,
        )
        content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.58)

        tk.Label(
            content,
            text="Math Game",
            font=(FONT_FAMILY_DISPLAY, 34, "bold"),
            fg="#5BCBFF",
            bg=APP_SURFACE_COLOR,
        ).pack(pady=(28, 10))

        tk.Label(
            content,
            text="Qt portal is unavailable. Using the emergency launcher.",
            font=(FONT_FAMILY_UI, 15, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR,
        ).pack(pady=(0, 8))

        tk.Label(
            content,
            text="The full start screen now lives in qt_portal.py. You can still continue with the same three entry points below.",
            font=(FONT_FAMILY_TEXT, 11),
            fg="#D5EAFF",
            bg=APP_SURFACE_COLOR,
            wraplength=560,
            justify="center",
        ).pack(pady=(0, 22))

        button_wrap = tk.Frame(content, bg=APP_SURFACE_COLOR)
        button_wrap.pack()

        for text, callback in (
            ("Admin Login", self.admin_login),
            ("Student Login", self.student_login),
            ("Guest Login (T20)", self.start_t20_flow),
        ):
            btn = self._create_glossy_button(
                text=text,
                callback=callback,
                width=19,
                font=(FONT_FAMILY_UI, 15, "bold"),
                parent=button_wrap,
                variant="amber",
            )
            btn.pack(pady=8)

        tk.Label(
            content,
            text="© 2026 SynCraft Solution",
            font=(FONT_FAMILY_UI, 10),
            fg="#89A9CA",
            bg=APP_SURFACE_COLOR,
        ).pack(side="bottom", pady=(0, 20))

    def _handle_start_screen_selection(self, selected_action):
        if selected_action == "admin":
            self.admin_login()
            return True
        if selected_action == "student":
            self.student_login()
            return True
        if selected_action == "guest":
            self.start_t20_flow()
            return True
        if selected_action is None:
            self.root.destroy()
            return True
        return False

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
                    self._ensure_root_viewport()
                    try:
                        self.root.lift()
                        self.root.focus_force()
                    except tk.TclError:
                        pass

            if self._handle_start_screen_selection(selected_action):
                return

        self._show_legacy_start_screen()

    # ------- Admin Login Flow --------

    def _open_qt_login(self, heading_text, required_role, success_handler, on_back):
        if not callable(run_qt_login):
            return False

        try:
            if self.root.winfo_exists():
                self.root.withdraw()
            result = run_qt_login(heading_text=heading_text, required_role=required_role)
        except Exception:
            return False
        finally:
            if self.root.winfo_exists():
                self.root.deiconify()
                self._ensure_root_viewport()
                try:
                    self.root.lift()
                    self.root.focus_force()
                except tk.TclError:
                    pass

        if result and result.get("action") == "success" and result.get("user"):
            success_handler(result["user"])
            return True

        on_back()
        return True

    def admin_login(self) -> None:
        """Open the admin login flow, preferring the Qt experience when available."""
        if self._open_qt_login(
            heading_text="Admin Login",
            required_role="admin",
            success_handler=self.handle_admin_auth_success,
            on_back=self.show_start_screen,
        ):
            return

        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            self.canvas.destroy()
        LoginScreen(
            self.root,
            on_login_success=self.handle_admin_auth_success,
            on_back=self.show_start_screen,
            heading_text="Admin Login",
        )

    def handle_admin_auth_success(self, user):
        if user["role"] == "admin":
            if self.root.winfo_exists():
                clear_root(self.root)
            if callable(run_qt_admin_panel):
                run_qt_admin_panel(
                    self.root,
                    user,
                    handle_logout=lambda: self.show_login_screen(),
                    handle_upload=self.upload_advanced_questions,
                )
            else:
                show_admin_panel(
                    self.root,
                    user,
                    handle_logout=lambda: self.show_login_screen(),
                    handle_upload=self.upload_advanced_questions,
                )
        else:
            messagebox.showerror(
            "Access Denied",
            "This portal is restricted to Administrators."
            )
    

    def show_login_screen(self):
        if self._open_qt_login(
            heading_text="Admin Login",
            required_role="admin",
            success_handler=self.handle_admin_auth_success,
            on_back=self.show_start_screen,
        ):
            return

        clear_root(self.root)
        LoginScreen(
        self.root,
        on_login_success=self.handle_admin_auth_success,
        on_back=self.show_start_screen,
        heading_text="Admin Login",
        )

    def student_login(self):
        if self._open_qt_login(
            heading_text="Student Login",
            required_role="student",
            success_handler=self.handle_student_auth_success,
            on_back=self.show_start_screen,
        ):
            return

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
        color_bg = "#07111F"
        color_surface = "#0D1A2C"
        color_surface_soft = "#12243A"
        color_text = "#F4F8FF"
        color_muted = "#8EA6C1"
        color_border = "#1D3652"
        color_primary = "#2E7CFF"
        color_primary_active = "#235FCA"
        color_success = APP_ACCENT_COLOR
        color_success_active = "#D96E14"
        color_danger = "#C95D4A"
        color_danger_active = "#A44637"
        color_neutral = "#17314A"
        color_neutral_active = "#214767"
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
        center_x = canvas_w // 2
        hud_top = max(42, int(canvas_h * 0.07))
        is_compact = canvas_w < 820

        if self.timer_label is None:
            elapsed_time = int(time.time() - self.quiz_start_time) if self.quiz_start_time else 0
            timer_mins, timer_secs = divmod(elapsed_time, 60)
            timer_text = f"{timer_mins:02}:{timer_secs:02}"
            timer_center_x = center_x if is_compact else (canvas_w - max(84, int(canvas_w * 0.12)))
            timer_center_y = hud_top + (48 if is_compact else 0)
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
                hud_top,
                text="Advance Maths Quiz",
                font=(FONT_FAMILY_UI, 20 if is_compact else 22, "bold"),
                fill="white",
                tags=("advanced_static",),
            )
            self.advanced_question_counter_item = self.canvas.create_text(
                center_x,
                hud_top + (38 if is_compact else 40),
                text="",
                font=(FONT_FAMILY_UI, 14),
                fill="#E0E0E0",
                tags=("advanced_static",),
            )
            self.advanced_score_item = self.canvas.create_text(
                center_x,
                hud_top + (66 if is_compact else 70),
                text="",
                font=(FONT_FAMILY_UI, 14),
                fill="#E0E0E0",
                tags=("advanced_static",),
            )

            bar_w = max(340, min(620, int(canvas_w * 0.48)))
            bar_x1 = center_x - (bar_w // 2)
            bar_x2 = center_x + (bar_w // 2)
            bar_y1 = hud_top + (84 if is_compact else 90)
            bar_y2 = bar_y1 + 20
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
            self.advanced_back_y = max(120, canvas_h - 44)
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
        bar_w = max(340, min(620, int(canvas_w * 0.48)))
        bar_x1 = center_x - (bar_w // 2)
        bar_x2 = center_x + (bar_w // 2)
        bar_y1 = hud_top + (84 if is_compact else 90)
        bar_y2 = bar_y1 + 20
        self.canvas.coords(
            self.advanced_progress_fill_item,
            bar_x1,
            bar_y1,
            bar_x1 + int((bar_x2 - bar_x1) * progress),
            bar_y2,
        )

        # Dynamic question layout: long questions get more vertical room automatically.
        question_wrap = max(360, min(760, int(canvas_w * 0.72)))
        self.advanced_question_item = self.canvas.create_text(
            center_x,
            bar_y2 + 28,
            text=q_data["question"],
            font=(FONT_FAMILY_UI, 16, "bold"),
            fill="white",
            width=question_wrap,
            anchor="n",
            tags=("advanced_dynamic",),
        )
        bbox = self.canvas.bbox(self.advanced_question_item)
        q_bottom = bbox[3] if bbox else 250
        option_start_y = max(bar_y2 + 84, q_bottom + 24)
        back_y = min(self.advanced_back_y, canvas_h - 45)

        option_count = len(q_data["options"])
        option_button_height = 50
        available_span = max(200, int((back_y - 35) - option_start_y))
        option_step = max(option_button_height + 10, available_span // max(1, option_count))

        option_font_size = 14 if len(q_data["question"]) < 120 else 13
        option_wrap = max(320, min(620, int(canvas_w * 0.60)))
        option_width_chars = max(24, min(42, int(option_wrap / 10)))
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
            (self.canvas.winfo_width() // 2) if self.canvas.winfo_exists() else self._sx(300),
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

        card_w = max(750, min(700, int(canvas_w * 0.43)))
        card_h = max(850, min(1050, int(canvas_h * 0.66)))
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
            card_y1 + int(card_h * 0.10),
            text="Session Summary",
            font=(FONT_FAMILY_UI, body_size - 1, "bold"),
            fill="#9AB6D6",
            state="hidden",
        )

        title_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.22),
            text="Advanced Maths\nQuiz Completed!",
            font=(FONT_FAMILY_UI, title_size, "bold"),
            fill=title_color,
            width=summary_width + 20,
            justify="center",
            state="hidden",
        )
        score_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.41),
            text=f"Your Score: 0 / {total}",
            font=(FONT_FAMILY_UI, score_size, "bold"),
            fill="white",
            state="hidden",
        )
        summary_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.52),
            text=summary,
            font=(FONT_FAMILY_UI, body_size, "bold"),
            fill="#D7E3FC",
            width=summary_width,
            justify="center",
            state="hidden",
        )
        accuracy_item = canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.63),
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
        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 1:
            canvas_h = 800
        center_x = canvas_w // 2
        title_y = max(90, int(canvas_h * 0.20))
        start_y = max(210, int(canvas_h * 0.40))
        spacing = max(82, int(canvas_h * 0.12))
        self.canvas.create_text(
            center_x,
            title_y,
            text="Select Challenge Mode",
            font=(FONT_FAMILY_UI, max(22, int(canvas_h * 0.032)), "bold"),
            fill="white",
        )

        levels = [("Easy", "green"), ("Intermediate", "amber"), ("Expert", "blue")]
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
        back_y = min(canvas_h - 80, last_level_y + max(80, int(canvas_h * 0.11)))
        self.canvas.create_window(center_x, back_y, window=back_btn)

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
        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 1:
            canvas_h = 800
        center_x = canvas_w // 2
        title_y = max(90, int(canvas_h * 0.20))
        start_y = max(210, int(canvas_h * 0.40))
        spacing = max(82, int(canvas_h * 0.12))
        self.canvas.create_text(
            center_x,
            title_y,
            text="Select Time Control",
            font=(FONT_FAMILY_UI, max(22, int(canvas_h * 0.032)), "bold"),
            fill="white",
        )

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
        back_y = min(canvas_h - 80, last_mode_y + max(80, int(canvas_h * 0.11)))
        self.canvas.create_window(center_x, back_y, window=back_btn)


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
        lane_w = max(500, min(760, int(canvas_w * 0.84)))
        lane_x1 = (canvas_w - lane_w) // 2
        button_x_positions = [
            lane_x1 + int(lane_w * 0.14),
            lane_x1 + int(lane_w * 0.38),
            lane_x1 + int(lane_w * 0.62),
            lane_x1 + int(lane_w * 0.86),
        ]
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
                button_x_positions[i],
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
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width() if self.canvas.winfo_exists() else 600
        if canvas_w <= 1:
            canvas_w = 600
        lane_w = max(500, min(760, int(canvas_w * 0.84)))
        lane_x1 = (canvas_w - lane_w) // 2
        lane_x2 = lane_x1 + lane_w
        x_pos = random.randint(lane_x1 + 10, lane_x2 - 90)
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
        card_w = max(560, min(1080, int(canvas_w * 0.80)))
        card_h = max(460, min(760, int(canvas_h * 0.82)))
        card_x1 = center_x - (card_w // 2)
        card_x2 = center_x + (card_w // 2)
        card_y1 = (canvas_h - card_h) // 2
        card_y2 = card_y1 + card_h

        canvas.create_rectangle(
            card_x1 - 4,
            card_y1 - 4,
            card_x2 + 4,
            card_y2 + 4,
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
            card_x1 + 20,
            card_y1 + 16,
            card_x2 - 20,
            card_y1 + 24,
            fill="#59B9EC",
            outline="",
        )

        heading_size = max(24, min(42, int(card_h * 0.08)))
        subheading_size = max(15, min(22, int(card_h * 0.042)))
        body_wrap = max(420, card_w - 110)

        canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.11),
            text="T20 Student Challenge" if is_student_t20 else "T20 Guest Challenge",
            font=(FONT_FAMILY_DISPLAY, heading_size, "bold"),
            fill="white",
        )
        canvas.create_text(
            center_x,
            card_y1 + int(card_h * 0.17),
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

        text_top_y = card_y1 + int(card_h * 0.23)
        buttons_band_h = max(90, int(card_h * 0.17))
        text_bottom_limit = card_y2 - buttons_band_h - 20
        body_size = max(11, min(18, int(card_h * 0.033)))
        text_item = None

        while body_size >= 10:
            if text_item is not None:
                canvas.delete(text_item)
            text_item = canvas.create_text(
                card_x1 + 44,
                text_top_y,
                text=instructions_text,
                font=(FONT_FAMILY_UI, body_size),
                fill="#E2ECF7",
                anchor="nw",
                width=body_wrap,
                justify="left",
            )
            bbox = canvas.bbox(text_item)
            if bbox and bbox[3] <= text_bottom_limit:
                break
            body_size -= 1

        divider_y = text_bottom_limit + 8
        canvas.create_line(card_x1 + 24, divider_y, card_x2 - 24, divider_y, fill="#244A72", width=1)

        btn_row = tk.Frame(self.root, bg="#10243A")
        begin_btn = tk.Button(
            btn_row,
            text="Start T20",
            font=(FONT_FAMILY_UI, 14, "bold"),
            width=14,
            bg="#3FAE4D",
            fg="white",
            activebackground="#2E8B3A",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: self._play_button_and_execute(self.show_t20_difficulty_selection),
        )
        begin_btn.pack(side="left", padx=(0, 12))

        back_btn = self._create_back_button(
            text="Back",
            callback=self.show_operation_screen if is_student_t20 else self.show_start_screen,
            width=14,
            font=(FONT_FAMILY_UI, 14, "bold"),
            parent=btn_row,
        )
        back_btn.configure(
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            bg="#2A3B57",
            fg="#E6EDFF",
            activebackground="#3A5378",
            activeforeground="white",
            cursor="hand2",
        )
        back_btn.pack(side="left")

        btn_y = card_y2 - max(34, int(buttons_band_h * 0.48))
        canvas.create_window(center_x, btn_y, window=btn_row)

    def show_t20_difficulty_selection(self):
        self.clear_screen()
        self.draw_bg()
        self.root.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 600)
        canvas_h = max(self.canvas.winfo_height(), 800)
        center_x = canvas_w // 2
        is_student_t20 = getattr(self, "t20_session_mode", "guest") == "student"
        level_callback = self.set_t20_level_student if is_student_t20 else self.set_t20_level_guest
        back_callback = self.show_operation_screen if is_student_t20 else self.show_start_screen

        title_y = max(110, int(canvas_h * 0.22))
        first_btn_y = max(220, int(canvas_h * 0.45))
        gap_y = max(90, int(canvas_h * 0.15))

        self.canvas.create_text(
            center_x,
            title_y,
            text="Select Challenge Mode",
            font=(FONT_FAMILY_DISPLAY, max(28, int(canvas_h * 0.045)), "bold"),
            fill="white",
        )
        
        # Easy Button
        easy_btn = tk.Button(self.root, text="EASY (28 Qs)", font=(FONT_FAMILY_UI, 18, "bold"),
                             width=15, height=2, bg="#4CAF50", fg="white",
                             command=lambda: self._play_button_and_execute(lambda: level_callback("easy")))
        self.canvas.create_window(center_x, first_btn_y, window=easy_btn)
        
        # Hard Button
        hard_btn = tk.Button(self.root, text="HARD (56 Qs)", font=(FONT_FAMILY_UI, 18, "bold"),
                             width=15, height=2, bg="#e74c3c", fg="white",
                             command=lambda: self._play_button_and_execute(lambda: level_callback("hard")))
        self.canvas.create_window(center_x, first_btn_y + gap_y, window=hard_btn)
        
        # Back Button
        back_btn = self._create_back_button(
            text="Back",
            callback=back_callback,
            width=12,
            font=(FONT_FAMILY_TEXT, 13, "bold"),
        )
        back_y = min(canvas_h - 90, first_btn_y + (2 * gap_y))
        self.canvas.create_window(center_x, back_y, window=back_btn)

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
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width() if self.canvas.winfo_exists() else 600
        canvas_h = self.canvas.winfo_height() if self.canvas.winfo_exists() else 800
        if canvas_w <= 1:
            canvas_w = 600
        if canvas_h <= 1:
            canvas_h = 800
        center_x = canvas_w // 2
        hud_top = max(34, int(canvas_h * 0.06))
        content_w = max(500, min(760, int(canvas_w * 0.80)))
        content_x1 = center_x - (content_w // 2)
        content_x2 = center_x + (content_w // 2)
        max_q = 28 if getattr(self, "t20_level", "easy") == "easy" else 56
        next_q = min(getattr(self, "t20_q_count", 0) + 1, max_q)

        if not getattr(self, "_t20_screen_ready", False):
            self.clear_screen()
            self.draw_bg()

            self.canvas.create_text(
                center_x,
                hud_top,
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
            self.canvas.create_window(max(70, int(canvas_w * 0.09)), hud_top, window=exit_btn, tags=("t20_static",))

            mins, secs = divmod(self.t20_time_left, 60)
            self.t20_ui_timer = self.canvas.create_text(
                content_x1 + 24,
                hud_top + 36,
                text=f"{mins}:{secs:02d}",
                font=(FONT_FAMILY_MONO, 16, "bold"),
                fill="red",
                anchor="w",
                tags=("t20_static",),
            )

            self.t20_ui_score = self.canvas.create_text(
                center_x,
                hud_top + 66,
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
                content_x2 - 24,
                hud_top + 36,
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
        question_y = hud_top + 132
        option_start_y = question_y + 90
        option_gap = max(58, int(canvas_h * 0.085))
        option_width_chars = max(24, min(44, int(content_w / 10)))
        option_wrap = max(320, min(640, int(content_w * 0.90)))
        self.canvas.create_text(
            center_x,
            question_y,
            text=q_text,
            font=(FONT_FAMILY_UI, max(20, min(28, int(canvas_h * 0.035))), "bold"),
            fill="white",
            width=max(380, int(content_w * 0.90)),
            tags=("t20_dynamic",),
        )

        # MCQ Buttons (aligned as per your 2nd image)
        for i, opt in enumerate(opts):
            btn = tk.Button(self.root, text=str(opt), font=(FONT_FAMILY_UI, 14), width=option_width_chars,
                            bg="#263238", fg="white", activebackground="#455A64",
                            command=lambda o=opt: (sound_manager.play_pop_sound(), self.process_t20_answer(o)))
            self.t20_option_buttons.append(btn)
            self.canvas.create_window(
                center_x,
                option_start_y + (i * option_gap),
                window=btn,
                width=option_wrap,
                tags=("t20_dynamic",),
            )

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
        self.field_default_border = "#21374F"
        self.field_active_border = "#4EC9FF"
        self.field_shells = {}

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
        card_width = max(620, min(available_w - 160, 840))

        # Login card: wider & taller, centered within the column
        login_card = tk.Frame(
            center_column,
            bg=APP_SURFACE_COLOR,
            padx=24,
            pady=24,
            highlightthickness=1,
            highlightbackground="#27425E",
            width=card_width,
            height=380,
        )
        login_card.pack(padx=32, pady=(0, 64))
        # Respect the explicit width/height instead of shrinking to children
        login_card.pack_propagate(False)

        top_strip = tk.Frame(login_card, bg="#FF8A2B", height=6)
        top_strip.pack(fill="x", pady=(0, 18))

        card_body = tk.Frame(login_card, bg=APP_SURFACE_COLOR)
        card_body.pack(fill="both", expand=True)

        hero_panel = tk.Frame(
            card_body,
            bg="#11243A",
            width=280,
            padx=24,
            pady=24,
            highlightthickness=1,
            highlightbackground="#23415E",
        )
        hero_panel.pack(side="left", fill="y", padx=(0, 22))
        hero_panel.pack_propagate(False)

        tk.Label(
            hero_panel,
            text="MISSION CONTROL",
            font=(FONT_FAMILY_UI, 9, "bold"),
            fg="#74CFFF",
            bg="#11243A",
        ).pack(anchor="w")
        tk.Label(
            hero_panel,
            text=self.heading_text,
            font=(FONT_FAMILY_DISPLAY, 24, "bold"),
            fg=APP_TITLE_COLOR,
            bg="#11243A",
        ).pack(anchor="w", pady=(10, 6))
        tk.Label(
            hero_panel,
            text="Sign in to continue.",
            font=(FONT_FAMILY_TEXT, 10),
            fg="#A8C2DE",
            bg="#11243A",
            justify="left",
            wraplength=220,
        ).pack(anchor="w", pady=(0, 8))

        form_panel = tk.Frame(card_body, bg=APP_SURFACE_COLOR)
        form_panel.pack(side="left", fill="both", expand=True)

        status_row = tk.Frame(form_panel, bg=APP_SURFACE_COLOR)
        status_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            status_row,
            text="AUTH PORTAL",
            font=(FONT_FAMILY_UI, 9, "bold"),
            fg="#74CFFF",
            bg=APP_SURFACE_COLOR,
        ).pack(side="left")
        # tk.Label(
        #     status_row,
        #     text="LIVE",
        #     font=(FONT_FAMILY_UI, 9, "bold"),
        #     fg="#091726",
        #     bg="#7EE081",
        #     padx=10,
        #     pady=3,
        # ).pack(side="right")

        tk.Label(
            form_panel,
            text="Welcome Back",
            font=(FONT_FAMILY_TEXT, 22, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w")
        tk.Label(
            form_panel,
            text="Enter your credentials.",
            font=(FONT_FAMILY_TEXT, 10),
            fg="#A5BCD7",
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w", pady=(3, 18))

        self._build_field_group(
            form_panel,
            label_text="Login ID",
            prefix_text="ID",
            field_attr="login_id",
            hint_text="",
        )
        self._build_field_group(
            form_panel,
            label_text="Password",
            prefix_text="KEY",
            field_attr="password",
            hint_text="",
            is_password=True,
        )

        button_base = tk.Frame(form_panel, bg=APP_SURFACE_COLOR)
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
        self._set_field_highlight(self.login_id, True)

    def _build_field_group(self, parent, label_text, prefix_text, field_attr, hint_text, is_password=False):
        tk.Label(
            parent,
            text=label_text,
            font=(FONT_FAMILY_TEXT, 10, "bold"),
            fg=APP_TEXT_COLOR,
            bg=APP_SURFACE_COLOR
        ).pack(anchor="w")

        field_shell = tk.Frame(
            parent,
            bg="#091726",
            highlightthickness=1,
            highlightbackground=self.field_default_border,
        )
        field_shell.pack(fill="x", pady=(6, 6))

        tk.Label(
            field_shell,
            text=prefix_text,
            font=(FONT_FAMILY_UI, 9, "bold"),
            fg="#74CFFF",
            bg="#091726",
            padx=14,
            pady=12,
        ).pack(side="left")

        entry = tk.Entry(
            field_shell,
            font=(FONT_FAMILY_TEXT, 11),
            bg="#091726",
            fg=APP_TEXT_COLOR,
            insertbackground=APP_TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=0,
            show="*" if is_password else "",
        )
        if is_password:
            entry.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=8, ipady=6)
        else:
            entry.pack(side="left", fill="x", expand=True, padx=(4, 12), pady=8, ipady=6)

        if is_password:
            self.password_visible = False
            self.password_show_label = "SHOW"
            self.password_hide_label = "HIDE"
            self.password_toggle_btn = tk.Button(
                field_shell,
                text=self.password_show_label,
                command=self._toggle_password_visibility,
                font=(FONT_FAMILY_UI, 8, "bold"),
                bg="#173149",
                fg="#C9D7FF",
                activebackground="#23415E",
                activeforeground=APP_TEXT_COLOR,
                relief="flat",
                bd=0,
                width=7,
                takefocus=False,
                cursor="hand2"
            )
            self.password_toggle_btn.pack(side="right", padx=(0, 8), pady=8, ipady=6)
            self.password_toggle_btn.bind("<Enter>", lambda _: self.password_toggle_btn.config(bg="#23415E"))
            self.password_toggle_btn.bind("<Leave>", lambda _: self.password_toggle_btn.config(bg="#173149"))
            self._set_password_visibility(False)

        if hint_text:
            tk.Label(
                parent,
                text=hint_text,
                font=(FONT_FAMILY_TEXT, 9),
                fg="#7F9CBC",
                bg=APP_SURFACE_COLOR,
                justify="left",
            ).pack(anchor="w", pady=(0, 14))
        else:
            tk.Frame(parent, bg=APP_SURFACE_COLOR, height=8).pack(anchor="w")

        setattr(self, field_attr, entry)
        self.field_shells[entry] = field_shell
        entry.bind("<FocusIn>", self._handle_field_focus, add="+")
        entry.bind("<FocusOut>", self._handle_field_blur, add="+")

    def _set_field_highlight(self, widget, is_active):
        field_shell = self.field_shells.get(widget)
        if field_shell and field_shell.winfo_exists():
            field_shell.config(
                highlightbackground=self.field_active_border if is_active else self.field_default_border
            )

    def _handle_field_focus(self, event):
        self._set_field_highlight(event.widget, True)

    def _handle_field_blur(self, event):
        self._set_field_highlight(event.widget, False)

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


QT_LOGIN_COPY = {
    "admin": {
        "eyebrow": "ADMIN AUTH",
        "subtitle": "Secure access for administrators.",
        "body": "Sign in to continue.",
    },
    "student": {
        "eyebrow": "STUDENT AUTH",
        "subtitle": "Secure access for students.",
        "body": "Sign in to continue.",
    },
}


if QApplication is not None:
    class QtLoginWindow(QWidget):
        def __init__(self, heading_text="Login", required_role=None):
            super().__init__()
            self.heading_text = heading_text
            self.required_role = required_role
            self.selected_user = None
            self.result_action = "back"
            self.password_visible = False
            self._stars = []
            self._starfield_size = None
            self._space_phase = 0.0
            self._last_space_tick = time.perf_counter()

            self.setWindowTitle(f"{heading_text} - Math Game")
            self.resize(1040, 640)
            self.setMinimumSize(900, 580)
            self.setObjectName("root")
            self.setStyleSheet(
                """
                QWidget#root {
                    background: transparent;
                }
                QFrame#shell {
                    background: #184B74;
                    border: 2px solid #3CD1FF;
                    border-radius: 28px;
                }
                QFrame#inner {
                    background: rgba(10, 31, 53, 0.94);
                    border: 1px solid #265985;
                    border-radius: 22px;
                }
                QFrame#heroPanel {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #133150, stop:0.55 #10263F, stop:1 #0C1B2D);
                    border: 1px solid #285D88;
                    border-radius: 20px;
                }
                QLabel#eyebrow {
                    color: #CFF4FF;
                    background: #19456C;
                    border: 1px solid #59DAFF;
                    border-radius: 13px;
                    font: 700 12px 'Segoe UI';
                    padding: 7px 14px;
                }
                QLabel#heroTitle {
                    color: #F6FBFF;
                    font: 900 40px Impact;
                }
                QLabel#heroSub {
                    color: #76CFFF;
                    font: 700 18px 'Segoe UI';
                }
                QLabel#heroBody, QLabel#formBody, QLabel#hintText {
                    color: #CFE2F7;
                    font: 400 13px 'Segoe UI';
                }
                QLabel#statusText {
                    color: #7CD5FF;
                    font: 700 11px 'Segoe UI';
                }
                QLabel#statusPill {
                    color: #091726;
                    background: #7EE081;
                    border-radius: 11px;
                    font: 700 11px 'Segoe UI';
                    padding: 4px 12px;
                }
                QLabel#formTitle {
                    color: #F7FBFF;
                    font: 700 28px 'Segoe UI';
                }
                QLabel#formLabel {
                    color: #F7FBFF;
                    font: 700 11px 'Segoe UI';
                }
                QFrame#fieldWrap {
                    background: #091726;
                    border: 1px solid #264967;
                    border-radius: 16px;
                }
                QLabel#fieldPrefix {
                    color: #7AD2FF;
                    font: 700 10px 'Segoe UI';
                    padding-left: 14px;
                    padding-right: 8px;
                }
                QLineEdit {
                    background: transparent;
                    color: #F4F8FF;
                    border: none;
                    font: 400 14px 'Segoe UI';
                    padding: 14px 8px 14px 0;
                }
                QLineEdit:focus {
                    color: #FFFFFF;
                }
                QPushButton#toggleButton {
                    background: #173149;
                    color: #D7E8FF;
                    border: none;
                    border-radius: 12px;
                    font: 700 10px 'Segoe UI';
                    padding: 10px 14px;
                }
                QPushButton#toggleButton:hover {
                    background: #23415E;
                }
                QPushButton#toggleButton:pressed {
                    background: #11263A;
                }
                QPushButton#primaryButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FFB34F, stop:0.48 #FF9727, stop:1 #D66B0F);
                    color: #091726;
                    border: 1px solid #FFD08A;
                    border-radius: 22px;
                    font: 700 14px 'Segoe UI';
                    padding: 13px 18px;
                }
                QPushButton#primaryButton:hover {
                    background: #FFAA36;
                }
                QPushButton#primaryButton:pressed {
                    background: #D96F12;
                }
                QPushButton#secondaryButton {
                    background: #11253B;
                    color: #DCEBFF;
                    border: 1px solid #315B7F;
                    border-radius: 20px;
                    font: 700 13px 'Segoe UI';
                    padding: 11px 18px;
                }
                QPushButton#secondaryButton:hover {
                    background: #18314C;
                }
                QPushButton#secondaryButton:pressed {
                    background: #0C1D2F;
                }
                QLabel#inlineStatus {
                    border-radius: 12px;
                    font: 600 11px 'Segoe UI';
                    padding: 9px 12px;
                }
                """
            )
            self._space_timer = QTimer(self)
            self._space_timer.timeout.connect(self._advance_space_scene)
            self._space_timer.start(16)
            self._build_ui()

        def _build_ui(self):
            copy = QT_LOGIN_COPY.get(self.required_role, QT_LOGIN_COPY["student"])

            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(70, 46, 70, 32)
            root_layout.setSpacing(20)
            root_layout.addStretch(1)

            shell = QFrame()
            shell.setObjectName("shell")
            shell.setMaximumWidth(1120)
            shell_layout = QVBoxLayout(shell)
            shell_layout.setContentsMargins(28, 18, 28, 18)
            shell_layout.setSpacing(18)

            top_line = QFrame()
            top_line.setFixedHeight(5)
            top_line.setStyleSheet("background: #46D8FF; border-radius: 2px;")
            shell_layout.addWidget(top_line)

            inner = QFrame()
            inner.setObjectName("inner")
            inner_layout = QHBoxLayout(inner)
            inner_layout.setContentsMargins(34, 32, 34, 32)
            inner_layout.setSpacing(34)

            hero_panel = QFrame()
            hero_panel.setObjectName("heroPanel")
            hero_panel.setMinimumWidth(280)
            hero_layout = QVBoxLayout(hero_panel)
            hero_layout.setContentsMargins(26, 26, 26, 26)
            hero_layout.setSpacing(12)

            eyebrow = QLabel(copy["eyebrow"])
            eyebrow.setObjectName("eyebrow")
            eyebrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            hero_layout.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignLeft)

            title = QLabel(self.heading_text)
            title.setObjectName("heroTitle")
            title.setWordWrap(True)
            hero_layout.addWidget(title)

            subtitle = QLabel(copy["subtitle"])
            subtitle.setObjectName("heroSub")
            subtitle.setWordWrap(True)
            hero_layout.addWidget(subtitle)

            body = QLabel(copy["body"])
            body.setObjectName("heroBody")
            body.setWordWrap(True)
            hero_layout.addWidget(body)
            hero_layout.addStretch(1)

            form_col = QVBoxLayout()
            form_col.setSpacing(12)

            status_row = QHBoxLayout()
            status_row.setSpacing(12)

            status_text = QLabel("AUTH PORTAL")
            status_text.setObjectName("statusText")
            status_row.addWidget(status_text, 0, Qt.AlignmentFlag.AlignLeft)

            status_row.addStretch(1)

            # status_pill = QLabel("LIVE")
            # status_pill.setObjectName("statusPill")
            # status_row.addWidget(status_pill, 0, Qt.AlignmentFlag.AlignRight)
            # form_col.addLayout(status_row)

            form_title = QLabel("Welcome Back")
            form_title.setObjectName("formTitle")
            form_col.addWidget(form_title)

            self.status_label = QLabel("Enter your credentials.")
            self.status_label.setObjectName("inlineStatus")
            self._set_status("Enter your credentials.", tone="info")
            form_col.addWidget(self.status_label)

            self.login_edit = self._build_field(
                form_col,
                label_text="Login ID",
                prefix_text="ID",
                placeholder="Enter your Login ID",
                hint_text="",
                is_password=False,
            )
            self.login_edit.setMaxLength(MAX_LOGIN_ID_LENGTH)

            self.password_edit = self._build_field(
                form_col,
                label_text="Password",
                prefix_text="KEY",
                placeholder="Enter your password",
                hint_text="",
                is_password=True,
            )
            self.password_edit.setMaxLength(MAX_PASSWORD_LENGTH)

            button_row = QHBoxLayout()
            button_row.setSpacing(12)

            back_button = QPushButton("Back")
            back_button.setObjectName("secondaryButton")
            back_button.setCursor(Qt.CursorShape.PointingHandCursor)
            back_button.clicked.connect(self._go_back)
            button_row.addWidget(back_button)

            sign_in_button = QPushButton("Sign In")
            sign_in_button.setObjectName("primaryButton")
            sign_in_button.setCursor(Qt.CursorShape.PointingHandCursor)
            sign_in_button.clicked.connect(self._submit)
            button_row.addWidget(sign_in_button, 1)
            form_col.addLayout(button_row)
            form_col.addStretch(1)

            inner_layout.addWidget(hero_panel, 10)
            inner_layout.addLayout(form_col, 11)
            shell_layout.addWidget(inner)

            root_layout.addWidget(shell, 0, Qt.AlignmentFlag.AlignHCenter)
            root_layout.addStretch(1)

            self.login_edit.returnPressed.connect(self.password_edit.setFocus)
            self.password_edit.returnPressed.connect(self._submit)
            self.login_edit.setFocus()

        def _build_field(self, layout, label_text, prefix_text, placeholder, hint_text, is_password=False):
            label = QLabel(label_text)
            label.setObjectName("formLabel")
            layout.addWidget(label)

            field_wrap = QFrame()
            field_wrap.setObjectName("fieldWrap")
            field_layout = QHBoxLayout(field_wrap)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(0)

            prefix = QLabel(prefix_text)
            prefix.setObjectName("fieldPrefix")
            prefix.setAlignment(Qt.AlignmentFlag.AlignCenter)
            prefix.setMinimumWidth(54)
            field_layout.addWidget(prefix)

            entry = QLineEdit()
            entry.setPlaceholderText(placeholder)
            entry.setFrame(False)
            if is_password:
                entry.setEchoMode(QLineEdit.EchoMode.Password)
            field_layout.addWidget(entry, 1)

            if is_password:
                self.password_toggle_btn = QPushButton("SHOW")
                self.password_toggle_btn.setObjectName("toggleButton")
                self.password_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self.password_toggle_btn.clicked.connect(self._toggle_password_visibility)
                field_layout.addWidget(self.password_toggle_btn)
                field_layout.setContentsMargins(0, 0, 8, 0)
            else:
                field_layout.setContentsMargins(0, 0, 12, 0)

            layout.addWidget(field_wrap)

            if hint_text:
                hint = QLabel(hint_text)
                hint.setObjectName("hintText")
                hint.setWordWrap(True)
                layout.addWidget(hint)

            return entry

        def _set_status(self, message, tone="error"):
            palette = {
                "error": ("#FFD5D0", "#3A1715", "#8A2F24"),
                "info": ("#D7EEFF", "#10263E", "#2E5E8B"),
            }
            fg, bg, border = palette.get(tone, palette["error"])
            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"""
                QLabel#inlineStatus {{
                    color: {fg};
                    background: {bg};
                    border: 1px solid {border};
                    border-radius: 12px;
                    font: 600 11px 'Segoe UI';
                    padding: 9px 12px;
                }}
                """
            )

        def _toggle_password_visibility(self):
            self.password_visible = not self.password_visible
            self.password_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if self.password_visible else QLineEdit.EchoMode.Password
            )
            self.password_toggle_btn.setText("HIDE" if self.password_visible else "SHOW")
            self.password_edit.setFocus()

        def _go_back(self):
            self.result_action = "back"
            self.close()

        def _submit(self):
            login_id = self.login_edit.text().strip()
            password = self.password_edit.text()

            if not login_id:
                self._set_status("Login ID is required.", tone="error")
                self.login_edit.setFocus()
                return

            if len(login_id) > MAX_LOGIN_ID_LENGTH:
                self._set_status(
                    f"Login ID cannot exceed {MAX_LOGIN_ID_LENGTH} characters.",
                    tone="error",
                )
                self.login_edit.setFocus()
                return

            if not LOGIN_ID_PATTERN.fullmatch(login_id):
                self._set_status(
                    "Login ID can contain only letters, numbers, dot (.), underscore (_) and hyphen (-).",
                    tone="error",
                )
                self.login_edit.setFocus()
                return

            if not password:
                self._set_status("Password is required.", tone="error")
                self.password_edit.setFocus()
                return

            if len(password) > MAX_PASSWORD_LENGTH:
                self._set_status(
                    f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters.",
                    tone="error",
                )
                self.password_edit.setFocus()
                return

            if self.login_edit.text() != login_id:
                self.login_edit.setText(login_id)

            user = login_user(login_id, password)
            if not user:
                self._set_status("Invalid credentials. Check your Login ID and password.", tone="error")
                self.password_edit.selectAll()
                self.password_edit.setFocus()
                return

            if self.required_role and user.get("role") != self.required_role:
                role_label = "Administrators" if self.required_role == "admin" else "Students"
                self._set_status(f"This portal is restricted to {role_label}.", tone="error")
                self.password_edit.selectAll()
                self.password_edit.setFocus()
                return

            self.selected_user = user
            self.result_action = "success"
            self.close()

        def closeEvent(self, event):
            if self.result_action is None:
                self.result_action = "back"
            super().closeEvent(event)

        def _ensure_stars(self):
            size_key = (self.width(), self.height())
            if self._starfield_size == size_key:
                return
            rng = random.Random(11)
            stars = []
            star_count = max(44, (self.width() * self.height()) // 19000)
            for _ in range(star_count):
                stars.append(
                    {
                        "x": rng.randint(18, max(18, self.width() - 18)),
                        "y": rng.randint(18, max(18, self.height() - 18)),
                        "r": rng.choice((2, 2, 3)),
                        "phase": rng.random() * math.pi * 2,
                        "speed": rng.uniform(0.7, 1.5),
                    }
                )
            self._stars = stars
            self._starfield_size = size_key

        def _advance_space_scene(self):
            now = time.perf_counter()
            dt = min(0.05, max(0.0, now - self._last_space_tick))
            self._last_space_tick = now
            self._space_phase = (self._space_phase + (dt * 1.55)) % math.tau
            self.update()

        def _draw_star(self, painter, x, y, size, brightness):
            sparkle = max(2.0, size * (1.0 + (brightness * 0.9)))
            vertical_reach = max(3.0, sparkle * 1.7)
            horizontal_reach = max(2.0, sparkle * 1.2)
            inner_notch = max(1.0, sparkle * 0.42)

            star_path = QPainterPath()
            star_path.moveTo(x, y - vertical_reach)
            star_path.lineTo(x + inner_notch, y - inner_notch)
            star_path.lineTo(x + horizontal_reach, y)
            star_path.lineTo(x + inner_notch, y + inner_notch)
            star_path.lineTo(x, y + vertical_reach)
            star_path.lineTo(x - inner_notch, y + inner_notch)
            star_path.lineTo(x - horizontal_reach, y)
            star_path.lineTo(x - inner_notch, y - inner_notch)
            star_path.closeSubpath()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawPath(star_path)

            center_r = max(1.0, sparkle * 0.25)
            painter.drawEllipse(QRectF(x - center_r, y - center_r, center_r * 2, center_r * 2))

        def paintEvent(self, event):
            self._ensure_stars()
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.fillRect(self.rect(), QColor("#07111F"))

            phase = self._space_phase
            saturn_dx = math.sin(phase * 0.92) * 7
            saturn_dy = math.cos(phase * 0.68) * 5
            mars_dx = math.cos(phase * 0.76) * 6
            mars_dy = math.sin(phase * 0.98) * 5
            moon_angle = phase * 0.95
            moon_orbit_x = math.cos(moon_angle) * 24
            moon_orbit_y = math.sin(moon_angle) * 16

            painter.setPen(Qt.PenStyle.NoPen)

            nebula_left = QRadialGradient(self.width() * 0.26, self.height() * 0.24, 260)
            nebula_left.setColorAt(0.0, QColor(56, 209, 255, 55))
            nebula_left.setColorAt(0.45, QColor(43, 23, 98, 110))
            nebula_left.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(nebula_left)
            painter.drawEllipse(QRectF(40, -10, 520, 360))

            nebula_right = QRadialGradient(self.width() * 0.82, self.height() * 0.28, 210)
            nebula_right.setColorAt(0.0, QColor(46, 124, 255, 70))
            nebula_right.setColorAt(0.5, QColor(20, 60, 128, 90))
            nebula_right.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(nebula_right)
            painter.drawEllipse(QRectF(self.width() - 360, 40, 300, 240))

            orbit_pen = QPen(QColor(56, 209, 255, 48))
            orbit_pen.setWidth(2)
            orbit_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(orbit_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(86 + saturn_dx, 136 + saturn_dy, 330, 112))

            # Draw the rear Saturn ring first so the planet sits between back and front arcs.
            ring_pen_back = QPen(QColor(255, 255, 255, 58))
            ring_pen_back.setWidth(10)
            painter.setPen(ring_pen_back)
            painter.drawArc(QRectF(86 + saturn_dx, 136 + saturn_dy, 330, 112), 18 * 16, 144 * 16)

            painter.setPen(Qt.PenStyle.NoPen)

            saturn = QRadialGradient(256 + saturn_dx, 160 + saturn_dy, 140, 212 + saturn_dx, 124 + saturn_dy)
            saturn.setColorAt(0.0, QColor("#FFF4CF"))
            saturn.setColorAt(0.34, QColor("#E3C97D"))
            saturn.setColorAt(0.68, QColor("#BA9350"))
            saturn.setColorAt(1.0, QColor("#7A5428"))
            painter.setBrush(saturn)
            painter.drawEllipse(QRectF(120 + saturn_dx, 58 + saturn_dy, 250, 250))

            painter.setBrush(QColor(255, 255, 255, 42))
            painter.drawEllipse(QRectF(182 + saturn_dx, 96 + saturn_dy, 62, 50))

            painter.setBrush(QColor(129, 95, 44, 120))
            for rect in (
                QRectF(150 + saturn_dx, 128 + saturn_dy, 178, 26),
                QRectF(166 + saturn_dx, 168 + saturn_dy, 150, 24),
                QRectF(146 + saturn_dx, 206 + saturn_dy, 164, 22),
                QRectF(188 + saturn_dx, 238 + saturn_dy, 112, 18),
            ):
                painter.drawEllipse(rect)

            mars = QRadialGradient(
                self.width() - 180 + mars_dx,
                166 + mars_dy,
                94,
                self.width() - 198 + mars_dx,
                144 + mars_dy,
            )
            mars.setColorAt(0.0, QColor("#FFD2A8"))
            mars.setColorAt(0.34, QColor("#E6935E"))
            mars.setColorAt(0.72, QColor("#B85633"))
            mars.setColorAt(1.0, QColor("#742A17"))
            painter.setBrush(mars)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(self.width() - 256 + mars_dx, 92 + mars_dy, 156, 156))

            painter.setBrush(QColor(255, 255, 255, 34))
            painter.drawEllipse(QRectF(self.width() - 214 + mars_dx, 118 + mars_dy, 42, 32))

            painter.setBrush(QColor(126, 48, 27, 110))
            for rect in (
                QRectF(self.width() - 230 + mars_dx, 138 + mars_dy, 28, 22),
                QRectF(self.width() - 178 + mars_dx, 178 + mars_dy, 34, 28),
                QRectF(self.width() - 148 + mars_dx, 132 + mars_dy, 22, 18),
                QRectF(self.width() - 216 + mars_dx, 206 + mars_dy, 18, 14),
            ):
                painter.drawEllipse(rect)

            ring_pen_front = QPen(QColor("#59DAFF"))
            ring_pen_front.setWidth(4)
            painter.setPen(ring_pen_front)
            painter.drawArc(QRectF(86 + saturn_dx, 136 + saturn_dy, 330, 112), 198 * 16, 158 * 16)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 138, 43, 44))
            painter.drawEllipse(QRectF(self.width() - 228 + mars_dx, self.height() - 152 + mars_dy, 132, 102))

            moon_rect = QRectF(
                self.width() - 178 + mars_dx + moon_orbit_x,
                162 + mars_dy + moon_orbit_y,
                22,
                22,
            )
            painter.setBrush(QColor(255, 255, 255, 38))
            painter.drawEllipse(moon_rect.adjusted(-4, -4, 4, 4))
            painter.setPen(QPen(QColor("#CFEFFF"), 1))
            painter.setBrush(QColor("#EAF6FF"))
            painter.drawEllipse(moon_rect)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(170, 190, 210, 120))
            painter.drawEllipse(moon_rect.adjusted(5, 6, -4, -3))

            painter.setBrush(QColor("#38D1FF"))
            for x, y, r in (
                (92, 82, 2),
                (132, 44, 3),
                (self.width() - 124, 74, 2),
                (self.width() - 82, 132, 3),
                (self.width() - 142, self.height() - 96, 2),
            ):
                painter.drawEllipse(QRectF(x, y, r * 2, r * 2))

            for star in self._stars:
                twinkle = (math.sin((self._space_phase * star["speed"]) + star["phase"]) + 1.0) / 2.0
                self._draw_star(painter, star["x"], star["y"], star["r"], twinkle)


    def run_qt_login(heading_text="Login", required_role=None):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        login_window = QtLoginWindow(heading_text=heading_text, required_role=required_role)
        login_window.showMaximized()
        login_window.raise_()
        login_window.activateWindow()

        while login_window.isVisible():
            app.processEvents()
            time.sleep(0.016)

        return {
            "action": login_window.result_action,
            "user": login_window.selected_user,
        }
else:
    run_qt_login = None


QT_ADMIN_PANEL_STYLES = """
QDialog {
    background: #07111F;
}
QWidget {
    color: #F4F7FF;
    font-family: 'Exo 2';
    font-size: 13px;
}
QWidget#dashboardRoot {
    background: transparent;
}
QFrame#shell {
    background: rgba(7, 17, 31, 0.95);
    border: 1px solid rgba(56, 209, 255, 0.16);
    border-radius: 30px;
}
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(8, 19, 33, 0.99),
        stop:0.55 rgba(13, 34, 56, 0.99),
        stop:1 rgba(7, 17, 31, 0.99));
    border: 1px solid rgba(56, 209, 255, 0.18);
    border-radius: 24px;
}
QFrame#topCard, QFrame#heroCard, QFrame#moduleCard, QFrame#railCard, QFrame#metricCard {
    background: rgba(14, 27, 45, 0.94);
    border: 1px solid rgba(41, 81, 113, 0.56);
    border-radius: 24px;
}
QFrame#heroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(12, 33, 56, 0.98),
        stop:0.55 rgba(14, 27, 45, 0.98),
        stop:1 rgba(8, 19, 33, 0.98));
}
QFrame#mapCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(8, 19, 33, 0.98),
        stop:1 rgba(13, 34, 56, 0.98));
    border: 1px solid rgba(56, 209, 255, 0.16);
    border-radius: 24px;
}
QLabel#brandTitle {
    font: 800 22px 'Rajdhani';
    color: #FFFFFF;
}
QLabel#brandSub {
    color: #9CC9E8;
    font: 600 11px 'Exo 2';
}
QPushButton#navPrimary, QPushButton#navSecondary, QPushButton#navDanger {
    text-align: left;
    padding: 12px 16px;
    border-radius: 16px;
    font: 700 12px 'Rajdhani';
}
QPushButton#navPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2E7CFF, stop:1 #38D1FF);
    color: #07111F;
    border: none;
}
QPushButton#navPrimary:hover {
    background: #55D9FF;
}
QPushButton#navSecondary {
    background: rgba(255, 255, 255, 0.04);
    color: #DDE4FF;
    border: 1px solid rgba(56, 209, 255, 0.10);
}
QPushButton#navSecondary:hover {
    background: rgba(56, 209, 255, 0.10);
}
QPushButton#navDanger {
    background: rgba(255, 138, 43, 0.15);
    color: #FFE6D0;
    border: 1px solid rgba(255, 138, 43, 0.28);
}
QPushButton#navDanger:hover {
    background: rgba(255, 138, 43, 0.24);
}
QLabel#eyebrow {
    color: #D6F6FF;
    background: rgba(56, 209, 255, 0.14);
    border: 1px solid rgba(56, 209, 255, 0.22);
    border-radius: 12px;
    padding: 6px 12px;
    font: 700 11px 'Rajdhani';
}
QLabel#titleLarge {
    color: #FFFFFF;
    font: 800 34px 'Rajdhani';
}
QLabel#heroTitle {
    color: #FFFFFF;
    font: 800 28px 'Rajdhani';
}
QLabel#heroBody, QLabel#bodyMuted, QLabel#activityText, QLabel#sectionBody {
    color: #A9CAE5;
    font: 500 12px 'Exo 2';
}
QLabel#metricLabel {
    color: #80CFFF;
    font: 700 11px 'Rajdhani';
}
QLabel#metricValue {
    color: #FFFFFF;
    font: 800 24px 'Rajdhani';
}
QLabel#sectionTitle {
    color: #FFFFFF;
    font: 800 18px 'Rajdhani';
}
QLabel#fieldLabel {
    color: #DDE4FF;
    font: 700 11px 'Rajdhani';
}
QLabel#settingsKey {
    color: #80CFFF;
    font: 700 11px 'Rajdhani';
}
QLabel#settingsValue {
    color: #FFFFFF;
    font: 700 13px 'Exo 2';
}
QLineEdit {
    background: rgba(255, 255, 255, 0.04);
    color: #F4F7FF;
    border: 1px solid rgba(56, 209, 255, 0.14);
    border-radius: 14px;
    padding: 12px 14px;
    selection-background-color: #2E7CFF;
}
QLineEdit:focus {
    border: 1px solid rgba(56, 209, 255, 0.56);
}
QPushButton#primaryAction, QPushButton#secondaryAction, QPushButton#ghostAction, QPushButton#dangerAction {
    border-radius: 16px;
    padding: 11px 16px;
    font: 700 12px 'Rajdhani';
}
QPushButton#primaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2E7CFF, stop:1 #38D1FF);
    color: #07111F;
    border: none;
}
QPushButton#primaryAction:hover {
    background: #55D9FF;
}
QPushButton#secondaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB05D, stop:1 #FF8A2B);
    color: #07111F;
    border: none;
}
QPushButton#secondaryAction:hover {
    background: #FFC57F;
}
QPushButton#ghostAction {
    background: rgba(255, 255, 255, 0.04);
    color: #E3E8FF;
    border: 1px solid rgba(56, 209, 255, 0.10);
}
QPushButton#ghostAction:hover {
    background: rgba(56, 209, 255, 0.10);
}
QPushButton#dangerAction {
    background: rgba(255, 138, 43, 0.14);
    color: #FFE7D1;
    border: 1px solid rgba(255, 138, 43, 0.20);
}
QPushButton#dangerAction:hover {
    background: rgba(255, 138, 43, 0.24);
}
QTableWidget {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(56, 209, 255, 0.10);
    border-radius: 16px;
    gridline-color: rgba(56, 209, 255, 0.08);
    selection-background-color: rgba(46, 124, 255, 0.35);
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background: rgba(255, 255, 255, 0.05);
    color: #DDE4FF;
    border: none;
    border-bottom: 1px solid rgba(56, 209, 255, 0.12);
    padding: 10px;
    font: 700 11px 'Rajdhani';
}
QScrollArea {
    border: none;
    background: transparent;
}
"""


def _format_qt_admin_attempt_time(raw_value):
    if not raw_value:
        return "-"
    if hasattr(raw_value, "strftime"):
        return raw_value.strftime("%Y-%m-%d %H:%M:%S")
    return str(raw_value).replace("T", " ")[:19]


def _normalize_qt_admin_student_row(row):
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


def _qt_admin_table_item(value, alignment=None):
    item = QTableWidgetItem("" if value is None else str(value))
    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
    if alignment is not None:
        item.setTextAlignment(alignment)
    return item


if QApplication is not None:
    class _QtAdminBaseDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("adminDialog")
            self.setStyleSheet(QT_ADMIN_PANEL_STYLES)
            self.setModal(True)

        def _info(self, title, message):
            QMessageBox.information(self, title, message)

        def _error(self, title, message):
            QMessageBox.critical(self, title, message)

        def _confirm(self, title, message):
            return QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes


    class QtRocketWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumSize(290, 250)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

            painter.setPen(Qt.PenStyle.NoPen)

            panel_gradient = QLinearGradient(0, 0, self.width(), self.height())
            panel_gradient.setColorAt(0.0, QColor(9, 28, 49, 180))
            panel_gradient.setColorAt(0.55, QColor(15, 40, 66, 135))
            panel_gradient.setColorAt(1.0, QColor(7, 17, 31, 40))
            painter.setBrush(panel_gradient)
            painter.drawRoundedRect(self.rect().adjusted(10, 10, -10, -10), 26, 26)

            glow = QRadialGradient(self.width() * 0.60, self.height() * 0.44, self.width() * 0.34)
            glow.setColorAt(0.0, QColor(56, 209, 255, 105))
            glow.setColorAt(0.55, QColor(46, 124, 255, 42))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(glow)
            painter.drawEllipse(QRectF(self.width() * 0.24, self.height() * 0.08, self.width() * 0.62, self.height() * 0.68))

            orbit_pen = QPen(QColor(56, 209, 255, 95))
            orbit_pen.setWidth(2)
            orbit_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(orbit_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(34, 26, self.width() - 82, self.height() - 72))
            painter.drawArc(QRectF(78, 46, self.width() - 150, self.height() - 112), 20 * 16, 220 * 16)

            painter.setPen(Qt.PenStyle.NoPen)
            for x, y, r, color in (
                (32, 42, 3, "#38D1FF"),
                (58, 86, 2, "#FFFFFF"),
                (self.width() - 72, 50, 4, "#FF8A2B"),
                (self.width() - 40, 98, 2, "#38D1FF"),
                (74, self.height() - 42, 3, "#FFFFFF"),
                (self.width() - 94, self.height() - 52, 3, "#38D1FF"),
            ):
                painter.setBrush(QColor(color))
                painter.drawEllipse(QRectF(x, y, r * 2, r * 2))

            for x0, y0, x1, y1 in (
                (28, 166, 96, 144),
                (42, 188, 124, 162),
                (58, 208, 142, 182),
            ):
                streak_pen = QPen(QColor(56, 209, 255, 42))
                streak_pen.setWidth(3)
                painter.setPen(streak_pen)
                painter.drawLine(x0, y0, x1, y1)

            painter.save()
            painter.translate(self.width() * 0.54, self.height() * 0.54)
            painter.rotate(-25)

            exhaust_glow = QRadialGradient(-82, 0, 52)
            exhaust_glow.setColorAt(0.0, QColor(255, 176, 93, 160))
            exhaust_glow.setColorAt(0.6, QColor(255, 138, 43, 70))
            exhaust_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(exhaust_glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(-132, -52, 108, 104))

            flame_outer = QPainterPath()
            flame_outer.moveTo(-84, 0)
            flame_outer.cubicTo(-138, -18, -144, -54, -96, -42)
            flame_outer.cubicTo(-125, -10, -126, 10, -96, 42)
            flame_outer.cubicTo(-144, 54, -138, 18, -84, 0)
            flame_gradient = QLinearGradient(-132, 0, -56, 0)
            flame_gradient.setColorAt(0.0, QColor("#FF8A2B"))
            flame_gradient.setColorAt(0.55, QColor("#FFB05D"))
            flame_gradient.setColorAt(1.0, QColor("#FFF1B8"))
            painter.fillPath(flame_outer, flame_gradient)

            flame_inner = QPainterPath()
            flame_inner.moveTo(-74, 0)
            flame_inner.cubicTo(-112, -10, -112, -28, -80, -20)
            flame_inner.cubicTo(-96, -6, -96, 6, -80, 20)
            flame_inner.cubicTo(-112, 28, -112, 10, -74, 0)
            painter.fillPath(flame_inner, QColor("#FFF6D6"))

            fin_back = QPainterPath()
            fin_back.moveTo(-14, -10)
            fin_back.lineTo(-54, -66)
            fin_back.lineTo(-2, -40)
            fin_back.closeSubpath()
            fin_back_gradient = QLinearGradient(-54, -66, 4, -10)
            fin_back_gradient.setColorAt(0.0, QColor("#1A5FDB"))
            fin_back_gradient.setColorAt(1.0, QColor("#38D1FF"))
            painter.fillPath(fin_back, fin_back_gradient)

            fin_front = QPainterPath()
            fin_front.moveTo(-14, 10)
            fin_front.lineTo(-58, 68)
            fin_front.lineTo(2, 38)
            fin_front.closeSubpath()
            fin_front_gradient = QLinearGradient(-58, 68, 10, 12)
            fin_front_gradient.setColorAt(0.0, QColor("#FF8A2B"))
            fin_front_gradient.setColorAt(1.0, QColor("#FFD08A"))
            painter.fillPath(fin_front, fin_front_gradient)

            body = QPainterPath()
            body.moveTo(-48, 0)
            body.cubicTo(-18, -58, 58, -56, 96, 0)
            body.cubicTo(58, 56, -18, 58, -48, 0)
            body_gradient = QLinearGradient(-50, -44, 92, 44)
            body_gradient.setColorAt(0.0, QColor("#FDFEFF"))
            body_gradient.setColorAt(0.38, QColor("#EAF6FF"))
            body_gradient.setColorAt(1.0, QColor("#BFD6E8"))
            painter.fillPath(body, body_gradient)

            shadow_pen = QPen(QColor(17, 45, 78, 70))
            shadow_pen.setWidth(2)
            painter.setPen(shadow_pen)
            painter.drawPath(body)

            stripe = QPainterPath()
            stripe.moveTo(-2, -22)
            stripe.cubicTo(16, -18, 38, -10, 52, 0)
            stripe.cubicTo(38, 10, 16, 18, -2, 22)
            stripe.cubicTo(6, 10, 6, -10, -2, -22)
            painter.fillPath(stripe, QColor(46, 124, 255, 210))

            nose = QPainterPath()
            nose.moveTo(56, -18)
            nose.cubicTo(80, -14, 94, -7, 102, 0)
            nose.cubicTo(94, 7, 80, 14, 56, 18)
            nose.cubicTo(66, 8, 66, -8, 56, -18)
            painter.fillPath(nose, QColor("#FF8A2B"))

            cockpit_outer = QRadialGradient(18, 0, 28)
            cockpit_outer.setColorAt(0.0, QColor("#DDF7FF"))
            cockpit_outer.setColorAt(0.45, QColor("#73C9FF"))
            cockpit_outer.setColorAt(1.0, QColor("#1445A6"))
            painter.setBrush(cockpit_outer)
            painter.setPen(QPen(QColor("#EAF6FF"), 2))
            painter.drawEllipse(QRectF(-4, -20, 38, 40))

            painter.setBrush(QColor(255, 255, 255, 120))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(2, -16, 12, 10))

            nozzle = QPainterPath()
            nozzle.moveTo(-52, -10)
            nozzle.lineTo(-68, -14)
            nozzle.lineTo(-68, 14)
            nozzle.lineTo(-52, 10)
            nozzle.closeSubpath()
            painter.fillPath(nozzle, QColor("#2A4259"))

            wing = QPainterPath()
            wing.moveTo(6, 18)
            wing.lineTo(56, 56)
            wing.lineTo(22, 4)
            wing.closeSubpath()
            wing_gradient = QLinearGradient(8, 14, 56, 56)
            wing_gradient.setColorAt(0.0, QColor("#2E7CFF"))
            wing_gradient.setColorAt(1.0, QColor("#38D1FF"))
            painter.fillPath(wing, wing_gradient)

            painter.restore()


    class QtStudentManagerDialog(_QtAdminBaseDialog):
        def __init__(self, on_data_changed, parent=None):
            super().__init__(parent)
            self.on_data_changed = on_data_changed
            self.students_cache = []
            self.selected_student_id = None
            self.setWindowTitle("Manage Students")
            self.resize(1120, 650)
            self._build_ui()
            self.reload_students()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(24, 24, 24, 24)
            root.setSpacing(18)

            title = QLabel("Manage Students")
            title.setObjectName("sectionTitle")
            root.addWidget(title)

            subtitle = QLabel("Select a student, update details, or delete the account.")
            subtitle.setObjectName("sectionBody")
            root.addWidget(subtitle)

            content = QHBoxLayout()
            content.setSpacing(18)
            root.addLayout(content, 1)

            table_card = QFrame()
            table_card.setObjectName("moduleCard")
            table_layout = QVBoxLayout(table_card)
            table_layout.setContentsMargins(18, 18, 18, 18)
            table_layout.setSpacing(12)

            self.table = QTableWidget(0, 5)
            self.table.setHorizontalHeaderLabels(["Student", "Std", "Batch", "Roll", "Login ID"])
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for index in range(1, 5):
                self.table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
            self.table.itemSelectionChanged.connect(self._load_selected_student)
            table_layout.addWidget(self.table)
            content.addWidget(table_card, 11)

            form_card = QFrame()
            form_card.setObjectName("moduleCard")
            form_layout = QVBoxLayout(form_card)
            form_layout.setContentsMargins(18, 18, 18, 18)
            form_layout.setSpacing(12)

            form_title = QLabel("Student Details")
            form_title.setObjectName("sectionTitle")
            form_layout.addWidget(form_title)

            self.name_edit = self._create_field(form_layout, "Student Name")
            self.grade_edit = self._create_field(form_layout, "Standard (1-10)")
            self.batch_edit = self._create_field(form_layout, "Batch")
            self.enroll_edit = self._create_field(form_layout, "Enrollment/Roll No")

            self.login_label = QLabel("Login ID: -")
            self.login_label.setObjectName("bodyMuted")
            form_layout.addWidget(self.login_label)
            form_layout.addStretch(1)

            actions = QHBoxLayout()
            actions.setSpacing(10)
            for text, object_name, callback in (
                ("Save Changes", "primaryAction", self.save_student_changes),
                ("Delete Student", "dangerAction", self.delete_selected_student),
                ("Close", "ghostAction", self.accept),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                actions.addWidget(button)
            form_layout.addLayout(actions)
            content.addWidget(form_card, 9)

        def _create_field(self, layout, label_text):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label)
            edit = QLineEdit()
            layout.addWidget(edit)
            return edit

        def _selected_student(self):
            if self.selected_student_id is None:
                return None
            for student in self.students_cache:
                if student["id"] == self.selected_student_id:
                    return student
            return None

        def _load_selected_student(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.students_cache):
                self.selected_student_id = None
                return

            student = self.students_cache[row]
            self.selected_student_id = student["id"]
            self.name_edit.setText(student.get("name") or "")
            self.grade_edit.setText("" if student.get("grade") is None else str(student.get("grade")))
            self.batch_edit.setText(student.get("batch") or "")
            enroll = student.get("enrollment_id")
            self.enroll_edit.setText("" if enroll is None else str(enroll))
            self.login_label.setText(f"Login ID: {student.get('login_id') or '-'}")

        def reload_students(self, selected_id=None):
            try:
                raw_students = get_all_students()
            except Exception as exc:
                self._error("Error", f"Failed to load students.\n{exc}")
                return

            self.students_cache = [_normalize_qt_admin_student_row(row) for row in raw_students]
            self.table.setRowCount(len(self.students_cache))

            for row_index, student in enumerate(self.students_cache):
                values = [
                    student.get("name") or "-",
                    student.get("grade") if student.get("grade") is not None else "-",
                    student.get("batch") or "-",
                    student.get("enrollment_id") if student.get("enrollment_id") is not None else "-",
                    student.get("login_id") or "-",
                ]
                for col_index, value in enumerate(values):
                    alignment = Qt.AlignmentFlag.AlignCenter if col_index > 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    self.table.setItem(row_index, col_index, _qt_admin_table_item(value, int(alignment)))

            if not self.students_cache:
                self.selected_student_id = None
                self.name_edit.clear()
                self.grade_edit.clear()
                self.batch_edit.clear()
                self.enroll_edit.clear()
                self.login_label.setText("Login ID: -")
                return

            index_to_select = 0
            if selected_id:
                for index, student in enumerate(self.students_cache):
                    if student["id"] == selected_id:
                        index_to_select = index
                        break

            self.table.selectRow(index_to_select)
            self._load_selected_student()

        def save_student_changes(self):
            student = self._selected_student()
            if not student:
                self._error("Validation Error", "Select a student first.")
                return

            name = self.name_edit.text().strip()
            grade_text = self.grade_edit.text().strip()
            batch = self.batch_edit.text().strip()
            enrollment_text = self.enroll_edit.text().strip()

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
                self._error("Validation Error", "\n".join(errors))
                return

            try:
                updated = update_student_details(
                    student["id"],
                    name=name,
                    grade=int(grade_text),
                    batch=batch,
                    enrollment_id=int(enrollment_text) if enrollment_text else student["enrollment_id"],
                )
            except Exception as exc:
                self._error("Error", f"Failed to update student.\n{exc}")
                return

            if not updated:
                self._error("Error", "Student not found or update failed.")
                return

            self._info("Updated", "Student details updated.")
            if callable(self.on_data_changed):
                self.on_data_changed()
            self.reload_students(selected_id=student["id"])

        def delete_selected_student(self):
            student = self._selected_student()
            if not student:
                self._error("Validation Error", "Select a student first.")
                return

            login_value = student.get("login_id") or "-"
            enrollment_value = student.get("enrollment_id")
            enrollment_value = enrollment_value if enrollment_value is not None else "-"
            confirmed = self._confirm(
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
            )
            if not confirmed:
                return

            try:
                deleted = delete_student_account(student["id"])
            except Exception as exc:
                self._error("Error", f"Failed to delete student.\n{exc}")
                return

            if not deleted:
                self._error("Error", "Student not found or already deleted.")
                self.reload_students()
                return

            self._info("Deleted", "Student account deleted successfully.")
            if callable(self.on_data_changed):
                self.on_data_changed()
            self.reload_students()


    class QtAnalyticsDialog(_QtAdminBaseDialog):
        def __init__(self, student_data, on_reset=None, parent=None):
            super().__init__(parent)
            self.student_data = student_data
            self.on_reset = on_reset
            self.analytics = []
            self.setWindowTitle(f"Analytics: {student_data.get('name', 'Student')}")
            self.resize(980, 620)
            self._build_ui()
            self.reload_analytics()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(24, 24, 24, 24)
            root.setSpacing(16)

            heading = QLabel(self.student_data.get("name") or "Student")
            heading.setObjectName("sectionTitle")
            root.addWidget(heading)

            meta = self.student_data.get("login_id") or "No login id"
            sub = QLabel(f"Detailed attempts and mastery history for {meta}.")
            sub.setObjectName("sectionBody")
            root.addWidget(sub)

            self.summary = QLabel("")
            self.summary.setObjectName("bodyMuted")
            root.addWidget(self.summary)

            self.table = QTableWidget(0, 8)
            self.table.setHorizontalHeaderLabels(
                ["Section", "Topic", "Level", "Score", "Total Q", "Accuracy", "Avg Speed", "Date"]
            )
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            for index in range(2, 8):
                self.table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
            root.addWidget(self.table, 1)

            actions = QHBoxLayout()
            actions.setSpacing(10)
            for text, object_name, callback in (
                ("Export CSV", "ghostAction", self.export_csv),
                ("Reset Student Data", "dangerAction", self.reset_analytics),
                ("Close", "primaryAction", self.accept),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                actions.addWidget(button)
            root.addLayout(actions)

        def reload_analytics(self):
            student_id = self.student_data.get("id")
            self.analytics = get_detailed_analytics(student_id) if student_id else []
            self.table.setRowCount(len(self.analytics))

            for row_index, entry in enumerate(self.analytics):
                accuracy = float(entry.get("accuracy", 0.0) or 0.0)
                values = [
                    entry.get("section") or "-",
                    entry.get("topic") or "-",
                    entry.get("sub_level") or entry.get("level") or "-",
                    entry.get("score") if entry.get("score") is not None else "-",
                    entry.get("total_q") if entry.get("total_q") is not None else "-",
                    f"{accuracy * 100:.0f}%",
                    f"{float(entry.get('avg_speed') or 0):.2f}s",
                    _format_qt_admin_attempt_time(entry.get("date")),
                ]
                for col_index, value in enumerate(values):
                    alignment = Qt.AlignmentFlag.AlignCenter if col_index != 1 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    self.table.setItem(row_index, col_index, _qt_admin_table_item(value, int(alignment)))

            self.summary.setText(f"Loaded {len(self.analytics)} recorded attempt(s).")

        def export_csv(self):
            if not self.analytics:
                self._info("Export", "No analytics data available to export.")
                return

            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", self.student_data.get("name", "student")).strip("_") or "student"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Analytics CSV",
                os.path.join(PROJECT_ROOT, f"{safe_name}_analytics.csv"),
                "CSV Files (*.csv);;All Files (*.*)",
            )
            if not file_path:
                return

            try:
                with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["Section", "Topic", "Level", "Score", "Total Q", "Accuracy", "Avg Speed", "Date"])
                    for entry in self.analytics:
                        writer.writerow(
                            [
                                entry.get("section") or "",
                                entry.get("topic") or "",
                                entry.get("sub_level") or entry.get("level") or "",
                                entry.get("score") or 0,
                                entry.get("total_q") or 0,
                                f"{float(entry.get('accuracy') or 0) * 100:.2f}",
                                f"{float(entry.get('avg_speed') or 0):.2f}",
                                _format_qt_admin_attempt_time(entry.get("date")),
                            ]
                        )
            except Exception as exc:
                self._error("Export Error", f"Could not export CSV.\n{exc}")
                return

            self._info("Export Success", f"CSV exported to:\n{file_path}")

        def reset_analytics(self):
            student_id = self.student_data.get("id")
            student_name = self.student_data.get("name", "this student")
            if not student_id:
                self._error("Reset Error", "Student record is missing an ID.")
                return

            if not self._confirm(
                "Reset Analytics",
                f"Delete all analytics attempts for {student_name}?\n\nThis cannot be undone.",
            ):
                return

            try:
                deleted_rows = reset_student_analytics(student_id)
            except Exception as exc:
                self._error("Reset Error", f"Could not reset analytics.\n{exc}")
                return

            self.reload_analytics()
            if callable(self.on_reset):
                self.on_reset()

            if deleted_rows == 0:
                self._info("Reset Complete", f"No analytics attempts were found for {student_name}.")
            else:
                self._info("Reset Complete", f"Deleted {deleted_rows} analytics attempt(s) for {student_name}.")


    class QtProgressDialog(_QtAdminBaseDialog):
        def __init__(self, on_data_changed, parent=None):
            super().__init__(parent)
            self.on_data_changed = on_data_changed
            self.progress_rows = []
            self.setWindowTitle("Student Progress")
            self.resize(1260, 680)
            self._build_ui()
            self.load_progress()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(24, 24, 24, 24)
            root.setSpacing(16)

            title = QLabel("Student Progress & Scores")
            title.setObjectName("sectionTitle")
            root.addWidget(title)

            subtitle = QLabel("Track attempts, open analytics, and export reports as CSV or Excel.")
            subtitle.setObjectName("sectionBody")
            root.addWidget(subtitle)

            self.status_label = QLabel("")
            self.status_label.setObjectName("bodyMuted")
            root.addWidget(self.status_label)

            self.table = QTableWidget(0, 10)
            self.table.setHorizontalHeaderLabels(
                ["Student", "Std", "Batch", "Roll", "Login ID", "Attempts", "Avg Score", "Best", "Last", "Last Attempt"]
            )
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            for index in (1, 2, 3, 5, 6, 7, 8, 9):
                self.table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
            root.addWidget(self.table, 1)

            actions = QHBoxLayout()
            actions.setSpacing(10)
            for text, object_name, callback in (
                ("Refresh", "ghostAction", self.load_progress),
                ("View Analytics", "primaryAction", self.view_student_analytics),
                ("Export CSV", "ghostAction", self.export_csv),
                ("Export Excel", "ghostAction", self.export_excel),
                ("Close", "secondaryAction", self.accept),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                actions.addWidget(button)
            root.addLayout(actions)

        def _build_row_values(self, row, placeholder="-"):
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
                _format_qt_admin_attempt_time(row.get("last_attempt_at")),
            ]

        def load_progress(self):
            try:
                self.progress_rows = get_student_progress()
            except Exception as exc:
                self._error("Error", f"Failed to load progress.\n{exc}")
                return

            self.table.setRowCount(len(self.progress_rows))
            for row_index, row in enumerate(self.progress_rows):
                values = self._build_row_values(row, placeholder="-")
                for col_index, value in enumerate(values):
                    alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter if col_index in (0, 4, 9) else Qt.AlignmentFlag.AlignCenter
                    self.table.setItem(row_index, col_index, _qt_admin_table_item(value, int(alignment)))

            self.status_label.setText(
                "No student records found." if not self.progress_rows else f"Loaded {len(self.progress_rows)} student record(s)."
            )

        def _selected_row(self):
            row_index = self.table.currentRow()
            if row_index < 0 or row_index >= len(self.progress_rows):
                return None
            return self.progress_rows[row_index]

        def view_student_analytics(self):
            student_data = self._selected_row()
            if not student_data:
                self._error("No Selection", "Please select a student from the table.")
                return

            dialog = QtAnalyticsDialog(student_data, on_reset=self._after_analytics_reset, parent=self)
            dialog.exec()

        def _after_analytics_reset(self):
            self.load_progress()
            if callable(self.on_data_changed):
                self.on_data_changed()

        def export_csv(self):
            if not self.progress_rows:
                self._info("Export", "No student data available to export.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Student Progress (CSV)",
                os.path.join(PROJECT_ROOT, "student_progress.csv"),
                "CSV Files (*.csv);;All Files (*.*)",
            )
            if not file_path:
                return

            headers = ["Student", "Std", "Batch", "Roll", "Login ID", "Attempts", "Avg Score", "Best", "Last", "Last Attempt"]
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(headers)
                    for row in self.progress_rows:
                        writer.writerow(self._build_row_values(row, placeholder=""))
            except Exception as exc:
                self._error("Export Error", f"Could not export CSV.\n{exc}")
                return

            self._info("Export Success", f"CSV exported to:\n{file_path}")

        def export_excel(self):
            if Workbook is None:
                self._error("Missing Dependency", "Excel export requires openpyxl.\nInstall with: pip install openpyxl")
                return

            if not self.progress_rows:
                self._info("Export", "No student data available to export.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Student Progress (Excel)",
                os.path.join(PROJECT_ROOT, "student_progress.xlsx"),
                "Excel Files (*.xlsx);;All Files (*.*)",
            )
            if not file_path:
                return

            headers = ["Student", "Std", "Batch", "Roll", "Login ID", "Attempts", "Avg Score", "Best", "Last", "Last Attempt"]
            try:
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Student Progress"
                worksheet.append(headers)
                for row in self.progress_rows:
                    worksheet.append(self._build_row_values(row, placeholder=""))
                worksheet.freeze_panes = "A2"
                worksheet.auto_filter.ref = f"A1:J{len(self.progress_rows) + 1}"
                workbook.save(file_path)
            except Exception as exc:
                self._error("Export Error", f"Could not export Excel.\n{exc}")
                return

            self._info("Export Success", f"Excel exported to:\n{file_path}")


    class QtQuestionManagerDialog(_QtAdminBaseDialog):
        def __init__(self, game=None, on_data_changed=None, parent=None):
            super().__init__(parent)
            self.game = game
            self.on_data_changed = on_data_changed
            self.db_files = []
            self.setWindowTitle("Manage Advanced Question Files")
            self.resize(980, 620)
            self._build_ui()
            self.refresh_files()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(24, 24, 24, 24)
            root.setSpacing(16)

            title = QLabel("Manage Advanced Question Files")
            title.setObjectName("sectionTitle")
            root.addWidget(title)

            subtitle = QLabel("Upload TXT files, choose the active quiz bank, or remove old question sets.")
            subtitle.setObjectName("sectionBody")
            subtitle.setWordWrap(True)
            root.addWidget(subtitle)

            self.status_label = QLabel("")
            self.status_label.setObjectName("bodyMuted")
            root.addWidget(self.status_label)

            self.table = QTableWidget(0, 4)
            self.table.setHorizontalHeaderLabels(["Filename", "Type", "Description", "Uploaded At"])
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            root.addWidget(self.table, 1)

            actions = QHBoxLayout()
            actions.setSpacing(10)
            for text, object_name, callback in (
                ("Use Selected", "primaryAction", self.use_selected_file),
                ("Upload TXT...", "secondaryAction", self.upload_files),
                ("Delete", "dangerAction", self.delete_selected_file),
                ("Refresh", "ghostAction", self.refresh_files),
                ("Close", "ghostAction", self.accept),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                actions.addWidget(button)
            root.addLayout(actions)

        def _selected_file(self):
            row_index = self.table.currentRow()
            if row_index < 0 or row_index >= len(self.db_files):
                return None
            return self.db_files[row_index]

        def refresh_files(self):
            try:
                self.db_files = get_all_files()
            except Exception as exc:
                self.db_files = []
                self.status_label.setText(f"Error loading files: {exc}")
                self.table.setRowCount(0)
                return

            self.table.setRowCount(len(self.db_files))
            for row_index, row in enumerate(self.db_files):
                values = [
                    row.get("filename") or row.get("id"),
                    row.get("file_type") or "-",
                    row.get("description") or "-",
                    _format_qt_admin_attempt_time(row.get("uploaded_at")),
                ]
                for col_index, value in enumerate(values):
                    alignment = Qt.AlignmentFlag.AlignCenter if col_index == 1 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    self.table.setItem(row_index, col_index, _qt_admin_table_item(value, int(alignment)))

            if self.db_files:
                self.status_label.setText(f"Loaded {len(self.db_files)} question bank(s).")
            else:
                self.status_label.setText("No uploaded files yet.")

        def use_selected_file(self):
            row = self._selected_file()
            if not row:
                self._error("Select File", "Please select a file from the list.")
                return

            try:
                full_row = get_file_by_id(row["id"])
                if not full_row:
                    self._error("Error", "File not found in the database.")
                    return

                tmp_dir = os.path.join(PROJECT_ROOT, "assets")
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_path = os.path.join(tmp_dir, full_row["filename"])
                with open(tmp_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write(full_row["file_content"])

                if self.game is not None:
                    self.game.load_advanced_questions_from_file(tmp_path)
                    self.game.advanced_questions_file = tmp_path
            except Exception as exc:
                self._error("Error", f"Could not load DB file.\n{exc}")
                return

            if callable(self.on_data_changed):
                self.on_data_changed()
            self._info("Active File Updated", f"Now using: {full_row['filename']}")
            self.status_label.setText(f"Active questions file set to {full_row['filename']}.")

        def upload_files(self):
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select TXT file(s) to upload",
                PROJECT_ROOT,
                "Text Files (*.txt);;All Files (*.*)",
            )
            if not file_paths:
                return

            uploaded = 0
            failed = 0
            for path in file_paths:
                try:
                    with open(path, "r", encoding="utf-8") as file_handle:
                        content = file_handle.read()
                    upload_file(os.path.basename(path), content, file_type="questions", description=None)
                    uploaded += 1
                except Exception:
                    failed += 1

            self.refresh_files()
            if callable(self.on_data_changed):
                self.on_data_changed()
            self.status_label.setText(f"Uploaded {uploaded} file(s); {failed} failed.")

        def delete_selected_file(self):
            row = self._selected_file()
            if not row:
                self._error("Select File", "Select a file to delete.")
                return

            if not self._confirm("Confirm Delete", f"Soft-delete this file from DB?\n\n{row.get('filename') or row.get('id')}"):
                return

            try:
                ok = soft_delete_file(row["id"])
            except Exception as exc:
                self._error("Error", f"Could not delete file.\n{exc}")
                return

            if not ok:
                self._error("Error", "File not found or already deleted.")
                return

            self.refresh_files()
            if callable(self.on_data_changed):
                self.on_data_changed()
            self.status_label.setText("File soft-deleted from DB.")


    class QtAdminPanelWindow(QWidget):
        def __init__(self, root, user, handle_logout, handle_upload):
            super().__init__()
            self.root = root
            self.user = user or {}
            self.handle_logout = handle_logout
            self.handle_upload = handle_upload
            self.student_count = 0
            self.file_count = 0
            self.total_attempts = 0
            self.progress_rows = []
            self.files_cache = []
            self.result_action = "logout"
            self._build_ui()
            self.refresh_dashboard_data()

        def _build_ui(self):
            self.setObjectName("dashboardRoot")
            self.setWindowTitle("Admin Panel - Math Game")
            self.resize(1480, 900)
            self.setMinimumSize(1260, 760)
            self.setStyleSheet(QT_ADMIN_PANEL_STYLES)

            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(34, 28, 34, 28)
            root_layout.setSpacing(0)

            shell = QFrame()
            shell.setObjectName("shell")
            shell_layout = QHBoxLayout(shell)
            shell_layout.setContentsMargins(18, 18, 18, 18)
            shell_layout.setSpacing(18)
            root_layout.addWidget(shell)

            sidebar = QFrame()
            sidebar.setObjectName("sidebar")
            sidebar.setFixedWidth(218)
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.setContentsMargins(18, 20, 18, 20)
            sidebar_layout.setSpacing(14)
            shell_layout.addWidget(sidebar)

            brand = QFrame()
            brand_layout = QVBoxLayout(brand)
            brand_layout.setContentsMargins(0, 0, 0, 0)
            brand_layout.setSpacing(4)
            brand_title = QLabel("Math Game")
            brand_title.setObjectName("brandTitle")
            brand_sub = QLabel("Admin command deck")
            brand_sub.setObjectName("brandSub")
            brand_layout.addWidget(brand_title)
            brand_layout.addWidget(brand_sub)
            sidebar_layout.addWidget(brand)

            nav_hint = QLabel("Choose a task. Each item below goes somewhere meaningful.")
            nav_hint.setObjectName("bodyMuted")
            nav_hint.setWordWrap(True)
            sidebar_layout.addWidget(nav_hint)

            for text, object_name, callback in (
                ("+ Add Student", "navPrimary", self._focus_create_student),
                ("Manage Students", "navSecondary", self.open_student_manager),
                ("Progress Reports", "navSecondary", self.open_progress_dialog),
                ("Question Bank", "navSecondary", self.open_question_manager),
                ("Settings", "navSecondary", self._focus_admin_account),
                ("Logout", "navDanger", self.request_logout),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                sidebar_layout.addWidget(button)
            sidebar_layout.addStretch(1)

            content_wrap = QHBoxLayout()
            content_wrap.setSpacing(18)
            shell_layout.addLayout(content_wrap, 1)

            self.center_scroll = QScrollArea()
            self.center_scroll.setWidgetResizable(True)
            self.center_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            content_wrap.addWidget(self.center_scroll, 1)

            center = QWidget()
            self.center_scroll.setWidget(center)
            center_layout = QVBoxLayout(center)
            center_layout.setContentsMargins(0, 0, 6, 0)
            center_layout.setSpacing(18)

            top_card = QFrame()
            top_card.setObjectName("topCard")
            top_layout = QHBoxLayout(top_card)
            top_layout.setContentsMargins(22, 18, 22, 18)
            top_layout.setSpacing(18)

            title_wrap = QVBoxLayout()
            title_wrap.setSpacing(8)
            eyebrow = QLabel("ADMIN PANEL")
            eyebrow.setObjectName("eyebrow")
            eyebrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            title_wrap.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignLeft)
            self.title_label = QLabel("Welcome, Admin")
            self.title_label.setObjectName("titleLarge")
            title_wrap.addWidget(self.title_label)
            body = QLabel("Use the sidebar to move through student setup, reports, question banks, and admin settings.")
            body.setObjectName("bodyMuted")
            body.setWordWrap(True)
            title_wrap.addWidget(body)
            top_layout.addLayout(title_wrap, 1)

            self.avatar_label = QLabel("A")
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.avatar_label.setFixedSize(56, 56)
            self.avatar_label.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7A59FF, stop:1 #FF7A45);"
                "border-radius: 28px; color: #FFFFFF; font: 800 20px 'Segoe UI';"
            )
            top_layout.addWidget(self.avatar_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            center_layout.addWidget(top_card)

            metrics_row = QHBoxLayout()
            metrics_row.setSpacing(16)
            self.metric_cards = {}
            for key, label in (("students", "Students"), ("files", "Question Banks"), ("attempts", "Attempts")):
                card = QFrame()
                card.setObjectName("metricCard")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(18, 16, 18, 16)
                card_layout.setSpacing(6)
                metric_label = QLabel(label)
                metric_label.setObjectName("metricLabel")
                metric_value = QLabel("0")
                metric_value.setObjectName("metricValue")
                hint = QLabel("")
                hint.setObjectName("bodyMuted")
                hint.setWordWrap(True)
                card_layout.addWidget(metric_label)
                card_layout.addWidget(metric_value)
                card_layout.addWidget(hint)
                metrics_row.addWidget(card, 1)
                self.metric_cards[key] = {"value": metric_value, "hint": hint}
            center_layout.addLayout(metrics_row)

            hero_card = QFrame()
            hero_card.setObjectName("heroCard")
            hero_layout = QHBoxLayout(hero_card)
            hero_layout.setContentsMargins(26, 24, 26, 24)
            hero_layout.setSpacing(18)

            hero_text = QVBoxLayout()
            hero_text.setSpacing(10)
            available = QLabel("Available Now | Admin Flow Upgrade")
            available.setObjectName("eyebrow")
            available.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            hero_text.addWidget(available, 0, Qt.AlignmentFlag.AlignLeft)
            hero_title = QLabel("Design student access, credentials, and reporting from one control deck.")
            hero_title.setObjectName("heroTitle")
            hero_title.setWordWrap(True)
            hero_text.addWidget(hero_title)
            hero_body = QLabel("The layout follows the dark dashboard reference while keeping the same admin capabilities intact.")
            hero_body.setObjectName("heroBody")
            hero_body.setWordWrap(True)
            hero_text.addWidget(hero_body)
            hero_hint = QLabel("Student setup, score tracking, question banks, and security live in one mission deck.")
            hero_hint.setObjectName("bodyMuted")
            hero_hint.setWordWrap(True)
            hero_text.addWidget(hero_hint)
            hero_text.addStretch(1)
            hero_layout.addLayout(hero_text, 12)

            hero_visual = QFrame()
            hero_visual.setObjectName("moduleCard")
            hero_visual_layout = QVBoxLayout(hero_visual)
            hero_visual_layout.setContentsMargins(12, 12, 12, 12)
            hero_visual_layout.setSpacing(6)
            rocket_art = QtRocketWidget()
            hero_visual_layout.addWidget(rocket_art, 1)
            rocket_title = QLabel("Rocket Control")
            rocket_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rocket_title.setObjectName("sectionTitle")
            hero_visual_layout.addWidget(rocket_title)
            rocket_copy = QLabel("Asteroid-theme visuals keep the admin deck connected to the game instead of looking like a generic dashboard.")
            rocket_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rocket_copy.setWordWrap(True)
            rocket_copy.setObjectName("bodyMuted")
            hero_visual_layout.addWidget(rocket_copy)
            hero_layout.addWidget(hero_visual, 7)
            center_layout.addWidget(hero_card)

            self.add_student_card = QFrame()
            self.add_student_card.setObjectName("moduleCard")
            add_layout = QVBoxLayout(self.add_student_card)
            add_layout.setContentsMargins(22, 20, 22, 20)
            add_layout.setSpacing(14)
            add_title = QLabel("Student Launch Bay")
            add_title.setObjectName("sectionTitle")
            add_layout.addWidget(add_title)
            add_sub = QLabel("Create a student profile, generate credentials, and prepare them for the next mission.")
            add_sub.setObjectName("sectionBody")
            add_sub.setWordWrap(True)
            add_layout.addWidget(add_sub)
            add_grid = QGridLayout()
            add_grid.setHorizontalSpacing(14)
            add_grid.setVerticalSpacing(10)
            add_layout.addLayout(add_grid)
            self.student_name_edit = self._build_labeled_edit(add_grid, 0, 0, "Student Name", placeholder="Enter full student name")
            self.student_grade_edit = self._build_labeled_edit(add_grid, 0, 1, "Standard (1-10)", placeholder="e.g. 5")
            self.student_batch_edit = self._build_labeled_edit(add_grid, 1, 0, "Batch (optional)", placeholder="e.g. A1 or 2026")
            self.student_roll_edit = self._build_labeled_edit(add_grid, 1, 1, "Enrollment/Roll No", placeholder="Numeric roll number")
            add_actions = QHBoxLayout()
            add_actions.setSpacing(10)
            for text, object_name, callback in (
                ("Create Student Login", "primaryAction", self.add_student),
                ("Clear", "ghostAction", self._clear_student_form),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                add_actions.addWidget(button)
            add_actions.addStretch(1)
            add_layout.addLayout(add_actions)
            center_layout.addWidget(self.add_student_card)

            credentials_card = QFrame()
            credentials_card.setObjectName("moduleCard")
            credentials_layout = QVBoxLayout(credentials_card)
            credentials_layout.setContentsMargins(22, 20, 22, 20)
            credentials_layout.setSpacing(12)
            cred_title = QLabel("Generated Credentials")
            cred_title.setObjectName("sectionTitle")
            credentials_layout.addWidget(cred_title)
            self.generated_login = QLabel("Login ID: -")
            self.generated_login.setStyleSheet("font: 700 14px 'Consolas'; color: #F6F7FF;")
            self.generated_pass = QLabel("Password: -")
            self.generated_pass.setStyleSheet("font: 700 14px 'Consolas'; color: #F6F7FF;")
            credentials_layout.addWidget(self.generated_login)
            credentials_layout.addWidget(self.generated_pass)
            cred_actions = QHBoxLayout()
            cred_actions.setSpacing(10)
            copy_button = QPushButton("Copy Credentials")
            copy_button.setObjectName("ghostAction")
            copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_button.clicked.connect(self.copy_generated_credentials)
            clear_creds_btn = QPushButton("Clear Credentials")
            clear_creds_btn.setObjectName("ghostAction")
            clear_creds_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_creds_btn.clicked.connect(self.clear_generated_credentials)
            cred_actions.addWidget(copy_button)
            cred_actions.addWidget(clear_creds_btn)
            cred_actions.addStretch(1)
            credentials_layout.addLayout(cred_actions)
            center_layout.addWidget(credentials_card)

            self.admin_account_card = QFrame()
            self.admin_account_card.setObjectName("moduleCard")
            admin_layout = QVBoxLayout(self.admin_account_card)
            admin_layout.setContentsMargins(22, 20, 22, 20)
            admin_layout.setSpacing(14)
            admin_title = QLabel("Settings")
            admin_title.setObjectName("sectionTitle")
            admin_layout.addWidget(admin_title)
            admin_sub = QLabel("Manage admin access, security changes, and quick deck maintenance from one settings panel.")
            admin_sub.setObjectName("sectionBody")
            admin_sub.setWordWrap(True)
            admin_layout.addWidget(admin_sub)
            status_row = QHBoxLayout()
            status_row.setSpacing(16)
            current_label = QLabel("Current Admin")
            current_label.setObjectName("settingsKey")
            self.admin_identity_value = QLabel("-")
            self.admin_identity_value.setObjectName("settingsValue")
            status_row.addWidget(current_label)
            status_row.addWidget(self.admin_identity_value, 1)
            admin_layout.addLayout(status_row)
            admin_grid = QGridLayout()
            admin_grid.setHorizontalSpacing(14)
            admin_grid.setVerticalSpacing(10)
            admin_layout.addLayout(admin_grid)
            self.admin_login_edit = self._build_labeled_edit(admin_grid, 0, 0, "Admin Login ID", placeholder="Enter login ID")
            self.admin_password_edit = self._build_labeled_edit(admin_grid, 0, 1, "New Password", placeholder="Leave blank to keep current password", echo=True)
            self.admin_confirm_password_edit = self._build_labeled_edit(admin_grid, 1, 0, "Confirm New Password", placeholder="Retype new password", echo=True)
            admin_actions = QHBoxLayout()
            admin_actions.setSpacing(10)
            for text, object_name, callback in (
                ("Save Settings", "secondaryAction", self.update_admin_account),
                ("Refresh Deck", "primaryAction", self.refresh_dashboard_data),
                ("Clear Credentials Panel", "ghostAction", self.clear_generated_credentials),
                ("Show / Hide Password", "ghostAction", self.toggle_admin_password_visibility),
            ):
                button = QPushButton(text)
                button.setObjectName(object_name)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(callback)
                admin_actions.addWidget(button)
            admin_actions.addStretch(1)
            admin_layout.addLayout(admin_actions)
            center_layout.addWidget(self.admin_account_card)
            center_layout.addStretch(1)

            right_rail = QVBoxLayout()
            right_rail.setSpacing(18)
            content_wrap.addLayout(right_rail)

            map_card = QFrame()
            map_card.setObjectName("mapCard")
            map_layout = QVBoxLayout(map_card)
            map_layout.setContentsMargins(20, 20, 20, 20)
            map_layout.setSpacing(10)
            map_title = QLabel("Live Admin Map")
            map_title.setObjectName("sectionTitle")
            map_layout.addWidget(map_title)
            self.map_status = QLabel("Awaiting dashboard refresh.")
            self.map_status.setObjectName("sectionBody")
            self.map_status.setWordWrap(True)
            map_layout.addWidget(self.map_status)
            self.map_meta = QLabel("")
            self.map_meta.setObjectName("bodyMuted")
            self.map_meta.setWordWrap(True)
            map_layout.addWidget(self.map_meta)
            map_layout.addStretch(1)
            right_rail.addWidget(map_card)

            quick_card = QFrame()
            quick_card.setObjectName("railCard")
            quick_layout = QVBoxLayout(quick_card)
            quick_layout.setContentsMargins(20, 20, 20, 20)
            quick_layout.setSpacing(10)
            quick_title = QLabel("Flight Checks")
            quick_title.setObjectName("sectionTitle")
            quick_layout.addWidget(quick_title)
            self.flight_labels = []
            for _ in range(4):
                label = QLabel("")
                label.setObjectName("activityText")
                label.setWordWrap(True)
                quick_layout.addWidget(label)
                self.flight_labels.append(label)
            quick_button = QPushButton("Open Settings")
            quick_button.setObjectName("primaryAction")
            quick_button.setCursor(Qt.CursorShape.PointingHandCursor)
            quick_button.clicked.connect(self._focus_admin_account)
            quick_layout.addWidget(quick_button)
            right_rail.addWidget(quick_card)

            activity_card = QFrame()
            activity_card.setObjectName("railCard")
            activity_layout = QVBoxLayout(activity_card)
            activity_layout.setContentsMargins(20, 20, 20, 20)
            activity_layout.setSpacing(10)
            activity_title = QLabel("Activity")
            activity_title.setObjectName("sectionTitle")
            activity_layout.addWidget(activity_title)
            self.activity_labels = []
            for _ in range(5):
                label = QLabel("No activity yet.")
                label.setObjectName("activityText")
                label.setWordWrap(True)
                activity_layout.addWidget(label)
                self.activity_labels.append(label)
            activity_layout.addStretch(1)
            right_rail.addWidget(activity_card, 1)

        def _build_labeled_edit(self, grid, row, col, label_text, placeholder="", echo=False):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            grid.addWidget(label, row * 2, col)
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setClearButtonEnabled(True)
            if echo:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            grid.addWidget(edit, row * 2 + 1, col)
            return edit

        def _get_welcome_name(self):
            welcome_name = "Admin"
            if isinstance(self.user, dict):
                welcome_name = self.user.get("login_id") or self.user.get("name") or "Admin"
            if welcome_name == "Admin":
                try:
                    admin_info = get_admin_user()
                    if admin_info and admin_info.get("login_id"):
                        welcome_name = admin_info.get("login_id")
                except Exception:
                    pass
            return welcome_name

        def _scroll_to_top(self):
            self.center_scroll.verticalScrollBar().setValue(0)

        def _focus_create_student(self):
            QApplication.processEvents()
            target_y = max(0, self.add_student_card.y() - 18)
            self.center_scroll.verticalScrollBar().setValue(target_y)
            self.student_name_edit.setFocus()

        def _focus_admin_account(self):
            self.center_scroll.verticalScrollBar().setValue(self.center_scroll.verticalScrollBar().maximum())
            self.admin_login_edit.setFocus()

        def open_question_manager(self):
            dialog = QtQuestionManagerDialog(game=self.handle_upload.__self__ if hasattr(self.handle_upload, "__self__") else None, on_data_changed=self.refresh_dashboard_data, parent=self)
            dialog.exec()
            self.refresh_dashboard_data()

        def request_logout(self):
            self.result_action = "logout"
            self.close()

        def closeEvent(self, event):
            self.result_action = "logout"
            super().closeEvent(event)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.fillRect(self.rect(), QColor("#07111F"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(10, 64, 98, 92))
            painter.drawEllipse(QRectF(70, 30, 440, 280))
            painter.setBrush(QColor(22, 47, 87, 130))
            painter.drawEllipse(QRectF(self.width() - 430, 70, 320, 250))
            painter.setBrush(QColor(255, 138, 43, 58))
            painter.drawEllipse(QRectF(self.width() - 240, self.height() - 250, 180, 180))

            for x, y, color in (
                (180, 84, "#38D1FF"),
                (240, 110, "#FFFFFF"),
                (1260, 180, "#38D1FF"),
                (1195, 258, "#FF8A2B"),
                (1310, 314, "#38D1FF"),
                (1128, 388, "#FFFFFF"),
            ):
                painter.setBrush(QColor(color))
                painter.drawEllipse(QRectF(x, y, 6, 6))

            painter.save()
            painter.translate(self.width() - 180, 115)
            painter.rotate(18)
            painter.setBrush(QColor("#FF8A2B"))
            flame = QPainterPath()
            flame.moveTo(-18, 0)
            flame.cubicTo(-46, -10, -52, -26, -22, -20)
            flame.cubicTo(-46, -3, -46, 3, -22, 20)
            flame.cubicTo(-52, 26, -46, 10, -18, 0)
            painter.fillPath(flame, QColor("#FF8A2B"))

            body = QPainterPath()
            body.moveTo(0, -18)
            body.cubicTo(26, -26, 58, -16, 74, 0)
            body.cubicTo(58, 16, 26, 26, 0, 18)
            body.cubicTo(10, 6, 10, -6, 0, -18)
            painter.fillPath(body, QColor("#EAF6FF"))
            painter.setBrush(QColor("#2E7CFF"))
            painter.drawEllipse(QRectF(28, -8, 18, 18))

            fin_top = QPainterPath()
            fin_top.moveTo(12, -10)
            fin_top.lineTo(2, -34)
            fin_top.lineTo(28, -16)
            fin_top.closeSubpath()
            painter.fillPath(fin_top, QColor("#38D1FF"))

            fin_bottom = QPainterPath()
            fin_bottom.moveTo(12, 10)
            fin_bottom.lineTo(2, 34)
            fin_bottom.lineTo(28, 16)
            fin_bottom.closeSubpath()
            painter.fillPath(fin_bottom, QColor("#FF8A2B"))
            painter.restore()

        def _show_info(self, title, message):
            QMessageBox.information(self, title, message)

        def _show_error(self, title, message):
            QMessageBox.critical(self, title, message)

        def refresh_dashboard_data(self):
            try:
                students = get_all_students()
            except Exception:
                students = []
            try:
                self.progress_rows = get_student_progress()
            except Exception:
                self.progress_rows = []
            try:
                self.files_cache = get_all_files()
            except Exception:
                self.files_cache = []

            self.student_count = len(students)
            self.file_count = len(self.files_cache)
            self.total_attempts = sum(int(row.get("attempts_count") or 0) for row in self.progress_rows)

            self.metric_cards["students"]["value"].setText(str(self.student_count))
            self.metric_cards["students"]["hint"].setText("Active student records in the roster.")
            self.metric_cards["files"]["value"].setText(str(self.file_count))
            self.metric_cards["files"]["hint"].setText("Uploaded question banks ready for advanced quiz use.")
            self.metric_cards["attempts"]["value"].setText(str(self.total_attempts))
            self.metric_cards["attempts"]["hint"].setText("Recorded attempts across basic, advanced, and T20 modes.")

            welcome_name = self._get_welcome_name()
            self.title_label.setText(f"Welcome, {welcome_name}")
            self.avatar_label.setText(welcome_name[:1].upper())
            self.map_status.setText(f"{self.student_count} students visible across the control deck.")
            self.map_meta.setText(f"{self.file_count} question bank(s) stored. {self.total_attempts} attempt(s) tracked so far.")
            self.reload_admin_info()
            self._refresh_flight_checks()
            self._refresh_activity_feed()

        def _refresh_flight_checks(self):
            checks = [
                f"Student bay: {'ready' if self.student_count >= 0 else 'offline'} with {self.student_count} roster entries.",
                f"Quiz fuel: {self.file_count} uploaded question bank(s) available.",
                f"Telemetry: {self.total_attempts} total attempt record(s) across the game.",
                f"Security: admin settings synced for {self.admin_identity_value.text() or 'Admin'}.",
            ]
            for label, text in zip(self.flight_labels, checks):
                label.setText(text)

        def _refresh_activity_feed(self):
            activity_lines = []
            recent_rows = sorted(self.progress_rows, key=lambda row: str(row.get("last_attempt_at") or ""), reverse=True)
            for row in recent_rows[:3]:
                student = row.get("name") or "Student"
                last_attempt = _format_qt_admin_attempt_time(row.get("last_attempt_at"))
                attempts = int(row.get("attempts_count") or 0)
                activity_lines.append(f"{student} | {attempts} attempts | last: {last_attempt}")

            for row in self.files_cache[:2]:
                filename = row.get("filename") or "Unnamed file"
                uploaded_at = _format_qt_admin_attempt_time(row.get("uploaded_at"))
                activity_lines.append(f"Question bank: {filename} | uploaded {uploaded_at}")

            while len(activity_lines) < len(self.activity_labels):
                activity_lines.append("Waiting for new admin activity.")

            for label, text in zip(self.activity_labels, activity_lines):
                label.setText(text)

        def reload_admin_info(self):
            try:
                admin = get_admin_user()
            except Exception as exc:
                self._show_error("Error", f"Failed to load admin info.\n{exc}")
                return

            if not admin:
                self.admin_login_edit.clear()
                self.admin_password_edit.clear()
                self.admin_confirm_password_edit.clear()
                self.admin_identity_value.setText("-")
                return

            admin_login_id = admin.get("login_id") or ""
            self.admin_login_edit.setText(admin_login_id)
            self.admin_password_edit.clear()
            self.admin_confirm_password_edit.clear()
            self.admin_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.admin_confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.admin_identity_value.setText(admin_login_id or "Admin")

        def toggle_admin_password_visibility(self):
            visible = self.admin_password_edit.echoMode() == QLineEdit.EchoMode.Password
            next_mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
            self.admin_password_edit.setEchoMode(next_mode)
            self.admin_confirm_password_edit.setEchoMode(next_mode)

        def _clear_student_form(self):
            self.student_name_edit.clear()
            self.student_grade_edit.clear()
            self.student_batch_edit.clear()
            self.student_roll_edit.clear()
            self.student_name_edit.setFocus()

        def clear_generated_credentials(self):
            self.generated_login.setText("Login ID: -")
            self.generated_pass.setText("Password: -")

        def validate_student_form(self):
            name = self.student_name_edit.text().strip()
            grade_text = self.student_grade_edit.text().strip()
            batch = self.student_batch_edit.text().strip()
            enrollment_text = self.student_roll_edit.text().strip()

            errors = []
            if not name:
                errors.append("Student name is required.")
            elif len(name) > MAX_STUDENT_NAME_LENGTH:
                errors.append(f"Student name cannot exceed {MAX_STUDENT_NAME_LENGTH} characters.")
            elif not STUDENT_NAME_PATTERN.fullmatch(name):
                errors.append("Student name can contain only letters, spaces, apostrophe ('), dot (.) and hyphen (-).")

            if not grade_text:
                errors.append("Standard is required.")
            elif not grade_text.isdigit():
                errors.append("Standard must be a number between 1 and 10.")
            elif not (1 <= int(grade_text) <= 10):
                errors.append("Standard must be between 1 and 10.")

            if batch:
                if len(batch) > MAX_BATCH_LENGTH:
                    errors.append(f"Batch cannot exceed {MAX_BATCH_LENGTH} characters.")
                elif not BATCH_PATTERN.fullmatch(batch):
                    errors.append("Batch can contain only letters, numbers, spaces, slash (/), hyphen (-) and underscore (_).")

            if not enrollment_text:
                errors.append("Enrollment/Roll number is required.")
            elif not enrollment_text.isdigit():
                errors.append("Enrollment/Roll number must be numeric.")

            if errors:
                self._show_error("Validation Error", "\n".join(errors))
                return None

            return name, int(grade_text), batch, int(enrollment_text)

        def add_student(self):
            validated = self.validate_student_form()
            if not validated:
                return

            name, grade, batch, enrollment_id = validated
            try:
                login_id, temp_password = create_student_user(
                    name=name,
                    grade=grade,
                    batch=batch if batch else "00",
                    enrollment_id=enrollment_id,
                )
            except Exception as exc:
                self._show_error("Error", f"Failed to create student.\n{exc}")
                return

            self.generated_login.setText(f"Login ID: {login_id}")
            self.generated_pass.setText(f"Password: {temp_password}")
            self._show_info("Student Created", f"Successfully created: {login_id}")
            self._clear_student_form()
            self.refresh_dashboard_data()

        def copy_generated_credentials(self):
            login_text = self.generated_login.text()
            password_text = self.generated_pass.text()
            login_value = login_text.split(":", 1)[1].strip() if ":" in login_text else "-"
            password_value = password_text.split(":", 1)[1].strip() if ":" in password_text else "-"
            if login_value == "-" and password_value == "-":
                self._show_info("Copy", "No generated credentials to copy yet.")
                return
            QApplication.clipboard().setText(f"Login ID: {login_value}\nPassword: {password_value}")
            self._show_info("Copied", "Generated credentials copied to clipboard.")

        def update_admin_account(self):
            new_login = self.admin_login_edit.text().strip() or None
            new_pass = self.admin_password_edit.text().strip() or None
            confirm_pass = self.admin_confirm_password_edit.text().strip() or None

            if new_login is None and new_pass is None:
                self._show_info("No Changes", "Nothing to update for admin account.")
                return

            if new_login is not None and len(new_login) < 3:
                self._show_error("Validation Error", "Login ID must be at least 3 characters long.")
                return

            if new_login is not None and len(new_login) > MAX_LOGIN_ID_LENGTH:
                self._show_error("Validation Error", f"Login ID cannot exceed {MAX_LOGIN_ID_LENGTH} characters.")
                return

            if new_login is not None and not LOGIN_ID_PATTERN.fullmatch(new_login):
                self._show_error("Validation Error", "Login ID can contain only letters, numbers, dot (.), underscore (_) and hyphen (-).")
                return

            if new_pass is not None and len(new_pass) > MAX_PASSWORD_LENGTH:
                self._show_error("Validation Error", f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters.")
                return

            if new_pass is not None and len(new_pass) < 6:
                self._show_error("Validation Error", "New password must be at least 6 characters long.")
                return

            if new_pass is not None and confirm_pass != new_pass:
                self._show_error("Validation Error", "Confirm New Password must match the new password.")
                return

            try:
                updated = update_admin_credentials(new_login=new_login, new_password=new_pass)
            except Exception as exc:
                self._show_error("Error", f"Failed to update admin account.\n{exc}")
                return

            if not updated:
                self._show_error("Error", "Admin account not found or no changes applied.")
                return

            self._show_info("Success", "Admin account updated successfully.")
            self.admin_password_edit.clear()
            self.admin_confirm_password_edit.clear()
            self.admin_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.admin_confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.refresh_dashboard_data()

        def open_student_manager(self):
            dialog = QtStudentManagerDialog(on_data_changed=self.refresh_dashboard_data, parent=self)
            dialog.exec()
            self.refresh_dashboard_data()

        def open_progress_dialog(self):
            dialog = QtProgressDialog(on_data_changed=self.refresh_dashboard_data, parent=self)
            dialog.exec()
            self.refresh_dashboard_data()


    def run_qt_admin_panel(root, user, handle_logout, handle_upload):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        root_hidden = False
        if root is not None and root.winfo_exists():
            try:
                root.withdraw()
                root_hidden = True
            except tk.TclError:
                root_hidden = False

        window = QtAdminPanelWindow(root, user, handle_logout, handle_upload)
        window.showMaximized()
        window.raise_()
        window.activateWindow()

        while window.isVisible():
            app.processEvents()
            if root is not None and root.winfo_exists():
                try:
                    root.update_idletasks()
                    root.update()
                except tk.TclError:
                    pass
            time.sleep(0.016)

        if root_hidden and root is not None and root.winfo_exists():
            try:
                root.deiconify()
            except tk.TclError:
                pass

        if callable(handle_logout):
            handle_logout()
else:
    run_qt_admin_panel = None

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
   
