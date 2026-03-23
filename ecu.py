"""
Claude code !!!
Car ECU (Engine Control Unit) Simulation
A comprehensive ECU implementation modeling real automotive control systems.
"""

import time
import math
import random
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from collections import deque


# ─── Enums ────────────────────────────────────────────────────────────────────

class EngineState(Enum):
    OFF        = "OFF"
    CRANKING   = "CRANKING"
    IDLE       = "IDLE"
    RUNNING    = "RUNNING"
    OVERHEAT   = "OVERHEAT"
    FAULT      = "FAULT"


class GearPosition(Enum):
    PARK    = "P"
    REVERSE = "R"
    NEUTRAL = "N"
    DRIVE   = "D"
    MANUAL  = "M"


class FaultCode(Enum):
    P0100 = "Mass Air Flow Sensor Fault"
    P0110 = "Intake Air Temp Sensor Fault"
    P0115 = "Coolant Temp Sensor Fault"
    P0130 = "O2 Sensor Circuit Fault (Bank 1)"
    P0170 = "Fuel Trim Malfunction"
    P0300 = "Random/Multiple Cylinder Misfire"
    P0400 = "EGR Flow Malfunction"
    P0420 = "Catalyst Efficiency Below Threshold"
    P0500 = "Vehicle Speed Sensor Fault"
    P0700 = "Transmission Control System Fault"


# ─── Sensor Models ────────────────────────────────────────────────────────────

@dataclass
class SensorReading:
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    valid: bool = True

    def __repr__(self):
        return f"{self.value:.2f} {self.unit}"


class Sensor:
    def __init__(self, name: str, min_val: float, max_val: float,
                 noise_sigma: float = 0.0, unit: str = ""):
        self.name        = name
        self.min_val     = min_val
        self.max_val     = max_val
        self.noise_sigma = noise_sigma
        self.unit        = unit
        self._raw        = 0.0
        self.fault       = False

    def read(self) -> SensorReading:
        if self.fault:
            return SensorReading(value=0.0, unit=self.unit, valid=False)
        noise = random.gauss(0, self.noise_sigma) if self.noise_sigma else 0.0
        value = max(self.min_val, min(self.max_val, self._raw + noise))
        return SensorReading(value=round(value, 3), unit=self.unit)

    def set(self, value: float):
        self._raw = value


# ─── Fuel System ──────────────────────────────────────────────────────────────

class FuelSystem:
    """Port fuel injection model with stoichiometric (lambda) control."""

    STOICH_AFR    = 14.7   # Stoichiometric air-fuel ratio (gasoline)
    BASE_PRESSURE = 3.5    # bar

    def __init__(self):
        self.fuel_trim_short  = 0.0   # %  (-25 to +25)
        self.fuel_trim_long   = 0.0   # %  (-25 to +25)
        self.lambda_target    = 1.0   # λ target
        self.injector_pw      = 0.0   # ms  injector pulse width
        self.rail_pressure    = self.BASE_PRESSURE
        self.fuel_level       = 60.0  # litres
        self._consumption_rate = 0.0  # L/hr

    def calculate_injection(self, load: float, rpm: float,
                             coolant_temp: float, intake_temp: float) -> float:
        """Return injector pulse width in ms."""
        # Base pulse width from volumetric efficiency lookup
        ve = self._volumetric_efficiency(rpm, load)
        safe_rpm = max(rpm, 1.0)
        base_pw = (load * ve * 10.0) / safe_rpm  # simplified

        # Temperature corrections
        temp_corr = 1.0 + max(0, (80 - coolant_temp) / 80) * 0.15
        intake_corr = 1.0 - (intake_temp - 25) / 500

        # Trim corrections
        trim = 1.0 + (self.fuel_trim_short + self.fuel_trim_long) / 100.0

        self.injector_pw = base_pw * temp_corr * intake_corr * trim
        self.injector_pw = max(0.0, min(30.0, self.injector_pw))

        # Estimate consumption (L/hr)
        self._consumption_rate = (rpm * self.injector_pw * 4) / 3_600_000 * 0.72
        self.fuel_level = max(0.0, self.fuel_level - self._consumption_rate / 3600)

        return self.injector_pw

    def _volumetric_efficiency(self, rpm: float, load: float) -> float:
        """Simplified VE map."""
        peak_rpm = 4500
        ve_base  = 0.85
        ve = ve_base * math.sin(math.pi * rpm / (peak_rpm * 2)) * load
        return max(0.1, min(1.0, ve))

    def closed_loop_correction(self, lambda_actual: float):
        """PI correction toward lambda target."""
        error = self.lambda_target - lambda_actual
        self.fuel_trim_short = max(-25.0, min(25.0,
                                               self.fuel_trim_short + error * 5))
        if abs(self.fuel_trim_short) > 10:
            self.fuel_trim_long = max(-25.0, min(25.0,
                                                  self.fuel_trim_long + error * 0.5))

    @property
    def consumption_rate(self) -> float:
        return self._consumption_rate


