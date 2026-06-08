import sys
import mmap
import struct
import math
import numpy as np
import os
import json
from datetime import datetime

# 1. IMPORT AND START THE CORE ENGINE FIRST
from PyQt5.QtWidgets import QApplication

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# 2. ONLY AFTER THAT, IMPORT GRAPHICS LIBRARIES
import pyqtgraph as pg
import pyqtgraph.exporters # Required for image exporting
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt

class ACCSharedMemory:
    def __init__(self):
        self.shm = None
        self.try_connect()

    def try_connect(self):
        try:
            self.shm = mmap.mmap(-1, 256, "Local\\acpmf_physics")
            return True
        except FileNotFoundError:
            self.shm = None
            return False

    def read(self):
        if self.shm is None:
            if not self.try_connect():
                return 0.0, 0.0, 0.0

        try:
            self.shm.seek(0)
            data = self.shm.read(32)
            unpacked = struct.unpack('<ifffiiff', data)
            
            brake = unpacked[2] * 100.0
            steer = abs(unpacked[6])
            speed = unpacked[7]
            
            # Stability and security fix: Catch NaN and Infinite values
            if math.isnan(brake) or math.isinf(brake): brake = 0.0
            if math.isnan(steer) or math.isinf(steer): steer = 0.0
            if math.isnan(speed) or math.isinf(speed): speed = 0.0
            
            return speed, brake, steer
        except Exception:
            return 0.0, 0.0, 0.0

class TrailBrakingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trail Braking Analyzer")
        self.resize(500, 500)
        
        # Keep window always on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot = pg.PlotWidget(background='k')
        layout.addWidget(self.plot)
        
        # Locked aspect ratio, fixed 0-100 grid
        self.plot.setAspectLocked(True)
        self.plot.setXRange(0, 100, padding=0)
        self.plot.setYRange(0, 100, padding=0)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setLabel('bottom', 'Steering (Elastic 0-100%)')
        self.plot.setLabel('left', 'Brake Pressure (Elastic 0-100%)')
        
        # 1. Static Red Friction Circle
        self.ideal_curve = self.plot.plot([], [], pen=pg.mkPen(color='r', width=3, style=Qt.DashLine))
        ref_x = np.linspace(0, 100, 100)
        ref_y = 100.0 * np.sqrt(1.0 - (ref_x / 100.0)**2)
        self.ideal_curve.setData(ref_x, ref_y)
        
        # 2. Real-time Green Line
        self.actual_curve = self.plot.plot([], [], pen=pg.mkPen(color='g', width=4))
        
        self.score_text = pg.TextItem("", color='#f1c40f', anchor=(0.5, 0.5))
        self.score_text.setPos(50, 50) 
        font = self.score_text.textItem.font()
        font.setPointSize(80)
        font.setBold(True)
        self.score_text.textItem.setFont(font)
        self.plot.addItem(self.score_text)
        
        self.acc = ACCSharedMemory()
        self.state = "IDLE"
        self.x_steer = []
        self.y_brake = []
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(20)

    def calculate_score(self, s_norm, b_norm):
        if len(b_norm) < 5: return 1

        # Isolate only the release phase for evaluation (from max brake to zero)
        max_idx = np.argmax(b_norm)
        b_trail = b_norm[max_idx:]
        s_trail = s_norm[max_idx:]

        if len(b_trail) < 5: return 1

        # SHAPE ERROR (MAE): Compare the green line directly to the red circle
        s_clamped = np.clip(s_trail, 0, 100)
        ideal_b = np.sqrt(np.clip(100**2 - s_clamped**2, 0, None))
        mae = np.mean(np.abs(ideal_b - b_trail))

        # PUMPING: Are we pumping the brake?
        diffs = np.diff(b_trail)
        # Strict mode: Even tiny > 0.5% vibrations are errors
        pumps = diffs[diffs > 0.5]
        pump_penalty = np.sum(pumps)

        print(f"Corner Exit! Shape Error (MAE): {mae:.1f} | Pumping Penalty: {pump_penalty:.1f}")

        # SCORING - STRICT PRO MODE
        score = 5.0
        
        # 1. Shape error: Tolerance 5.0. Penalty 0.30.
        if mae > 5.0:
            score -= (mae - 5.0) * 0.30
            
        # 2. Pumping: Penalty 0.30.
        score -= pump_penalty * 0.30

        final_score = int(np.clip(round(score), 1, 5))

        # --- DATA EXPORT AND SAVING LOGIC ---
        try:
            # Create folders if they do not exist
            os.makedirs("images", exist_ok=True)
            os.makedirs("data", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Save data in JSONL format
            log_entry = {
                "timestamp": timestamp,
                "score": final_score,
                "mae": round(float(mae), 2),
                "pump_penalty": round(float(pump_penalty), 2)
            }
            with open("data/braking_history.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            # 2. Save image (force UI to draw before exporting)
            QApplication.processEvents()
            exporter = pg.exporters.ImageExporter(self.plot.scene())
            # Name the image so the score is visible in the filename
            exporter.export(f"images/brake_{timestamp}_score_{final_score}.png")
            
        except Exception as e:
            print(f"Saving failed: {e}")

        return final_score

    def update_data(self):
        speed, brake, steer = self.acc.read()

        if self.state == "IDLE":
            if speed > 30 and brake > 5.0:
                self.state = "RECORDING"
                self.x_steer = []
                self.y_brake = []
                self.actual_curve.setData([], [])
                self.score_text.setText("")

        elif self.state == "RECORDING":
            self.x_steer.append(steer)
            self.y_brake.append(brake)

            # LIVE SCALING: The green line stretches on screen instantly
            s_arr = np.array(self.x_steer)
            b_arr = np.array(self.y_brake)

            # Prevent division by zero
            max_s = max(np.max(s_arr), 0.05) 
            max_b = max(np.max(b_arr), 10.0)

            s_norm = (s_arr / max_s) * 100.0
            b_norm = (b_arr / max_b) * 100.0

            # Draw the stretching elastic line
            self.actual_curve.setData(s_norm, b_norm)

            # Trigger: Foot is completely off the brake
            if brake < 1.0:
                self.state = "WAITING"
                
                # Calculate score based on the normalized data and trigger save
                score = self.calculate_score(s_norm, b_norm)
                self.score_text.setText(str(score))
                
                # Keep the result on screen for 3 seconds
                QTimer.singleShot(3000, self.reset_to_idle)

    def reset_to_idle(self):
        self.actual_curve.setData([], [])
        self.score_text.setText("")
        self.state = "IDLE"

if __name__ == '__main__':
    window = TrailBrakingApp()
    window.show()
    sys.exit(app.exec_())