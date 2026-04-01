import math
import random
import sys
import time

from PySide6.QtCore import QEasingCurve, QElapsedTimer, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

# This file implements a custom splash screen with an animated rocket launch scene.
class RocketSplashScreen(QWidget):
    def __init__(self, duration_ms=2800):
        super().__init__()
        self.duration_ms = duration_ms
        self.elapsed = QElapsedTimer()
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.update)
        self.finish_timer = QTimer(self)
        self.finish_timer.setSingleShot(True)
        self.finish_timer.timeout.connect(self.close)
        self._stars = []
        self._starfield_size = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("background: #15101F;")
        self.resize(1280, 720)

    def set_screen_geometry(self, rect):
        self.setGeometry(rect)
        self._starfield_size = None

    def showEvent(self, event):
        super().showEvent(event)
        self.elapsed.start()
        self.frame_timer.start(16)
        self.finish_timer.start(self.duration_ms)

    def closeEvent(self, event):
        self.frame_timer.stop()
        self.finish_timer.stop()
        super().closeEvent(event)

    def _ease_out_cubic(self, value):
        value = max(0.0, min(1.0, value))
        return 1.0 - ((1.0 - value) ** 3)

    def _ease_in_out(self, value):
        value = max(0.0, min(1.0, value))
        curve = QEasingCurve(QEasingCurve.Type.InOutCubic)
        return curve.valueForProgress(value)

    def _ensure_stars(self):
        size_key = (self.width(), self.height())
        if self._starfield_size == size_key:
            return

        splash_rng = random.Random(42)
        stars = []
        star_count = max(32, (self.width() * self.height()) // 18000)
        for _ in range(star_count):
            stars.append(
                {
                    "x": splash_rng.randint(18, max(18, self.width() - 18)),
                    "y": splash_rng.randint(18, max(18, self.height() - 18)),
                    "size": splash_rng.choice((2, 2, 3, 4)),
                    "phase": splash_rng.uniform(0.0, math.tau),
                    "speed": splash_rng.uniform(0.9, 1.8),
                }
            )
        self._stars = stars
        self._starfield_size = size_key

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

    def _draw_background(self, painter):
        painter.fillRect(self.rect(), QColor("#15101F"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#26174F"))
        painter.drawEllipse(QRectF(-70, 20, self.width() * 0.48, self.height() * 0.34))
        painter.setBrush(QColor("#143675"))
        painter.drawEllipse(QRectF(self.width() * 0.60, 80, self.width() * 0.46, self.height() * 0.28))

    def _draw_moon(self, painter, elapsed_sec):
        moon_y = self.height() * 0.44
        moon_r = min(self.width(), self.height()) * 0.20 * (0.85 + (0.15 * self._ease_out_cubic(min(1.0, elapsed_sec / 1.0))))
        center_x = self.width() / 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F7EFD0"))
        painter.drawEllipse(QRectF(center_x - moon_r, moon_y - moon_r, moon_r * 2, moon_r * 2))

        painter.setBrush(QColor("#DCCEA0"))
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
            painter.drawEllipse(QRectF(cx - crater_r, cy - crater_r, crater_r * 2, crater_r * 2))

        return center_x, moon_y, moon_r

    def _draw_rocket(self, painter, x, y, scale, flame_scale, rotation_deg, elapsed_sec):
        body_w = 46 * scale
        body_h = 112 * scale
        nose_h = 28 * scale
        fin_w = 20 * scale
        fin_h = 28 * scale
        booster_w = 14 * scale
        booster_h = 18 * scale
        window_r = max(7.0, 9 * scale)

        left = -(body_w / 2)
        right = body_w / 2
        top = -(body_h / 2)
        bottom = body_h / 2
        body_top = top + (body_h * 0.10)
        body_bottom = bottom - (body_h * 0.18)
        skirt_top = body_bottom - (body_h * 0.06)

        angle_rad = math.radians(rotation_deg)
        exhaust_dx = -math.sin(angle_rad)
        exhaust_dy = math.cos(angle_rad)
        side_dx = math.cos(angle_rad)
        side_dy = math.sin(angle_rad)
        exhaust_start_x = x + (exhaust_dx * (body_h * 0.30))
        exhaust_start_y = y + (exhaust_dy * (body_h * 0.30))
        smoke_len = 78 * scale * max(0.55, flame_scale)
        puff_count = 7
        painter.setPen(Qt.PenStyle.NoPen)
        for index in range(puff_count):
            t = index / max(1, puff_count - 1)
            launch_boost = 1.0 + (0.55 * max(0.0, 1.0 - min(1.0, elapsed_sec / 0.9)))
            drift = math.sin((elapsed_sec * 4.0) + (index * 0.65)) * (6.5 * scale) * (1 - t)
            puff_x = exhaust_start_x + (exhaust_dx * smoke_len * t) + (side_dx * drift)
            puff_y = exhaust_start_y + (exhaust_dy * smoke_len * t) + (side_dy * drift)
            radius = (12 + (26 * t)) * scale * launch_boost
            alpha = max(22, int((150 - (t * 96)) * max(0.45, flame_scale)))
            painter.setBrush(QColor(245, 242, 252, alpha))
            painter.drawEllipse(QRectF(puff_x - radius, puff_y - radius, radius * 2, radius * 2))
            if index < puff_count - 1:
                bridge_r = radius * 0.66
                painter.setBrush(QColor(220, 215, 235, max(18, alpha - 24)))
                painter.drawEllipse(
                    QRectF(
                        puff_x - bridge_r + (exhaust_dx * radius * 0.55),
                        puff_y - bridge_r + (exhaust_dy * radius * 0.55),
                        bridge_r * 2,
                        bridge_r * 2,
                    )
                )

        painter.save()
        painter.translate(x, y)
        painter.rotate(rotation_deg)
        painter.setPen(QPen(QColor("#4B3567"), 2))
        painter.setBrush(QColor("#B993E6"))
        nose_path = QPainterPath()
        nose_path.moveTo(0, top - nose_h)
        nose_path.quadTo(right - (body_w * 0.02), body_top + 2, right - (body_w * 0.10), body_top)
        nose_path.lineTo(left + (body_w * 0.10), body_top)
        nose_path.quadTo(left + (body_w * 0.02), body_top + 2, 0, top - nose_h)
        painter.drawPath(nose_path)

        painter.setBrush(QColor("#9A7ACC"))
        painter.drawRoundedRect(QRectF(left, body_top, body_w, body_bottom - body_top), max(14.0, 16 * scale), max(14.0, 16 * scale))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#7D62AD"))
        left_panel = QPainterPath()
        left_panel.moveTo(left + (body_w * 0.10), body_top + (body_h * 0.02))
        left_panel.lineTo(-(body_w * 0.04), body_top + (body_h * 0.10))
        left_panel.lineTo(-(body_w * 0.02), body_bottom - (body_h * 0.02))
        left_panel.lineTo(left + (body_w * 0.08), body_bottom - (body_h * 0.04))
        left_panel.closeSubpath()
        painter.drawPath(left_panel)

        painter.setBrush(QColor("#C8ACEF"))
        right_panel = QPainterPath()
        right_panel.moveTo((body_w * 0.04), body_top + (body_h * 0.02))
        right_panel.lineTo(right - (body_w * 0.08), body_top + (body_h * 0.08))
        right_panel.lineTo(right - (body_w * 0.06), body_bottom - (body_h * 0.04))
        right_panel.lineTo((body_w * 0.02), body_bottom - (body_h * 0.02))
        right_panel.closeSubpath()
        painter.drawPath(right_panel)

        painter.setPen(QPen(QColor("#4B3567"), 2))
        painter.setBrush(QColor("#7A58B0"))
        left_fin = QPainterPath()
        left_fin.moveTo(left + (body_w * 0.08), body_bottom - (body_h * 0.10))
        left_fin.quadTo(left - (fin_w * 0.65), bottom + (fin_h * 0.55), left - fin_w, bottom + fin_h)
        left_fin.lineTo(-(body_w * 0.10), skirt_top)
        left_fin.closeSubpath()
        painter.drawPath(left_fin)

        right_fin = QPainterPath()
        right_fin.moveTo(right - (body_w * 0.08), body_bottom - (body_h * 0.10))
        right_fin.quadTo(right + (fin_w * 0.65), bottom + (fin_h * 0.55), right + fin_w, bottom + fin_h)
        right_fin.lineTo((body_w * 0.10), skirt_top)
        right_fin.closeSubpath()
        painter.drawPath(right_fin)

        painter.setBrush(QColor("#52465F"))
        painter.drawRoundedRect(QRectF(-(booster_w / 2), skirt_top, booster_w, booster_h), max(4.0, 5 * scale), max(4.0, 5 * scale))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#5A447A"))
        window_cy = body_top + (body_h * 0.26)
        painter.drawEllipse(QRectF(-(window_r + 5), window_cy - (window_r + 5), (window_r + 5) * 2, (window_r + 5) * 2))
        painter.setBrush(QColor("#FFF8FF"))
        painter.drawEllipse(QRectF(-window_r, window_cy - window_r, window_r * 2, window_r * 2))

        flame_h = 34 * scale * flame_scale
        if flame_h > 6:
            flame_top = skirt_top + booster_h - 2
            glow_r = max(10.0, 18 * scale * flame_scale)
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.drawEllipse(QRectF(-glow_r, flame_top - 2, glow_r * 2, glow_r * 1.6))
            flame_path = QPainterPath()
            flame_path.moveTo(0, flame_top + flame_h)
            flame_path.quadTo(-(10 * scale), flame_top + (flame_h * 0.30), 0, flame_top)
            flame_path.quadTo((10 * scale), flame_top + (flame_h * 0.30), 0, flame_top + flame_h)
            painter.setBrush(QColor("#F1F0F5"))
            painter.drawPath(flame_path)
        painter.restore()

    def paintEvent(self, event):
        self._ensure_stars()
        elapsed_sec = self.elapsed.elapsed() / 1000.0 if self.elapsed.isValid() else 0.0

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._draw_background(painter)

        for star in self._stars:
            twinkle = 0.55 + (0.45 * abs(math.sin((elapsed_sec * star["speed"]) + star["phase"])))
            self._draw_star(painter, star["x"], star["y"], star["size"], twinkle)

        center_x, moon_y, moon_r = self._draw_moon(painter, elapsed_sec)

        rocket_progress = min(1.0, elapsed_sec / 1.35)
        rocket_eased = self._ease_out_cubic(rocket_progress)
        rocket_x = (self.width() * 0.46) + ((self.width() * 0.04) * rocket_eased)
        rocket_x += math.sin(rocket_progress * math.pi) * (self.width() * 0.016)
        rocket_start_y = self.height() + 140
        rocket_end_y = (moon_y + moon_r) - (self.height() * 0.02)
        rocket_y = rocket_start_y - ((rocket_start_y - rocket_end_y) * rocket_eased)
        rocket_scale = 0.78 + (0.18 * rocket_eased)
        flame_scale = max(0.0, 1.0 - (rocket_progress * 0.60))
        rotation_progress = self._ease_in_out(max(0.0, min(1.0, (elapsed_sec - 0.15) / 1.25)))
        settle = 1.0 - self._ease_out_cubic(min(1.0, max(0.0, (elapsed_sec - 0.95) / 0.8)))
        wobble = math.sin(elapsed_sec * 3.1) * 0.7 * settle
        rotation_deg = (17.0 * rotation_progress) + wobble
        self._draw_rocket(painter, rocket_x, rocket_y, rocket_scale, flame_scale, rotation_deg, elapsed_sec)

        orbit_progress = self._ease_in_out(max(0.0, min(1.0, (elapsed_sec - 0.9) / 0.9)))
        if orbit_progress > 0:
            pen = QPen(QColor("#FFFFFF"), 5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            orbit_rect = QRectF(center_x - (moon_r * 1.32), moon_y - (moon_r * 0.10), moon_r * 2.64, moon_r * 1.28)
            painter.drawArc(orbit_rect, 196 * 16, int(238 * orbit_progress) * 16)

        title_progress = self._ease_out_cubic(max(0.0, min(1.0, (elapsed_sec - 0.95) / 0.9)))
        if title_progress > 0:
            title_size = int(max(36, min(92, (min(self.width(), self.height()) * 0.086) * (0.74 + (0.26 * title_progress)))))
            title_font = QFont("Comic Sans MS", title_size, QFont.Weight.Bold)
            title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
            painter.setFont(title_font)
            shadow_offset = max(3, int(title_size * 0.07))
            title_y = moon_y - (moon_r * 0.23)

            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(QRectF(0, title_y + shadow_offset, self.width(), title_size * 1.9), Qt.AlignmentFlag.AlignHCenter, "Math\nGame")
            painter.setPen(QColor("#2E2C37"))
            painter.drawText(QRectF(0, title_y, self.width(), title_size * 1.9), Qt.AlignmentFlag.AlignHCenter, "Math\nGame")

            subtitle_font = QFont("Segoe UI", max(12, int(title_size * 0.24)), QFont.Weight.Bold)
            painter.setFont(subtitle_font)
            painter.setPen(QColor("#2E2C37"))
            painter.drawText(QRectF(0, moon_y + (moon_r * 0.34), self.width(), 40), Qt.AlignmentFlag.AlignHCenter, "Ready for launch")

        footer_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(footer_font)
        painter.setPen(QColor("#D4D8F7"))
        painter.drawText(QRectF(0, self.height() - 58, self.width(), 30), Qt.AlignmentFlag.AlignHCenter, "SynCraft Solution")


def run_qt_splash(duration_ms=2800):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    splash = RocketSplashScreen(duration_ms=duration_ms)
    screen = app.primaryScreen()
    if screen is not None:
        splash.set_screen_geometry(screen.geometry())
        splash.showMaximized()
    else:
        splash.show()
    splash.raise_()
    splash.activateWindow()
    while splash.isVisible():
        app.processEvents()
        time.sleep(0.016)