# ─── Ignition System ──────────────────────────────────────────────────────────

class IgnitionSystem:
    """Spark timing control with knock detection."""

    BASE_ADVANCE_TABLE = {  # RPM: base advance (degrees BTDC)
        800:  8,  1200: 12, 1600: 16, 2000: 18,
        2500: 22, 3000: 26, 3500: 28, 4000: 30,
        4500: 32, 5000: 30, 5500: 28, 6000: 25,
    }

    def __init__(self):
        self.timing_advance  = 10.0   # degrees BTDC
        self.knock_retard    = 0.0    # degrees retard due to knock
        self.knock_count     = 0
        self.dwell_time      = 3.5    # ms coil dwell
        self.misfire_count   = 0

    def calculate_timing(self, rpm: float, load: float,
                          coolant_temp: float, knock_signal: float) -> float:
        """Compute final ignition advance."""
        base = self._interpolate_advance(rpm)

        # Load correction (less advance at high load)
        load_corr = (1.0 - load) * 5.0

        # Temperature correction (retard when cold)
        temp_corr = max(-8.0, (coolant_temp - 80) / 10)

        # Knock retard (fast retard, slow recover)
        if knock_signal > 0.7:
            self.knock_retard = min(10.0, self.knock_retard + 3.0)
            self.knock_count += 1
        else:
            self.knock_retard = max(0.0, self.knock_retard - 0.25)

        self.timing_advance = base + load_corr + temp_corr - self.knock_retard
        self.timing_advance = max(-5.0, min(45.0, self.timing_advance))
        return self.timing_advance

    def _interpolate_advance(self, rpm: float) -> float:
        keys = sorted(self.BASE_ADVANCE_TABLE.keys())
        for i, k in enumerate(keys[:-1]):
            if k <= rpm <= keys[i + 1]:
                t = (rpm - k) / (keys[i + 1] - k)
                return (self.BASE_ADVANCE_TABLE[k] * (1 - t) +
                        self.BASE_ADVANCE_TABLE[keys[i + 1]] * t)
        if rpm < keys[0]:
            return self.BASE_ADVANCE_TABLE[keys[0]]
        return self.BASE_ADVANCE_TABLE[keys[-1]]


# ─── Throttle & Airflow ───────────────────────────────────────────────────────

class ThrottleBody:
    """Electronic throttle control (ETC/drive-by-wire)."""

    def __init__(self):
        self.pedal_position    = 0.0   # 0–100 %
        self.throttle_position = 0.0   # 0–100 %
        self.target_position   = 0.0
        self.maf               = 0.0   # g/s mass air flow
        self.map_pressure      = 101.3 # kPa manifold absolute pressure
        self._velocity         = 0.0

    def update(self, dt: float, rpm: float, idle_target: float = 800):
        """Servo model with idle speed control."""
        # Idle air correction
        if self.pedal_position < 2.0:
            idle_corr = (idle_target - rpm) * 0.01
            self.target_position = max(3.0, min(12.0, 5.0 + idle_corr))
        else:
            self.target_position = self.pedal_position

        # 2nd-order throttle servo response
        error = self.target_position - self.throttle_position
        self._velocity += error * 50 * dt
        self._velocity *= 0.85
        self.throttle_position += self._velocity * dt
        self.throttle_position = max(0.0, min(100.0, self.throttle_position))

        # MAF from throttle + rpm (simplified)
        alpha = math.radians(self.throttle_position * 0.9)
        self.maf = 2.4 * math.sin(alpha) * (rpm / 1000) ** 0.5

        # MAP estimation
        self.map_pressure = 101.3 - (90 - self.throttle_position) * 0.7
        self.map_pressure = max(20.0, min(101.3, self.map_pressure))

    @property
    def engine_load(self) -> float:
        return self.throttle_position / 100.0


