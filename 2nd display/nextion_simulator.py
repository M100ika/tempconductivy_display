"""
Nextion HMI Simulator - Thermal Conductivity Measurement System
Имитация данных ESP32 для тестирования дисплея Nextion

Использование:
  python nextion_simulator.py

Настройте COM порт и скорость ниже:
"""

import serial
import time
import random
import threading
import sys

# ============================================================
# НАСТРОЙКИ
# ============================================================
COM_PORT = "COM7"        # <<< ИЗМЕНИТЕ НА СВОЙ COM ПОРТ
BAUD_RATE = 115200
REFRESH_MS = 500         # Интервал обновления данных (мс)

# ============================================================
# NEXTION PROTOCOL
# ============================================================
TERMINATOR = b'\xff\xff\xff'

def nextion_cmd(ser, cmd):
    """Отправить команду на Nextion с терминатором 0xFF 0xFF 0xFF"""
    try:
        ser.write((cmd + TERMINATOR).encode('utf-8', errors='replace'))
    except Exception as e:
        print(f"[SEND ERROR] {e}")

def nextion_set_int(ser, var, val):
    """Установить числовую переменную: var.val=val"""
    nextion_cmd(ser, f"{var}.val={val}")

def nextion_set_txt(ser, comp, txt):
    """Установить текст: comp.txt="txt" """
    # Экранируем кавычки внутри текста
    escaped = txt.replace('"', '\\"')
    nextion_cmd(ser, f'{comp}.txt="{escaped}"')

# ============================================================
# ИМИТАЦИЯ ДАННЫХ
# ============================================================

class SensorSimulator:
    """Имитация 5 термопар и нагревателя"""

    def __init__(self):
        # Текущие температуры
        self.temps = [25.0, 30.0, 22.0, 28.0, 45.0]   # T1-T5
        # Целевые температуры (для плавного изменения)
        self.targets = [450.0, 320.0, 280.0, 510.0, 890.0]
        # Min/Max
        self.tmin = [1200, 1200, 1200, 1200, 1200]
        self.tmax = [0, 0, 0, 0, 0]
        # Скорость изменения
        self.rates = [0, 0, 0, 0, 0]
        # Предыдущие температуры (для расчёта rate)
        self.prev_temps = self.temps.copy()
        # Нагреватель: 0=IDLE, 1=ACTIVE, 2=ERROR
        self.heater = 0
        # Фаза симуляции
        self.phase = 0       # 0=нагрев, 1=стабильность, 2=перегрев, 3=охлаждение
        self.tick = 0

    def update(self):
        """Обновить значения (вызывать каждые REFRESH_MS)"""
        self.tick += 1
        self.prev_temps = [int(round(t)) for t in self.temps]

        # Автоматическая смена фаз для реалистичной симуляции
        if self.tick < 30:
            self.phase = 0    # Нагрев
            self.heater = 1
        elif self.tick < 60:
            self.phase = 1    # Стабильность
            self.heater = 1
        elif self.tick == 60:
            self.phase = 2    # Перегрев!
            self.heater = 2
        elif self.tick == 65:
            self.phase = 3    # Охлаждение
            self.heater = 0
        elif self.tick > 95:
            self.tick = 0     # Цикл заново
            self.phase = 0
            self.heater = 1
            for i in range(5):
                self.temps[i] = random.uniform(20, 35)
                self.tmin[i] = 1200
                self.tmax[i] = 0

        for i in range(5):
            if self.phase == 0:
                # Нагрев — приближаемся к целевым
                diff = self.targets[i] - self.temps[i]
                self.temps[i] += diff * 0.05 + random.uniform(-2, 2)
            elif self.phase == 1:
                # Стабильность — небольшие колебания
                self.temps[i] += random.uniform(-5, 5)
            elif self.phase == 2:
                # Перегрев — T5 растёт сильно
                if i == 4:
                    self.temps[i] += random.uniform(5, 15)
                else:
                    self.temps[i] += random.uniform(-3, 3)
            elif self.phase == 3:
                # Охлаждение
                self.temps[i] -= random.uniform(2, 8)

            # Ограничения 0-1200
            self.temps[i] = max(0, min(1200, self.temps[i]))

            # Целочисленное значение
            val = int(round(self.temps[i]))

            # Min/Max
            if val < self.tmin[i]:
                self.tmin[i] = val
            if val > self.tmax[i]:
                self.tmax[i] = val

            # Rate (°C/s = разница за 0.5с × 2)
            self.rates[i] = (val - self.prev_temps[i]) * 2


