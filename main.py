import sys
from collections import Counter
import mss
import math

LOG_FN = None
CAPTURE_METHOD_LOGGED = set()

def set_log_fn(fn):
    global LOG_FN
    LOG_FN = fn

def log_capture_issue(message):
    if callable(LOG_FN):
        LOG_FN(message)
    else:
        print(message)

def log_capture_method_once(method):
    if method in CAPTURE_METHOD_LOGGED:
        return
    CAPTURE_METHOD_LOGGED.add(method)
    log_capture_issue(f"Capture method: {method}")

def get_color_name(r, g, b):
    """
    Convert RGB values (0-255) to color name.
    Finds the closest matching color from 30 common colors.
    """
    colors = {
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
        "brown": (165, 42, 42),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gray": (128, 128, 128),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "lime": (0, 255, 0),
        "navy": (0, 0, 128),
        "maroon": (128, 0, 0),
        "olive": (128, 128, 0),
        "teal": (0, 128, 128),
        "silver": (192, 192, 192),
        "gold": (255, 215, 0),
        "crimson": (220, 20, 60),
        "indigo": (75, 0, 130),
        "violet": (238, 130, 238),
        "salmon": (250, 128, 114),
        "coral": (255, 127, 80),
        "khaki": (240, 230, 140),
        "tan": (210, 180, 140),
        "lavender": (230, 230, 250),
        "turquoise": (64, 224, 208),
        "beige": (245, 245, 220),
    }

    min_distance = float("inf")
    closest_color = None
    for color_name, (cr, cg, cb) in colors.items():
        distance = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if distance < min_distance:
            min_distance = distance
            closest_color = color_name
    return closest_color

def format_color_samples(colors, limit=3):
    if not colors:
        return "[]"
    samples = []
    for color, count in Counter(colors).most_common(limit):
        r, g, b = color
        name = get_color_name(r, g, b)
        samples.append(f"{name} {color} x{count}")
    return ", ".join(samples)

def state_display(state):
    if state == "active":
        return "ON"
    if state == "inactive":
        return "OFF"
    return state

def get_pixel_color(x, y):
    # Cross-platform pixel color detection with multi-monitor support
    try:
        if sys.platform == "darwin":
            # macOS: Prefer window-based capture at point to avoid desktop background
            import struct
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            from Quartz import CGWindowListCreateImage, kCGWindowListOptionIncludingWindow
            from Quartz import kCGWindowImageDefault, kCGWindowImageBoundsIgnoreFraming, kCGWindowImageBestResolution
            from Quartz import CGImageGetDataProvider, CGDataProviderCopyData, CGImageGetBytesPerRow
            from Quartz import CGImageGetWidth, CGImageGetHeight
            from Quartz import CoreGraphics as CG

            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID) or []
            window_id = None
            window_bounds = None
            for info in window_list:
                bounds = info.get("kCGWindowBounds")
                if not bounds:
                    continue
                bx = bounds.get("X")
                by = bounds.get("Y")
                bw = bounds.get("Width")
                bh = bounds.get("Height")
                if bx is None or by is None or bw is None or bh is None:
                    continue
                if bx <= x < bx + bw and by <= y < by + bh:
                    window_id = info.get("kCGWindowNumber")
                    window_bounds = (bx, by, bw, bh)
                    break

            if window_id is not None:
                log_capture_method_once("macOS window image")
                bx, by, bw, bh = window_bounds
                window_rect = CG.CGRectMake(int(bx), int(by), int(bw), int(bh))
                image = CGWindowListCreateImage(
                    window_rect,
                    kCGWindowListOptionIncludingWindow,
                    window_id,
                    kCGWindowImageBoundsIgnoreFraming | kCGWindowImageBestResolution,
                )
            else:
                log_capture_method_once("macOS window image (no window found)")
                image = None

            if image:
                data_provider = CGImageGetDataProvider(image)
                data = CGDataProviderCopyData(data_provider)
                buf = bytes(data)
                bytes_per_row = CGImageGetBytesPerRow(image)
                img_width = CGImageGetWidth(image)
                img_height = CGImageGetHeight(image)
                bx, by, bw, bh = window_bounds
                local_x = int(x - bx)
                local_y = int(y - by)
                if 0 <= local_x < img_width and 0 <= local_y < img_height:
                    colors = []
                    for dy in range(-4, 5):
                        for dx in range(-4, 5):
                            px = local_x + dx
                            py = local_y + dy
                            if 0 <= px < img_width and 0 <= py < img_height:
                                i = py * bytes_per_row + px * 4
                                b, g, r, a = struct.unpack_from("BBBB", buf, i)
                                colors.append((r, g, b))
                    if colors:
                        most_common = Counter(colors).most_common(1)[0][0]
                        return most_common, colors
                log_capture_issue("Capture method: macOS window image (point outside window image)")

        with mss.mss() as sct:
            log_capture_method_once("mss virtual screen")
            virtual = sct.monitors[0]
            v_left = virtual["left"]
            v_top = virtual["top"]
            v_right = v_left + virtual["width"]
            v_bottom = v_top + virtual["height"]

            if not (v_left <= x < v_right and v_top <= y < v_bottom):
                return (128, 128, 128), []

            monitor = None
            for m in sct.monitors[1:]:
                m_left = m["left"]
                m_top = m["top"]
                m_right = m_left + m["width"]
                m_bottom = m_top + m["height"]
                if m_left <= x < m_right and m_top <= y < m_bottom:
                    monitor = m
                    break
            if monitor is None:
                monitor = virtual

            left = max(monitor["left"], x - 4)
            top = max(monitor["top"], y - 4)
            right = min(monitor["left"] + monitor["width"], x + 5)
            bottom = min(monitor["top"] + monitor["height"], y + 5)
            width = max(0, right - left)
            height = max(0, bottom - top)
            if width == 0 or height == 0:
                return (128, 128, 128), []

            img = sct.grab({"left": left, "top": top, "width": width, "height": height})
            raw = img.raw  # BGRA bytes
            colors = []
            for i in range(width * height):
                b = raw[i * 4]
                g = raw[i * 4 + 1]
                r = raw[i * 4 + 2]
                colors.append((r, g, b))

            if colors:
                most_common = Counter(colors).most_common(1)[0][0]
                return most_common, colors
            return (128, 128, 128), []
    except Exception as e:
        msg = str(e)
        if "could not create image" in msg.lower() or "display" in msg.lower():
            log_capture_issue("Screen capture failed. On macOS, grant Screen Recording permission to the Python app (System Settings → Privacy & Security → Screen Recording).")
        else:
            log_capture_issue(f"Screen capture failed: {e}")
        colors = []
        for i in range(-4, 5):
            for j in range(-4, 5):
                try:
                    color = pyautogui.pixel(x + i, y + j)
                    colors.append(color)
                except Exception:
                    pass
        if colors:
            most_common = Counter(colors).most_common(1)[0][0]
            return most_common, colors
        return (128, 128, 128), []
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pyautogui
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DelayedTooltipButton(QPushButton):
    def __init__(self, text, tooltip_text, parent=None):
        super().__init__(text, parent)
        self.tooltip_text = tooltip_text
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_tooltip)

    def enterEvent(self, event):
        self.timer.start(3000)  # 3 seconds
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.timer.stop()
        super().leaveEvent(event)

    def show_tooltip(self):
        QToolTip.showText(self.mapToGlobal(self.rect().center()), self.tooltip_text)

class FuelGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.maximum = 100
        self.setMinimumSize(200, 100)

    def setValue(self, value, maximum):
        self.value = value
        self.maximum = maximum
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        
        # Draw gauge background
        painter.setPen(QPen(QColor(Qt.GlobalColor.black), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(center, 80, 80)
        
        # Color zones
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))  # Red zone
        painter.drawPie(center.x()-80, center.y()-80, 160, 160, 0, 5760)  # 0-25%
        painter.setBrush(QBrush(QColor(255, 255, 0)))  # Yellow zone
        painter.drawPie(center.x()-80, center.y()-80, 160, 160, 5760, 5760)  # 25-50%
        painter.setBrush(QBrush(QColor(0, 255, 0)))  # Green zone
        painter.drawPie(center.x()-80, center.y()-80, 160, 160, 11520, 11520)  # 50-100%
        
        # Draw needle
        if self.maximum > 0:
            angle = 180 - (self.value / self.maximum) * 180  # 180 to 0 degrees
            needle_length = 70
            end_point = QPoint(
                int(center.x() + needle_length * math.cos(math.radians(angle))),
                int(center.y() - needle_length * math.sin(math.radians(angle)))
            )
            painter.setPen(QPen(QColor(Qt.GlobalColor.red), 3))
            painter.drawLine(center, end_point)
        
        # Draw text
        painter.setPen(QColor(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 10))
        text = f"{self.value}/{self.maximum}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, text)

class AutoScalingBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = 0
        self.maximum = 100
        self.setMinimumHeight(30)

    def setValue(self, current, maximum):
        self.current = current
        self.maximum = maximum
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        margin = 5
        bar_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Background
        painter.setPen(QPen(QColor(Qt.GlobalColor.black), 1))
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawRect(bar_rect)
        
        # Fill
        if self.maximum > 0:
            fill_width = int((self.current / self.maximum) * bar_rect.width())
            fill_rect = QRect(bar_rect.left(), bar_rect.top(), fill_width, bar_rect.height())
            
            # Gradient based on percentage
            percentage = self.current / self.maximum
            if percentage > 0.5:
                color1 = QColor(0, 255, 0)  # Green
                color2 = QColor(255, 255, 0)  # Yellow
            else:
                color1 = QColor(255, 255, 0)  # Yellow
                color2 = QColor(255, 0, 0)  # Red
            
            gradient = QLinearGradient(fill_rect.topLeft().toPointF(), fill_rect.topRight().toPointF())
            gradient.setColorAt(0, color1)
            gradient.setColorAt(1, color2)
            
            painter.setBrush(QBrush(gradient))
            painter.drawRect(fill_rect)
        
        # Text
        painter.setPen(QColor(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        text = f"{self.current}/{self.maximum}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = 0
        self.maximum = 100
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(1000)  # 1 second animation
        self.setMinimumSize(100, 100)

    def setValue(self, current, maximum):
        self.animation.stop()
        self.animation.setStartValue(self.current)
        self.animation.setEndValue(current)
        self.maximum = maximum
        self.animation.start()

    @pyqtProperty(int)
    def value(self):
        return self.current

    @value.setter
    def value(self, val):
        self.current = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 10
        
        # Background circle
        painter.setPen(QPen(QColor(200, 200, 200), 10))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        
        # Progress arc
        if self.maximum > 0:
            percentage = self.current / self.maximum
            painter.setPen(QPen(self.getColor(percentage), 10))
            start_angle = 90 * 16  # 12 o'clock
            span_angle = -45 * 16  # 45 degrees clockwise
            painter.drawArc(center.x()-radius, center.y()-radius, 
                          radius*2, radius*2, start_angle, int(span_angle * percentage))
        
        # Text
        painter.setPen(QColor(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        text = f"{self.current}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def getColor(self, percentage):
        if percentage > 0.6:
            return QColor(0, 255, 0)  # Green
        elif percentage > 0.3:
            return QColor(255, 255, 0)  # Yellow
        else:
            return QColor(255, 0, 0)  # Red

class ArcProgress(QWidget):
    def __init__(self, label="", tooltip_text="", parent=None):
        super().__init__(parent)
        self.current = 0
        self.maximum = 100
        self.label = label
        self.tooltip_text = tooltip_text
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_tooltip)
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)

    def enterEvent(self, event):
        self.timer.start(3000)  # 3 seconds
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.timer.stop()
        super().leaveEvent(event)

    def show_tooltip(self):
        QToolTip.showText(self.mapToGlobal(self.rect().center()), self.tooltip_text)

    def setValue(self, current, maximum):
        self.current = current
        self.maximum = maximum
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center_x = int(rect.center().x())
        center_y = int(rect.center().y())
        radius = min(rect.width(), rect.height()) // 2 - 20  # Adjust for thicker arc (12px)
        
        # Convert clock positions to angles
        # Start from 3 o'clock (0°), go counter-clockwise 180° (rotated 90° counter-clockwise from 9 o'clock)
        # Qt uses 16ths of a degree, 0 = 3 o'clock, positive = counter-clockwise
        start_angle = 0 * 16  # 3 o'clock position
        # Arc spans 180 degrees counter-clockwise
        total_span = 180 * 16
        
        # Background arc (grey)
        painter.setPen(QPen(QColor(220, 220, 220), 12))  # Twice as thick
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(center_x-radius, center_y-radius, 
                       radius*2, radius*2, start_angle, total_span)
        
        # Progress arc - shrinks counter-clockwise from the start
        if self.maximum > 0:
            percentage = self.current / self.maximum
            # Calculate start angle offset to shrink from the beginning
            start_offset = int(total_span * (1 - percentage))
            current_start_angle = start_angle + start_offset
            progress_span = total_span - start_offset
            
            color = self.getColor(percentage)
            painter.setPen(QPen(color, 12))  # Twice as thick
            painter.drawArc(center_x-radius, center_y-radius, 
                          radius*2, radius*2, current_start_angle, progress_span)
        
        # Label text immediately above the value
        painter.setPen(QColor(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 9))
        label_rect = QRect(rect.left(), rect.top() + 25, rect.width(), 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.label)
        
        # Value text in center
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_rect = QRect(rect.left(), rect.top() + 45, rect.width(), 30)
        if self.maximum >= 60:
            # Display as minutes:seconds
            mins = int(self.current // 60)
            secs = int(self.current % 60)
            text = f"{mins}:{secs:02d}"
        else:
            text = f"{int(self.current)}"
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, text)

    def getColor(self, percentage):
        # Green at 100%, gradually turn to red when <10% remaining
        if percentage >= 0.9:
            return QColor(0, 255, 0)  # Bright green
        elif percentage >= 0.7:
            return QColor(100, 255, 0)  # Yellow-green
        elif percentage >= 0.5:
            return QColor(200, 255, 0)  # Yellow
        elif percentage >= 0.3:
            return QColor(255, 200, 0)  # Orange
        elif percentage >= 0.1:
            return QColor(255, 100, 0)  # Red-orange
        else:
            return QColor(255, 0, 0)  # Red

class FT8Clicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.json'
        self.load_settings()
        self.init_ui()
        self.check_screen_recording_permission()
        set_log_fn(self.log)
        self.setup_timers()
        self.color_timer.start(1000)
        self.learning = False
        self.current_band = '40m'
        self.click_history = []
        self.current_bar_start = None  # For real-time growing bar
        self.running = False
        self.paused = False
        self.all_bands = ['160m', '80m', '40m', '30m', '20m', '17m', '15m', '12m', '10m', '6m', '2m', '70cm']
        self.band_order = [b for b in self.all_bands if b in self.learned_buttons and b in self.visible_bands]
        self.current_band_index = self.band_order.index(self.current_band) if self.current_band in self.band_order else 0
        self.band_cycle_counter = 0
        self.button_to_learn = None
        self.locating = False
        self.button_to_locate = None
        self.short_qso_count = 0
        self.last_tx_time = None
        self.enable_tx_cooldown = False
        self.cooldown_timer = QTimer()
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.timeout.connect(lambda: setattr(self, 'enable_tx_cooldown', False))
        self.display_names = {'enable_tx': 'Enable Tx', 'tx6': 'Tx 6'}
        self.last_button_states = {}
        self.flash_restore_styles = {}

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'click_interval': 0.5,
                'visible_bands': ['40m', '20m', '17m', '15m', '12m', '10m'],
                'cq_time': 90,
                'cqs_remaining': 10,
                'app_time': 30*60,
                'learned_buttons': {}
            }
        self.visible_bands = self.settings.get('visible_bands', ['40m', '20m', '17m', '15m', '12m', '10m'])
        self.learned_buttons = self.settings.get('learned_buttons', {})
        if 'tx_enable' in self.learned_buttons and 'enable_tx' not in self.learned_buttons:
            self.learned_buttons['enable_tx'] = self.learned_buttons.pop('tx_enable')
        # Convert old format to new
        for btn, data in self.learned_buttons.items():
            if 'color' in data:
                data['states'] = {str(data['color']): 'inactive'}
                del data['color']
        self.click_interval = self.settings.get('click_interval', 0.5)
        self.cq_remaining = self.settings.get('cq_time', 90)
        self.app_remaining = self.settings.get('app_time', 30*60)
        self.cqs_remaining = self.settings.get('cqs_remaining', 10)

    def save_settings(self):
        self.settings['learned_buttons'] = self.learned_buttons
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def init_ui(self):
        self.setWindowTitle("FT8Clicker v0.6")
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Button List
        button_group = QGroupBox("Button List")
        button_group.setStyleSheet("QGroupBox::title { font-weight: bold; font-size: 14pt; } QGroupBox { background-color: #f0f0f0; }")
        self.button_layout = QVBoxLayout(button_group)
        self.enable_tx_btn = DelayedTooltipButton("Enable Tx", "Click to manually enable TX or learn its position. Enables transmission in FT8 software.")
        self.enable_tx_btn.clicked.connect(lambda: self.manual_click('enable_tx'))
        self.enable_tx_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.button_layout.addWidget(self.enable_tx_btn)
        self.tx6_btn = DelayedTooltipButton("Tx 6 (CQ)", "Click to manually send CQ call or learn its position. Sends a CQ signal in FT8 software.")
        self.tx6_btn.clicked.connect(lambda: self.manual_click('tx6'))
        self.tx6_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.button_layout.addWidget(self.tx6_btn)
        self.band_buttons = {}
        for band in self.visible_bands:
            btn = DelayedTooltipButton(band, f"Click to select {band} band or learn its position. Changes to {band} frequency in FT8 software.")
            btn.clicked.connect(lambda checked, b=band: self.select_band(b))
            btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.button_layout.addWidget(btn)
            self.band_buttons[band] = btn
        left_layout.addWidget(button_group)

        # Learn and Locate
        learn_locate_group = QGroupBox("Learn & Locate")
        learn_locate_group.setStyleSheet("QGroupBox::title { font-weight: bold; font-size: 14pt; } QGroupBox { background-color: #f0f0f0; }")
        learn_layout = QHBoxLayout(learn_locate_group)
        self.learn_btn = DelayedTooltipButton("LEARN", "Enter learning mode to capture button positions. Click a button, move mouse to FT8 software button, press L.")
        self.learn_btn.clicked.connect(self.learn_button)
        learn_layout.addWidget(self.learn_btn)
        self.locate_btn = DelayedTooltipButton("LOCATE", "Enter locate mode to move mouse to learned button positions. Click a button to move cursor there.")
        self.locate_btn.clicked.connect(self.locate_button)
        learn_layout.addWidget(self.locate_btn)
        left_layout.addWidget(learn_locate_group)

        # Main buttons
        main_btn_group = QGroupBox("Controls")
        main_btn_group.setStyleSheet("QGroupBox::title { font-weight: bold; font-size: 14pt; } QGroupBox { background-color: #f0f0f0; }")
        main_btn_layout = QGridLayout(main_btn_group)
        self.start_btn = DelayedTooltipButton("STOPPED", "Start or stop the automation. Red=stopped, Green=running.")
        self.start_btn.clicked.connect(self.toggle_start_stop)
        self.start_btn.setStyleSheet("background-color: red; color: white;")
        main_btn_layout.addWidget(self.start_btn, 0, 0)
        self.pause_btn = DelayedTooltipButton("PAUSE", "Pause or resume automation when running.")
        self.pause_btn.clicked.connect(self.pause_clicking)
        main_btn_layout.addWidget(self.pause_btn, 0, 1)
        self.settings_btn = DelayedTooltipButton("Settings", "Open settings dialog to configure intervals, timers, and visible bands.")
        self.settings_btn.clicked.connect(self.open_settings)
        main_btn_layout.addWidget(self.settings_btn, 1, 0)
        self.help_btn = DelayedTooltipButton("Help", "Open help dialog with usage instructions and troubleshooting.")
        self.help_btn.clicked.connect(self.open_help)
        main_btn_layout.addWidget(self.help_btn, 1, 1)
        left_layout.addWidget(main_btn_group)

        main_layout.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Status
        status_group = QGroupBox("Status")
        status_group.setStyleSheet("QGroupBox::title { font-weight: bold; font-size: 14pt; } QGroupBox { background-color: #f0f0f0; }")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("Status: Stopped")
        status_layout.addWidget(self.status_label)
        
        # Arc Progress Indicators
        arcs_layout = QHBoxLayout()
        arcs_layout.setSpacing(10)
        
        self.cq_arc = ArcProgress("CQ Time", "Shows remaining time until automatic CQ. Resets when TX is enabled. Green=plenty, Yellow=warning, Red=critical.")
        self.cqs_arc = ArcProgress("CQs Left", "Shows remaining CQ calls until automatic band change. Decrements on each CQ (manual or auto).")
        self.app_arc = ArcProgress("App Time", "Shows remaining time until automatic app stop. Counts down total runtime.")
        
        arcs_layout.addWidget(self.cq_arc)
        arcs_layout.addWidget(self.cqs_arc)
        arcs_layout.addWidget(self.app_arc)
        
        status_layout.addLayout(arcs_layout)
        
        right_layout.addWidget(status_group)

        # Graph
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        # Log
        log_group = QGroupBox("Log")
        log_group.setStyleSheet("QGroupBox::title { font-weight: bold; font-size: 14pt; } QGroupBox { background-color: #f0f0f0; }")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        export_log_btn = QPushButton("Export Log")
        export_log_btn.clicked.connect(self.export_log)
        log_layout.addWidget(export_log_btn)
        right_layout.addWidget(log_group)

        # Footer
        footer = QLabel("© 2026 FT8Clicker by 5N0YEN. MIT License.")
        footer.setStyleSheet("font-size: 10px;")
        right_layout.addWidget(footer)

        main_layout.addWidget(right_panel)

        # Keyboard shortcuts
        self.shortcut_s = QShortcut(QKeySequence('S'), self)
        self.shortcut_s.activated.connect(self.toggle_start_stop)
        self.shortcut_p = QShortcut(QKeySequence('P'), self)
        self.shortcut_p.activated.connect(self.pause_clicking)
        self.pause_btn.setVisible(False)
        self.pause_btn.setStyleSheet("background-color: white; color: black;")

        # Event filter for learning
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.locating:
            learned_button = False
            if obj == self.enable_tx_btn and 'enable_tx' in self.learned_buttons:
                learned_button = True
            elif obj == self.tx6_btn and 'tx6' in self.learned_buttons:
                learned_button = True
            else:
                for band, btn in self.band_buttons.items():
                    if obj == btn and band in self.learned_buttons:
                        learned_button = True
                        break
            if not learned_button and obj != self.locate_btn:
                self.locating = False
                self.button_to_locate = None
                self.locate_btn.setText("LOCATE")
                self.locate_btn.setStyleSheet("")
                self.revert_button_colors()
                self.log("LOCATE mode OFF")

        if event.type() == QEvent.Type.MouseButtonPress and self.learning:
            in_button_list = False
            if obj == self.enable_tx_btn or obj == self.tx6_btn:
                in_button_list = True
            else:
                for _, btn in self.band_buttons.items():
                    if obj == btn:
                        in_button_list = True
                        break
            if not in_button_list and obj != self.learn_btn:
                self.learning = False
                self.button_to_learn = None
                self.learn_btn.setText("LEARN")
                self.learn_btn.setStyleSheet("")
                self.revert_button_colors()
                self.log("LEARN mode OFF")
        
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_L and self.learning:
            self.capture_position()
            return True
        return super().eventFilter(obj, event)

    def learn_button(self):
        if self.learning:
            self.learning = False
            self.log("Learning cancelled.")
            self.learn_btn.setText("LEARN")
            self.learn_btn.setStyleSheet("")
            self.button_to_learn = None
            self.revert_button_colors()
            self.log("LEARN mode OFF")
        else:
            self.learning = True
            self.button_to_learn = None
            self.log("Select a button, then move the mouse cursor to the FT8 app button and press L")
            self.learn_btn.setText("LEARNING")
            self.learn_btn.setStyleSheet("background-color: yellow;")
            self.log("LEARN mode ON")

    def capture_position(self):
        if not self.learning or not self.button_to_learn:
            return
        try:
            x, y = pyautogui.position()
            try:
                color, colors = get_pixel_color(x, y)
            except Exception as pixel_error:
                self.log(f"Warning: Could not get pixel color: {pixel_error}, using default")
                color, colors = (128, 128, 128), []  # default gray
            button_type = self.button_to_learn
            initial_state = "inactive"
            self.learned_buttons[button_type] = {'pos': (x, y), 'states': {str(color): initial_state}}
            self.learning = False
            self.button_to_learn = None
            self.log(
                f"Learned `{self.display_names.get(button_type, button_type)}` at location {x},{y} "
                f"with color `{get_color_name(*color)}` {color} ({state_display(initial_state)}), "
                f"sampled: {format_color_samples(colors)}"
            )
            self.save_settings()
            self.band_order = [b for b in self.all_bands if b in self.learned_buttons and b in self.visible_bands]
            self.current_band_index = self.band_order.index(self.current_band) if self.current_band in self.band_order else 0
            self.learn_btn.setText("LEARN")
            self.learn_btn.setStyleSheet("")
            self.revert_button_colors()
        except Exception as e:
            self.learning = False
            self.button_to_learn = None
            self.log(f"Error learning position: {e}")
            self.learn_btn.setText("LEARN")
            self.learn_btn.setStyleSheet("")
            self.revert_button_colors()

    def locate_button(self):
        if self.locating:
            self.locating = False
            self.log("Locating cancelled.")
            self.locate_btn.setText("LOCATE")
            self.locate_btn.setStyleSheet("")
            self.button_to_locate = None
            self.revert_button_colors()
            self.log("LOCATE mode OFF")
        else:
            self.locating = True
            self.button_to_locate = None
            self.log("Select a button to locate.")
            self.locate_btn.setText("LOCATING")
            self.locate_btn.setStyleSheet("background-color: yellow;")
            self.log("LOCATE mode ON")

    def manual_click(self, button_type):
        if self.learning:
            if self.button_to_learn:
                # deselect previous
                self.revert_button_colors()
            self.button_to_learn = button_type
            self.log(f"Button selected for learning: {button_type}")
            # set color
            if button_type == 'enable_tx':
                self.enable_tx_btn.setStyleSheet("background-color: yellow;")
            elif button_type == 'tx6':
                self.tx6_btn.setStyleSheet("background-color: yellow;")
            elif button_type in self.band_buttons:
                self.band_buttons[button_type].setStyleSheet("background-color: yellow;")
        else:
            # Flash the button
            if button_type == 'enable_tx':
                self.flash_button(self.enable_tx_btn)
            elif button_type == 'tx6':
                self.flash_button(self.tx6_btn)
            
            if self.locating:
                if button_type in self.learned_buttons:
                    pos = self.learned_buttons[button_type]['pos']
                    try:
                        current_color, _ = get_pixel_color(pos[0], pos[1])
                        states = self.learned_buttons[button_type]['states']
                        current_state = states.get(str(current_color), 'unknown')
                        self.log(f"Button {button_type} state: {current_state}")
                    except Exception as e:
                        self.log(f"Error getting state for {button_type}: {e}")
                    pyautogui.moveTo(pos[0], pos[1])
                    self.log(f"Moved mouse to {button_type} position")
                    self.locating = False
                    self.button_to_locate = None
                    self.locate_btn.setText("LOCATE")
                    self.locate_btn.setStyleSheet("")
                    self.revert_button_colors()
                else:
                    self.log(f"{button_type} not learned")
                    self.locating = False
                    self.button_to_locate = None
                    self.locate_btn.setText("LOCATE")
                    self.locate_btn.setStyleSheet("")
                    self.revert_button_colors()
            elif button_type in self.learned_buttons:
                pos = self.learned_buttons[button_type]['pos']
                try:
                    current_pos = pyautogui.position()
                    pyautogui.click(pos[0], pos[1])
                    pyautogui.moveTo(current_pos[0], current_pos[1])
                    self.log(f"Manual click on {button_type}")
                    # Decrement CQ counter if CQ button was clicked manually
                    if button_type == 'tx6' and self.cqs_remaining > 0:
                        self.cqs_remaining -= 1
                        self.cqs_arc.setValue(self.cqs_remaining, self.settings['cqs_remaining'])
                    graph_event = 'cq' if button_type == 'tx6' else button_type
                    self.update_graph(graph_event)
                except Exception as e:
                    self.log(f"Error in manual click: {e}")
            else:
                self.log(f"{button_type} not learned")

    def click_learned_button(self, button_type, log_message=None, graph_event=None):
        if button_type not in self.learned_buttons:
            return False
        pos = self.learned_buttons[button_type]['pos']
        try:
            current_pos = pyautogui.position()
            pyautogui.click(pos[0], pos[1])
            pyautogui.moveTo(current_pos[0], current_pos[1])
            if log_message:
                self.log(log_message)
            if graph_event:
                self.update_graph(graph_event)
            
            # Decrement CQ counter if CQ button was clicked
            if button_type == 'tx6' and self.cqs_remaining > 0:
                self.cqs_remaining -= 1
                self.cqs_arc.setValue(self.cqs_remaining, self.settings['cqs_remaining'])
            
            return True
        except Exception as e:
            self.log(f"Error clicking {button_type}: {e}")
            return False

    def select_band(self, band):
        if self.learning:
            if self.button_to_learn:
                # deselect previous
                self.revert_button_colors()
            self.button_to_learn = band
            self.log(f"Button selected for learning: {band}")
            self.band_buttons[band].setStyleSheet("background-color: yellow;")
        else:
            self.current_band = band
            self.log(f"Selected band: {band}")
            self.flash_button(self.band_buttons[band])
        
    def toggle_start_stop(self):
        if self.running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.status_label.setText("Status: Running")
            self.log("Started clicking")
            self.start_btn.setText("RUNNING")
            self.start_btn.setStyleSheet("background-color: green; color: white;")
            self.pause_btn.setVisible(True)
            self.pause_btn.setText("PAUSE")
            self.pause_btn.setStyleSheet("background-color: white; color: black;")
            self.cq_remaining = self.settings['cq_time']
            self.app_remaining = self.settings['app_time']
            self.cqs_remaining = self.settings['cqs_remaining']
            # Update arc progress indicators
            self.cq_arc.setValue(self.cq_remaining, self.settings['cq_time'])
            self.cqs_arc.setValue(self.cqs_remaining, self.settings['cqs_remaining'])
            self.app_arc.setValue(self.app_remaining, self.settings['app_time'])
            self.cq_timer.start(1000)
            self.app_timer.start(1000)
            self.color_timer.start(1000)
            self.graph_timer.start(100)  # Update graph every 100ms for smooth growing bar
            self.click_timer = QTimer()
            self.click_timer.timeout.connect(self.clicking_loop)
            self.click_timer.start(int(self.click_interval * 1000))
            self.band_cycle_counter = 0
            self.short_qso_count = 0
            self.last_tx_time = None
            self.enable_tx_cooldown = False

    def pause_clicking(self):
        if self.running:
            if self.paused:
                self.paused = False
                self.status_label.setText("Status: Running")
                self.log("Resumed clicking")
                self.pause_btn.setStyleSheet("background-color: white; color: black;")
                self.cq_timer.start(1000)
                self.app_timer.start(1000)
                self.graph_timer.start(100)
                if hasattr(self, 'click_timer'):
                    self.click_timer.start(int(self.click_interval * 1000))
            else:
                self.paused = True
                self.status_label.setText("Status: Paused")
                self.log("Paused clicking")
                self.pause_btn.setStyleSheet("background-color: yellow; color: black;")
                self.cq_timer.stop()
                self.app_timer.stop()
                self.graph_timer.stop()
                if hasattr(self, 'click_timer'):
                    self.click_timer.stop()

    def stop_clicking(self):
        # Finalize any growing bar
        if hasattr(self, 'current_bar_start') and self.current_bar_start is not None:
            timestamp = datetime.now()
            duration = (timestamp - self.current_bar_start).total_seconds()
            self.click_history.append((self.current_bar_start, timestamp, 'stop', duration))
            self.current_bar_start = None
            self.plot_graph()
            
        self.running = False
        self.paused = False
        self.status_label.setText("Status: Stopped")
        self.log("Stopped clicking")
        self.start_btn.setText("STOPPED")
        self.start_btn.setStyleSheet("background-color: red; color: white;")
        self.pause_btn.setVisible(False)
        self.pause_btn.setStyleSheet("background-color: white; color: black;")
        self.cq_timer.stop()
        self.app_timer.stop()
        self.graph_timer.stop()
        if hasattr(self, 'click_timer'):
            self.click_timer.stop()

    def clicking_loop(self):
        if not self.running or self.paused:
            return
        if self.enable_tx_cooldown:
            return
        if 'enable_tx' in self.learned_buttons:
            pos = self.learned_buttons['enable_tx']['pos']
            try:
                current_color, _ = get_pixel_color(pos[0], pos[1])
                states = self.learned_buttons['enable_tx']['states']
                current_state = states.get(str(current_color), 'unknown')
                if current_state == 'inactive':  # Only click if inactive to enable
                    self.click_learned_button('enable_tx', "Auto-clicked Enable Tx", 'enable_tx')
                    self.cq_remaining = self.settings['cq_time']
                    self.band_cycle_counter += 1
                    if self.cqs_remaining > 0 and self.band_cycle_counter >= self.cqs_remaining:
                        self.change_band()
                        self.band_cycle_counter = 0
                    self.enable_tx_cooldown = True
                    self.cooldown_timer.start(2000)  # 2 second cooldown
            except Exception as e:
                self.log(f"Error in clicking loop for enable_tx: {e}")

    def auto_cq(self):
        if self.running and not self.paused:
            self.cq_remaining -= 1
            self.cq_arc.setValue(self.cq_remaining, self.settings['cq_time'])
            if self.cq_remaining <= 0:
                if 'tx6' in self.learned_buttons:
                    pos = self.learned_buttons['tx6']['pos']
                    try:
                        current_color, _ = get_pixel_color(pos[0], pos[1])
                        states = self.learned_buttons['tx6']['states']
                        current_state = states.get(str(current_color), 'unknown')
                        if current_state == 'inactive':  # Only click if inactive to send CQ
                            self.click_learned_button('tx6', "Auto-clicked CQ", 'cq')
                            self.cq_remaining = self.settings['cq_time']
                            self.cq_arc.setValue(self.cq_remaining, self.settings['cq_time'])
                    except Exception as e:
                        self.log(f"Error in auto_cq: {e}")

    def auto_stop(self):
        if self.running:
            self.app_remaining -= 1
            self.app_arc.setValue(self.app_remaining, self.settings['app_time'])
            if self.app_remaining <= 0:
                self.stop_clicking()
                self.log("App stopped due to time limit")
                self.update_graph('stop')

    def change_band(self):
        if not self.band_order:
            self.log("No learned bands available for cycling")
            return
        self.current_band_index = (self.current_band_index + 1) % len(self.band_order)
        new_band = self.band_order[self.current_band_index]
        if new_band in self.learned_buttons:
            pos = self.learned_buttons[new_band]['pos']
            try:
                current_color, _ = get_pixel_color(pos[0], pos[1])
                states = self.learned_buttons[new_band]['states']
                current_state = states.get(str(current_color), 'unknown')
                if current_state != 'active':  # Only click if not already active
                    if self.click_learned_button(new_band, f"Changed to band {new_band}", 'band_change'):
                        self.current_band = new_band
                        self.cqs_remaining = self.settings['cqs_remaining']
                        self.cqs_arc.setValue(self.cqs_remaining, self.settings['cqs_remaining'])
            except Exception as e:
                self.log(f"Error in change_band: {e}")

    def update_graph(self, event_type):
        timestamp = datetime.now()
        
        # If there's a current growing bar, finalize it with the event color
        if hasattr(self, 'current_bar_start') and self.current_bar_start is not None:
            duration = (timestamp - self.current_bar_start).total_seconds()
            self.click_history.append((self.current_bar_start, timestamp, event_type, duration))
            self.current_bar_start = None
        
        # Start a new growing bar
        self.current_bar_start = timestamp
        
        if len(self.click_history) > 50:
            self.click_history.pop(0)
            
        # Runaway detection
        if event_type == 'enable_tx':
            if self.last_tx_time:
                duration = (timestamp - self.last_tx_time).total_seconds()
                if duration < 5:
                    self.short_qso_count += 1
                    if self.short_qso_count >= 3:
                        self.log("Runaway detected: 3 short QSOs (<5s) in a row, stopping automation.")
                        self.stop_clicking()
                else:
                    self.short_qso_count = 0
            self.last_tx_time = timestamp
        
        self.plot_graph()

    def plot_graph(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not self.click_history and self.current_bar_start is None:
            self.canvas.draw()
            return
            
        colors = {'enable_tx': 'green', 'cq': 'yellow', 'band_change': 'orange', 'stop': 'red'}
        color_names = {'enable_tx': 'Enable TX', 'cq': 'CQ Call', 'band_change': 'Band Change', 'stop': 'Stop'}
        
        # Plot completed bars (show last 100, or less initially)
        bars = []
        max_bars = min(100, max(10, len(self.click_history) + (1 if self.current_bar_start else 0)))
        start_index = max(0, len(self.click_history) - (max_bars - (1 if self.current_bar_start else 0)))
        for i, (start_time, end_time, event_type, duration) in enumerate(self.click_history[start_index:], start_index):  
            bar = ax.bar(i - start_index, duration, color=colors.get(event_type, 'blue'), width=0.8)
            bars.append((bar[0], start_time, end_time, event_type, duration, i + 1))
        
        # Plot current growing bar (grey)
        if hasattr(self, 'current_bar_start') and self.current_bar_start is not None:
            current_duration = (datetime.now() - self.current_bar_start).total_seconds()
            bar_position = len(self.click_history) - start_index
            growing_bar = ax.bar(bar_position, current_duration, color='grey', width=0.8, alpha=0.7)
            bars.append((growing_bar[0], self.current_bar_start, None, 'growing', current_duration, len(self.click_history) + 1))
        
        # Set axis limits - X auto-scales from 10 to 100, Y auto-scales with initial max 30
        ax.set_xlim(-0.5, max_bars - 0.5)
        # Y axis auto-scales, but ensure it starts at 0 and has a reasonable initial range
        y_max = max(30, max([duration for _, _, _, _, duration, _ in bars] + [30]))
        ax.set_ylim(0, y_max)
        
        # Add light grey horizontal lines
        ax.grid(True, which='both', axis='y', color='lightgrey', alpha=0.3)
        
        ax.set_xlabel('Click Sequence Number')
        ax.set_ylabel('Duration (seconds)')
        ax.set_title('Click Event Timeline')
        
        # Remove tooltips/hover functionality
        
        self.canvas.draw()

    def update_growing_bar(self):
        """Update the growing bar in real-time"""
        if hasattr(self, 'current_bar_start') and self.current_bar_start is not None:
            self.plot_graph()

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")

    def clear_log(self):
        self.log_text.clear()

    def export_log(self):
        with open('log.txt', 'w') as f:
            f.write(self.log_text.toPlainText())
        self.log("Log exported to log.txt")

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)

        # Click interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Click Interval (s):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setValue(self.click_interval)
        self.interval_spin.setRange(0.1, 3.0)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # CQ Time
        cq_layout = QHBoxLayout()
        cq_layout.addWidget(QLabel("CQ Time (s):"))
        self.cq_spin = QSpinBox()
        self.cq_spin.setValue(self.settings['cq_time'])
        self.cq_spin.setRange(60, 3000)
        cq_layout.addWidget(self.cq_spin)
        layout.addLayout(cq_layout)

        # CQs Remaining
        cqs_layout = QHBoxLayout()
        cqs_layout.addWidget(QLabel("CQs Remaining:"))
        self.cqs_spin = QSpinBox()
        self.cqs_spin.setValue(self.settings['cqs_remaining'])
        self.cqs_spin.setRange(0, 100)
        cqs_layout.addWidget(self.cqs_spin)
        layout.addLayout(cqs_layout)

        # App Time
        app_layout = QHBoxLayout()
        app_layout.addWidget(QLabel("App Time (min):"))
        self.app_spin = QSpinBox()
        self.app_spin.setValue(self.settings['app_time'] // 60)
        self.app_spin.setRange(5, 240)
        app_layout.addWidget(self.app_spin)
        layout.addLayout(app_layout)

        # Visible bands
        bands_group = QGroupBox("Visible Bands")
        bands_layout = QVBoxLayout(bands_group)
        self.band_checks = {}
        for band in self.all_bands:
            cb = QCheckBox(band)
            cb.setChecked(band in self.visible_bands)
            bands_layout.addWidget(cb)
            self.band_checks[band] = cb
        layout.addWidget(bands_group)

        # Unlearn all
        unlearn_btn = QPushButton("Unlearn All")
        unlearn_btn.clicked.connect(self.unlearn_all)
        layout.addWidget(unlearn_btn)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_settings_dialog(dialog))
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def open_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("FT8Clicker Help")
        dialog.setMinimumSize(600, 400)
        dialog.setSizeGripEnabled(True)
        layout = QVBoxLayout(dialog)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(
            "FT8Clicker Help\n\n"
            "Start/Stop\n"
            "- STOPPED (red): automation is stopped and counters are paused.\n"
            "- RUNNING (green): counters reset to settings and automation starts.\n\n"
            "Pause\n"
            "- PAUSE ON (yellow): pauses all automation and timers.\n"
            "- PAUSE OFF (white): resumes automation and timers.\n\n"
            "Learn\n"
            "- Click LEARN, select a button, move to the FT8 app button and press L.\n"
            "- Clicking outside the button list exits LEARN mode.\n\n"
            "Locate\n"
            "- Click LOCATE, then click a learned button to move the cursor there.\n"
            "- Clicking outside learned buttons exits LOCATE mode.\n\n"
            "WSJT-x Configuration\n"
            "- Set TX Watchdog > CQ Time to prevent unpredictable behavior.\n\n"
            "Screen Recording (macOS)\n"
            "- Enable Screen Recording for Visual Studio Code or your Python app.\n"
            "  System Settings → Privacy & Security → Screen Recording.\n\n"
            "Logs\n"
            "- The log records mode changes, button states, and automation actions.\n"
        )
        layout.addWidget(help_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def save_settings_dialog(self, dialog):
        self.click_interval = self.interval_spin.value()
        self.settings['click_interval'] = self.click_interval
        self.settings['cq_time'] = self.cq_spin.value()
        self.settings['cqs_remaining'] = self.cqs_spin.value()
        self.settings['app_time'] = self.app_spin.value() * 60
        self.visible_bands = [b for b in self.all_bands if self.band_checks[b].isChecked()]
        self.settings['visible_bands'] = self.visible_bands
        self.band_order = [b for b in self.all_bands if b in self.learned_buttons and b in self.visible_bands]
        self.save_settings()
        dialog.accept()
        self.update_ui_bands()

    def update_ui_bands(self):
        # Clear old
        for btn in list(self.band_buttons.values()):
            self.button_layout.removeWidget(btn)
            btn.deleteLater()
        self.band_buttons.clear()
        # Add new
        for band in self.visible_bands:
            btn = DelayedTooltipButton(band, f"Click to select {band} band or learn its position. Changes to {band} frequency in FT8 software.")
            btn.clicked.connect(lambda checked, b=band: self.select_band(b))
            btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.button_layout.addWidget(btn)
            self.band_buttons[band] = btn

    def unlearn_all(self):
        self.learned_buttons.clear()
        self.save_settings()
        self.band_order = [b for b in self.all_bands if b in self.learned_buttons and b in self.visible_bands]
        self.current_band_index = 0
        self.log("Unlearned all buttons")

    def revert_button_colors(self):
        self.enable_tx_btn.setStyleSheet("")
        self.tx6_btn.setStyleSheet("")
        for band, btn in self.band_buttons.items():
            btn.setStyleSheet("")

    def update_button_colors(self):
        for button_type, data in self.learned_buttons.items():
            pos = data['pos']
            try:
                current_color, colors = get_pixel_color(pos[0], pos[1])
            except Exception as e:
                self.log(f"Warning: Could not get pixel color for {button_type}: {e}, using default")
                current_color, colors = None, []
            if current_color:
                states = data['states']
                color_key = str(current_color)
                if len(states) <= 1:
                    current_state = "inactive"
                    if color_key not in states:
                        states[color_key] = current_state
                        self.log(
                            f"Learned new state for {button_type}: {state_display(current_state)} with color "
                            f"`{get_color_name(*current_color)}` {current_color}, sampled: {format_color_samples(colors)}"
                        )
                        self.save_settings()
                else:
                    detected_state = self.classify_button_state(current_color)
                    if color_key not in states or states.get(color_key) != detected_state:
                        states[color_key] = detected_state
                        self.log(
                            f"Learned new state for {button_type}: {state_display(detected_state)} with color "
                            f"`{get_color_name(*current_color)}` {current_color}, sampled: {format_color_samples(colors)}"
                        )
                        self.save_settings()
                    current_state = detected_state
                last_state = self.last_button_states.get(button_type)
                if current_state != last_state:
                    self.last_button_states[button_type] = current_state
                    display_name = self.display_names.get(button_type, button_type)
                    if current_state in ("active", "inactive"):
                        self.log(f"Button {display_name} detected {state_display(current_state)}")
            # Set UI button color to match detected color
            if not (self.learning and button_type == self.button_to_learn):
                if current_color:
                    r, g, b = current_color
                    color_style = f"background-color: rgb({r}, {g}, {b});"
                else:
                    color_style = ""
                if button_type == 'enable_tx':
                    self.enable_tx_btn.setStyleSheet(color_style)
                elif button_type == 'tx6':
                    self.tx6_btn.setStyleSheet(color_style)
                elif button_type in self.band_buttons:
                    self.band_buttons[button_type].setStyleSheet(color_style)

    def classify_button_state(self, color):
        r, g, b = color
        name = get_color_name(r, g, b)
        if name in ("white", "gray", "silver", "black"):
            return "inactive"
        return "active"

    def flash_button(self, button):
        if button in self.flash_restore_styles:
            return  # already flashing
        original_style = button.styleSheet()
        self.flash_restore_styles[button] = original_style
        button.setStyleSheet("background-color: yellow;")
        QTimer.singleShot(200, lambda: self.restore_flash_style(button))

    def restore_flash_style(self, button):
        if button in self.flash_restore_styles:
            button.setStyleSheet(self.flash_restore_styles[button])
            del self.flash_restore_styles[button]

    def setup_timers(self):
        self.cq_timer = QTimer()
        self.cq_timer.timeout.connect(self.auto_cq)
        self.app_timer = QTimer()
        self.app_timer.timeout.connect(self.auto_stop)
        self.color_timer = QTimer()
        self.color_timer.timeout.connect(self.update_button_colors)
        self.graph_timer = QTimer()
        self.graph_timer.timeout.connect(self.update_growing_bar)

    def check_screen_recording_permission(self):
        if sys.platform != "darwin":
            return
        try:
            from Quartz import CGPreflightScreenCaptureAccess
        except Exception:
            return
        try:
            allowed = CGPreflightScreenCaptureAccess()
        except Exception:
            return
        if not allowed:
            QMessageBox.warning(
                self,
                "Screen Recording Permission Required",
                "Screen Recording permission is required for pixel detection.\n\n"
                "Open System Settings → Privacy & Security → Screen Recording, "
                "enable it for Visual Studio Code (or your Python app if running from Terminal), "
                "then restart FT8Clicker.",
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FT8Clicker()
    window.show()
    sys.exit(app.exec())