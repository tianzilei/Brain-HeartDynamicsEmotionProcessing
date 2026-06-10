"""
sendMessage 对比 v2 — 每条之间用 CH1→CH2 跳变隔离
"""
import serial, time

PORT = "COM4"; BAUDRATE = 9600
ser = serial.Serial()
ser.port = PORT; ser.baudrate = BAUDRATE
ser.bytesize = serial.EIGHTBITS; ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE; ser.timeout = 0.5
ser.dtr = False; ser.rts = False; ser.open()

def flush_channel():
    """用 CH1(0x02)→CH0(0x01) 跳变清状态"""
    ser.write(b'\x02'); ser.flush(); time.sleep(0.1)
    ser.write(b'\x01'); ser.flush(); time.sleep(0.1)

print(f"[OK] {PORT} @ {BAUDRATE}\n")

tests = [
    ("A: raw b'\\x04'",           b'\x04'),
    ("B: bytes(chr(4),'utf-8')",  bytes(chr(4), 'utf-8')),
    ("C: str(4).encode() = 0x34", str(4).encode()),
    ("D: bytes([4])",             bytes([4])),
    ("E: bytes(bytearray([2]))",  bytes(bytearray([2]))),
]

for label, data in tests:
    flush_channel()
    time.sleep(2.0)
    print(f"{'='*50}")
    print(f"  {label}")
    print(f"  data={data!r} hex={data.hex()}")
    ser.write(data); ser.flush()
    print(f"  SENT -> check fNIRS")
    time.sleep(3.0)

ser.close()
print("\n[DONE]")
