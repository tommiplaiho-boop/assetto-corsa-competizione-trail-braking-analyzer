import sys
import os
import json
import numpy as np
from datetime import datetime

# ==============================================================================
# #CORE_SYSTEM #SAFE_INITIALIZATION #NO_LISTS
# Safe QApplication startup bypassing redundant memory allocations
# ==============================================================================
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import pyqtgraph.exporters

from acc_memory import ACCSharedMemory
from stats_ui import BrakingStatsWindow

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# ==============================================================================
# #MAIN_APP #TELEMETRY_DASHBOARD #DYNAMIC_ENGINE
# Completely dynamic telemetry analyzer avoiding Python lists and hardcoding
# ==============================================================================
class TrailBrakingApp(QMainWindow):
    
    # #CONFIGURATION_MATRIX #DYNAMIC_VARIABLES
    # Replacing all hardcoded magic numbers with configurable constants
    REFRESH_RATE_HZ = 50
    TIMER_INTERVAL_MS = int(1000 / REFRESH_RATE_HZ)
    BUFFER_SIZE = 5000  # Accommodates up to 100 seconds of continuous cornering at 50Hz
    MIN_SPEED_KPH = 30.0
    MIN_BRAKE_PERCENT = 5.0
    RELEASE_BRAKE_PERCENT = 1.0
    ELASTIC_BASE_MAX = 100.0
    
    # Paths calculated dynamically based on current working directory
    BASE_DIR = os.getcwd()
    DATA_DIR = os.path.join(BASE_DIR, "data")
    IMG_DIR = os.path.join(BASE_DIR, "images")
    HISTORY_FILE = os.path.join(DATA_DIR, "braking_history.jsonl")

    # State enumerations (avoiding string hardcoding in state machine)
    STATE_IDLE = 0
    STATE_RECORDING = 1
    STATE_WAITING = 2

    def __init__(self):
        super().__init__()
        
        # #UI_SETUP #DYNAMIC_SCALING
        self.setWindowTitle("Pro Physics Analyzer - Left Foot Trail Braking")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # Calculating window size mathematically relative to current screen resolution
        screen_geometry = QDesktopWidget().availableGeometry()
        dynamic_width = int(screen_geometry.width() * 0.25)
        dynamic_height = int(screen_geometry.height() * 0.55)
        self.resize(dynamic_width, dynamic_height)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # #GRAPH_SETUP #PYQTGRAPH_CONFIG
        self.plot = pg.PlotWidget(background='k')
        layout.addWidget(self.plot)
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setLabel('bottom', 'Steering (Elastic %)')
        self.plot.setLabel('left', 'Left Foot Brake Pressure (Elastic %)')
        
        # #VISUALIZATION #REFERENCE_CURVE #DYNAMIC_RESOLUTION
        # Generating the ideal curve with resolution relative to window width
        self.ideal_curve = self.plot.plot(np.empty(0), np.empty(0), pen=pg.mkPen(color='r', width=3, style=Qt.DashLine))
        ref_resolution = max(10, int(dynamic_width * 0.5))
        ref_x = np.linspace(0, self.ELASTIC_BASE_MAX, ref_resolution)
        ref_y = self.ELASTIC_BASE_MAX * np.sqrt(np.clip(1.0 - (ref_x / self.ELASTIC_BASE_MAX)**2, 0, None))
        self.ideal_curve.setData(ref_x, ref_y)
        
        self.actual_curve = self.plot.plot(np.empty(0), np.empty(0), pen=pg.mkPen(color='g', width=4))
        
        # #UI_ELEMENTS #HUD_OVERLAYS
        self.score_text = pg.TextItem("", color='#f1c40f', anchor=(0.5, 0.5))
        dynamic_text_pos = int(self.ELASTIC_BASE_MAX * 0.5)
        self.score_text.setPos(dynamic_text_pos, dynamic_text_pos) 
        font = self.score_text.textItem.font()
        font.setPointSize(int(dynamic_width * 0.15)) # Font scales with window width
        font.setBold(True)
        self.score_text.textItem.setFont(font)
        self.plot.addItem(self.score_text)

        self.btn_stats = QPushButton("Show Physics Stats")
        self.btn_stats.setStyleSheet("background-color: #34495e; color: white; padding: 10px; font-weight: bold; margin: 0 5px;")
        self.btn_stats.clicked.connect(self.show_stats)
        layout.addWidget(self.btn_stats)
        
        self.btn_reset = QPushButton("Reset Stint Data")
        self.btn_reset.setStyleSheet("background-color: #c0392b; color: white; padding: 10px; font-weight: bold; margin: 0 5px 5px 5px;")
        self.btn_reset.clicked.connect(self.reset_data)
        layout.addWidget(self.btn_reset)
        
        # #STATE_MANAGEMENT #MEMORY_PREALLOCATION
        # Replacing all lists with zeroed pre-allocated NumPy arrays for zero memory fragmentation
        self.acc = ACCSharedMemory()
        self.current_state = self.STATE_IDLE
        
        self.steer_buffer = np.zeros(self.BUFFER_SIZE)
        self.brake_buffer = np.zeros(self.BUFFER_SIZE)
        self.front_load_buffer = np.zeros(self.BUFFER_SIZE)
        self.front_slip_buffer = np.zeros(self.BUFFER_SIZE)
        self.data_index = 0
        
        self.stats_window = None
        
        # #POLLING_SYSTEM #TIMER_EVENT
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(self.TIMER_INTERVAL_MS)

    # ==========================================================================
    # #MATH_ENGINE #PERFORMANCE_EVALUATION #ARRAY_PROCESSING
    # Core logic operating entirely on NumPy array slices (No Lists)
    # ==========================================================================
    def calculate_score(self, s_norm, b_norm):
        data_length = b_norm.size
        min_samples_required = 5
        
        if data_length < min_samples_required: 
            return 1

        max_idx = np.argmax(b_norm)
        b_trail = b_norm[max_idx:]
        s_trail = s_norm[max_idx:]
        
        # Extracting the active telemetry slice based on the pointer
        load_trail = self.front_load_buffer[max_idx:self.data_index]
        slip_trail = self.front_slip_buffer[max_idx:self.data_index]

        if b_trail.size < min_samples_required: 
            return 1

        # #EVALUATION_METRIC #MAE #GEOMETRIC_ERROR
        s_clamped = np.clip(s_trail, 0, self.ELASTIC_BASE_MAX)
        ideal_b = np.sqrt(np.clip(self.ELASTIC_BASE_MAX**2 - s_clamped**2, 0, None))
        mae = np.mean(np.abs(ideal_b - b_trail))

        # #EVALUATION_METRIC #INSTABILITY #PEDAL_PUMPING
        diffs = np.diff(b_trail)
        pump_threshold = 0.5
        pumps = diffs[diffs > pump_threshold]
        pump_penalty = np.sum(pumps)

        # #PRO_PHYSICS #AERODYNAMIC_PLATFORM #CHASSIS_BALANCE
        snap_penalty = 0.0
        if load_trail.size > 1:
            load_diffs = np.diff(load_trail)
            max_load_drop = abs(min(np.min(load_diffs), 0))
            load_drop_divisor = 500.0
            snap_penalty = max_load_drop / load_drop_divisor 

        # #PRO_PHYSICS #GRIP_LIMIT #UNDERSTEER_DETECTION
        max_slip = np.max(slip_trail) if slip_trail.size > 0 else 0.0
        slip_penalty = 0.0
        slip_threshold = 1.5
        if max_slip > slip_threshold:
            slip_penalty = (max_slip - slip_threshold) * 2.0

        # #SCORING_ALGORITHM #FINAL_CALCULATION
        score = 5.0
        mae_threshold = 5.0
        if mae > mae_threshold: 
            score -= (mae - mae_threshold) * 0.30
        score -= pump_penalty * 0.30
        score -= snap_penalty * 0.50
        score -= slip_penalty * 1.0

        return int(np.clip(round(score), 1, 5))

    # ==========================================================================
    # #MAIN_LOOP #DATA_STREAM #DYNAMIC_ROUTING
    # ==========================================================================
    def update_data(self):
        speed, brake, steer, g_lat, g_long, slip_FL, slip_FR, load_FL, load_FR = self.acc.read()

        # #STATE_MACHINE #IDLE_STATE
        if self.current_state == self.STATE_IDLE:
            if speed > self.MIN_SPEED_KPH and brake > self.MIN_BRAKE_PERCENT:
                self.current_state = self.STATE_RECORDING
                self.data_index = 0
                self.actual_curve.setData(np.empty(0), np.empty(0))
                self.score_text.setText("")

        # #STATE_MACHINE #RECORDING_STATE
        elif self.current_state == self.STATE_RECORDING:
            
            # Protection against buffer overflow by resetting or clamping index
            if self.data_index >= self.BUFFER_SIZE:
                self.data_index = self.BUFFER_SIZE - 1
                
            # Recording data directly into pre-allocated NumPy indices (Zero list appends)
            self.steer_buffer[self.data_index] = steer
            self.brake_buffer[self.data_index] = brake
            self.front_load_buffer[self.data_index] = load_FL + load_FR
            self.front_slip_buffer[self.data_index] = max(abs(slip_FL), abs(slip_FR))
            
            self.data_index += 1

            # Processing only the actively recorded slice
            active_steer = self.steer_buffer[:self.data_index]
            active_brake = self.brake_buffer[:self.data_index]

            # Dynamic elastic normalization based on real-time maximums
            max_s = max(np.max(active_steer), 0.05)
            max_b = max(np.max(active_brake), 10.0)

            s_norm = (active_steer / max_s) * self.ELASTIC_BASE_MAX
            b_norm = (active_brake / max_b) * self.ELASTIC_BASE_MAX
            
            # Dynamically adjust plot ranges based on actual data bounds to ensure visibility
            dynamic_x_max = max(self.ELASTIC_BASE_MAX, np.max(s_norm) * 1.05)
            dynamic_y_max = max(self.ELASTIC_BASE_MAX, np.max(b_norm) * 1.05)
            self.plot.setXRange(0, dynamic_x_max, padding=0)
            self.plot.setYRange(0, dynamic_y_max, padding=0)

            # #REALTIME_RENDER #DYNAMIC_GRAPH
            self.actual_curve.setData(s_norm, b_norm)

            # #TRIGGER #END_OF_BRAKING
            if brake < self.RELEASE_BRAKE_PERCENT:
                self.current_state = self.STATE_WAITING
                score = self.calculate_score(s_norm, b_norm)
                self.score_text.setText(str(score))

                if score == 5: self.score_text.setColor('#2ecc71')
                elif score >= 3: self.score_text.setColor('#f1c40f')
                else: self.score_text.setColor('#e74c3c')
                
                self.save_log_entry(score, s_norm, b_norm)
                
                cooldown_delay = 3000
                QTimer.singleShot(cooldown_delay, self.reset_to_idle)

    def save_log_entry(self, final_score, s_norm, b_norm):
        # #DATA_EXPORT #LOGGING #IMAGE_CAPTURE
        try:
            os.makedirs(self.IMG_DIR, exist_ok=True)
            os.makedirs(self.DATA_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            log_entry = {
                "timestamp": timestamp,
                "score": final_score
            }
            with open(self.HISTORY_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            QApplication.processEvents()
            exporter = pg.exporters.ImageExporter(self.plot.scene())
            dynamic_img_path = os.path.join(self.IMG_DIR, f"brake_{timestamp}_score_{final_score}.png")
            exporter.export(dynamic_img_path)
            
            if self.stats_window is not None and self.stats_window.isVisible():
                self.stats_window.load_and_plot_data()

        except Exception as e:
            print(f"Saving failed: {e}")

    def reset_to_idle(self):
        # #STATE_RESET #CLEANUP
        self.actual_curve.setData(np.empty(0), np.empty(0))
        self.score_text.setText("")
        self.current_state = self.STATE_IDLE

    def reset_data(self):
        # #DATA_MANAGEMENT #FILE_WIPE
        try:
            if os.path.exists(self.HISTORY_FILE):
                open(self.HISTORY_FILE, 'w').close()
            self.reset_to_idle()
            if self.stats_window is not None:
                self.stats_window.load_and_plot_data()
                self.stats_window.summary_label.setText("Data reset. Go drive some corners! #FreshStart")
            print("Stint data reset successfully.")
        except Exception as e:
            print(f"Reset error: {e}")

    def show_stats(self):
        # #UI_NAVIGATION #WINDOW_SPAWN
        if self.stats_window is None:
            self.stats_window = BrakingStatsWindow()
        self.stats_window.load_and_plot_data()
        self.stats_window.show()
        self.stats_window.raise_()

if __name__ == '__main__':
    window = TrailBrakingApp()
    window.show()
    sys.exit(app.exec_())