class ErrorLogSimulator:
    """Имитация журнала ошибок"""

    ERROR_CODES = [
        ("ERR-01", "Over threshold T1"),
        ("ERR-01", "Over threshold T2"),
        ("ERR-01", "Over threshold T3"),
        ("ERR-01", "Over threshold T4"),
        ("ERR-01", "Over threshold T5"),
        ("ERR-02", "Sensor T1 fault"),
        ("ERR-02", "Sensor T3 fault"),
        ("ERR-03", "Comm timeout"),
        ("ERR-04", "Heater overload"),
        ("ERR-05", "ADC overflow"),
    ]

    def __init__(self):
        self.entries = [""] * 10
        self.count = 0

    def add_entry(self):
        """Добавить случайную ошибку"""
        code, desc = random.choice(self.ERROR_CODES)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
        entry = f"{code}|{timestamp}|{desc}"

        # Сдвинуть вниз
        for i in range(9, 0, -1):
            self.entries[i] = self.entries[i - 1]
        self.entries[0] = entry
        self.count += 1

        return self.entries.copy()


# ============================================================
# ОТПРАВКА ДАННЫХ НА NEXTION
# ============================================================

def send_sensor_data(ser, sim):
    """Отправить температуры и статус нагревателя"""
    for i in range(5):
        val = int(round(sim.temps[i]))
        nextion_set_int(ser, f"t{i+1}_val", val)
        nextion_set_int(ser, f"t{i+1}_min", sim.tmin[i])
        nextion_set_int(ser, f"t{i+1}_max", sim.tmax[i])
        nextion_set_int(ser, f"t{i+1}_rate", sim.rates[i])

    nextion_set_int(ser, "heater_status", sim.heater)


def send_system_info(ser):
    """Отправить системную информацию (Page 4)"""
    nextion_set_txt(ser, "espStatus", "Connected")
    nextion_set_txt(ser, "wifiStatus", "Connected")
    nextion_set_txt(ser, "ssidVal", "Nazarbayev_Uni")
    nextion_set_txt(ser, "ipAddr", "IP:192.168.1.42")
    nextion_set_txt(ser, "macAddr", "MAC:A4:CF:12:34:56:78")
    print("  [SYS] System info sent")


def send_error_log(ser, log_sim):
    """Отправить журнал ошибок на Nextion"""
    entries = log_sim.add_entry()
    for i in range(10):
        nextion_set_txt(ser, f"log{i+1}", entries[i])
    nextion_set_int(ser, "errCount", log_sim.count)
    nextion_cmd(ser, "cov errCount,errCnt.txt,0")
    print(f"  [LOG] Error #{log_sim.count}: {entries[0]}")


# ============================================================
# ОБРАБОТКА ВВОДА ОТ NEXTION
# ============================================================

def listen_nextion(ser):
    """Поток для чтения команд от Nextion"""
    buffer = ""
    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
                buffer += data

                # Ищем команды (заканчиваются 0xFF 0xFF 0xFF)
                while '\xff\xff\xff' in buffer:
                    cmd, _, buffer = buffer.partition('\xff\xff\xff')
                    cmd = cmd.strip('\x00').strip()
                    if cmd:
                        handle_command(ser, cmd)
            time.sleep(0.01)
        except Exception as e:
            print(f"[LISTEN ERROR] {e}")
            time.sleep(0.1)


