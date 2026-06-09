"""
Synamp High-Nibble Test
========================
Tests whether the device distinguishes high nibble values.
Sends all 16 high-nibble variants for each low-nibble value,
grouped for easy comparison.
"""
import serial
import sys
import time
from datetime import datetime
from pathlib import Path

PORT = "COM4"
BAUDRATE = 115200
GAP = 0.5  # seconds between sends
OUTPUT_DIR = Path(__file__).parent / "mapping_results"
OUTPUT_DIR.mkdir(exist_ok=True)


def open_serial():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.5)
        print(f"[OK] {PORT} @ {BAUDRATE}")
        return ser
    except Exception as e:
        print(f"[X] Cannot open {PORT}: {e}")
        return None


def main():
    ser = open_serial()
    if ser is None:
        return

    results = []
    total = 0

    print("\n" + "=" * 60)
    print("  High-Nibble Test: 0x00–0xFF grouped by low nibble")
    print("  For each byte, type what the device shows.")
    print("  Type 'q' to quit & save, 's' to skip, Enter to repeat last")
    print("=" * 60 + "\n")

    last_input = ""

    try:
        for low in range(16):
            print(f"\n{'─' * 50}")
            print(f"  Group: low nibble = 0x{low:1X} ({low:04b})")
            print(f"  Testing high nibble variants: 0x{low:02X} through 0x{(low | 0xF0):02X}")
            print(f"{'─' * 50}")

            for high in range(16):
                byte_val = (high << 4) | low
                sent_hex = f"0x{byte_val:02X}"
                sent_bin = f"{byte_val:08b}"
                high_nib = f"{high:X} ({high:04b})"
                low_nib = f"{low:X} ({low:04b})"

                # Reset
                ser.write(b'\x00')
                time.sleep(0.2)
                # Send
                ser.write(bytes([byte_val]))

                total += 1
                print(f"  [{total:3d}] {sent_hex} bin={sent_bin}  hi={high_nib}  lo={low_nib}")
                print(f"       Device → ", end="", flush=True)

                raw = input().strip()

                if raw.lower() == 'q':
                    print("\nQuitting. Saving...")
                    _save(results, OUTPUT_DIR)
                    ser.close()
                    return
                elif raw.lower() == 's':
                    results.append((byte_val, sent_hex, sent_bin, "SKIPPED"))
                    continue
                elif raw == '':
                    raw = last_input
                    print(f"       (repeated: {raw})")

                last_input = raw
                results.append((byte_val, sent_hex, sent_bin, raw))

    except KeyboardInterrupt:
        print("\nInterrupted. Saving...")

    ser.close()
    _save(results, OUTPUT_DIR)


def _save(results, output_dir):
    import csv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"high_nibble_test_{ts}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_dec", "sent_hex", "sent_bin", "device_received"])
        for row in results:
            writer.writerow(row)

    print(f"\n[OK] {len(results)} entries saved to: {csv_path}")

    # Group by low nibble and compare
    groups = {}
    for byte_val, sent_hex, sent_bin, recv in results:
        low = byte_val & 0x0F
        groups.setdefault(low, []).append(recv)

    print(f"\nSummary by low nibble:")
    for low in sorted(groups.keys()):
        vals = groups[low]
        unique = sorted(set(v for v in vals if v != "SKIPPED"))
        if len(unique) == 1:
            print(f"  0x{low:1X}: all → {unique[0]}")
        else:
            print(f"  0x{low:1X}: {len(unique)} unique values → {unique}")


if __name__ == "__main__":
    main()
