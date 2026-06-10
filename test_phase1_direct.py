"""
Phase 1 — 直接连接测试 (绕过中转设备)
======================================
连接方式: PC → 设备 (Synamp / fNIRS 单独直连)
目的: 排除中转设备嫌疑，确认设备本身对单字节和序列的响应。

用法:
  python test_phase1_direct.py              # 交互式选择测试
  python test_phase1_direct.py --port COM4  # 指定端口
  python test_phase1_direct.py --all        # 运行全部测试
  python test_phase1_direct.py --single     # 仅单字节测试
  python test_phase1_direct.py --sequence   # 仅序列测试
"""
import serial
import time
import sys

# ── Config ──────────────────────────────────────────────────
PORT = "COM4"
BAUDRATE = 9600
PULSE_WIDTH = 0.005   # 5ms (与 _lastrun.py 一致)
RESET_GAP = 0.05      # 50ms (原 3ms 太短, Synamp 来不及复位)
SEQ_GAP = 0.3         # 300ms (与 _lastrun.py 一致)

START_SEQ = [0x01, 0x02, 0x04, 0x02, 0x01]
END_SEQ   = [0x04, 0x02, 0x01, 0x02, 0x04]

SYNAMP_MAP = {
    0x00: 192, 0x01: 160, 0x02: 224, 0x03: 144,
    0x04: 208, 0x05: 176, 0x06: 240, 0x07: 136,
    0x08: 200, 0x09: 168, 0x0A: 232, 0x0B: 136,
    0x0C: 216, 0x0D: 184, 0x0E: 248, 0x0F: 152,
}
FNIRS_MAP = {0x01: "CH0", 0x02: "CH1", 0x04: "CH2"}


def open_port(port=PORT):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = BAUDRATE
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 0.5
    ser.dtr = False
    ser.rts = False
    ser.open()
    return ser


def send_byte(ser, b, label=""):
    """发送单个字节 (0x00→value→0x00 协议, 与 _lastrun.py 一致)"""
    fnirs = FNIRS_MAP.get(b, f"?{b}")
    synamp = SYNAMP_MAP.get(b, "?")
    print(f"  >>> SEND: 0x{b:02X}  |  fNIRS→{fnirs}  |  Synamp→{synamp}  {label}")
    ser.write(b'\x00')
    time.sleep(RESET_GAP)
    ser.write(bytes([b]))
    ser.flush()
    time.sleep(PULSE_WIDTH)
    ser.write(b'\x00')
    ser.flush()


def send_sequence(ser, seq, label):
    """发送5字节序列 (0x00→b→0x00, 间隔 SEQ_GAP)"""
    fnirs_view = " → ".join(FNIRS_MAP.get(b, f"?{b}") for b in seq)
    synamp_view = " → ".join(str(SYNAMP_MAP.get(b, "?")) for b in seq)
    hex_view = " → ".join(f"0x{b:02X}" for b in seq)
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"  Bytes:   {hex_view}")
    print(f"  fNIRS:   {fnirs_view}")
    print(f"  Synamp:  {synamp_view}")
    print(f"  Gap:     {int(SEQ_GAP*1000)}ms  |  总时长: ~{len(seq)*SEQ_GAP:.1f}s")
    print(f"{'='*55}")

    for i, b in enumerate(seq):
        send_byte(ser, b, f"[{i+1}/{len(seq)}]")
        if i < len(seq) - 1:
            time.sleep(SEQ_GAP)
    time.sleep(1.0)


def test_single_bytes(ser):
    """测试 1.1-1.3: 单字节 0x01, 0x02, 0x04"""
    print("\n" + "=" * 55)
    print("  PHASE 1.1-1.3: 单字节测试")
    print("  发送 0x01, 0x02, 0x04，间隔 2s")
    print("=" * 55)
    for b in [0x01, 0x02, 0x04]:
        send_byte(ser, b)
        print(f"  [WAIT] 观察设备显示 (2s)...")
        time.sleep(2.0)
    print("\n  [OK] 单字节测试完成。请检查设备显示。\n")


