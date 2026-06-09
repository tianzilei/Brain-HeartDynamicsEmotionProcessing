"""
COM Port Signal Test Tool
Supports: string, bytes (hex/escaped), integer, float, custom binary, repeated signals,
          transition-pair encoding for 3-bit channel devices

Interactive mode:  python serial_signal_test.py
CLI mode:          python serial_signal_test.py --string "hello\\r\\n"
                   python serial_signal_test.py --hex "FF 00 0A"
                   python serial_signal_test.py --integer 12345 --int-fmt uint32
                   python serial_signal_test.py --float 3.14 --float-fmt float32
                   python serial_signal_test.py --repeated 5 --string "ping"
                   python serial_signal_test.py --encoded "0,3,7,2"
                   python serial_signal_test.py --monitor
                   python serial_signal_test.py --list
                   python serial_signal_test.py --read
"""

import serial
import serial.tools.list_ports
import struct
import time
import sys
import argparse


# ── Config ──────────────────────────────────────────────────
CONFIG = {
    "port": None,
    "baudrate": 115200,
    "bytesize": serial.EIGHTBITS,
    "parity": serial.PARITY_NONE,
    "stopbits": serial.STOPBITS_ONE,
    "timeout": 1.0,
    "encoding": "utf-8",
}


# ── Port Management ────────────────────────────────────────

