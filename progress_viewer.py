import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
import pyqtgraph as pg

class ProgressViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trail Braking - Progress History")
        self.resize(800, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Refresh button
        self.btn_refresh = QPushButton("Refresh Data")
        self.btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(self.btn_refresh)
        
        # Graph
        self.plot = pg.PlotWidget(background='k')
        layout.addWidget(self.plot)
        self.plot.setLabel('bottom', 'Corner Sequence (Time)')
        self.plot.setLabel('left', 'Score (1-5)')
        self.plot.setYRange(0, 5.5)
        self.plot.showGrid(x=False, y=True, alpha=0.3)
        
        self.load_data()

    def load_data(self):
        self.plot.clear()
        
        filepath = "data/braking_history.jsonl"
        if not os.path.exists(filepath):
            print("Data log not found. Drive a few corners first!")
            return
            
        scores = []
        with open(filepath, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    scores.append(data["score"])
                except json.JSONDecodeError:
                    continue
                    
        if not scores:
            return
            
        x_axis = list(range(1, len(scores) + 1))
        
        # Draw points (Scatter)
        scatter = pg.ScatterPlotItem(x=x_axis, y=scores, size=10, pen=pg.mkPen(None), brush=pg.mkBrush(0, 255, 0, 150))
        self.plot.addItem(scatter)
        
        # Draw moving average (Trend) if there are enough corners
        if len(scores) > 5:
            window_size = 5
            moving_avg = [sum(scores[i:i+window_size])/window_size for i in range(len(scores)-window_size+1)]
            x_trend = list(range(window_size, len(scores) + 1))
            
            trend_line = self.plot.plot(x_trend, moving_avg, pen=pg.mkPen(color='y', width=3, style=pg.QtCore.Qt.DashLine))
        
        print(f"Loaded history for {len(scores)} corners.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProgressViewer()
    window.show()
    sys.exit(app.exec_())