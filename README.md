# ACC Trail Braking Pro Analyzer

# ACC Trail Braking Pro Analyzer
> **Current Project Status: v0.0.1-alpha** > This is an early alpha release. The core telemetry framework and strict scoring algorithm are fully functional, but features are subject to further refinement based on testing and user feedback.

A real-time kinetic telemetry overlay for Assetto Corsa Competizione (ACC) designed specifically to refine left-foot trail braking muscle memory. 

Traditional telemetry tools force you to analyze your mistakes *after* the session. This tool provides **immediate, real-time visual biofeedback** during the corner, projecting your brake release and steering input onto a dynamic, elastic friction circle.

## Features

* **Elastic Friction Circle:** The visualization dynamically scales based on your maximum input. It perfectly maps the physical relationship between releasing the brake pressure and increasing the steering angle.
* **Strict "Pro-Mode" Scoring (1-5):** Once your foot leaves the brake pedal completely, the app calculates a score based on real-world physics:
  * **Shape Error (MAE):** Penalizes any deviation from a perfect friction circle arc.
  * **Pumping Penalty:** Highly sensitive detection for any micro-vibrations or "pumping" of the brake pedal during the release phase. Ideal for mastering high-end load cell pedals.
* **Always-On-Top Overlay:** The window with a standard Windows title bar sits neatly over your ACC gameplay, allowing you to position and drag it anywhere on your screen.
* **Data Logging & Progress Tracking:** Automatically saves an image of every braking zone and logs the scoring data into a JSONL file.
* **Progress Viewer:** A standalone app to visualize your learning curve and moving average across hundreds of corners.

## How to Use (.exe Version)

The easiest way to use the analyzer without installing Python:

1. Download the latest compiled release.
2. Launch ACC and load into a track.
3. Simply double-click the `.exe` file to start the analyzer.
4. Drive! The analyzer will automatically start recording when you apply brake pressure and are moving above 30 km/h.

## Developer Installation (Python Version)

If you prefer to run the raw source code, ensure you have Python 3.8+ installed.

Install the required Python libraries:
```bash
pip install pyqt5 pyqtgraph numpy