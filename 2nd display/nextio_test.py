"""
Nextion Quick Test - проверка связи с дисплеем
Запуск: python nextion_test.py
"""

import serial
import time

COM_PORT = "COM7"   # <<< ВАШ COM ПОРТ

def cmd(ser, command):
    """Send command to Nextion"""
    data = command.encode('utf-8') + b'\xff\xff\xff'
    ser.write(data)
    print(f"  >>> {command}")
    time.sleep(0.1)

def main():
    print("Nextion Connection Test")
    print(f"Port: {COM_PORT}")

    try:
        ser = serial.Serial(COM_PORT, 115200, timeout=1)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    time.sleep(2)  # Wait for Nextion to be ready
    print("\n--- Test 1: Dim screen (if connected, screen will dim) ---")
    cmd(ser, "dim=30")
    time.sleep(2)

    print("\n--- Test 2: Restore brightness ---")
    cmd(ser, "dim=100")
    time.sleep(1)

    print("\n--- Test 3: Go to Page 1 ---")
    cmd(ser, "page 1")
    time.sleep(1)

    print("\n--- Test 4: Set global variables directly ---")
    cmd(ser, "t1_val.val=123")
    cmd(ser, "t2_val.val=456")
    cmd(ser, "t3_val.val=789")
    cmd(ser, "t4_val.val=234")
    cmd(ser, "t5_val.val=567")
    cmd(ser, "heater_status.val=1")
    time.sleep(1)

    print("\n--- Test 5: Try cov conversion manually ---")
    cmd(ser, "cov t1_val,t0.txt,0")
    time.sleep(1)

    print("\n--- Test 6: Set text directly on component ---")
    cmd(ser, 't0.txt="HELLO NEXTION"')
    time.sleep(1)

    print("\n--- Test 7: Check all text component names on Page 1 ---")
    # Try common component names
    for name in ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9",
                 "t10", "t11", "t12", "t13", "t14", "t15"]:
        cmd(ser, f'{name}.txt="OK"')

    time.sleep(2)

    print("\n--- Test 8: Read response from Nextion ---")
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        print(f"  <<< Received: {data.hex()}")
    else:
        print("  <<< No response from Nextion (this is normal)")

    print("\nDone! Check the display:")
    print("  - Did screen dim in Test 1? If YES = UART works")
    print("  - Do you see 'HELLO NEXTION' or 'OK' anywhere? If YES = text works")
    print("  - If nothing visible = component names don't match or z-order issue")

    ser.close()

if __name__ == "__main__":
    main()
