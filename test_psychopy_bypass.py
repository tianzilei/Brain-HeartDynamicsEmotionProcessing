"""
终极测试 v2: 绕过 sendMessage()，直接用 serialPort.com.write()
"""
import time
from psychopy.hardware import DeviceManager

PORT = "COM4"; BAUDRATE = 9600

dm = DeviceManager()
dm.addDevice(
    deviceName='COM', port=PORT, baudrate=BAUDRATE,
    byteSize=8, stopBits=1, parity='N',
    deviceClass='psychopy.hardware.serialdevice.SerialDevice',
    pauseDuration=(None or 0.1) / 3,
)

sp = dm.getDevice('COM')
print(f"[OK] PsychoPy SerialDevice open: {sp.com.is_open}")

print("\n=== Test A: sp.com.write(b'\\x04') -- bypass sendMessage ===")
sp.com.write(b'\x04')
sp.com.flush()
print("  SENT via sp.com.write()")
print("  >> Check fNIRS (expected: 4/CH2)")
time.sleep(3.0)

print("\n=== Test B: sp.sendMessage(chr(4)) -- PsychoPy API ===")
sp.sendMessage(chr(4))
print(f"  SENT: chr(4)={chr(4)!r}")
print("  >> Check fNIRS (expected: 4/CH2 or NOTHING)")
time.sleep(3.0)

print("\n=== Test C: sp.com.write(b'\\x02') -- bypass again ===")
sp.com.write(b'\x02')
sp.com.flush()
print("  SENT via sp.com.write()")
print("  >> Check fNIRS (expected: 2/CH1)")

sp.com.close()
print("\n[DONE]")
