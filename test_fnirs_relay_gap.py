"""
fNIRS + 转接盒: 间隔容忍度测试 (无 0x00 复位, 直接跳变)
==========================================================
测试 fNIRS 经过转接盒后，在不同字节间隔下的响应。
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
print("============================================")
print("fNIRS relay box gap tolerance test")
print("Sequence: 0x01->0x02->0x04 (no 0x00 reset)")
print("============================================")

gaps = [0.3, 0.5, 1.0, 2.0]

for gap in gaps:
    print(f"\n--- gap = {gap}s ---")
    for b in [0x01, 0x02, 0x04]:
        ser.write(bytes([b]))
        ser.flush()
        print(f"  SENT: 0x{b:02X}")
        time.sleep(gap)
    print(f"  >> Check fNIRS: expected CH0,CH1,CH2 (1,2,4)")
    time.sleep(2.0)

ser.close()
print("\n[DONE]")
