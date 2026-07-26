import sys
import json
import os
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg

# ==============================================================================
# #CORE_SYSTEM #SAFE_INITIALIZATION
# Safe QApplication startup to prevent memory reservation crashes
# ==============================================================================
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# ==============================================================================
# #DATA_PIPELINE #GENERATOR_YIELD #NO_LISTS
# Memory-efficient generator avoiding Python lists entirely
# ==============================================================================
def stream_telemetry_data(filepath):
    with open(filepath, "r") as f:
        for line in f:
            stripped_line = line.strip()
            if not stripped_line: 
                continue
            try:
                data = json.loads(stripped_line)
                if "score" in data and data["score"] is not None:
                    yield float(data["score"])
            except Exception:
                continue

class ProgressViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ======================================================================
        # #UI_SETUP #DYNAMIC_SCALING
        # ======================================================================
        self.setWindowTitle("Left Foot Trail Braking - Live Progress History")
        self.setWindowFlags(Qt.WindowStaysOnTopHint) # #ALWAYS_ON_TOP
        
        # Dynamic window sizing based on active screen resolution
        screen_geometry = QDesktopWidget().availableGeometry()
        self.resize(int(screen_geometry.width() * 0.4), int(screen_geometry.height() * 0.4))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.info_label = QLabel("Waiting for data... #Telemetry #ProPhysics")
        self.info_label.setStyleSheet("color: #ecf0f1; font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(self.info_label)
        
        self.btn_refresh = QPushButton("Manual Refresh (Auto-updating in background...)")
        self.btn_refresh.clicked.connect(lambda: self.load_data(silent=False))
        self.btn_refresh.setStyleSheet("background-color: #2980b9; color: white; padding: 8px; font-weight: bold;")
        layout.addWidget(self.btn_refresh)
        
        # #GRAPH_SETUP
        self.plot = pg.PlotWidget(background='#1e1e1e')
        layout.addWidget(self.plot)
        self.plot.setLabel('bottom', 'Corner Sequence (Time)')
        self.plot.setLabel('left', 'Score')
        self.plot.showGrid(x=False, y=True, alpha=0.3)
        
        self.last_data_count = 0
        self.load_data(silent=False)
        
        # #BACKGROUND_WORKER #POLLING_SYSTEM
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(lambda: self.load_data(silent=True))
        self.auto_timer.start(2000)

    def load_data(self, silent=False):
        filepath = "data/braking_history.jsonl"
        if not os.path.exists(filepath):
            if not silent:
                self.info_label.setText("Data log not found. Drive a few corners first! #AwaitingData")
            return
            
        # ======================================================================
        # #DATA_PROCESSING #DYNAMIC_COMPUTATION
        # ======================================================================
        try:
            # Utilizing numpy fromiter to bypass standard Python lists completely
            y_scores = np.fromiter(stream_telemetry_data(filepath), dtype=float)
        except Exception as e:
            if not silent:
                print(f"File read error: {e}")
            return
            
        data_count = y_scores.size
        if data_count == 0:
            return
            
        if silent and data_count == self.last_data_count:
            return
            
        self.last_data_count = data_count
        self.plot.clear()
        
        # Dynamic axis scaling based on actual performance data boundaries
        min_score = np.min(y_scores)
        max_score = np.max(y_scores)
        margin = (max_score - min_score) * 0.1 if max_score > min_score else 0.5
        self.plot.setYRange(min_score - margin, max_score + margin)
        
        x_axis = np.arange(1, data_count + 1)
        
        # #VISUALIZATION #SCATTER_PLOT
        scatter = pg.ScatterPlotItem(x=x_axis, y=y_scores, size=10, pen=pg.mkPen(None), brush=pg.mkBrush(46, 204, 113, 200))
        self.plot.addItem(scatter)
        
        # #DYNAMIC_MATH #MOVING_AVERAGE
        # Window size adapts mathematically to the volume of telemetry data
        if data_count > 3:
            dynamic_window = max(2, int(data_count * 0.15))
            moving_avg = np.convolve(y_scores, np.ones(dynamic_window)/dynamic_window, mode='valid')
            x_trend = np.arange(dynamic_window, data_count + 1)
            
            trend_line = self.plot.plot(x_trend, moving_avg, pen=pg.mkPen(color='#f1c40f', width=3, style=Qt.DashLine))
        
        # #UI_UPDATE
        avg_all = np.mean(y_scores)
        self.info_label.setText(f"Loaded {data_count} corners | Overall Average Score: {avg_all:.1f}  #LeftFootBraking #ProPhysics")

if __name__ == '__main__':
    window = ProgressViewer()
    window.show()
    sys.exit(app.exec_())