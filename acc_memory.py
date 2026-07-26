import mmap
import struct
import math

# ==============================================================================
# #TELEMETRY_ENGINE #MEMORY_MAPPING #ACC_PHYSICS
# ACC Shared Memory Reader for Raw Physics Data
# ==============================================================================
class ACCSharedMemory:
    def __init__(self):
        self.shm = None
        # #OPTIMIZATION #STRUCT_COMPILATION
        # Pre-compiling the struct format to reduce CPU overhead during high-frequency polling
        self.unpack_format = struct.Struct('<ifffiiffffffffffffffff')
        self.try_connect()

    def try_connect(self):
        # #CONNECTION_HANDLING #SHARED_MEMORY_ACCESS
        # Attempting to map ACC's shared memory physics page
        try:
            self.shm = mmap.mmap(-1, 256, "Local\\acpmf_physics")
            return True
        except FileNotFoundError:
            self.shm = None
            return False

    def read(self):
        # #DATA_POLLING #CONNECTION_VALIDATION
        if self.shm is None:
            if not self.try_connect():
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        try:
            self.shm.seek(0)
            # #DATA_READING #BYTE_EXTRACTION
            # Reading 88 bytes to reach the required wheelLoad data
            data = self.shm.read(88)
            
            # Unpacking data using the pre-compiled struct format
            unpacked = self.unpack_format.unpack(data)
            
            # #CORE_METRICS #TELEMETRY_DATA
            speed = unpacked[7]
            brake = unpacked[2] * 100.0
            steer = abs(unpacked[6])
            
            # #PRO_PHYSICS #ADVANCED_DYNAMICS
            g_lat = unpacked[11]   # Lateral G-force (X)
            g_long = unpacked[13]  # Longitudinal G-force (Z)
            slip_FL = unpacked[14] # Slip Ratio Front Left
            slip_FR = unpacked[15] # Slip Ratio Front Right
            load_FL = unpacked[18] # Suspension Load Front Left (Newtons)
            load_FR = unpacked[19] # Suspension Load Front Right (Newtons)
            
            # #DATA_SANITIZATION #ERROR_PREVENTION
            # Failsafe mechanism against NaN and Infinite values
            if math.isnan(brake) or math.isinf(brake): brake = 0.0
            if math.isnan(steer) or math.isinf(steer): steer = 0.0
            if math.isnan(speed) or math.isinf(speed): speed = 0.0
            
            return speed, brake, steer, g_lat, g_long, slip_FL, slip_FR, load_FL, load_FR
        except Exception:
            # #EXCEPTION_HANDLING #FALLBACK_VALUES
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0