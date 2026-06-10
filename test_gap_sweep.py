"""
Phase 2/4 — Gap 容忍度扫描 (fNIRS 时序测试)
==============================================
目的: 找到 fNIRS 设备能可靠检测的最小字节间隔。
背景: alignment marker 使用 300ms gap → fNIRS 只收到一个信号。
      可能需要 500ms, 1000ms, 甚至 2000ms。

测试矩阵:
  - 序列: START (0x01→0x02→0x04→0x02→0x01)
  - gap 值: 100, 200, 300, 500, 750, 1000, 1500, 2000 ms
  - 脉宽: 5ms (默认), 可选 10ms, 50ms

用法:
  python test_gap_sweep.py                  # 交互式
  python test_gap_sweep.py --auto           # 自动扫描全部 gap
  python test_gap_sweep.py --gap 1000       # 仅测试指定 gap
  python test_gap_sweep.py --port COM4
"""
import serial
import time
import sys

PORT = "COM4"
BAUDRATE = 9600

START_SEQ = [0x01, 0x02, 0x04, 0x02, 0x01]
END_SEQ   = [0x04, 0x02, 0x01, 0x02, 0x04]

# 默认扫描的 gap 值 (ms)
DEFAULT_GAPS_MS = [100, 200, 300, 500, 750, 1000, 1500, 2000]
# 脉宽选项 (ms)
PULSE_WIDTHS_MS = [5, 10, 50]

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


def send_sequence_with_params(ser, seq, gap_s, pulse_width_s, label):
    """发送序列，使用指定的 gap 和脉宽"""
    fnirs_view = " → ".join(FNIRS_MAP.get(b, f"?{b}") for b in seq)
    synamp_view = " → ".join(str(SYNAMP_MAP.get(b, "?")) for b in seq)
    hex_view = " → ".join(f"0x{b:02X}" for b in seq)
    
    print(f"\n{'─'*55}")
    print(f"  {label}")
    print(f"  Bytes:    {hex_view}")
    print(f"  fNIRS:    {fnirs_view}")
    print(f"  Synamp:   {synamp_view}")
    print(f"  Gap:      {int(gap_s*1000)}ms  |  Pulse: {int(pulse_width_s*1000)}ms")
    print(f"  Duration: ~{len(seq)*gap_s:.1f}s")
    print(f"{'─'*55}")
    
    for i, b in enumerate(seq):
        ser.write(b'\x00')
        time.sleep(0.003)
        ser.write(bytes([b]))
        ser.flush()
        time.sleep(pulse_width_s)
        ser.write(b'\x00')
        ser.flush()
        print(f"    [{i+1}/{len(seq)}] sent 0x{b:02X}")
        if i < len(seq) - 1:
            time.sleep(gap_s)
    time.sleep(1.0)


def run_gap_sweep(ser, seq, seq_label, gaps_ms, pulse_ms=5, auto=False):
    """对每个 gap 值发送序列，记录设备响应"""
    print(f"\n{'='*60}")
    print(f"  Gap 扫描: {seq_label}")
    print(f"  脉宽: {pulse_ms}ms")
    print(f"  测试 gap: {gaps_ms} ms")
    print(f"{'='*60}")
    
    results = []
    for gap_ms in gaps_ms:
        gap_s = gap_ms / 1000.0
        pulse_s = pulse_ms / 1000.0
        send_sequence_with_params(
            ser, seq, gap_s, pulse_s,
            f"{seq_label} @ gap={gap_ms}ms pulse={pulse_ms}ms"
        )
        
        if auto:
            print(f"  [WAIT] 自动等待 3s...")
            time.sleep(3.0)
        else:
            resp = input(f"  >>> fNIRS 收到几个信号? Synamp 收到几个? (回车继续, s=跳过剩余): ").strip()
            if resp.lower() == 's':
                print(f"  [SKIP] 跳过剩余测试")
                break
            results.append((gap_ms, resp))
    
    if results:
        print(f"\n{'='*60}")
        print(f"  扫描结果汇总 ({seq_label}):")
        print(f"  {'Gap (ms)':<12} {'设备反馈'}")
        print(f"  {'─'*12} {'─'*30}")
        for gap_ms, resp in results:
            print(f"  {gap_ms:<12} {resp}")
        print(f"{'='*60}")
    
    return results


