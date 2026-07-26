import os
import json
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

# ==============================================================================
# #DATA_PIPELINE #GENERATOR_YIELD #NO_LISTS
# Extremely fast, memory-efficient data stream bypassing Python lists entirely
# ==============================================================================
def stream_diagnostics_data(filepath):
    with open(filepath, "r") as f:
        for line in f:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            try:
                data = json.loads(stripped_line)
                # Yielding a tuple directly to map into a structured NumPy array
                yield (
                    data.get("score", 0.0),
                    data.get("mae", 0.0),
                    data.get("pump_penalty", 0.0),
                    data.get("snap_penalty", 0.0),
                    data.get("slip_penalty", 0.0)
                )
            except ValueError:
                continue

# ==============================================================================
# #STATS_DASHBOARD #DYNAMIC_ENGINE #EXPERT_SYSTEM
# Dynamic dashboard utilizing vectorized calculations for instant rendering
# ==============================================================================
class BrakingStatsWindow(QMainWindow):
    
    # #CONFIGURATION_MATRIX #DYNAMIC_VARIABLES
    BASE_DIR = os.getcwd()
    DATA_DIR = os.path.join(BASE_DIR, "data")
    HISTORY_FILE = os.path.join(DATA_DIR, "braking_history.jsonl")
    
    # Thresholds and Constants
    MAX_SCORE = 5.0
    GOOD_SCORE_THRESHOLD = 3.0
    ELITE_SCORE_THRESHOLD = 4.5
    BAR_WIDTH = 0.6
    
    # Color Palette definitions
    COLOR_EXCELLENT = pg.mkBrush(46, 204, 113)  # Green
    COLOR_WARNING = pg.mkBrush(241, 196, 15)    # Yellow
    COLOR_CRITICAL = pg.mkBrush(231, 76, 60)    # Red
    COLOR_BACKGROUND = 'k'
    
    # Memory structure definition for high-speed parsing
    STRUCT_DTYPE = np.dtype([
        ('score', np.float32),
        ('mae', np.float32),
        ('pump', np.float32),
        ('snap', np.float32),
        ('slip', np.float32)
    ])

    def __init__(self):
        super().__init__()
        
        # #UI_SETUP #DYNAMIC_SCALING
        self.setWindowTitle("Left Foot Trail Braking - Physics Diagnostics")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # Scaling window relative to the user's current display properties
        screen_geometry = QDesktopWidget().availableGeometry()
        dynamic_width = int(screen_geometry.width() * 0.4)
        dynamic_height = int(screen_geometry.height() * 0.45)
        self.resize(dynamic_width, dynamic_height)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # #UI_ELEMENTS
        self.summary_label = QLabel("Loading physics diagnostics...")
        dynamic_font_size = max(10, int(dynamic_width * 0.015))
        self.summary_label.setFont(QFont("Arial", dynamic_font_size, QFont.Bold))
        self.summary_label.setStyleSheet("color: white; background-color: #2c3e50; padding: 10px;")
        layout.addWidget(self.summary_label)
        
        self.plot = pg.PlotWidget(background=self.COLOR_BACKGROUND)
        layout.addWidget(self.plot)
        self.plot.setLabel('bottom', 'Corner Event Sequence')
        self.plot.setLabel('left', f'Trail Braking Score (1-{int(self.MAX_SCORE)})')
        self.plot.setYRange(0, self.MAX_SCORE * 1.1)
        self.plot.showGrid(x=False, y=True, alpha=0.3)
        
        self.load_and_plot_data()

    def load_and_plot_data(self):
        self.plot.clear()
        
        if not os.path.exists(self.HISTORY_FILE) or os.stat(self.HISTORY_FILE).st_size == 0:
            self.summary_label.setText("No telemetry found. Drive some corners first! #AwaitingData")
            return
            
        # ======================================================================
        # #DATA_PROCESSING #MEMORY_MAPPING
        # Bypassing python lists and directly constructing a mapped array
        # ======================================================================
        try:
            data_matrix = np.fromiter(stream_diagnostics_data(self.HISTORY_FILE), dtype=self.STRUCT_DTYPE)
        except Exception as e:
            self.summary_label.setText(f"File read error: {e}")
            return
            
        data_count = data_matrix.size
        if data_count == 0:
            return
            
        # Extracting specific arrays instantly
        scores = data_matrix['score']
        x_axis = np.arange(1, data_count + 1)
        
        # ======================================================================
        # #VISUALIZATION #VECTORIZED_MASKING #ZERO_LOOPS
        # Applying colors via boolean masks instead of iterating arrays to build lists
        # ======================================================================
        mask_excellent = scores == self.MAX_SCORE
        mask_warning = (scores >= self.GOOD_SCORE_THRESHOLD) & (scores < self.MAX_SCORE)
        mask_critical = scores < self.GOOD_SCORE_THRESHOLD
        
        # Rendering only the masked segments dynamically
        if np.any(mask_excellent):
            self.plot.addItem(pg.BarGraphItem(x=x_axis[mask_excellent], height=scores[mask_excellent], width=self.BAR_WIDTH, brush=self.COLOR_EXCELLENT))
        
        if np.any(mask_warning):
            self.plot.addItem(pg.BarGraphItem(x=x_axis[mask_warning], height=scores[mask_warning], width=self.BAR_WIDTH, brush=self.COLOR_WARNING))
            
        if np.any(mask_critical):
            self.plot.addItem(pg.BarGraphItem(x=x_axis[mask_critical], height=scores[mask_critical], width=self.BAR_WIDTH, brush=self.COLOR_CRITICAL))
        
        # ======================================================================
        # #EXPERT_SYSTEM #MATH_ANALYSIS #VECTORIZED_SUMS
        # Instant diagnostics utilizing C-level NumPy summations
        # ======================================================================
        total_mae = np.sum(data_matrix['mae'])
        total_snap = np.sum(data_matrix['snap'])
        total_slip = np.sum(data_matrix['slip'])
        avg_score = np.mean(scores)
        
        analysis_text = f"Analyzed: {data_count} Corners | Avg Score: {avg_score:.1f}/{self.MAX_SCORE:.1f}\n"
        
        if total_snap > total_mae:
            analysis_text += "Physics Alert: SUSPENSION SNAP DETECTED #ChassisImbalance\n"
            analysis_text += "Your brake release is bouncing the front suspension. Weight transfer is too violent."
        elif total_slip > total_mae:
            analysis_text += "Physics Alert: EXCESSIVE SLIP (UNDERSTEER) #GripLimit\n"
            analysis_text += "You are pushing the front tires past their grip limit during the turn-in phase."
        elif avg_score >= self.ELITE_SCORE_THRESHOLD:
            analysis_text += "Stint Evaluation: ELITE PRO LEVEL #PerfectTrailBraking\n"
            analysis_text += "Perfect synchronization and flawless aerodynamic load transfer."
        else:
            analysis_text += "Stint Evaluation: DEVELOPING TECHNIQUE #KeepPushing\n"
            analysis_text += "Focus on smoothing out the release phase for consistent left foot braking."
            
        self.summary_label.setText(analysis_text)