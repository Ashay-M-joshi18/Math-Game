import random
import sys
import time

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
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
        self.setMinimumHeight(138)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

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
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        layout.addWidget(button)


class PortalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_action = None
        self._stars = []
        self._starfield_size = None

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
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        self.root_layout = QVBoxLayout(scroll_content)
        self.root_layout.setContentsMargins(72, 52, 72, 30)
        self.root_layout.setSpacing(20)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        self.shell.setMaximumWidth(1120)
        self.shell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.shell_layout = QVBoxLayout(self.shell)
        self.shell_layout.setContentsMargins(28, 18, 28, 18)
        self.shell_layout.setSpacing(18)

        top_line = QFrame()
        top_line.setFixedHeight(5)
        top_line.setStyleSheet("background: #46D8FF; border-radius: 2px;")
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
        hero_col.setSpacing(12)

        eyebrow = QLabel("SPACE MISSION HQ")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hero_col.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel("Math Game")
        self.title_label.setObjectName("heroTitle")
        hero_col.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.sub_label = QLabel("Playful number missions for young space explorers")
        self.sub_label.setObjectName("heroSub")
        self.sub_label.setWordWrap(True)
        hero_col.addWidget(self.sub_label)

        self.body_label = QLabel(
            "Jump into bright space portals, practise arithmetic with meteor rounds, and build confidence through quick wins and progress tracking."
        )
        self.body_label.setObjectName("heroBody")
        self.body_label.setWordWrap(True)
        hero_col.addWidget(self.body_label)

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

        self.note_label = QLabel(
            "Choose a portal to launch the same game systems with a brighter, more kid-friendly mission control look."
        )
        self.note_label.setObjectName("heroNote")
        self.note_label.setWordWrap(True)
        hero_col.addWidget(self.note_label)
        hero_col.addStretch(1)

        self.right_widget = QWidget()
        self.right_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        right_col = QVBoxLayout(self.right_widget)
        right_col.setSpacing(14)

        self.portal_title = QLabel("Choose your portal")
        self.portal_title.setObjectName("portalTitle")
        right_col.addWidget(self.portal_title)

        self.portal_desc = QLabel("Each route keeps the same game logic. Only the mission entry point changes.")
        self.portal_desc.setObjectName("portalDesc")
        self.portal_desc.setWordWrap(True)
        right_col.addWidget(self.portal_desc)

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
            QFont("Segoe UI", 18 if tight else 20 if compact else 24, QFont.Weight.Bold)
        )
        self.portal_title.setFont(
            QFont("Segoe UI", 18 if tight else 20 if compact else 22, QFont.Weight.Bold)
        )

        self.body_label.setMaximumWidth(16777215 if compact else 420)
        self.note_label.setMaximumWidth(16777215 if compact else 420)
        self.portal_desc.setMaximumWidth(16777215 if compact else 380)

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
            painter.drawEllipse(
                QRectF(star["x"] - star["r"], star["y"] - star["r"], star["r"] * 2, star["r"] * 2)
            )


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
