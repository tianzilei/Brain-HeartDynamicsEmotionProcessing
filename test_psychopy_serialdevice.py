"""
终极测试: 使用 PsychoPy SerialDevice API (同 _lastrun.py)
==========================================================
直接 import psychopy 的 SerialDevice，用与 _lastrun.py 完全相同的方式发送。
"""
import time
from psychopy.hardware import DeviceManager
from psychopy.hardware.serialdevice import SerialDevice

PORT = "COM4"
BAUDRATE = 9600

# 完全按照 _lastrun.py 的方式创建设备
dm = DeviceManager()
dm.addDevice(
    deviceName='COM',
    port=PORT,
    baudrate=BAUDRATE,
    byteSize=8,
    stopBits=1,
    parity='N',
    deviceClass='psychopy.hardware.serialdevice.SerialDevice',
    pauseDuration=(None or 0.1) / 3,
)

serialPort = dm.getDevice('COM')
print(f"[OK] PsychoPy SerialDevice: {PORT} @ {BAUDRATE}")
print(f"     device class: {type(serialPort).__name__}")
print(f"     is_open: {serialPort.com.is_open}")

print("\n" + "=" * 50)
print("Test 1: sendMessage(chr(4))  -- string (like alignment marker)")
print("=" * 50)
serialPort.sendMessage(chr(4))
print(f"  SENT: chr(4) = {chr(4)!r}")
print("  >> Check fNIRS (expected: 4/CH2)")
time.sleep(3.0)

print("\n" + "=" * 50)
print("Test 2: sendMessage(chr(1)) then sendMessage(chr(2)) -- channel switch")
print("=" * 50)
serialPort.sendMessage(chr(1))
print(f"  SENT: chr(1) = {chr(1)!r}")
time.sleep(1.0)
serialPort.sendMessage(chr(2))
print(f"  SENT: chr(2) = {chr(2)!r}")
print("  >> Check fNIRS (expected: 1 then 2)")
time.sleep(3.0)

print("\n" + "=" * 50)
print("Test 3: sendMessage(bytes(chr(4), 'utf-8')) -- bytes (like serialPort_2)")
print("=" * 50)
data = bytes(chr(4), 'utf-8')
serialPort.sendMessage(data)
print(f"  SENT: {data!r} hex={data.hex()}")
print("  >> Check fNIRS (expected: 4/CH2)")
time.sleep(3.0)

print("\n" + "=" * 50)
print("Test 4: sendMessage(bytes(bytearray([2]))) -- bytes (like STOP trigger)")
print("=" * 50)
data = bytes(bytearray([2]))
serialPort.sendMessage(data)
print(f"  SENT: {data!r} hex={data.hex()}")
print("  >> Check fNIRS (expected: 2/CH1)")
time.sleep(3.0)

serialPort.com.close()
print("\n[DONE]")
