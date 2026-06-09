"""
Device Serial Receiver Test Tool
==================================
Purpose: Test and reverse-engineer a device's serial signal reception logic.
The device has its own display/log — you send signals from this PC,
then check the device's display to verify what it received.

Modes:
  Interactive: python device_serial_test.py
  Quick send:  python device_serial_test.py --hex "FF 00 0A"
  Batch probe: python device_serial_test.py --probe
  Monitor:     python device_serial_test.py --monitor
"""

import serial
import serial.tools.list_ports
import struct
import time
import sys
import argparse
from datetime import datetime
from pathlib import Path


# ── Config ──────────────────────────────────────────────────
COMMON_BAUDRATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

DEFAULT_CONFIG = {
    "port": "COM4",
    "baudrate": 115200,
    "bytesize": serial.EIGHTBITS,
    "parity": serial.PARITY_NONE,
    "stopbits": serial.STOPBITS_ONE,
    "timeout": 0.5,
}

LOG_DIR = Path(__file__).parent / "test_logs"
LOG_DIR.mkdir(exist_ok=True)


# ── Logging ─────────────────────────────────────────────────

def _log_path():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"device_test_{ts}.log"


_log_file = None


def log(msg="", also_print=True):
    """Log to file and optionally print to console."""
    global _log_file
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    if also_print:
        print(line)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()


# ── Port Management ─────────────────────────────────────────

def list_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        log("[!] No COM ports detected.")
        return []
    log("Available COM ports:")
    for i, p in enumerate(ports):
        log(f"  [{i}] {p.device}  —  {p.description}")
    return ports


def open_port(port="COM4", baudrate=115200, timeout=0.5):
    """Open serial connection. Returns (Serial, config_dict)."""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=DEFAULT_CONFIG["bytesize"],
            parity=DEFAULT_CONFIG["parity"],
            stopbits=DEFAULT_CONFIG["stopbits"],
            timeout=timeout,
        )
        cfg = {"port": port, "baudrate": baudrate}
        log(f"[OK] Connected: {port} @ {baudrate} baud, timeout={timeout}s")
        return ser, cfg
    except serial.SerialException as e:
        log(f"[X] Cannot open {port} @ {baudrate}: {e}")
        return None, None


def try_baudrates(port="COM4", rates=None):
    """Try multiple baudrates in sequence. Returns (Serial, rate) or (None, None)."""
    if rates is None:
        rates = COMMON_BAUDRATES
    log(f"\n=== Baudrate Scan on {port} ===")
    for rate in rates:
        ser, cfg = open_port(port, rate, timeout=0.3)
        if ser:
            # Quick send a test byte and check for echo/response
            ser.reset_input_buffer()
            ser.write(b'\x00')
            time.sleep(0.1)
            waiting = ser.in_waiting
            log(f"  {rate:>8} baud — buffer: {waiting} bytes after sending 0x00")
            return ser, cfg
    log("[X] Could not open port at any baudrate.")
    return None, None


# ── Send Functions ──────────────────────────────────────────

def send_and_read(ser, data, label="", read_after=True, read_delay=0.1):
    """Send data, optionally read response. Returns response bytes or empty."""
    ser.reset_input_buffer()
    count = ser.write(data)
    hex_str = data.hex(" ").upper() if data else "(empty)"
    desc = f"{label}  [{count} bytes]  HEX: {hex_str}"
    log(f"  >>> SENT: {desc}")

    if read_after:
        time.sleep(read_delay)
        waiting = ser.in_waiting
        if waiting > 0:
            raw = ser.read(waiting)
            log(f"  <<<  RECV ({waiting} bytes): {raw!r}")
            return raw
        else:
            log(f"  <<<  (no response)")
    return b""


def send_hex(ser, hex_str):
    """Send raw hex bytes. e.g. 'FF 00 0A'"""
    try:
        cleaned = hex_str.replace("0x", "").replace(",", " ").replace(";", " ")
        data = bytes.fromhex(cleaned)
        send_and_read(ser, data, f"HEX '{hex_str}'")
    except ValueError:
        log(f"[X] Invalid hex: {hex_str}")


