//=================================================================
// program.s  —  Global definitions for Thermal Conductivity HMI
// Device: TJC4832T135_011  (320×480, 65K colors)
// MCU:   ESP32 via UART 115200 baud
//=================================================================

//--- System variables ---
int sys0=0
int sys1=0
int sys2=0

//--- UART & display ---
baud=115200
dim=100
recmod=0

//--- Application variables ---
// Page navigation
int currentPage=0

// Sensor data (integer °C values, 0–1200)
int t1_val=0
int t2_val=0
int t3_val=0
int t4_val=0
int t5_val=0

// T5 progress bar (0–100 mapped from 0–1200)
int t5bar=0

// Min/Max tracking per sensor
int t1_min=1200,t1_max=0
int t2_min=1200,t2_max=0
int t3_min=1200,t3_max=0
int t4_min=1200,t4_max=0
int t5_min=1200,t5_max=0

// Rate of change (°C/s)
int t1_rate=0
int t2_rate=0
int t3_rate=0
int t4_rate=0
int t5_rate=0

// Heater status: 0=IDLE, 1=ACTIVE, 2=ERROR
int heater_status=0

// Selected sensor for Page 3 detail view (1–5)
int selectedSensor=1

// Error log count
int errCount=0

// Splash timer flag
int splashDone=0

//--- Start on Page 0 ---
page 0