# ─── Thermal Management ───────────────────────────────────────────────────────

class ThermalSystem:
    """Coolant temperature model with thermostat and fan control."""

    THERMOSTAT_OPEN  = 88.0   # °C
    FAN_ON_TEMP      = 95.0   # °C
    FAN_OFF_TEMP     = 90.0   # °C
    OVERHEAT_TEMP    = 120.0  # °C

    def __init__(self):
        self.coolant_temp   = 20.0   # °C
        self.oil_temp       = 20.0   # °C
        self.intake_temp    = 25.0   # °C
        self.fan_active     = False
        self.thermostat_open = False

    def update(self, dt: float, load: float, rpm: float, ambient: float = 25.0):
        # Heat generated by combustion
        heat_in = load * (rpm / 6000) * 0.4

        # Thermostat logic
        self.thermostat_open = self.coolant_temp >= self.THERMOSTAT_OPEN

        # Cooling efficiency
        road_speed_factor = min(1.0, load * 1.2)
        fan_factor = 1.0 if self.fan_active else 0.3
        cooling = ((self.coolant_temp - ambient) / 100) * (road_speed_factor + fan_factor * 0.5)

        if self.thermostat_open:
            self.coolant_temp += (heat_in - cooling) * dt * 2.5
        else:
            self.coolant_temp += heat_in * dt * 1.0

        self.coolant_temp = max(ambient, self.coolant_temp)

        # Fan switching hysteresis
        if self.coolant_temp >= self.FAN_ON_TEMP:
            self.fan_active = True
        elif self.coolant_temp <= self.FAN_OFF_TEMP:
            self.fan_active = False

        # Oil temp lags coolant
        self.oil_temp += (self.coolant_temp - self.oil_temp) * 0.02 * dt

        # Intake temp
        self.intake_temp = ambient + (self.coolant_temp - ambient) * 0.1

    @property
    def is_overheat(self) -> bool:
        return self.coolant_temp >= self.OVERHEAT_TEMP


# ─── Engine Model ─────────────────────────────────────────────────────────────

class Engine:
    """4-cylinder DOHC engine physics model."""

    IDLE_RPM      = 800
    REDLINE       = 6500
    MAX_TORQUE    = 250   # Nm
    DISPLACEMENT  = 1998  # cc

    def __init__(self):
        self.rpm         = 0.0
        self.torque      = 0.0
        self.power_kw    = 0.0
        self.lambda_val  = 1.0
        self._running    = False
        self._inertia    = 0.15   # kg·m²

    def update(self, dt: float, load: float, ignition_advance: float,
               injector_pw: float, state: EngineState):
        if state not in (EngineState.IDLE, EngineState.RUNNING):
            if state == EngineState.CRANKING:
                self.rpm += (400 - self.rpm) * dt * 3 + random.gauss(0, 10)
                self.rpm = max(0.0, self.rpm)
            else:
                self.rpm = max(0.0, self.rpm - 500 * dt)
            self.torque = 0.0
            self.power_kw = 0.0
            return

        # Torque production
        target_torque = self._torque_map(self.rpm, load, ignition_advance)
        self.torque += (target_torque - self.torque) * min(1.0, dt * 15)

        # Target RPM from load
        idle   = self.IDLE_RPM
        target_rpm = idle + load * (self.REDLINE - idle)

        # RPM dynamics with inertia
        rpm_error    = target_rpm - self.rpm
        rpm_accel    = rpm_error * 4.0                        # governor gain
        self.rpm    += rpm_accel * dt + random.gauss(0, 3)
        self.rpm     = max(0.0, min(self.REDLINE + 200, self.rpm))

        # Power
        self.power_kw = (self.torque * self.rpm) / 9549.3

        # Lambda (simplified)
        self.lambda_val = 1.0 + random.gauss(0, 0.01) + (load - 0.5) * 0.02

    def _torque_map(self, rpm: float, load: float, advance: float) -> float:
        """Simplified torque surface."""
        rpm_factor = math.sin(math.pi * rpm / self.REDLINE) if rpm > 0 else 0
        adv_factor = 1.0 + (advance - 20) / 100
        return self.MAX_TORQUE * rpm_factor * load * adv_factor


