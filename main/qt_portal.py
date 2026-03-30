import random
import sys
import time

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PortalCard(QFrame):
    def __init__(self, badge, title, description, button_text, accent, on_click):
        super().__init__()
        self.setObjectName("portalCard")
        self.setMinimumHeight(150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(14)

        badge_label = QLabel(badge)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_label.setFixedSize(34, 34)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                background: {accent};
                color: #102033;
                border-radius: 17px;
                font: 700 15px 'Segoe UI';
            }}
            """
        )
        header.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignTop)

        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(0, 0, 0, 0)
        text_wrap.setSpacing(4)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setStyleSheet("color: #F6FBFF; font: 700 15px 'Segoe UI';")
        text_wrap.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        desc_label.setStyleSheet("color: #D6E9FF; font: 400 11px 'Segoe UI';")
        text_wrap.addWidget(desc_label)
        header.addLayout(text_wrap, 1)

        layout.addLayout(header)
        layout.addStretch(1)

        button = QPushButton(button_text)
        button.clicked.connect(on_click)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(44)
        button.setMinimumWidth(220)
        button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB34F, stop:0.48 #FF9727, stop:1 #D66B0F);
                color: white;
                border: 1px solid #FFD08A;
                border-radius: 22px;
                font: 700 14px 'Segoe UI';
                padding: 0 20px;
            }
            QPushButton:hover { background: #FFAA36; }
            QPushButton:pressed { background: #D96F12; }
            """
        )
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)


class PortalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_action = None
        self._stars = []
        self._starfield_size = None

        self.setWindowTitle("Math Game")
        self.resize(1260, 760)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(
            """
            QWidget#root {
                background: transparent;
            }
            QFrame#shell {
                background: #1A5A89;
                border: 2px solid #3CD1FF;
                border-radius: 26px;
            }
            QFrame#inner {
                background: rgba(17, 87, 130, 0.45);
                border: 1px solid #2B8BC0;
                border-radius: 20px;
            }
            QLabel#eyebrow {
                color: #C8F6FF;
                background: #214E84;
                border: 1px solid #59DAFF;
                border-radius: 12px;
                font: 700 12px 'Segoe UI';
                padding: 7px 14px;
            }
            QLabel#heroTitle {
                color: #58C7FF;
                font: 900 52px Impact;
            }
            QLabel#heroSub {
                color: #F7FBFF;
                font: 700 24px 'Segoe UI';
            }
            QLabel#heroBody, QLabel#portalDesc, QLabel#heroNote {
                color: #D6E9FF;
                font: 400 14px 'Segoe UI';
            }
            QLabel#portalTitle {
                color: #F7FBFF;
                font: 700 22px 'Segoe UI';
            }
            QLabel#chip {
                color: #F5FBFF;
                font: 700 12px 'Segoe UI';
                border-radius: 14px;
                padding: 8px 14px;
            }
            QFrame#portalCard {
                background: #0E5C85;
                border: 2px solid #38D1FF;
                border-radius: 18px;
            }
            QLabel#footer {
                color: #DFEBFF;
                font: 600 12px 'Segoe UI';
            }
            QLabel#footerSmall {
                color: #A9C0E0;
                font: 600 11px 'Segoe UI';
            }
            """
        )
        self.setObjectName("root")
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(72, 52, 72, 30)
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
        inner_layout.setContentsMargins(38, 34, 38, 34)
        inner_layout.setSpacing(42)

        hero_col = QVBoxLayout()
        hero_col.setSpacing(12)

        eyebrow = QLabel("SPACE MISSION HQ")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hero_col.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignLeft)

        title = QLabel("Math Game")
        title.setObjectName("heroTitle")
        title.setMaximumWidth(400)
        hero_col.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)

        sub = QLabel("Playful number missions for young space explorers")
        sub.setObjectName("heroSub")
        sub.setWordWrap(True)
        sub.setMaximumWidth(420)
        hero_col.addWidget(sub)

        body = QLabel(
            "Jump into bright space portals, practise arithmetic with meteor rounds, and build confidence through quick wins and progress tracking."
        )
        body.setObjectName("heroBody")
        body.setWordWrap(True)
        body.setMaximumWidth(420)
        hero_col.addWidget(body)

        chip_row_1 = QHBoxLayout()
        chip_row_1.setSpacing(12)
        for text, bg, border in (
            ("Quick Drills", "#103454", "#56B6FF"),
            ("Progress Reports", "#173149", "#FF9A3D"),
        ):
            chip = QLabel(text)
            chip.setObjectName("chip")
            chip.setStyleSheet(
                f"QLabel#chip {{ background: {bg}; border: 1px solid {border}; }}"
            )
            chip_row_1.addWidget(chip)
        chip_row_1.addStretch(1)
        hero_col.addLayout(chip_row_1)

        chip_row_2 = QHBoxLayout()
        chip_row_2.setSpacing(12)
        chip = QLabel("T20 Speed Arena")
        chip.setObjectName("chip")
        chip.setStyleSheet("QLabel#chip { background: #0F3A4F; border: 1px solid #5CD6C5; }")
        chip_row_2.addWidget(chip)
        chip_row_2.addStretch(1)
        hero_col.addLayout(chip_row_2)

        note = QLabel(
            "Choose a portal to launch the same game systems with a brighter, more kid-friendly mission control look."
        )
        note.setObjectName("heroNote")
        note.setWordWrap(True)
        note.setMaximumWidth(420)
        hero_col.addWidget(note)
        hero_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        portal_title = QLabel("Choose your portal")
        portal_title.setObjectName("portalTitle")
        right_col.addWidget(portal_title)

        portal_desc = QLabel("Each route keeps the same game logic. Only the mission entry point changes.")
        portal_desc.setObjectName("portalDesc")
        portal_desc.setWordWrap(True)
        portal_desc.setMaximumWidth(380)
        right_col.addWidget(portal_desc)

        cards_wrap = QVBoxLayout()
        cards_wrap.setSpacing(14)
        cards_wrap.addWidget(
            PortalCard(
                "A",
                "Admin Login",
                "Create student access, upload quiz banks, and review progress.",
                "Admin Login",
                "#5BB2FF",
                lambda: self._choose("admin"),
            )
        )
        cards_wrap.addWidget(
            PortalCard(
                "S",
                "Student Login",
                "Play missions, track profile history, and practise by level.",
                "Student Login",
                "#7CD8FF",
                lambda: self._choose("student"),
            )
        )
        cards_wrap.addWidget(
            PortalCard(
                "T20",
                "Guest Login (T20)",
                "Jump straight into a fast T20 classroom sprint mode.",
                "Guest Login (T20)",
                "#FFB15C",
                lambda: self._choose("guest"),
            )
        )
        right_col.addLayout(cards_wrap)
        right_col.addStretch(1)

        inner_layout.addLayout(hero_col, 11)
        inner_layout.addLayout(right_col, 10)
        shell_layout.addWidget(inner)

        root_layout.addWidget(shell, 0, Qt.AlignmentFlag.AlignHCenter)

        footer = QLabel("Built for playful practice, classroom demos, and progress-driven space adventures.")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root_layout.addWidget(footer)

        footer_small = QLabel("© 2026 SynCraft Solution")
        footer_small.setObjectName("footerSmall")
        footer_small.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root_layout.addWidget(footer_small)

        root_layout.addStretch(1)

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
                }
            )
        self._stars = stars
        self._starfield_size = size_key

    def paintEvent(self, event):
        self._ensure_stars()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#120A25"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2B1762"))
        painter.drawEllipse(QRectF(160, 22, 420, 280))
        painter.setBrush(QColor("#214B9A"))
        painter.drawEllipse(QRectF(self.width() - 360, 100, 280, 210))

        for star in self._stars:
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(star["x"] - star["r"], star["y"] - star["r"], star["r"] * 2, star["r"] * 2))


def run_qt_portal():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    portal = PortalWindow()
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        portal.move(
            geometry.center().x() - (portal.width() // 2),
            geometry.center().y() - (portal.height() // 2),
        )
    portal.show()
    portal.raise_()
    portal.activateWindow()

    while portal.isVisible():
        app.processEvents()
        time.sleep(0.016)
    return portal.selected_action
