"""
serialPort_2 行为复现测试 (raw pyserial, 绕过 PsychoPy)
========================================================
目的: 用 raw pyserial 精确复现 _lastrun.py 中 serialPort_2 的发送行为，
      排除 PsychoPy SerialDevice 层的嫌疑。

复现内容:
  - Start: 发送 0x04 (同 serialPort_2.sendMessage(bytes(chr(4), 'utf-8')))
  - Stop:  发送 0x02 (同 serialPort_2.sendMessage(bytes(bytearray([2]))))
  - 无 0x00 复位 (与 serialPort_2 一致 — alignment marker 有 0x00,
    但 Builder SerialOut 组件直接发送目标字节)

用法:
  python test_serialport2_replica.py              # 交互式
  python test_serialport2_replica.py --count 5    # 重复5次
  python test_serialport2_replica.py --port COM4
"""
import serial
import time
import sys

PORT = "COM4"
BAUDRATE = 9600

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


def simulate_serialport2_start(ser, method_label, start_byte):
    """
    模拟 serialPort_2 的 START 触发。
    
    _lastrun.py 实际代码:
      serialPort_2.sendMessage(bytes(chr(4), 'utf-8'))
    
    这等同于: ser.write(b'\x04')
    """
    data = bytes([start_byte])
    fnirs = FNIRS_MAP.get(start_byte, f"?")
    synamp = SYNAMP_MAP.get(start_byte, "?")
    
    print(f"  [{method_label}] START: 0x{start_byte:02X} → fNIRS:{fnirs} Synamp:{synamp}")
    print(f"       data = {data!r}  ({data.hex(' ').upper()})")
    ser.write(data)
    ser.flush()
    print(f"       ✅ 已发送 {len(data)} 字节")


def simulate_serialport2_stop(ser, method_label, stop_byte):
    """
    模拟 serialPort_2 的 STOP 触发。
    
    _lastrun.py 实际代码:
      serialPort_2.sendMessage(bytes(bytearray([2])))
    
    这等同于: ser.write(b'\x02')
    """
    data = bytes([stop_byte])
    fnirs = FNIRS_MAP.get(stop_byte, f"?")
    synamp = SYNAMP_MAP.get(stop_byte, "?")
    
    print(f"  [{method_label}] STOP:  0x{stop_byte:02X} → fNIRS:{fnirs} Synamp:{synamp}")
    print(f"       data = {data!r}  ({data.hex(' ').upper()})")
    ser.write(data)
    ser.flush()
    print(f"       ✅ 已发送 {len(data)} 字节")


def simulate_trial(ser, gap_between=1.0):
    """模拟一个完整的 trial: START → (等 gap) → STOP"""
    print(f"\n{'─'*50}")
    print(f"  模拟 1 个 Trial (serialPort_2: 4→2)")
    print(f"{'─'*50}")
    
    simulate_serialport2_start(ser, "A", 0x04)
    print(f"  ⏳ 等待 {gap_between}s (模拟刺激呈现)...")
    time.sleep(gap_between)
    simulate_serialport2_stop(ser, "A", 0x02)
    print(f"  ✅ Trial 完成\n")


def simulate_trial_with_reset(ser, gap_between=1.0):
    """模拟带 0x00 复位的 trial (像 alignment marker 那样)"""
    print(f"\n{'─'*50}")
    print(f"  模拟 1 个 Trial (带 0x00 复位: 0→4→0 ... 0→2→0)")
    print(f"{'─'*50}")
    
    # Start with reset protocol
    ser.write(b'\x00')
    time.sleep(0.003)
    ser.write(b'\x04')
    ser.flush()
    time.sleep(0.005)
    ser.write(b'\x00')
    ser.flush()
    print(f"  [B] START with reset: 0x00→0x04→0x00")
    
    time.sleep(gap_between)
    
    # Stop with reset protocol
    ser.write(b'\x00')
    time.sleep(0.003)
    ser.write(b'\x02')
    ser.flush()
    time.sleep(0.005)
    ser.write(b'\x00')
    ser.flush()
    print(f"  [B] STOP with reset:  0x00→0x02→0x00")
    print(f"  ✅ Trial (带复位) 完成\n")


