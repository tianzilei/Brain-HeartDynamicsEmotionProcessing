"""
_lastrun.py vs raw pyserial 对比测试
=====================================
模拟 serialPort_2 在 _lastrun.py 中的实际行为:
  Start: sendMessage(bytes(chr(4), 'utf-8'))  或 sendMessage(4)
  Stop:  sendMessage(bytes(bytearray([2])))   或 sendMessage(2)

对比三种可能的调用方式，看哪种与 raw pyserial 结果一致。
"""
import serial
import time

PORT = "COM4"
BAUDRATE = 9600

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

print(f"[OK] {PORT} @ {BAUDRATE}")
print("=" * 60)
print("Test A: raw pyserial (control) - ser.write(b'\\x04')")
print("=" * 60)
ser.write(b'\x04')
ser.flush()
print("  SENT: b'\\x04'")
print("  >> Check fNIRS (expected: 4 / CH2)")
time.sleep(2.0)

print("\n" + "=" * 60)
print("Test B: PsychoPy style - bytes(chr(4), 'utf-8')")
print("=" * 60)
data = bytes(chr(4), 'utf-8')
print(f"  data = {data!r}  hex = {data.hex()}")
ser.write(data)
ser.flush()
print("  SENT via ser.write(bytes(chr(4), 'utf-8'))")
print("  >> Check fNIRS (expected: 4 / CH2)")
time.sleep(2.0)

print("\n" + "=" * 60)
print("Test C: What if .ps1 NOT applied? sendMessage(4) as integer")
print("  str(4) =", repr(str(4)), "-> bytes =", str(4).encode())
print("=" * 60)
data = str(4).encode()
print(f"  data = {data!r}  hex = {data.hex()}")
ser.write(data)
ser.flush()
print("  SENT: str(4).encode() = b'4' = 0x34")
print("  >> Check fNIRS (expected: ? depends on low-bit parsing)")
time.sleep(2.0)

print("\n" + "=" * 60)
print("Test D: What if sendMessage(4) sends raw int as byte?")
print("=" * 60)
data = bytes([4])
print(f"  data = {data!r}  hex = {data.hex()}")
ser.write(data)
ser.flush()
print("  SENT: bytes([4]) = 0x04")
print("  >> Check fNIRS (expected: 4 / CH2)")
time.sleep(2.0)

print("\n" + "=" * 60)
print("Test E: bytearray (as used in STOP trigger)")
print("=" * 60)
data = bytes(bytearray([2]))
print(f"  data = {data!r}  hex = {data.hex()}")
ser.write(data)
ser.flush()
print("  SENT: bytes(bytearray([2])) = 0x02")
print("  >> Check fNIRS (expected: 2 / CH1)")
time.sleep(2.0)

ser.close()
print("\n[DONE] - Compare fNIRS readings for each test")
