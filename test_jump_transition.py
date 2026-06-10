"""
快速验证: 通道跳变测试 (无 0x00 复位)
======================================
发送 0x01 → 0x02 → 0x04 直接跳变，每个字节保持 500ms。
不插入 0x00，让设备自己检测边沿。
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
print("=====================================")
print("Test 1: 0x01 -> 0x02 -> 0x04 (direct transitions, 500ms each)")
print("  Synamp expected: 160 -> 224 -> 208")
print("  fNIRS expected:  CH0 -> CH1 -> CH2")
print("=====================================")

for b in [0x01, 0x02, 0x04]:
    ser.write(bytes([b]))
    ser.flush()
    print(f"  SENT: 0x{b:02X}")
    time.sleep(0.5)

time.sleep(2.0)

print("\n=====================================")
print("Test 2: Same with 1s hold per byte")
print("=====================================")

for b in [0x01, 0x02, 0x04]:
    ser.write(bytes([b]))
    ser.flush()
    print(f"  SENT: 0x{b:02X}")
    time.sleep(1.0)

ser.close()
print("\n[DONE]")
