"""
Block Alignment Marker — 5-byte Coded Sequence
===============================================
START: 0x01→0x02→0x04→0x02→0x01  (fNIRS: CH0→CH1→CH2→CH1→CH0)
END:   0x04→0x02→0x01→0x02→0x04  (fNIRS: CH2→CH1→CH0→CH1→CH2)

Each byte: 300ms gap, 0x00 reset between. Total ~1.5s per marker.
Robust to 1-2 dropped events — partial pattern still recognizable.

Usage:
  python alignment_marker_test.py START   # send START only
  python alignment_marker_test.py END     # send END only
  python alignment_marker_test.py BOTH    # send both (default)
"""
import serial
import time
import sys

PORT = "COM4"
BAUDRATE = 9600
PULSE_GAP = 0.3   # 300ms between pulses (fNIRS ~10Hz safe)

# Encoding sequences — symmetric, adjacent values always differ
START_SEQ = [0x01, 0x02, 0x04, 0x02, 0x01]
END_SEQ   = [0x04, 0x02, 0x01, 0x02, 0x04]

# Device output reference
SYNAMP_MAP = {
    0x00: 192, 0x01: 160, 0x02: 224, 0x03: 144,
    0x04: 208, 0x05: 176, 0x06: 240, 0x07: 136,
    0x08: 200, 0x09: 168, 0x0A: 232, 0x0B: 136,
    0x0C: 216, 0x0D: 184, 0x0E: 248, 0x0F: 152,
}
FNIRS_MAP = {0x01: "CH0", 0x02: "CH1", 0x04: "CH2"}


def open_port():
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
    return ser


def send_sequence(ser, seq, label):
    """Send a coded byte sequence with 0x00 resets between."""
    fnirs_view = " → ".join(FNIRS_MAP.get(b, f"?{b}") for b in seq)
    synamp_view = " → ".join(str(SYNAMP_MAP.get(b, "?")) for b in seq)
    hex_view = " → ".join(f"0x{b:02X}" for b in seq)

    print(f"  {label}")
    print(f"    Bytes:   {hex_view}")
    print(f"    fNIRS:   {fnirs_view}")
    print(f"    Synamp:  {synamp_view}")

    for i, b in enumerate(seq):
        ser.write(b'\x00')
        time.sleep(0.003)
        ser.write(bytes([b]))
        ser.flush()
        time.sleep(0.005)
        ser.write(b'\x00')
        ser.flush()
        print(f"    [{i+1}/{len(seq)}] sent 0x{b:02X}")
        if i < len(seq) - 1:
            time.sleep(PULSE_GAP)
    time.sleep(1.0)
    print()


def main():
    ser = open_port()
    mark = sys.argv[1].upper() if len(sys.argv) > 1 else "BOTH"

    print(f"[OK] {PORT} @ {BAUDRATE} | DTR=False RTS=False")
    print(f"Pulse gap: {int(PULSE_GAP*1000)}ms\n")

    if mark in ("START", "BOTH"):
        print("=" * 55)
        send_sequence(ser, START_SEQ, ">>> START MARKER")

    if mark in ("END", "BOTH"):
        print("=" * 55)
        send_sequence(ser, END_SEQ, ">>> END MARKER")

    ser.close()
    print("Done. Check device displays.")


if __name__ == "__main__":
    main()