def send_string(ser, text, ending="\r\n"):
    """Send UTF-8 string."""
    data = (text + ending).encode("utf-8")
    send_and_read(ser, data, f"STR '{text}'")


def send_integer(ser, value, fmt="<I"):
    """Send integer with struct packing. fmt: '<B' uint8, '<H' uint16, '<I' uint32, '<Q' uint64."""
    try:
        data = struct.pack(fmt, value)
        fmt_names = {"<B": "uint8", "<H": "uint16", "<I": "uint32", "<Q": "uint64"}
        name = fmt_names.get(fmt, fmt)
        send_and_read(ser, data, f"INT {value} ({name})")
    except struct.error as e:
        log(f"[X] Pack error: {e}")


def send_transition_encoded(ser, value, pair_gap=2.0):
    """Send a value (0-7) using 3-channel transition-pair encoding.
    Same encoding as fnirs.md documentation.
    0x00 to reset, then single-pulse or channel transition pair.
    """
    ENCODING = {
        0: [0x01],
        1: [0x01, 0x02],
        2: [0x01, 0x04],
        3: [0x02, 0x01],
        4: [0x02, 0x04],
        5: [0x04, 0x01],
        6: [0x04, 0x02],
        7: [0x02],
    }
    if value not in ENCODING:
        log(f"[X] Value {value} out of range (0-7)")
        return

    seq = ENCODING[value]
    label = " -> ".join(f"0x{b:02X}" for b in seq)
    log(f"  ENCODED [{value}] = {label} ({len(seq)} pulse(s))")

    # Reset
    ser.write(b'\x00')
    time.sleep(0.3)

    for i, b in enumerate(seq):
        ser.write(bytes([b]))
        if i < len(seq) - 1:
            time.sleep(pair_gap)


# ── Probe Mode ──────────────────────────────────────────────

def run_probe(ser, cfg):
    """Send a structured probe sequence of test signals.
    User should watch the device display/log after each group,
    then press Enter to continue to the next group.
    """
    log("\n" + "=" * 60)
    log("  DEVICE PROBE MODE")
    log("  Watch the device display after each group.")
    log("  Press Enter to continue to the next test group.")
    log("=" * 60)

    groups = [
        ("Single Bytes (0x00 – 0x0F)", [
            ("0x00 (all off)",  b'\x00'),
            ("0x01 (ch0 only)", b'\x01'),
            ("0x02 (ch1 only)", b'\x02'),
            ("0x03 (ch0+ch1)",  b'\x03'),
            ("0x04 (ch2 only)", b'\x04'),
            ("0x07 (ch0+ch1+ch2)", b'\x07'),
            ("0x08 (ch3)",      b'\x08'),
            ("0x0F (all 4 ch)",  b'\x0F'),
        ]),
        ("High Bit Bytes (0x10 – 0xFF)", [
            ("0x10 (ch4)", b'\x10'),
            ("0x20 (ch5)", b'\x20'),
            ("0x40 (ch6)", b'\x40'),
            ("0x80 (ch7)", b'\x80'),
            ("0xFF (all)", b'\xFF'),
        ]),
        ("Transition-Pair Encoded Values (0 – 7)", None),
        ("String Test (ASCII)", [
            ("Hello\\r\\n", b'Hello\r\n'),
            ("AT\\r\\n",    b'AT\r\n'),
        ]),
        ("Integer Formats", [
            ("uint8 = 255",  struct.pack("<B", 255)),
            ("uint16 = 1000", struct.pack("<H", 1000)),
            ("uint32 = 100000", struct.pack("<I", 100000)),
        ]),
    ]

    for group_name, items in groups:
        log(f"\n--- {group_name} ---")

        if group_name == "Transition-Pair Encoded Values (0 – 7)":
            for v in range(8):
                send_transition_encoded(ser, v)
                time.sleep(0.5)
            log("  (All 8 values sent. Check device display.)")
            input(f"\n>>> Check device, then press Enter to continue...")
            log(f"--- User continued ---")
            continue

        for label, data in items:
            ser.reset_input_buffer()
            ser.write(data)
            hex_str = data.hex(" ").upper()
            log(f"  >>> {label:30s}  [{len(data)}B] {hex_str}")
            # Quick read for echo
            time.sleep(0.1)
            waiting = ser.in_waiting
            if waiting > 0:
                raw = ser.read(waiting)
                log(f"  <<<  RECV: {raw!r}")
            time.sleep(0.2)

        input(f"\n>>> Check device display, then press Enter to continue...")
        log(f"--- User continued ---")

    log("\n[OK] Probe complete.")