def run_full_matrix(ser):
    """运行完整矩阵: START+END × 全部gaps × 全部脉宽"""
    print(f"\n{'='*60}")
    print(f"  完整矩阵扫描")
    print(f"  序列: START + END")
    print(f"  Gaps: {DEFAULT_GAPS_MS} ms")
    print(f"  Pulse widths: {PULSE_WIDTHS_MS} ms")
    print(f"  总测试数: 2 × {len(DEFAULT_GAPS_MS)} × {len(PULSE_WIDTHS_MS)} = {2*len(DEFAULT_GAPS_MS)*len(PULSE_WIDTHS_MS)}")
    print(f"{'='*60}")
    
    confirm = input("  确认开始? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  已取消")
        return
    
    for pulse_ms in PULSE_WIDTHS_MS:
        for seq, label in [(START_SEQ, "START"), (END_SEQ, "END")]:
            print(f"\n{'#'*60}")
            print(f"# {label} 序列 | Pulse={pulse_ms}ms")
            print(f"{'#'*60}")
            for gap_ms in DEFAULT_GAPS_MS:
                gap_s = gap_ms / 1000.0
                pulse_s = pulse_ms / 1000.0
                send_sequence_with_params(
                    ser, seq, gap_s, pulse_s,
                    f"{label} gap={gap_ms}ms pulse={pulse_ms}ms"
                )
                input(f"  >>> 记录设备显示后按 Enter...")


def interactive_menu(ser):
    while True:
        print(f"\n{'='*55}")
        print(f"  Gap 容忍度扫描 | {PORT} @ {BAUDRATE}")
        print(f"{'='*55}")
        print("  [1] START 序列 — 指定一个 gap 值")
        print("  [2] START 序列 — 扫描全部 gap (300~2000ms)")
        print("  [3] END   序列 — 扫描全部 gap")
        print("  [4] 完整矩阵扫描 (START+END × gaps × pulse widths)")
        print("  [5] 单字节测试 (0x04), 确认设备基本响应")
        print("  [Q] 退出")
        print(f"{'='*55}")
        cmd = input("> ").strip().lower()
        
        if cmd == '1':
            try:
                gap_ms = int(input("  Gap (ms): ").strip())
            except ValueError:
                print("  [?] 无效值")
                continue
            gap_s = gap_ms / 1000.0
            send_sequence_with_params(ser, START_SEQ, gap_s, 0.005, f"START @ {gap_ms}ms")
        elif cmd == '2':
            run_gap_sweep(ser, START_SEQ, "START", DEFAULT_GAPS_MS)
        elif cmd == '3':
            run_gap_sweep(ser, END_SEQ, "END", DEFAULT_GAPS_MS)
        elif cmd == '4':
            run_full_matrix(ser)
        elif cmd == '5':
            print("  发送 0x04...")
            ser.write(b'\x00')
            time.sleep(0.003)
            ser.write(b'\x04')
            ser.flush()
            time.sleep(0.005)
            ser.write(b'\x00')
            print("  [OK] 已发送 0x04 (fNIRS->CH2, Synamp->208)")
        elif cmd in ('q', 'quit', 'exit'):
            break
        else:
            print("  [?] 未知命令")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gap 容忍度扫描")
    parser.add_argument("--port", "-p", default=PORT)
    parser.add_argument("--auto", "-a", action="store_true", help="自动模式 (3s间隔)")
    parser.add_argument("--gap", "-g", type=int, help="仅测试指定 gap (ms)")
    parser.add_argument("--pulse", type=int, default=5, help="脉宽 (ms, 默认5)")
    parser.add_argument("--seq", default="START", choices=["START", "END"], help="测试序列")
    args = parser.parse_args()
    
    print(f"[CONNECT] {args.port} @ {BAUDRATE} ...")
    ser = open_port(args.port)
    print(f"[OK] 已连接: {args.port}\n")
    
    try:
        if args.gap:
            seq = START_SEQ if args.seq == "START" else END_SEQ
            gap_s = args.gap / 1000.0
            pulse_s = args.pulse / 1000.0
            send_sequence_with_params(ser, seq, gap_s, pulse_s,
                                       f"{args.seq} @ gap={args.gap}ms pulse={args.pulse}ms")
        elif args.auto:
            seq = START_SEQ if args.seq == "START" else END_SEQ
            run_gap_sweep(ser, seq, args.seq, DEFAULT_GAPS_MS, args.pulse, auto=True)
        else:
            interactive_menu(ser)
    finally:
        ser.close()
        print("\n[DISCONNECT] 端口已关闭。")


if __name__ == "__main__":
    main()
