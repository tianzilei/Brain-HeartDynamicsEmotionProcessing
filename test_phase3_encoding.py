"""
Phase 3 — sendMessage 编码方式对比测试
=======================================
目的: 确认 PsychoPy 中三种 sendMessage 调用方式是否产生相同的硬件输出。
背景: alignment marker 使用 sendMessage(chr(b)) (str) → Synamp 正确 ✅
      serialPort_2 使用 sendMessage(bytes(chr(4),'utf-8')) (bytes) → Synamp 168 ❌

三种编码方式:
  A: chr(b)                  — alignment marker 使用 (字符串)
  B: bytes(chr(b), 'utf-8')  — .ps1 补丁生成 (bytes)
  C: bytes(bytearray([b]))   — stop 触发使用 (bytes via bytearray)

用法:
  python test_phase3_encoding.py              # 交互式
  python test_phase3_encoding.py --auto       # 自动运行全部对比
  python test_phase3_encoding.py --port COM4
"""
import serial
import time
import sys

PORT = "COM4"
BAUDRATE = 9600
TEST_VALUES = [0x01, 0x02, 0x04]  # fNIRS 可识别的三个单 bit 值

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


def test_encoding(ser, b, method_label, data):
    """
    发送一个字节并打印实际发送的内容。
    data 是传给 ser.write() 的 bytes 对象。
    """
    fnirs = FNIRS_MAP.get(b, f"?{b}")
    synamp = SYNAMP_MAP.get(b, "?")
    hex_data = data.hex(' ').upper() if data else "(empty)"
    
    print(f"  ┌─ 方法: {method_label}")
    print(f"  │  目标值: 0x{b:02X}  |  fNIRS→{fnirs}  |  Synamp→{synamp}")
    print(f"  │  data = {data!r}")
    print(f"  │  HEX = {hex_data}")
    
    # 发送协议: 0x00 → value → 0x00
    ser.write(b'\x00')
    time.sleep(0.003)
    ser.write(data)
    ser.flush()
    time.sleep(0.005)
    ser.write(b'\x00')
    ser.flush()
    
    # 验证: 确认写入的字节数
    print(f"  │  实际写入 {len(data)} 字节: {data.hex(' ').upper()}")
    print(f"  └─ [OK] 已发送")


def run_comparison(ser, auto=False):
    """对每个测试值，用三种方法各发一次，观察设备显示。"""
    print(f"\n{'='*60}")
    print(f"  Phase 3 — 编码方式对比 | {PORT} @ {BAUDRATE}")
    print(f"{'='*60}")
    print(f"  三种方法对比:")
    print(f"    A: chr(b)                  → ser.write(bytes([b]))")
    print(f"    B: bytes(chr(b), 'utf-8')  → ser.write(bytes(chr(b), 'utf-8'))")
    print(f"    C: bytes(bytearray([b]))   → ser.write(bytes(bytearray([b])))")
    print(f"{'='*60}\n")
    
    for b in TEST_VALUES:
        print(f"\n{'─'*50}")
        print(f"  测试值: 0x{b:02X} (fNIRS: {FNIRS_MAP.get(b,'?')}, Synamp: {SYNAMP_MAP.get(b,'?')})")
        print(f"{'─'*50}")
        
        # 方法 A: 模拟 alignment marker (chr → string → write bytes)
        data_a = bytes([b])
        test_encoding(ser, b, "A: chr(b) → bytes([b])", data_a)
        print(f"  ⏳ 观察设备，预期 Synamp={SYNAMP_MAP.get(b)}, fNIRS={FNIRS_MAP.get(b)}")
        if auto:
            time.sleep(2.0)
        else:
            input(f"  >>> 按 Enter 继续...")
        
        # 方法 B: 模拟 .ps1 补丁 (bytes(chr(N), 'utf-8'))
        data_b = bytes(chr(b), 'utf-8')
        test_encoding(ser, b, "B: bytes(chr(b), 'utf-8')", data_b)
        print(f"  ⏳ 观察设备，预期同上")
        if auto:
            time.sleep(2.0)
        else:
            input(f"  >>> 按 Enter 继续...")
        
        # 方法 C: 模拟 stop 触发 (bytearray)
        data_c = bytes(bytearray([b]))
        test_encoding(ser, b, "C: bytes(bytearray([b]))", data_c)
        print(f"  ⏳ 观察设备，预期同上")
        if auto:
            time.sleep(2.0)
        else:
            input(f"  >>> 按 Enter 继续...")
    
    print(f"\n{'='*60}")
    print(f"  [OK] 编码对比完成。")
    print(f"  请记录: A/B/C 三种方法的设备显示是否一致。")
    print(f"{'='*60}")