# ── Monitor Mode ────────────────────────────────────────────

def run_monitor(ser, cfg):
    """Monitor serial input. Print everything received."""
    log(f"\n=== Monitoring {cfg['port']} @ {cfg['baudrate']} ===")
    log("  Press Ctrl+C to stop.\n")
    try:
        while True:
            raw = ser.read(1)
            if raw:
                b = raw[0]
                log(f"  <-- 0x{b:02X} ({b:3d})  {raw!r}")
    except KeyboardInterrupt:
        log("\nMonitoring stopped.")


# ── Interactive Mode ────────────────────────────────────────

def interactive(ser, cfg):
    """Interactive test loop."""
    while True:
        print(f"\n{'=' * 50}")
        print(f"  Device Tester  |  {cfg['port']} @ {cfg['baudrate']}")
        print(f"{'=' * 50}")
        print("  [H] Send Hex Bytes       (e.g. FF 00 0A)")
        print("  [S] Send String           (e.g. Hello)")
        print("  [I] Send Integer          (with struct packing)")
        print("  [E] Send Encoded (0-7)    (transition-pair)")
        print("  [P] Probe Mode            (structured batch test)")
        print("  [M] Monitor               (watch incoming data)")
        print(f"{'=' * 50}")
        print("  [B] Change Baudrate")
        print("  [L] List Ports")
        print("  [R] Read Buffer")
        print("  [Q] Quit")
        print(f"{'=' * 50}")

        cmd = input("> ").strip().lower()

        if cmd in ("h", "hex"):
            hx = input("  Hex (e.g. FF 00 0A): ").strip()
            if hx:
                send_hex(ser, hx)
            log(f"  >>> Check device display for received value.")

        elif cmd in ("s", "str"):
            text = input("  String: ")
            ending = input("  Ending (default \\r\\n, 'none' for none): ") or "\\r\\n"
            if ending.lower() == "none":
                ending = ""
            else:
                ending = ending.encode("utf-8").decode("unicode_escape")
            send_string(ser, text, ending)

        elif cmd in ("i", "int"):
            raw = input("  Integer value: ").strip()
            try:
                val = int(raw, 0)
            except ValueError:
                log("[X] Not a valid integer")
                continue
            print("  Formats: [0] uint8  [1] uint16  [2] uint32  [3] uint64")
            f_choice = input("  Format [2]: ").strip() or "2"
            fmts = {"0": "<B", "1": "<H", "2": "<I", "3": "<Q"}
            fmt = fmts.get(f_choice, "<I")
            send_integer(ser, val, fmt)

        elif cmd in ("e", "enc"):
            raw = input("  Value 0-7 (comma-separated for sequence): ").strip()
            parts = [p.strip() for p in raw.split(",")]
            for p in parts:
                try:
                    v = int(p, 0)
                    if 0 <= v <= 7:
                        send_transition_encoded(ser, v)
                        log(f"  >>> Check device display: should show channel transitions for value {v}")
                        input(f"  Press Enter for next value...")
                except ValueError:
                    log(f"[X] Invalid: {p}")

        elif cmd in ("p", "probe"):
            log("\nStarting structured probe...")
            log("Each group sends multiple signals. Check device after each group.")
            run_probe(ser, cfg)

        elif cmd in ("m", "mon"):
            run_monitor(ser, cfg)

        elif cmd in ("b", "baud"):
            print("Baud rates:")
            for i, r in enumerate(COMMON_BAUDRATES):
                marker = " <-- current" if r == cfg["baudrate"] else ""
                print(f"  [{i}] {r}{marker}")
            choice = input("Select: ").strip()
            if choice.isdigit() and 0 <= int(choice) < len(COMMON_BAUDRATES):
                new_rate = COMMON_BAUDRATES[int(choice)]
                ser.baudrate = new_rate
                cfg["baudrate"] = new_rate
                log(f"[OK] Baudrate = {new_rate}")

        elif cmd in ("l", "list"):
            list_ports()

        elif cmd in ("r", "read"):
            waiting = ser.in_waiting
            log(f"Buffer: {waiting} bytes waiting")
            if waiting > 0:
                data = ser.read(waiting)
                log(f"  RAW:  {data!r}")
                log(f"  HEX:  {data.hex(' ').upper()}")
                try:
                    decoded = data.decode("utf-8", errors="replace")
                    log(f"  UTF-8: {decoded}")
                except Exception:
                    pass

        elif cmd in ("q", "quit", "exit"):
            break

        else:
            log("[X] Unknown command.")


