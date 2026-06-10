"""
简化对比: raw write vs PsychoPy style (仅3条)
"""
import serial, time

PORT = "COM4"; BAUDRATE = 9600
ser = serial.Serial()
ser.port = PORT; ser.baudrate = BAUDRATE
ser.bytesize = serial.EIGHTBITS; ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE; ser.timeout = 0.5
ser.dtr = False; ser.rts = False; ser.open()

print(f"[OK] {PORT} @ {BAUDRATE}\n")
print("3 tests, 5s gap each. Watch fNIRS.\n")

# Test 1: raw 0x04
print("Test 1/3: raw b'\\x04' (baseline)")
ser.write(b'\x04'); ser.flush()
print("  SENT. fNIRS should show: 4")
time.sleep(5.0)

# Test 2: PsychoPy style
print("\nTest 2/3: bytes(chr(4),'utf-8') (.ps1 patch style)")
data = bytes(chr(4), 'utf-8')
ser.write(data); ser.flush()
print(f"  SENT {data!r}. fNIRS should show: 4")
time.sleep(5.0)

# Test 3: bytearray (stop trigger style)
print("\nTest 3/3: bytes(bytearray([2])) (stop trigger)")
data = bytes(bytearray([2]))
ser.write(data); ser.flush()
print(f"  SENT {data!r}. fNIRS should show: 2")
time.sleep(3.0)

ser.close()
print("\n[DONE]")