def test_sequence(ser, seq, label):
    """测试 1.4-1.5: START/END 序列"""
    send_sequence(ser, seq, label)
    print(f"  [OK] {label} 完成。请检查设备显示。\n")


def test_gap_variants(ser):
    """测试不同 gap 下的序列 (Phase 2 预测试)"""
    global SEQ_GAP
    original_gap = SEQ_GAP
    gaps = [0.3, 0.5, 1.0, 2.0]
    
    print("\n" + "=" * 55)
    print("  GAP 扫描: 测试 fNIRS 对间隔的容忍度")
    print("=" * 55)
    
    for gap in gaps:
        SEQ_GAP = gap
        send_sequence(ser, START_SEQ, f"START @ {int(gap*1000)}ms gap")
        input(f"  >>> 检查设备后按 Enter 继续...")
    
    SEQ_GAP = original_gap


def interactive_menu(ser):
    while True:
        print(f"\n{'='*55}")
        print(f"  Phase 1 — 直接连接测试 | {PORT} @ {BAUDRATE}")
        print(f"{'='*55}")
        print("  [1] 单字节 0x01 (fNIRS:CH0 / Synamp:160)")
        print("  [2] 单字节 0x02 (fNIRS:CH1 / Synamp:224)")
        print("  [3] 单字节 0x04 (fNIRS:CH2 / Synamp:208)")
        print("  [4] START 序列 (0x01→0x02→0x04→0x02→0x01)")
        print("  [5] END   序列 (0x04→0x02→0x01→0x02→0x04)")
        print("  [A] 全部单字节 + 序列")
        print("  [G] Gap 扫描 (300/500/1000/2000ms)")
        print("  [Q] 退出")
        print(f"{'='*55}")
        cmd = input("> ").strip().lower()
        
        if cmd == '1': send_byte(ser, 0x01)
        elif cmd == '2': send_byte(ser, 0x02)
        elif cmd == '3': send_byte(ser, 0x04)
        elif cmd == '4': send_sequence(ser, START_SEQ, "START")
        elif cmd == '5': send_sequence(ser, END_SEQ, "END")
        elif cmd == 'a':
            test_single_bytes(ser)
            input(">>> 检查单字节结果后按 Enter...")
            test_sequence(ser, START_SEQ, "START")
        elif cmd == 'g': test_gap_variants(ser)
        elif cmd in ('q', 'quit', 'exit'): break
        else: print("  [?] 未知命令")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 1 直接连接测试")
    parser.add_argument("--port", "-p", default=PORT)
    parser.add_argument("--all", "-a", action="store_true", help="运行全部: 单字节 + 序列 + gap")
    parser.add_argument("--single", "-s", action="store_true", help="仅单字节")
    parser.add_argument("--sequence", "-q", action="store_true", help="仅序列")
    parser.add_argument("--gap", "-g", action="store_true", help="仅 gap 扫描")
    args = parser.parse_args()
    
    port = args.port
    print(f"[CONNECT] {port} @ {BAUDRATE} ...")
    ser = open_port(port)
    print(f"[OK] 已连接: {port}\n")
    print("[WARN] 请确认: PC 直接连接设备 (不经过中转设备)")
    
    try:
        if args.all:
            test_single_bytes(ser)
            input(">>> 检查单字节结果后按 Enter...")
            test_sequence(ser, START_SEQ, "START 序列")
            input(">>> 检查 START 序列结果后按 Enter...")
            test_sequence(ser, END_SEQ, "END 序列")
            input(">>> 检查 END 序列结果后按 Enter...")
            test_gap_variants(ser)
        elif args.single:
            test_single_bytes(ser)
        elif args.sequence:
            test_sequence(ser, START_SEQ, "START 序列")
            test_sequence(ser, END_SEQ, "END 序列")
        elif args.gap:
            test_gap_variants(ser)
        else:
            interactive_menu(ser)
    finally:
        ser.close()
        print("\n[DISCONNECT] 端口已关闭。")


if __name__ == "__main__":
    main()