# ── CLI Mode ────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Device Serial Receiver Test Tool — Explore unknown device protocols.",
    )
    parser.add_argument("--port", "-p", default="COM4", help="COM port (default: COM4)")
    parser.add_argument("--baudrate", "-b", type=int, default=115200, help="Baud rate (default: 115200)")

    # Quick sends
    parser.add_argument("--hex", help="Send hex bytes (e.g. 'FF 00 0A')")
    parser.add_argument("--string", help="Send UTF-8 string")
    parser.add_argument("--ending", default="\\r\\n", help="Line ending for --string")
    parser.add_argument("--integer", type=lambda x: int(x, 0), help="Send integer value")
    parser.add_argument("--int-fmt", default="<I", help="Struct format: <B <H <I <Q (default: <I)")

    # Modes
    parser.add_argument("--probe", action="store_true", help="Run structured batch probe")
    parser.add_argument("--monitor", action="store_true", help="Monitor incoming serial data")
    parser.add_argument("--list", "-l", action="store_true", help="List COM ports and exit")
    parser.add_argument("--read", "-r", action="store_true", help="Read serial buffer and exit")

    return parser.parse_args()


def run_cli(args):
    if args.list:
        list_ports()
        return

    ser, cfg = open_port(args.port, args.baudrate)
    if ser is None:
        return

    try:
        if args.read:
            waiting = ser.in_waiting
            log(f"Buffer: {waiting} bytes waiting")
            if waiting > 0:
                data = ser.read(waiting)
                log(f"  RAW:  {data!r}")
                log(f"  HEX:  {data.hex(' ').upper()}")
            return

        if args.monitor:
            run_monitor(ser, cfg)
            return

        if args.probe:
            run_probe(ser, cfg)
            return

        if args.hex:
            send_hex(ser, args.hex)
        elif args.string:
            ending = args.ending.encode("utf-8").decode("unicode_escape") if args.ending else ""
            send_string(ser, args.string, ending)
        elif args.integer is not None:
            send_integer(ser, args.integer, args.int_fmt)
        else:
            interactive(ser, cfg)

    finally:
        ser.close()
        log("Port closed.")


# ── Main ────────────────────────────────────────────────────

def main():
    global _log_file
    log_path = _log_path()
    _log_file = open(log_path, "w", encoding="utf-8")
    log(f"Device Test Session — {datetime.now().isoformat()}", also_print=False)
    log(f"Log: {log_path}", also_print=True)
    log("", also_print=True)

    if len(sys.argv) > 1:
        run_cli(parse_args())
    else:
        # Interactive — auto-detect or use COM4
        ports = list(serial.tools.list_ports.comports())
        port = "COM4" if any("COM4" in p.device for p in ports) else None

        if port is None and ports:
            port = ports[0].device
            log(f"Auto-selected: {port}")
        elif port is None:
            log("[!] No COM ports found.")
            port = input("Enter port manually (e.g. COM3): ").strip()
            if not port:
                return

        rates = [115200, 9600, 57600, 38400, 19200, 230400]
        ser, cfg = try_baudrates(port, rates)
        if ser is None:
            log("[X] Cannot open port. Exiting.")
            return

        try:
            interactive(ser, cfg)
        finally:
            ser.close()
            log("Port closed.")
            _log_file.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting.")
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
