"""
Byte Mapping Tool — Reverse-engineer device byte reception
==========================================================
Sends 0x00 through 0xFF one at a time. After each send, you type
what the device's display/log shows. Results saved to CSV.
"""

import serial
import serial.tools.list_ports
import csv
import sys
import time
from datetime import datetime
from pathlib import Path


# ── Config ──────────────────────────────────────────────────
PORT = "COM4"
BAUDRATE = 9600

# Override via command line: python byte_mapping.py --scan --baud 115200
GAP_BETWEEN = 0.5       # seconds between sends (scan mode)
OUTPUT_DIR = Path(__file__).parent / "mapping_results"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Serial ──────────────────────────────────────────────────

def open_serial():
    try:
        ser = serial.Serial()
        ser.port = PORT
        ser.baudrate = BAUDRATE
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.timeout = 0.5
        ser.dtr = False   # 防止 STM32 复位
        ser.rts = False
        ser.open()
        print(f"[OK] {PORT} @ {BAUDRATE}")
        return ser
    except Exception as e:
        print(f"[X] Cannot open {PORT}: {e}")
        return None


# ── Main ────────────────────────────────────────────────────

def main():
    ser = open_serial()
    if ser is None:
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("Available ports:")
            for p in ports:
                print(f"  {p.device} — {p.description}")
        return

    results = []  # list of (sent_byte, sent_hex, sent_bin, received_input)
    start_all = datetime.now()

    print("\n" + "=" * 60)
    print("  Byte Mapping: 0x00 → 0xFF")
    print("  For each byte sent, type what the device shows.")
    print("  Commands: 's' = skip, 'r' = retry last, 'q' = quit & save")
    print("=" * 60 + "\n")

    try:
        for i in range(256):
            # Reset device state
            ser.write(b'\x00')
            time.sleep(0.3)

            # Send byte
            ser.write(bytes([i]))
            sent_hex = f"0x{i:02X}"
            sent_bin = f"{i:08b}"

            # Display
            elapsed = (datetime.now() - start_all).total_seconds()
            print(f"\n  [{i:3d}/255]  SENT: {sent_hex}  bin={sent_bin}  ({elapsed:.0f}s elapsed)")
            print(f"  Device shows: ", end="", flush=True)

            # Get user input
            raw = input().strip()

            if raw.lower() == 'q':
                print("\nQuitting early. Saving results so far...")
                break
            elif raw.lower() == 's':
                results.append((i, sent_hex, sent_bin, "SKIPPED"))
                continue
            elif raw.lower() == 'r':
                # Retry — decrement i so we redo this index
                if results:
                    results.pop()
                i -= 1
                continue

            results.append((i, sent_hex, sent_bin, raw))

    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving results so far...")

    finally:
        ser.close()
        print("Port closed.")

        # Save CSV
        if results:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = OUTPUT_DIR / f"byte_mapping_{ts}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["sent_dec", "sent_hex", "sent_bin", "device_received"])
                for row in results:
                    writer.writerow(row)

            print(f"\n[OK] {len(results)} entries saved to: {csv_path}")

            # Print summary of unique received values
            received_vals = [r[3] for r in results if r[3] != "SKIPPED"]
            unique = sorted(set(received_vals), key=lambda x: (len(x), x))
            print(f"\nUnique received values ({len(unique)}):")
            for v in unique:
                count = received_vals.count(v)
                # Find which sent values mapped to this
                mapped_from = [r[0] for r in results if r[3] == v]
                from_range = f"0x{mapped_from[0]:02X}–0x{mapped_from[-1]:02X}" if len(mapped_from) > 1 else f"0x{mapped_from[0]:02X}"
                print(f"  {v:20s}  ← {from_range}  ({count} bytes)")


def scan_mode(baudrate=None):
    """Non-interactive: send 0x00–0xFF rapidly, log everything."""
    global BAUDRATE
    if baudrate:
        BAUDRATE = baudrate
    ser = open_serial()
    if ser is None:
        return

    print(f"\nScan mode: sending 0x00 → 0xFF @ {BAUDRATE} baud, gap={GAP_BETWEEN}s each")
    print("Watch the device display. Press Ctrl+C to stop.\n")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = OUTPUT_DIR / f"scan_log_{ts}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_dec", "sent_hex", "sent_bin"])

        try:
            for i in range(256):
                ser.write(b'\x00')
                time.sleep(0.2)
                ser.write(bytes([i]))
                writer.writerow([i, f"0x{i:02X}", f"{i:08b}"])

                marker = ""
                if i == 0:   marker = " <-- all off"
                elif i <= 7: marker = " <-- low bits"
                elif i == 255: marker = " <-- all on"
                print(f"  [{i:3d}/255]  0x{i:02X}  bin={i:08b}{marker}")

                time.sleep(GAP_BETWEEN)

        except KeyboardInterrupt:
            print(f"\nStopped at {i}/255.")

    ser.close()
    print(f"\n[OK] Scan log saved to: {csv_path}")


if __name__ == "__main__":
    # Parse --scan and --baud args
    args = sys.argv[1:]
    if "--scan" in args:
        baud = None
        if "--baud" in args:
            idx = args.index("--baud")
            if idx + 1 < len(args):
                baud = int(args[idx + 1])
        scan_mode(baudrate=baud)
    else:
        main()
