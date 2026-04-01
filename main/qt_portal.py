import random
import sys
import time
import math

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PortalCard(QFrame):
    def __init__(self, badge, title, description, button_text, accent, on_click):
        super().__init__()
        self.setObjectName("portalCard")
        self.setMinimumHeight(128)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        shell = QHBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        accent_bar = QFrame()
        accent_bar.setFixedWidth(6)
        accent_bar.setStyleSheet(f"background: {accent}; border-radius: 3px;")
        shell.addWidget(accent_bar)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        shell.addLayout(layout, 1)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(14)

        badge_label = QLabel(badge)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_label.setFixedSize(36, 36)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                background: {accent};
                color: #102033;
                border-radius: 18px;
                font: 700 11px 'Segoe UI';
            }}
            """
        )
        header.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignTop)

        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(0, 0, 0, 0)
        text_wrap.setSpacing(3)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setStyleSheet("color: #F6FBFF; font: 700 16px 'Segoe UI';")
        text_wrap.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        desc_label.setStyleSheet("color: #AFC7DD; font: 400 10px 'Segoe UI';")
        text_wrap.addWidget(desc_label)
        header.addLayout(text_wrap, 1)

        layout.addLayout(header)
        layout.addStretch(1)

        button = QPushButton(button_text)
        button.clicked.connect(on_click)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(40)
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB34F, stop:0.48 #FF9727, stop:1 #D66B0F);
                color: white;
                border: 1px solid #FFD08A;
                border-radius: 20px;
                font: 700 13px 'Segoe UI';
                padding: 0 20px;
            }
            QPushButton:hover { background: #FFAA36; }
            QPushButton:pressed { background: #D96F12; }
            """
        )
        layout.addWidget(button)


class PortalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_action = None
        self._stars = []
        self._starfield_size = None
        self._space_phase = 0.0
        self._last_space_tick = time.perf_counter()

        self.setWindowTitle("Math Game")
        self.resize(1260, 760)
        self.setMinimumSize(760, 560)
        self.setStyleSheet(
            """
            QWidget#root {
                background: transparent;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QFrame#shell {
                background: #0E4B78;
                border: 2px solid #38D1FF;
                border-radius: 26px;
            }
            QFrame#inner {
                background: transparent;
                border: 1px solid #1F77AF;
                border-radius: 20px;
            }
            QLabel#eyebrow {
                color: #B9F7FF;
                background: #173C73;
                border: 1px solid #58E1FF;
                border-radius: 12px;
                font: 700 12px 'Segoe UI';
                padding: 7px 14px;
            }
            QLabel#heroTitle {
                color: #5BCBFF;
                font: 900 52px Impact;
            }
            QLabel#heroSub {
                color: #F7FBFF;
                font: 700 20px 'Segoe UI';
            }
            QLabel#heroBody, QLabel#portalDesc, QLabel#heroNote {
                color: #AFC7DD;
                font: 400 12px 'Segoe UI';
            }
            QLabel#portalTitle {
                color: #F6FBFF;
                font: 700 19px 'Segoe UI';
            }
            QLabel#chip {
                color: #DCEEFF;
                font: 700 11px 'Segoe UI';
                border-radius: 14px;
                padding: 7px 12px;
            }
            QFrame#portalCard {
                background: #0D5B84;
                border: 2px solid #38D1FF;
                border-radius: 24px;
            }
            QLabel#footer {
                color: #C7DDF3;
                font: 600 12px 'Segoe UI';
            }
            QLabel#footerSmall {
                color: #89A9CA;
                font: 600 11px 'Segoe UI';
            }
            """
        )
        self.setObjectName("root")
        self._space_timer = QTimer(self)
        self._space_timer.timeout.connect(self._advance_space_scene)
        self._space_timer.start(16)
        self._build_ui()

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        scroll.viewport().setAutoFillBackground(False)
        scroll.viewport().setStyleSheet("background: transparent;")
        outer_layout.addWidget(scroll)

        self.scroll = scroll
        self.scroll_content = QWidget()
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_content.setStyleSheet("background: transparent;")
        scroll.setWidget(self.scroll_content)

        self.root_layout = QVBoxLayout(self.scroll_content)
        self.root_layout.setContentsMargins(72, 52, 72, 30)
        self.root_layout.setSpacing(20)
        self.root_layout.addStretch(1)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        self.shell.setMaximumWidth(1120)
        self.shell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.shell_layout = QVBoxLayout(self.shell)
        self.shell_layout.setContentsMargins(28, 18, 28, 18)
        self.shell_layout.setSpacing(18)

        top_line = QFrame()
        top_line.setFixedHeight(5)
        top_line.setStyleSheet("background: #47D7FF; border-radius: 2px;")
        self.shell_layout.addWidget(top_line)

        inner = QFrame()
        inner.setObjectName("inner")
        self.inner_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.inner_layout.setContentsMargins(38, 34, 38, 34)
        self.inner_layout.setSpacing(42)
        inner.setLayout(self.inner_layout)

        self.hero_widget = QWidget()
        self.hero_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hero_col = QVBoxLayout(self.hero_widget)
        hero_col.setSpacing(10)

        eyebrow = QLabel("SPACE MISSION HQ")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hero_col.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel("Math Game")
        self.title_label.setObjectName("heroTitle")
        hero_col.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.sub_label = QLabel("Pick a portal and start playing.")
        self.sub_label.setObjectName("heroSub")
        self.sub_label.setWordWrap(True)
        hero_col.addWidget(self.sub_label)

        self.body_label = QLabel(
            "Fast maths practice with a simple space theme."
        )
        self.body_label.setObjectName("heroBody")
        self.body_label.setWordWrap(True)
        hero_col.addWidget(self.body_label)

        chip_row_1 = QHBoxLayout()
        chip_row_1.setSpacing(10)
        for text, bg, border in (
            ("Quick Play", "#102A43", "#56B6FF"),
            ("Track Progress", "#16233B", "#56B6FF"),
        ):
            chip = QLabel(text)
            chip.setObjectName("chip")
            chip.setStyleSheet(
                f"QLabel#chip {{ background: {bg}; border: 1px solid {border}; }}"
            )
            chip_row_1.addWidget(chip)
        chip_row_1.addStretch(1)
        hero_col.addLayout(chip_row_1)

        self.note_label = QLabel(
            ""
        )
        self.note_label.setObjectName("heroNote")
        self.note_label.setWordWrap(True)
        self.note_label.hide()
        hero_col.addStretch(1)

        self.right_widget = QWidget()
        self.right_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        right_col = QVBoxLayout(self.right_widget)
        right_col.setSpacing(16)

        self.portal_title = QLabel("Choose your portal")
        self.portal_title.setObjectName("portalTitle")
        right_col.addWidget(self.portal_title)

        self.portal_desc = QLabel("Choose how you want to enter.")
        self.portal_desc.setObjectName("portalDesc")
        self.portal_desc.setWordWrap(True)
        right_col.addWidget(self.portal_desc)

        cards_wrap = QVBoxLayout()
        cards_wrap.setSpacing(16)
        cards_wrap.addWidget(
            PortalCard(
                "A",
                "Admin Login",
                "Manage students and review progress.",
                "Admin Login",
                "#5BB2FF",
                lambda: self._choose("admin"),
            )
        )
        cards_wrap.addWidget(
            PortalCard(
                "S",
                "Student Login",
                "Practice, track scores, and improve.",
                "Student Login",
                "#7CD8FF",
                lambda: self._choose("student"),
            )
        )
        cards_wrap.addWidget(
            PortalCard(
                "T20",
                "Guest Login (T20)",
                "Jump into a quick T20 round.",
                "Guest Login (T20)",
                "#FFB15C",
                lambda: self._choose("guest"),
            )
        )
        right_col.addLayout(cards_wrap)
        right_col.addStretch(1)

        self.inner_layout.addWidget(self.hero_widget, 11)
        self.inner_layout.addWidget(self.right_widget, 10)
        self.shell_layout.addWidget(inner)

        self.root_layout.addWidget(self.shell, 0, Qt.AlignmentFlag.AlignHCenter)

        self.footer = QLabel("Built for playful practice, classroom demos, and progress-driven space adventures.")
        self.footer.setObjectName("footer")
        self.footer.setWordWrap(True)
        self.footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.root_layout.addWidget(self.footer)

        self.footer_small = QLabel("(c) 2026 SynCraft Solution")
        self.footer_small.setObjectName("footerSmall")
        self.footer_small.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.root_layout.addWidget(self.footer_small)

        self.root_layout.addStretch(1)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        width = self.width()
        compact = width < 980
        tight = width < 840

        self.root_layout.setContentsMargins(
            24 if compact else 72,
            24 if compact else 52,
            24 if compact else 72,
            22 if compact else 30,
        )
        self.shell_layout.setContentsMargins(
            18 if compact else 28,
            14 if compact else 18,
            18 if compact else 28,
            14 if compact else 18,
        )
        self.inner_layout.setContentsMargins(
            24 if compact else 38,
            24 if compact else 34,
            24 if compact else 38,
            24 if compact else 34,
        )
        self.inner_layout.setSpacing(24 if compact else 42)
        self.inner_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        )

        self.title_label.setFont(
            QFont("Impact", 32 if tight else 40 if compact else 52, QFont.Weight.Black)
        )
        self.sub_label.setFont(
            QFont("Segoe UI", 14 if tight else 16 if compact else 20, QFont.Weight.Bold)
        )
        self.portal_title.setFont(
            QFont("Segoe UI", 16 if tight else 18 if compact else 19, QFont.Weight.Bold)
        )

        self.body_label.setMaximumWidth(16777215 if compact else 360)
        self.note_label.setMaximumWidth(16777215 if compact else 360)
        self.portal_desc.setMaximumWidth(16777215 if compact else 300)
        self.shell.setMaximumWidth(16777215 if compact else 1120)
        minimum_shell_height = 560 if compact else 610
        self.shell.setMinimumHeight(minimum_shell_height)

        viewport_height = max(self.height() - 12, minimum_shell_height + 120)
        self.scroll_content.setMinimumHeight(viewport_height)

        footer_alignment = Qt.AlignmentFlag.AlignLeft if tight else Qt.AlignmentFlag.AlignHCenter
        self.footer.setAlignment(footer_alignment)
        self.footer_small.setAlignment(footer_alignment)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _choose(self, action):
        self.selected_action = action
        self.close()

    def _ensure_stars(self):
        size_key = (self.width(), self.height())
        if self._starfield_size == size_key:
            return
        rng = random.Random(7)
        stars = []
        star_count = max(40, (self.width() * self.height()) // 20000)
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

        # Draw the rear ring arc first so the planet sits between the two halves.
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

        for star in self._stars:
            twinkle = 0.55 + (0.45 * abs(math.sin((self._space_phase * star["speed"]) + star["phase"])))
            self._draw_star(painter, star["x"], star["y"], star["r"], twinkle)

        painter.setBrush(QColor("#38D1FF"))
        for x, y, r in (
            (92, 82, 2),
            (132, 44, 3),
            (self.width() - 124, 74, 2),
            (self.width() - 82, 132, 3),
            (self.width() - 142, self.height() - 96, 2),
        ):
            painter.drawEllipse(QRectF(x, y, r * 2, r * 2))


def run_qt_portal():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    portal = PortalWindow()
    portal.showMaximized()
    portal.raise_()
    portal.activateWindow()

    while portal.isVisible():
        app.processEvents()
        time.sleep(0.016)
    return portal.selected_action