# ─── Transmission ─────────────────────────────────────────────────────────────

class Transmission:
    """6-speed automatic with torque converter."""

    RATIOS = {1: 3.87, 2: 2.25, 3: 1.55, 4: 1.16, 5: 0.86, 6: 0.69}
    FINAL_DRIVE = 3.94

    def __init__(self):
        self.gear         = 1
        self.gear_pos     = GearPosition.PARK
        self.slip_ratio   = 0.0
        self.shift_in_progress = False
        self._shift_timer = 0.0

    def update(self, dt: float, rpm: float, load: float, speed_kmh: float):
        if self.gear_pos != GearPosition.DRIVE:
            return

        if self.shift_in_progress:
            self._shift_timer -= dt
            if self._shift_timer <= 0:
                self.shift_in_progress = False
            return

        # Upshift / downshift logic
        upshift_rpm   = 3000 + load * 2500
        downshift_rpm = 1500 + load * 800

        if rpm > upshift_rpm and self.gear < 6:
            self._shift(self.gear + 1)
        elif rpm < downshift_rpm and self.gear > 1:
            self._shift(self.gear - 1)

    def _shift(self, new_gear: int):
        self.gear = new_gear
        self.shift_in_progress = True
        self._shift_timer = 0.35

    def wheel_torque(self, engine_torque: float) -> float:
        ratio = self.RATIOS.get(self.gear, 1.0)
        return engine_torque * ratio * self.FINAL_DRIVE * 0.92


# ─── Diagnostic System (OBD-II) ───────────────────────────────────────────────

class DiagnosticSystem:
    """OBD-II fault monitoring and DTC management."""

    def __init__(self):
        self.active_faults: dict[FaultCode, int] = {}   # code → trip count
        self.freeze_frame: Optional[dict]          = None
        self.mil_on: bool                          = False  # MIL = Check Engine
        self._monitor_history: deque               = deque(maxlen=100)

    def run_monitors(self, state: EngineState, thermal: ThermalSystem,
                     fuel: FuelSystem, engine: Engine):
        """Run continuous OBD-II monitors."""
        # Coolant sensor monitor
        if not (-40 <= thermal.coolant_temp <= 130):
            self._set_fault(FaultCode.P0115)

        # Fuel trim monitor
        total_trim = abs(fuel.fuel_trim_short) + abs(fuel.fuel_trim_long)
        if total_trim > 40:
            self._set_fault(FaultCode.P0170)

        # Misfire monitor
        if engine.rpm > 0:
            rpm_variation = abs(engine.rpm % 10 - 5)
            if rpm_variation > 4.8:
                self._set_fault(FaultCode.P0300)

        # Lambda monitor
        if state == EngineState.RUNNING:
            if not (0.7 <= engine.lambda_val <= 1.3):
                self._set_fault(FaultCode.P0130)

        self.mil_on = len(self.active_faults) > 0

    def _set_fault(self, code: FaultCode):
        self.active_faults[code] = self.active_faults.get(code, 0) + 1
        if self.freeze_frame is None:
            self.freeze_frame = {"code": code, "time": time.time()}

    def clear_faults(self):
        self.active_faults.clear()
        self.freeze_frame = None
        self.mil_on = False

    def get_pid(self, pid: str) -> Optional[float]:
        """OBD-II PID query interface."""
        # Would be populated from ECU references in a real impl
        return None


# ─── ECU Main Controller ──────────────────────────────────────────────────────

