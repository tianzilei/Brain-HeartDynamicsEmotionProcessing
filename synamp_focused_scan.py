"""
Synamp Focused Scan — compares high-nibble variants non-interactively.
Sends key test values with pauses so you can observe the device.
"""
import serial
import time
import sys

PORT = "COM4"
BAUDRATE = 9600
GAP = 1.2  # seconds between sends (slower for observation)


def main():
    try:
        ser = serial.Serial()
        ser.port = PORT
        ser.baudrate = BAUDRATE
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.timeout = 0.5
        ser.dtr = False
        ser.rts = False
        ser.open()
    except Exception as e:
        print(f"[X] Cannot open {PORT}: {e}")
        return

    baud = int(sys.argv[1]) if len(sys.argv) > 1 else BAUDRATE
    ser.baudrate = baud
    print(f"[OK] {PORT} @ {baud} baud\n")

    # ─── Test 1: Same low nibble, different high nibble ───
    print("=" * 55)
    print("TEST 1: Does high nibble matter?")
    print("  Low nibble fixed = 0x0, high nibble varies 0→F")
    print("  If device shows same value each time → high nibble ignored")
    print("=" * 55)
    for high in range(16):
        byte_val = (high << 4) | 0x0
        ser.write(b'\x00'); time.sleep(0.2)
        ser.write(bytes([byte_val]))
        marker = " <-- low nibble=0, check if different from above" if high == 1 else ""
        print(f"  SENT: 0x{byte_val:02X}  (hi=0x{high:X} lo=0){marker}")
        time.sleep(GAP)

    # ─── Test 2: Same as Test 1 but with low nibble = 0xF ───
    print(f"\n{'=' * 55}")
    print("TEST 2: High nibble with low nibble = 0xF")
    print("  If results same as TEST 1 → high nibble truly ignored")
    print("=" * 55)
    for high in range(16):
        byte_val = (high << 4) | 0xF
        ser.write(b'\x00'); time.sleep(0.2)
        ser.write(bytes([byte_val]))
        marker = " <-- same high nibble as above, different low nibble" if high <= 3 else ""
        print(f"  SENT: 0x{byte_val:02X}  (hi=0x{high:X} lo=F){marker}")
        time.sleep(GAP)

    # ─── Test 3: Key boundary values ───
    print(f"\n{'=' * 55}")
    print("TEST 3: Selected values across full 0x00–0xFF range")
    print("=" * 55)
    test_values = [
        0x00, 0x01, 0x07, 0x08, 0x0F,
        0x10, 0x11, 0x17, 0x18, 0x1F,
        0x7F, 0x80, 0xFF,
        0x55, 0xAA, 0x33, 0xCC,
    ]
    for v in test_values:
        ser.write(b'\x00'); time.sleep(0.2)
        ser.write(bytes([v]))
        print(f"  SENT: 0x{v:02X}  bin={v:08b}  dec={v:3d}")
        time.sleep(GAP)

    ser.close()
    print(f"\n[OK] Scan complete. What did you observe?")


if __name__ == "__main__":
    main()