def compare_methods(ser):
    """对比: 不带复位 vs 带复位, 观察设备差异"""
    print(f"\n{'='*60}")
    print(f"  A/B 对比: 不带复位 vs 带 0x00 复位")
    print(f"{'='*60}")
    print(f"  A = 直接发送目标字节 (同 serialPort_2)")
    print(f"  B = 0x00→目标→0x00 (同 alignment marker)")
    print(f"{'='*60}")
    
    for b in [0x04, 0x02]:
        fnirs = FNIRS_MAP.get(b, "?")
        synamp = SYNAMP_MAP.get(b, "?")
        print(f"\n  测试值: 0x{b:02X} (fNIRS:{fnirs}, Synamp:{synamp})")
        
        # Method A: direct
        ser.write(bytes([b]))
        ser.flush()
        print(f"    A: sent {bytes([b])!r} → 观察设备")
        time.sleep(2.0)
        
        # Method B: with reset
        ser.write(b'\x00')
        time.sleep(0.003)
        ser.write(bytes([b]))
        ser.flush()
        time.sleep(0.005)
        ser.write(b'\x00')
        ser.flush()
        print(f"    B: sent 0x00→0x{b:02X}→0x00 → 观察设备")
        input(f"    >>> 按 Enter 继续...")
    
    print(f"\n  ✅ A/B 对比完成。")


def interactive_menu(ser):
    while True:
        print(f"\n{'='*55}")
        print(f"  serialPort_2 复现测试 | {PORT} @ {BAUDRATE}")
        print(f"{'='*55}")
        print("  [1] 模拟 1 个 Trial (4→2, 同 serialPort_2)")
        print("  [2] 模拟 1 个 Trial (带 0x00 复位)")
        print("  [3] A/B 对比 (不带复位 vs 带复位)")
        print("  [4] 连续 5 个 Trial (模拟 Part A)")
        print("  [5] 只发 START (0x04)")
        print("  [6] 只发 STOP  (0x02)")
        print("  [Q] 退出")
        print(f"{'='*55}")
        cmd = input("> ").strip().lower()
        
        if cmd == '1':
            simulate_trial(ser)
        elif cmd == '2':
            simulate_trial_with_reset(ser)
        elif cmd == '3':
            compare_methods(ser)
        elif cmd == '4':
            for i in range(5):
                print(f"\n  === Trial {i+1}/5 ===")
                simulate_trial(ser, gap_between=0.5)
                time.sleep(0.5)
        elif cmd == '5':
            simulate_serialport2_start(ser, "A", 0x04)
        elif cmd == '6':
            simulate_serialport2_stop(ser, "A", 0x02)
        elif cmd in ('q', 'quit', 'exit'):
            break
        else:
            print("  [?] 未知命令")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="serialPort_2 复现测试")
    parser.add_argument("--port", "-p", default=PORT)
    parser.add_argument("--count", "-c", type=int, default=1, help="重复次数")
    parser.add_argument("--compare", action="store_true", help="A/B 对比模式")
    parser.add_argument("--with-reset", action="store_true", help="使用 0x00 复位")
    args = parser.parse_args()
    
    print(f"[CONNECT] {args.port} @ {BAUDRATE} ...")
    ser = open_port(args.port)
    print(f"[OK] 已连接: {args.port}\n")
    
    try:
        if args.compare:
            compare_methods(ser)
        elif args.count > 1:
            for i in range(args.count):
                if args.with_reset:
                    simulate_trial_with_reset(ser, gap_between=0.5)
                else:
                    simulate_trial(ser, gap_between=0.5)
        else:
            interactive_menu(ser)
    finally:
        ser.close()
        print("\n[DISCONNECT] 端口已关闭。")


if __name__ == "__main__":
    main()