def handle_command(ser, cmd):
    """Обработать команду от Nextion"""
    print(f"\n  [RECV] Command from Nextion: '{cmd}'")

    if cmd == "WIFI_CFG":
        nextion_set_txt(ser, "espStatus", "Config...")
        nextion_set_txt(ser, "wifiStatus", "Config...")
        print("  [ACTION] WiFi config mode started")
        # Через 5 секунд "подключаемся обратно"
        time.sleep(5)
        nextion_set_txt(ser, "espStatus", "Connected")
        nextion_set_txt(ser, "wifiStatus", "Connected")
        nextion_set_txt(ser, "ssidVal", "New_WiFi")
        nextion_set_txt(ser, "ipAddr", "IP:192.168.1.100")
        print("  [ACTION] WiFi reconnected")

    elif cmd == "LOG_CLEAR":
        print("  [ACTION] Log cleared")

    elif cmd == "REFRESH_250":
        print("  [ACTION] Refresh rate set to 250ms")

    elif cmd == "REFRESH_500":
        print("  [ACTION] Refresh rate set to 500ms")

    elif cmd == "REFRESH_1000":
        print("  [ACTION] Refresh rate set to 1000ms")

    else:
        print(f"  [UNKNOWN] '{cmd}'")


# ============================================================
# ГЛАВНЫЙ ЦИКЛ
# ============================================================

def main():
    print("=" * 60)
    print("  Nextion HMI Simulator - Thermal Conductivity System")
    print("  Nazarbayev University")
    print("=" * 60)
    print(f"  COM Port: {COM_PORT}")
    print(f"  Baud Rate: {BAUD_RATE}")
    print(f"  Refresh: {REFRESH_MS}ms")
    print("=" * 60)

    # Подключение
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"\n  [OK] Connected to {COM_PORT}")
    except Exception as e:
        print(f"\n  [ERROR] Cannot open {COM_PORT}: {e}")
        print(f"  Check COM port and try again.")
        print(f"  Available ports:")
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            print(f"    - {p.device}: {p.description}")
        sys.exit(1)

    time.sleep(1)

    # Инициализация симуляторов
    sim = SensorSimulator()
    log_sim = ErrorLogSimulator()

    # Запуск потока для чтения команд от Nextion
    listener = threading.Thread(target=listen_nextion, args=(ser,), daemon=True)
    listener.start()

    # Отправить системную информацию
    send_system_info(ser)

    # Перейти на Page 1 (Dashboard)
    time.sleep(0.5)
    nextion_cmd(ser, "page 1")
    print("  [NAV] Switched to Page 1 (Dashboard)")

    tick_count = 0
    error_interval = 40   # Добавлять ошибку каждые N тиков
    sysinfo_interval = 100  # Обновлять системную информацию каждые N тиков

    print("\n  Simulation started! Press Ctrl+C to stop.\n")
    print("  " + "-" * 56)
    print(f"  {'Tick':>4} | {'T1':>5} | {'T2':>5} | {'T3':>5} | {'T4':>5} | {'T5':>5} | Heater")
    print("  " + "-" * 56)

    try:
        while True:
            tick_count += 1

            # Обновить симуляцию
            sim.update()

            # Отправить данные датчиков
            send_sensor_data(ser, sim)

            # Вывод в консоль
            t = [int(round(v)) for v in sim.temps]
            heater_names = {0: "IDLE  ", 1: "ACTIVE", 2: "ERROR "}
            phase_names = {0: "HEATING", 1: "STABLE ", 2: "OVERHEAT", 3: "COOLING"}
            print(f"  {tick_count:>4} | {t[0]:>5} | {t[1]:>5} | {t[2]:>5} | {t[3]:>5} | {t[4]:>5} | {heater_names[sim.heater]} | {phase_names[sim.phase]}")

            # Периодически добавлять ошибки
            if tick_count % error_interval == 0:
                send_error_log(ser, log_sim)

            # Периодически обновлять системную информацию
            if tick_count % sysinfo_interval == 0:
                send_system_info(ser)

            # Ждать до следующего обновления
            time.sleep(REFRESH_MS / 1000.0)

    except KeyboardInterrupt:
        print("\n\n  [STOP] Simulation stopped by user")
    finally:
        ser.close()
        print("  [OK] Serial port closed")


if __name__ == "__main__":
    main()
