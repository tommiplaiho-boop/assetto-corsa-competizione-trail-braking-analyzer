Assetto Corsa Competizione: Pro Physics & Trail Braking Analyzer
1. How the Program Works (The Mechanics)
The application is a real-time, ultra-low-latency telemetry analyzer built specifically for Assetto Corsa Competizione (ACC).

Live Telemetry Extraction: It taps directly into ACC's engine via Shared Memory mapping, pulling raw physics data at a high frequency (50Hz) without impacting game performance.

Dynamic Data Processing: Utilizing highly optimized NumPy arrays instead of standard memory lists, the program actively records steering angle, brake pressure, front suspension load, and tire slip ratios the moment a corner entry is detected.

Real-Time Visualization: As you drive, the tool plots your actual input curve (green line) against an ideal, dynamically calculated mathematical boundary (red dashed line).

Instant Diagnostics: Once the brake is fully released, a custom scoring algorithm immediately evaluates the maneuver, logging the data and updating a separate live diagnostic dashboard with physics-based feedback.

2. What It Is Based On (The Physics)
The underlying logic of the analyzer is firmly rooted in real-world motorsport physics and vehicle dynamics:

The Traction Circle (Friction Circle): A tire has a finite maximum grip limit. 100% of the grip can be used for braking or cornering. If you are blending both, the transition must be proportional. The program calculates the geometric Mean Absolute Error (MAE) between your input and the ideal curved boundary, penalizing inputs that fail to maximize the available grip.

Chassis Balance & Weight Transfer: The software actively monitors the combined load on the front suspension (measured in Newtons). If the brake is released too abruptly, it triggers a Suspension Snap penalty. An abrupt release decompresses the front springs violently, shifting the car's weight to the rear and instantly killing front-end grip.

Tire Saturation (Slip Ratio): The system tracks the physical slip ratio of the front tires. Pushing past the optimal slip angle triggers an Excessive Slip penalty, mathematically detecting understeer caused by over-driving the entry phase.

3. What Can Be Achieved (The Benefits)
Using this tool bridges the gap between guessing and knowing, allowing you to objectively refine your driving technique:

Mastering the Release Phase: Trail braking is not about how hard you press the brake, but how smoothly you let it go. This tool provides instant, visual feedback on the exact quality of your brake release.

Refining Left-Foot Braking: By analyzing the exact contour of the braking curve, you can effectively train and calibrate the delicate muscle memory required for elite-level left-foot braking.

Eliminating Pedal "Noise": The algorithm actively detects pedal pumping and micro-stutters. Smoothing out these nervous, jagged inputs ensures a highly stable aerodynamic platform throughout the corner.

Faster, More Consistent Laptimes: By synchronizing your steering input perfectly with your brake release, you maximize minimum corner speed, eliminate mid-corner understeer, and carry significantly more momentum onto the ensuing straights.