class ECU:
    """
    Engine Control Unit — main coordinator.
    Integrates all subsystems and runs the control loop.
    """

    def __init__(self):
        # Subsystems
        self.fuel        = FuelSystem()
        self.ignition    = IgnitionSystem()
        self.throttle    = ThrottleBody()
        self.thermal     = ThermalSystem()
        self.engine      = Engine()
        self.transmission = Transmission()
        self.diagnostics = DiagnosticSystem()

        # Sensors
        self.sensors = {
            "rpm":          Sensor("RPM",          0, 8000, 5.0,  "rpm"),
            "coolant_temp": Sensor("Coolant Temp",-40, 130, 0.5,  "°C"),
            "intake_temp":  Sensor("Intake Temp",  -40, 80,  0.3,  "°C"),
            "throttle_pos": Sensor("Throttle Pos",  0, 100, 0.2,  "%"),
            "maf":          Sensor("MAF",           0, 200, 0.1,  "g/s"),
            "map_kpa":      Sensor("MAP",          20, 110, 0.5,  "kPa"),
            "battery_v":    Sensor("Battery",      10,  16, 0.05, "V"),
            "oil_press":    Sensor("Oil Press",     0,   7, 0.05, "bar"),
            "vehicle_speed":Sensor("Speed",         0, 250, 0.1,  "km/h"),
            "fuel_level":   Sensor("Fuel Level",    0,  80, 0.0,  "L"),
        }

        # State
        self.state       = EngineState.OFF
        self.uptime      = 0.0
        self.speed_kmh   = 0.0
        self._key_on     = False

        # Control loop
        self._lock       = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running    = False
        self._dt         = 0.02   # 50 Hz control loop

    # ── Public API ────────────────────────────────────────────────────────────

    def key_on(self):
        self._key_on = True
        if self.state == EngineState.OFF:
            self.state = EngineState.CRANKING
            print("[ECU] Cranking engine...")

    def key_off(self):
        self._key_on = False
        self.state = EngineState.OFF
        print("[ECU] Engine off.")

    def set_throttle(self, position: float):
        """Set accelerator pedal position 0–100%."""
        with self._lock:
            self.throttle.pedal_position = max(0.0, min(100.0, position))

    def set_gear(self, pos: GearPosition):
        with self._lock:
            self.transmission.gear_pos = pos

    def start(self):
        """Start the ECU control loop in background thread."""
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[ECU] Control loop started at 50 Hz")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[ECU] Control loop stopped")

    def snapshot(self) -> dict:
        """Return current ECU state snapshot."""
        with self._lock:
            return {
                "state":         self.state.value,
                "uptime_s":      round(self.uptime, 1),
                "rpm":           round(self.engine.rpm, 0),
                "torque_nm":     round(self.engine.torque, 1),
                "power_kw":      round(self.engine.power_kw, 1),
                "throttle_pct":  round(self.throttle.throttle_position, 1),
                "load_pct":      round(self.throttle.engine_load * 100, 1),
                "coolant_c":     round(self.thermal.coolant_temp, 1),
                "oil_c":         round(self.thermal.oil_temp, 1),
                "intake_c":      round(self.thermal.intake_temp, 1),
                "fan":           self.thermal.fan_active,
                "maf_gs":        round(self.throttle.maf, 2),
                "map_kpa":       round(self.throttle.map_pressure, 1),
                "lambda":        round(self.engine.lambda_val, 3),
                "timing_deg":    round(self.ignition.timing_advance, 1),
                "knock_retard":  round(self.ignition.knock_retard, 1),
                "inj_pw_ms":     round(self.fuel.injector_pw, 3),
                "strim_pct":     round(self.fuel.fuel_trim_short, 2),
                "ltrim_pct":     round(self.fuel.fuel_trim_long, 2),
                "fuel_L":        round(self.fuel.fuel_level, 2),
                "consumption_lh": round(self.fuel.consumption_rate, 2),
                "gear":          self.transmission.gear,
                "gear_pos":      self.transmission.gear_pos.value,
                "speed_kmh":     round(self.speed_kmh, 1),
                "mil":           self.diagnostics.mil_on,
                "faults":        [c.name for c in self.diagnostics.active_faults],
            }

    # ── Control Loop ─────────────────────────────────────────────────────────

    def _loop(self):
        last = time.time()
        crank_time = 0.0

        while self._running:
            now = time.time()
            dt  = now - last
            last = now

            with self._lock:
                self._tick(dt)
                if self.state in (EngineState.IDLE, EngineState.RUNNING):
                    self.uptime += dt

            time.sleep(max(0, self._dt - (time.time() - now)))

    def _tick(self, dt: float):
        """Single control cycle."""
        load = self.throttle.engine_load

        # ── State machine ──
        if self.state == EngineState.CRANKING:
            if self.engine.rpm > 350:
                self.state = EngineState.IDLE
                print("[ECU] Engine started — idle mode")
        elif self.state == EngineState.IDLE:
            if load > 0.05:
                self.state = EngineState.RUNNING
        elif self.state == EngineState.RUNNING:
            if load < 0.03 and self.engine.rpm < self.engine.IDLE_RPM + 100:
                self.state = EngineState.IDLE
        if self.thermal.is_overheat and self.state not in (EngineState.OFF, EngineState.FAULT):
            self.state = EngineState.OVERHEAT
            print("[ECU] OVERHEAT detected!")

        # ── Subsystem updates ──
        self.throttle.update(dt, self.engine.rpm)
        timing   = self.ignition.calculate_timing(
            self.engine.rpm, load, self.thermal.coolant_temp,
            knock_signal=random.uniform(0, 0.3))
        inj_pw   = self.fuel.calculate_injection(
            load, self.engine.rpm, self.thermal.coolant_temp, self.thermal.intake_temp)
        self.engine.update(dt, load, timing, inj_pw, self.state)
        self.fuel.closed_loop_correction(self.engine.lambda_val)
        self.thermal.update(dt, load, self.engine.rpm)
        self.transmission.update(dt, self.engine.rpm, load, self.speed_kmh)

        # Speed estimation from wheel torque
        wheel_t = self.transmission.wheel_torque(self.engine.torque)
        accel   = (wheel_t / 1200) - (self.speed_kmh / 250) * 3  # drag
        self.speed_kmh = max(0.0, self.speed_kmh + accel * dt * 3.6)

        # ── Sensors ──
        self.sensors["rpm"].set(self.engine.rpm)
        self.sensors["coolant_temp"].set(self.thermal.coolant_temp)
        self.sensors["intake_temp"].set(self.thermal.intake_temp)
        self.sensors["throttle_pos"].set(self.throttle.throttle_position)
        self.sensors["maf"].set(self.throttle.maf)
        self.sensors["map_kpa"].set(self.throttle.map_pressure)
        self.sensors["battery_v"].set(random.gauss(14.2, 0.05))
        self.sensors["oil_press"].set(1.5 + self.engine.rpm / 3000)
        self.sensors["vehicle_speed"].set(self.speed_kmh)
        self.sensors["fuel_level"].set(self.fuel.fuel_level)

        # ── OBD monitors ──
        self.diagnostics.run_monitors(
            self.state, self.thermal, self.fuel, self.engine)