def list_com_ports():
    """List all available COM ports."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("[!] No COM ports detected.")
        return []
    print("Available COM ports:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device}  -  {p.description}")
    return [p.device for p in ports]


def auto_select_port():
    """Auto-detect the only COM port, or let user pick."""
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if len(ports) == 1:
        print(f"Auto-selected: {ports[0]}")
        return ports[0]
    if not ports:
        print("[!] No COM ports detected.")
        user = input("Enter port name manually (e.g. COM3): ").strip()
        return user if user else None
    list_com_ports()
    while True:
        choice = input(f"\nSelect port [0-{len(ports)-1}] or type name: ").strip()
        if not choice:
            return ports[0]
        if choice.isdigit() and 0 <= int(choice) < len(ports):
            return ports[int(choice)]
        return choice


def open_serial(port=None):
    """Open serial connection."""
    if port is None:
        port = auto_select_port()
    if not port:
        print("[X] No port specified. Exiting.")
        sys.exit(1)
    CONFIG["port"] = port
    try:
        ser = serial.Serial(
            port=CONFIG["port"],
            baudrate=CONFIG["baudrate"],
            bytesize=CONFIG["bytesize"],
            parity=CONFIG["parity"],
            stopbits=CONFIG["stopbits"],
            timeout=CONFIG["timeout"],
        )
        print(f"[OK] Connected: {CONFIG['port']} @ {CONFIG['baudrate']} baud")
        return ser
    except serial.SerialException as e:
        print(f"[X] Cannot open {CONFIG['port']}: {e}")
        sys.exit(1)


def try_read(ser, label="Received"):
    """Try to read echo data from serial buffer."""
    time.sleep(0.05)
    raw = ser.read(ser.in_waiting or 1024)
    if raw:
        print(f"  <-- {label}: {raw!r}")
        try:
            decoded = raw.decode("utf-8", errors="replace")
            if decoded != str(raw)[2:-1]:  # skip if same as repr
                print(f"      (UTF-8): {decoded}")
        except Exception:
            pass
    return raw


# ── Send Functions ──────────────────────────────────────────

def send_string(ser, text=None, ending="\r\n"):
    """Send a UTF-8 string."""
    if text is None:
        text = input("Enter string to send: ")
        if not text:
            return
        end = input("Line ending (default \\r\\n, 'none' for none): ").strip()
        if end == "none":
            ending = ""
        elif end:
            ending = end.encode("utf-8").decode("unicode_escape")
    full = text + ending
    ser.write(full.encode(CONFIG["encoding"]))
    print(f"[OK] Sent: {full!r}  ({len(full.encode(CONFIG['encoding']))} bytes)")
    try_read(ser)


def send_bytes_hex(ser, hex_str=None):
    """Send raw hex bytes (e.g., 'FF 00 0A')."""
    if hex_str is None:
        hex_str = input("Enter hex (e.g. FF 00 0A 1B): ").strip()
    try:
        cleaned = hex_str.replace("0x", "").replace(",", " ").replace(";", " ")
        data = bytes.fromhex(cleaned)
        ser.write(data)
        print(f"[OK] Sent {len(data)} bytes: {data.hex(' ').upper()}")
        try_read(ser)
    except ValueError:
        print("[X] Invalid hex string")


def send_bytes_escaped(ser, raw=None):
    """Send escaped bytes (\\r \\n \\x00 etc)."""
    if raw is None:
        raw = input("Enter escaped string (e.g. Hello\\r\\n or \\x00\\x01): ")
    try:
        data = raw.encode("utf-8").decode("unicode_escape").encode("latin-1")
        ser.write(data)
        print(f"[OK] Sent {len(data)} bytes: {data!r}")
        try_read(ser)
    except Exception as e:
        print(f"[X] Parse error: {e}")


def send_integer(ser, value=None, fmt=None):
    """Send an integer with specified encoding."""
    fmt_map = {
        "uint8":   ("<B",  "uint8 LE",  1, 0, 255),
        "int8":    ("<b",  "int8 LE",   1, -128, 127),
        "uint16":  ("<H",  "uint16 LE", 2, 0, 65535),
        "uint16be":(">H",  "uint16 BE", 2, 0, 65535),
        "uint32":  ("<I",  "uint32 LE", 4, 0, 4294967295),
        "uint32be":(">I",  "uint32 BE", 4, 0, 4294967295),
        "int32":   ("<i",  "int32 LE",  4, -2147483648, 2147483647),
        "int32be": (">i",  "int32 BE",  4, -2147483648, 2147483647),
        "uint64":  ("<Q",  "uint64 LE", 8, 0, 18446744073709551615),
        "int64":   ("<q",  "int64 LE",  8, -9223372036854775808, 9223372036854775807),
        "ascii":   (None,  "ASCII text", None, None, None),
    }

    if value is None:
        raw = input("Enter integer: ").strip()
        try:
            value = int(raw, 0)
        except ValueError:
            print("[X] Not a valid integer")
            return

    if fmt is None:
        print(f"\nValue: {value}  (0x{value & 0xFFFFFFFFFFFFFFFF:016X})")
        fmts = list(fmt_map.items())
        for i, (k, v) in enumerate(fmts):
            print(f"  [{i}] {k}  ({v[1]})")
        choice = input("Select encoding [0]: ").strip() or "0"
        if choice.isdigit() and 0 <= int(choice) < len(fmts):
            fmt = fmts[int(choice)][0]
        else:
            print("[X] Invalid choice")
            return

    if fmt not in fmt_map:
        print(f"[X] Unknown format: {fmt}")
        return

    pack_fmt, desc, size, lo, hi = fmt_map[fmt]

    if pack_fmt is None:
        data = str(value).encode("ascii")
    else:
        try:
            data = struct.pack(pack_fmt, value)
        except struct.error as e:
            print(f"[X] Value out of range: {e}")
            return

    ser.write(data)
    print(f"[OK] Sent ({desc}): {value}  ->  {len(data)} bytes: {data.hex(' ').upper()}")
    try_read(ser)


def send_float(ser, value=None, fmt=None):
    """Send a floating point number."""
    fmt_map = {
        "float32":   ("<f", "float32 LE", 4),
        "float32be": (">f", "float32 BE", 4),
        "float64":   ("<d", "float64 LE", 8),
        "float64be": (">d", "float64 BE", 8),
        "ascii":     (None, "ASCII text", None),
    }

    if value is None:
        raw = input("Enter float: ").strip()
        try:
            value = float(raw)
        except ValueError:
            print("[X] Not a valid number")
            return

    if fmt is None:
        print(f"Value: {value}")
        fmts = list(fmt_map.items())
        for i, (k, v) in enumerate(fmts):
            print(f"  [{i}] {k}  ({v[1]})")
        choice = input("Select encoding [0]: ").strip() or "0"
        if choice.isdigit() and 0 <= int(choice) < len(fmts):
            fmt = fmts[int(choice)][0]
        else:
            print("[X] Invalid choice")
            return

    if fmt not in fmt_map:
        print(f"[X] Unknown format: {fmt}")
        return

    pack_fmt, desc, size = fmt_map[fmt]

    if pack_fmt is None:
        data = str(value).encode("ascii")
    else:
        data = struct.pack(pack_fmt, value)

    ser.write(data)
    print(f"[OK] Sent ({desc}): {value}  ->  {len(data)} bytes: {data.hex(' ').upper()}")
    try_read(ser)


def send_repeated(ser, count=10, interval=0, data_func=None, data_args=None):
    """Repeatedly send a signal."""
    if data_func is None:
        print("\nSelect signal type:")
        print("  [1] String")
        print("  [2] Hex bytes")
        print("  [3] Escaped bytes")
        print("  [4] Integer")
        t = input("Select [1]: ").strip() or "1"
        count = int(input("Repeat count: ").strip())
        interval = float(input("Interval (sec, default 0): ").strip() or "0")

        if t == "1":
            s = input("Enter string: ")
            data = s.encode(CONFIG["encoding"])
            label = s
        elif t == "2":
            hx = input("Enter hex: ").strip()
            data = bytes.fromhex(hx.replace("0x", "").replace(",", " "))
            label = data.hex(" ").upper()
        elif t == "3":
            es = input("Enter escaped: ")
            data = es.encode("utf-8").decode("unicode_escape").encode("latin-1")
            label = repr(data)
        elif t == "4":
            val = int(input("Enter integer: ").strip(), 0)
            f = input("Format [uint32]: ").strip() or "<I"
            data = struct.pack(f, val)
            label = str(val)
        else:
            return
    else:
        if data_args is None:
            data_args = {}
        data = data_func(**data_args)
        label = repr(data)

    print(f"\nSending {count} times, interval {interval}s...")
    for i in range(count):
        ser.write(data)
        print(f"  [{i+1}/{count}] {label}")
        if interval > 0:
            time.sleep(interval)
        try_read(ser)
    print("[OK] Done")


def send_continuous(ser, duration=5.0, interval=0.1, data_func=None, data_args=None):
    """Send a signal continuously for a given duration."""
    if data_func is None:
        print("\nSelect signal type:")
        print("  [h] Hex bytes")
        print("  [i] Integer")
        choice = input("Select: ").strip().lower()
        duration = float(input("Duration (sec): ").strip())
        interval = float(input("Interval (sec): ").strip())

        if choice == "h":
            hx = input("Enter hex: ").strip()
            data = bytes.fromhex(hx.replace("0x", "").replace(",", " "))
        elif choice == "i":
            val = int(input("Enter integer: ").strip(), 0)
            f = input("Format [<I]: ").strip() or "<I"
            data = struct.pack(f, val)
        else:
            return
    else:
        if data_args is None:
            data_args = {}
        data = data_func(**data_args)

    print(f"Sending continuously for {duration}s, every {interval}s...")
    count = int(duration / interval)
    for i in range(count):
        ser.write(data)
        if interval > 0:
            time.sleep(interval)
    print(f"[OK] Sent {count} times")


# ── Transition-Pair Encoding (3-bit channel: 1,2,4) ──────────
# Maps values 0-7 to single-pulse / transition-pair sequences
# The receiving device only detects single-bit values (1,2,4),
# so we encode multi-bit values as ordered channel transitions.

ENCODING_MAP = {
    0: [0x01],                  # single pulse on ch1
    1: [0x01, 0x02],            # ch1 -> ch2
    2: [0x01, 0x04],            # ch1 -> ch4
    3: [0x02, 0x01],            # ch2 -> ch1
    4: [0x02, 0x04],            # ch2 -> ch4
    5: [0x04, 0x01],            # ch4 -> ch1
    6: [0x04, 0x02],            # ch4 -> ch2
    7: [0x02],                  # single pulse on ch2
}

# Reverse: (channel_sequence_tuple) -> value
DECODING_MAP = {
    (1,): 0,
    (1, 2): 1,
    (1, 4): 2,
    (2, 1): 3,
    (2, 4): 4,
    (4, 1): 5,
    (4, 2): 6,
    (2,): 7,
}

DEFAULT_PAIR_GAP = 2.0    # seconds between bytes within a pair
DEFAULT_VAL_GAP  = 3.0    # seconds between encoded values


def send_encoded_value(ser, value, pair_gap=DEFAULT_PAIR_GAP, val_gap=DEFAULT_VAL_GAP):
    """Send a single value (0-7) using transition-pair encoding.
    
    Automatically prepends 0x00 to reset all channels before sending.
    """
    if value not in ENCODING_MAP:
        print(f"[X] Value {value} out of range (0-7)")
        return
    seq = ENCODING_MAP[value]
    # Reset all channels
    ser.write(b'\x00')
    time.sleep(0.3)
    # Send the sequence
    for i, b in enumerate(seq):
        ser.write(bytes([b]))
        if i < len(seq) - 1:
            time.sleep(pair_gap)
    # Post-value gap
    time.sleep(val_gap)


def send_encoded_sequence(ser, values, pair_gap=DEFAULT_PAIR_GAP, val_gap=DEFAULT_VAL_GAP):
    """Send a list of values (0-7) as encoded transitions."""
    for v in values:
        seq = ENCODING_MAP.get(v)
        if seq is None:
            print(f"[X] Skipping invalid value {v}")
            continue
        label = '->'.join(f'0x{b:02X}' for b in seq)
        print(f"  [{v}] -> {label}  ({len(seq)} event(s))", flush=True)
        ser.write(b'\x00')
        time.sleep(0.3)
        for i, b in enumerate(seq):
            ser.write(bytes([b]))
            if i < len(seq) - 1:
                time.sleep(pair_gap)
        time.sleep(val_gap)


def decode_event_stream(raw_values, timeout=DEFAULT_VAL_GAP - 0.5):
    """Decode a stream of received channel values (1,2,4) into original values.
    
    Uses a timeout to distinguish single-pulse values from pair-starts.
    This is a synchronous decoder - pass all received values with timestamps.
    
    For real-time monitoring, use monitor_encoded() instead.
    """
    if not raw_values:
        return []
    
    results = []
    i = 0
    while i < len(raw_values):
        v = raw_values[i]
        # Check if this could start a pair
        if i + 1 < len(raw_values):
            pair = (v, raw_values[i + 1])
            if pair in DECODING_MAP and len(DECODING_MAP[pair]) > 1:
                # It's a valid pair - check timing
                # (In offline decode, we assume pairs are consecutive)
                results.append(DECODING_MAP[pair])
                i += 2
                continue
        # Single value
        single = (v,)
        if single in DECODING_MAP:
            results.append(DECODING_MAP[single])
        else:
            results.append(f"?{v}")  # Unknown
        i += 1
    return results


def monitor_encoded(ser, timeout=10.0):
    """Monitor serial input and decode transition-pair encoded values in real-time.
    
    Press Ctrl+C to stop.
    """
    print(f"Monitoring {CONFIG['port']} for encoded signals...")
    print("Decoding single-bit channels (1,2,4) -> original values (0-7)")
    print(f"Pair timeout: {DEFAULT_PAIR_GAP + 0.5}s  |  Press Ctrl+C to stop\n")
    
    buffer = []  # (value, timestamp)
    pair_timeout = DEFAULT_PAIR_GAP + 0.5  # slightly > pair_gap

    try:
        while True:
            raw = ser.read(1)
            if raw:
                v = raw[0]
                now = time.time()
                # Only process recognized channel values
                if v in (1, 2, 4):
                    buffer.append((v, now))

            # Try to decode completed values from buffer
            while len(buffer) >= 1:
                v0, t0 = buffer[0]
                if len(buffer) >= 2:
                    v1, t1 = buffer[1]
                    pair = (v0, v1)
                    if pair in DECODING_MAP and len(DECODING_MAP[pair][1] if isinstance(DECODING_MAP[pair], tuple) else 0) > 0:
                        # Check if this is really a pair (short gap) or two singles
                        if t1 - t0 < pair_timeout:
                            decoded = DECODING_MAP[pair]
                            print(f"  -> {decoded}  (raw: {v0},{v1})")
                            buffer.pop(0)
                            buffer.pop(0)
                            continue
                
                # Check if first event has timed out (it's a single)
                if time.time() - t0 > pair_timeout:
                    single = (v0,)
                    if single in DECODING_MAP:
                        decoded = DECODING_MAP[single]
                        print(f"  -> {decoded}  (raw: {v0})")
                    buffer.pop(0)
                else:
                    break  # wait for more data

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


# ── CLI Mode ────────────────────────────────────────────────

def build_parser():
    """Build argument parser for CLI mode."""
    parser = argparse.ArgumentParser(
        description="COM Port Signal Test Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serial_signal_test.py --list
  python serial_signal_test.py --read
  python serial_signal_test.py --string "hello"
  python serial_signal_test.py --string "AT\\r\\n"
  python serial_signal_test.py --hex "FF 00 0A 1B"
  python serial_signal_test.py --escaped "Hello\\r\\n"
  python serial_signal_test.py --integer 12345 --int-fmt uint32
  python serial_signal_test.py --float 3.14 --float-fmt float32
  python serial_signal_test.py --repeated 10 --interval 0.5 --hex "FF"
  python serial_signal_test.py --continuous 5 --interval 0.1 --hex "AA"
  python serial_signal_test.py --port COM4 --baudrate 9600 --string "test"
  python serial_signal_test.py --encoded "0,3,7,2"
  python serial_signal_test.py --encoded 5 --port COM4
  python serial_signal_test.py --monitor
        """
    )

    parser.add_argument("--port", "-p", help="COM port name (e.g. COM3)")
    parser.add_argument("--baudrate", "-b", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--list", "-l", action="store_true", help="List available COM ports and exit")
    parser.add_argument("--read", "-r", action="store_true", help="Read and print serial buffer content")

    # Signal types (mutually exclusive for simple sends)
    parser.add_argument("--string", help="Send a UTF-8 string")
    parser.add_argument("--ending", default="\\r\\n", help="Line ending for --string (default: \\r\\n, 'none' for no ending)")
    parser.add_argument("--hex", help="Send raw hex bytes (e.g. 'FF 00 0A')")
    parser.add_argument("--escaped", help="Send escaped bytes (e.g. 'Hello\\r\\n')")
    parser.add_argument("--integer", type=lambda x: int(x, 0), help="Send an integer value")
    parser.add_argument("--int-fmt", default="uint32", help="Integer encoding: uint8, int8, uint16, uint16be, uint32, uint32be, int32, int32be, uint64, int64, ascii (default: uint32)")
    parser.add_argument("--float", type=float, dest="float_val", help="Send a floating point value")
    parser.add_argument("--float-fmt", default="float32", help="Float encoding: float32, float32be, float64, float64be, ascii (default: float32)")

    # Transition-pair encoded values (for 3-bit channel device)
    parser.add_argument("--encoded", help="Send value(s) via transition-pair encoding. Single: '5', Sequence: '0,3,7,2'")
    parser.add_argument("--pair-gap", type=float, default=DEFAULT_PAIR_GAP, help=f"Gap between bytes within a pair (default: {DEFAULT_PAIR_GAP}s)")
    parser.add_argument("--val-gap", type=float, default=DEFAULT_VAL_GAP, help=f"Gap between encoded values (default: {DEFAULT_VAL_GAP}s)")
    parser.add_argument("--monitor", action="store_true", help="Monitor serial and decode transition-pair encoded signals in real-time")

    # Repeated / continuous
    parser.add_argument("--repeated", type=int, help="Send signal N times")
    parser.add_argument("--continuous", type=float, help="Send signal continuously for N seconds")
    parser.add_argument("--interval", type=float, default=0.5, help="Interval between repeated/continuous sends (default: 0.5s)")

    return parser


def run_cli(args):
    """Execute CLI commands."""
    # --list only
    if args.list:
        list_com_ports()
        return

    # --read only (just open, read, close)
    if args.read:
        ser = open_serial(args.port)
        waiting = ser.in_waiting
        print(f"Buffer: {waiting} bytes waiting")
        if waiting > 0:
            data = ser.read(waiting)
            print(f"  RAW:  {data!r}")
            print(f"  HEX:  {data.hex(' ').upper()}")
            try:
                print(f"  UTF-8: {data.decode('utf-8', errors='replace')}")
            except Exception:
                pass
        ser.close()
        return

    # Apply baudrate
    CONFIG["baudrate"] = args.baudrate

    # Open port
    ser = open_serial(args.port)

    try:
        # --string
        if args.string is not None:
            ending = args.ending
            if ending == "none" or ending == "None":
                ending = ""
            elif ending:
                ending = ending.encode("utf-8").decode("unicode_escape")

            if args.repeated:
                full_data = (args.string + ending).encode(CONFIG["encoding"])
                for i in range(args.repeated):
                    ser.write(full_data)
                    print(f"  [{i+1}/{args.repeated}] {args.string!r}")
                    if args.interval > 0:
                        time.sleep(args.interval)
                    try_read(ser)
                print(f"[OK] Sent {args.repeated} times")
            elif args.continuous:
                full_data = (args.string + ending).encode(CONFIG["encoding"])
                count = int(args.continuous / args.interval)
                for i in range(count):
                    ser.write(full_data)
                    if args.interval > 0:
                        time.sleep(args.interval)
                print(f"[OK] Sent {count} times over {args.continuous}s")
            else:
                send_string(ser, text=args.string, ending=ending)

        # --hex
        elif args.hex is not None:
            if args.repeated:
                cleaned = args.hex.replace("0x", "").replace(",", " ")
                data = bytes.fromhex(cleaned)
                for i in range(args.repeated):
                    ser.write(data)
                    print(f"  [{i+1}/{args.repeated}] {data.hex(' ').upper()}")
                    if args.interval > 0:
                        time.sleep(args.interval)
                print(f"[OK] Sent {args.repeated} times")
            elif args.continuous:
                cleaned = args.hex.replace("0x", "").replace(",", " ")
                data = bytes.fromhex(cleaned)
                count = int(args.continuous / args.interval)
                for i in range(count):
                    ser.write(data)
                    if args.interval > 0:
                        time.sleep(args.interval)
                print(f"[OK] Sent {count} times over {args.continuous}s")
            else:
                send_bytes_hex(ser, hex_str=args.hex)

        # --escaped
        elif args.escaped is not None:
            send_bytes_escaped(ser, raw=args.escaped)

        # --integer
        elif args.integer is not None:
            if args.repeated:
                fmt_map = {
                    "uint8": "<B", "int8": "<b", "uint16": "<H", "uint16be": ">H",
                    "uint32": "<I", "uint32be": ">I", "int32": "<i", "int32be": ">i",
                    "uint64": "<Q", "int64": "<q",
                }
                pf = fmt_map.get(args.int_fmt, "<I")
                data = struct.pack(pf, args.integer)
                for i in range(args.repeated):
                    ser.write(data)
                    print(f"  [{i+1}/{args.repeated}] {args.integer} ({data.hex(' ').upper()})")
                    if args.interval > 0:
                        time.sleep(args.interval)
                print(f"[OK] Sent {args.repeated} times")
            else:
                send_integer(ser, value=args.integer, fmt=args.int_fmt)

        # --float
        elif args.float_val is not None:
            if args.repeated:
                fmt_map = {"float32": "<f", "float32be": ">f", "float64": "<d", "float64be": ">d"}
                pf = fmt_map.get(args.float_fmt, "<f")
                data = struct.pack(pf, args.float_val)
                for i in range(args.repeated):
                    ser.write(data)
                    print(f"  [{i+1}/{args.repeated}] {args.float_val} ({data.hex(' ').upper()})")
                    if args.interval > 0:
                        time.sleep(args.interval)
                print(f"[OK] Sent {args.repeated} times")
            else:
                send_float(ser, value=args.float_val, fmt=args.float_fmt)

        # --encoded (transition-pair encoding for 3-bit channel device)
        elif args.encoded is not None:
            # Parse comma-separated values: "5" or "0,3,7,2"
            parts = [p.strip() for p in args.encoded.split(",")]
            values = []
            for p in parts:
                try:
                    v = int(p, 0)
                    if 0 <= v <= 7:
                        values.append(v)
                    else:
                        print(f"[X] Value {v} out of 0-7 range, skipping")
                except ValueError:
                    print(f"[X] Invalid value '{p}', skipping")

            if values:
                print("Encoding table (value -> channel transitions):")
                for v in values:
                    seq = ENCODING_MAP[v]
                    label = ' -> '.join(f'0x{b:02X}' for b in seq)
                    ch_label = ' -> '.join(str(b) for b in seq)
                    print(f"  {v} : {label}  (device sees: {ch_label})")
                print()
                send_encoded_sequence(ser, values, pair_gap=args.pair_gap, val_gap=args.val_gap)
                print("[OK] Done")

        # --monitor (real-time decode)
        elif args.monitor:
            monitor_encoded(ser)
            return

        else:
            # No explicit signal specified - run interactive mode
            interactive_mode(ser)
            return

    finally:
        ser.close()
        print("Port closed.")


# ── Interactive Mode ────────────────────────────────────────

def interactive_mode(ser):
    """Run interactive menu loop."""
    while True:
        print(f"\n{'=' * 50}")
        print(f"  COM Signal Tester  |  {CONFIG['port']} @ {CONFIG['baudrate']}")
        print(f"{'=' * 50}")
        print("  [1] Send String (UTF-8)")
        print("  [2] Send Hex Bytes")
        print("  [3] Send Escaped Bytes (\\r\\n \\x00)")
        print("  [4] Send Integer (uint8/16/32/64, int8/32/64)")
        print("  [5] Send Float (float32/64)")
        print("  [6] Send Repeated Signal")
        print("  [7] Send Continuous Signal")
        print("  [E] Send Encoded Value (0-7 via transition pairs)")
        print("  [M] Monitor & Decode (real-time)")
        print(f"{'=' * 50}")
        print("  [P] Select / Switch Port")
        print("  [B] Change Baudrate")
        print("  [L] List Ports")
        print("  [R] Read Buffer")
        print("  [Q] Quit")
        print(f"{'=' * 50}")

        cmd = input("> ").strip().lower()

        if cmd in ("1", "s"):
            send_string(ser)
        elif cmd in ("2", "h"):
            send_bytes_hex(ser)
        elif cmd in ("3", "e"):
            send_bytes_escaped(ser)
        elif cmd in ("4", "i"):
            send_integer(ser)
        elif cmd in ("5", "f"):
            send_float(ser)
        elif cmd in ("6", "x"):
            send_repeated(ser)
        elif cmd in ("7", "c"):
            send_continuous(ser)
        elif cmd in ("e",):
            raw = input("Enter value(s) 0-7 (comma-separated, e.g. 5 or 0,3,7): ").strip()
            parts = [p.strip() for p in raw.split(",")]
            values = []
            for p in parts:
                try:
                    v = int(p, 0)
                    if 0 <= v <= 7:
                        values.append(v)
                except ValueError:
                    pass
            if values:
                send_encoded_sequence(ser, values)
        elif cmd in ("m",):
            monitor_encoded(ser)
        elif cmd in ("p",):
            CONFIG["port"] = auto_select_port()
            ser.close()
            ser = open_serial()
        elif cmd in ("b",):
            rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
            print("Baud rates:")
            for i, r in enumerate(rates):
                m = " <-- current" if r == CONFIG["baudrate"] else ""
                print(f"  [{i}] {r}{m}")
            c = input("Select: ").strip()
            if c.isdigit() and 0 <= int(c) < len(rates):
                ser.baudrate = rates[int(c)]
                CONFIG["baudrate"] = rates[int(c)]
                print(f"[OK] Baudrate = {CONFIG['baudrate']}")
        elif cmd in ("l",):
            list_com_ports()
        elif cmd in ("r",):
            waiting = ser.in_waiting
            print(f"Buffer: {waiting} bytes waiting")
            if waiting > 0:
                data = ser.read(waiting)
                print(f"  RAW:  {data!r}")
                print(f"  HEX:  {data.hex(' ').upper()}")
                try:
                    print(f"  UTF-8: {data.decode('utf-8', errors='replace')}")
                except Exception:
                    pass
        elif cmd in ("q", "quit", "exit"):
            break
        else:
            print("[X] Invalid command")


# ── Main ────────────────────────────────────────────────────

def main():
    # Check for CLI arguments
    if len(sys.argv) > 1:
        parser = build_parser()
        args = parser.parse_args()
        run_cli(args)
    else:
        # Interactive mode
        print("=" * 50)
        print("  COM Port Signal Test Tool")
        print("  Use --help for CLI usage")
        print("=" * 50)
        ser = open_serial()
        try:
            interactive_mode(ser)
        finally:
            ser.close()
            print("Port closed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting.")
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()