def verify_byte_equivalence():
    """离线验证: 三种方法产生的 bytes 是否相同 (不连接设备)"""
    print(f"\n{'='*60}")
    print(f"  离线验证: Python 层面 bytes 等价性")
    print(f"{'='*60}")
    
    all_match = True
    for b in TEST_VALUES:
        a = bytes([b])
        b_enc = bytes(chr(b), 'utf-8')
        c = bytes(bytearray([b]))
        
        match_ab = a == b_enc
        match_ac = a == c
        match_bc = b_enc == c
        
        status = "[OK]" if (match_ab and match_ac) else "[FAIL]"
        print(f"  0x{b:02X}: A={a!r}  B={b_enc!r}  C={c!r}")
        print(f"         A==B: {match_ab}  |  A==C: {match_ac}  |  B==C: {match_bc}  {status}")
        
        if not (match_ab and match_ac):
            all_match = False
    
    if all_match:
        print(f"\n  [OK] 三种方法在 Python 层面完全等价。")
        print(f"       如果设备显示不同 -> 问题在 PsychoPy SerialDevice 或硬件层。")
    else:
        print(f"\n  [FAIL] Python 层面存在差异! 请检查编码方式。")
    
    return all_match


def interactive_menu(ser):
    while True:
        print(f"\n{'='*55}")
        print(f"  Phase 3 — 编码对比 | {PORT} @ {BAUDRATE}")
        print(f"{'='*55}")
        print("  [1] 测试 0x01 (三种方法对比)")
        print("  [2] 测试 0x02 (三种方法对比)")
        print("  [3] 测试 0x04 (三种方法对比)")
        print("  [A] 全部对比 (0x01, 0x02, 0x04)")
        print("  [V] 离线验证 (不连设备, Python 层面)")
        print("  [Q] 退出")
        print(f"{'='*55}")
        cmd = input("> ").strip().lower()
        
        if cmd == '1':
            for b_val in [0x01]:
                for method, data in [
                    ("A: chr", bytes([b_val])),
                    ("B: bytes-chr", bytes(chr(b_val), 'utf-8')),
                    ("C: bytearray", bytes(bytearray([b_val]))),
                ]:
                    test_encoding(ser, b_val, method, data)
                    input(">>> 按 Enter 继续...")
        elif cmd == '2':
            for b_val in [0x02]:
                for method, data in [
                    ("A: chr", bytes([b_val])),
                    ("B: bytes-chr", bytes(chr(b_val), 'utf-8')),
                    ("C: bytearray", bytes(bytearray([b_val]))),
                ]:
                    test_encoding(ser, b_val, method, data)
                    input(">>> 按 Enter 继续...")
        elif cmd == '3':
            for b_val in [0x04]:
                for method, data in [
                    ("A: chr", bytes([b_val])),
                    ("B: bytes-chr", bytes(chr(b_val), 'utf-8')),
                    ("C: bytearray", bytes(bytearray([b_val]))),
                ]:
                    test_encoding(ser, b_val, method, data)
                    input(">>> 按 Enter 继续...")
        elif cmd == 'a':
            run_comparison(ser, auto=False)
        elif cmd == 'v':
            verify_byte_equivalence()
        elif cmd in ('q', 'quit', 'exit'):
            break
        else:
            print("  [?] 未知命令")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 3 编码方式对比")
    parser.add_argument("--port", "-p", default=PORT)
    parser.add_argument("--auto", "-a", action="store_true", help="自动运行 (2s间隔, 无需按键)")
    parser.add_argument("--verify", "-v", action="store_true", help="仅离线验证, 不连设备")
    args = parser.parse_args()
    
    if args.verify:
        verify_byte_equivalence()
        return
    
    print(f"[CONNECT] {args.port} @ {BAUDRATE} ...")
    ser = open_port(args.port)
    print(f"[OK] 已连接: {args.port}\n")
    
    try:
        if args.auto:
            verify_byte_equivalence()
            run_comparison(ser, auto=True)
        else:
            interactive_menu(ser)
    finally:
        ser.close()
        print("\n🔌 端口已关闭。")


if __name__ == "__main__":
    main()