# ─── CLI Demo ─────────────────────────────────────────────────────────────────

def run_demo():
    print("=" * 60)
    print("  CAR ECU SIMULATION — Python")
    print("=" * 60)

    ecu = ECU()
    ecu.start()

    # ── Scenario ──────────────────────────────────────────────────
    print("\n[DEMO] Key ON — starting engine")
    ecu.key_on()
    time.sleep(2.5)

    print("[DEMO] Setting gear to DRIVE")
    ecu.set_gear(GearPosition.DRIVE)
    time.sleep(0.5)

    for throttle, label, duration in [
        (15,  "light cruise",    3.0),
        (40,  "moderate pull",   4.0),
        (80,  "hard acceleration", 5.0),
        (20,  "easing off",      3.0),
        (5,   "near idle",       2.0),
        (0,   "coasting",        2.0),
    ]:
        print(f"\n[DEMO] Throttle → {throttle}% ({label})")
        ecu.set_throttle(throttle)
        for _ in range(int(duration * 2)):
            time.sleep(0.5)
            snap = ecu.snapshot()
            print(
                f"  RPM:{snap['rpm']:>6.0f}  "
                f"TQ:{snap['torque_nm']:>5.1f}Nm  "
                f"Speed:{snap['speed_kmh']:>5.1f}km/h  "
                f"Gear:{snap['gear']}  "
                f"Coolant:{snap['coolant_c']:>5.1f}°C  "
                f"λ:{snap['lambda']:.3f}  "
                f"Timing:{snap['timing_deg']:>5.1f}°"
            )

    print("\n[DEMO] Key OFF")
    ecu.key_off()
    time.sleep(1)

    ecu.stop()

    # Final report
    snap = ecu.snapshot()
    print("\n" + "=" * 60)
    print("  FINAL ECU REPORT")
    print("=" * 60)
    for k, v in snap.items():
        print(f"  {k:<20} {v}")
    print("=" * 60)

    if snap["faults"]:
        print(f"\n  ⚠  Active DTCs: {', '.join(snap['faults'])}")
    else:
        print("\n  ✓  No fault codes stored")


if __name__ == "__main__":
    run_demo()
