"""
Quick verify: send 0x00–0x09 with corrected config (9600, DTR/RTS off, flush).
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

print(f"[OK] {PORT} @ {BAUDRATE} | DTR={ser.dtr} RTS={ser.rts}\n")
print("Sending 0x00–0x09 with Neuroscan protocol (0x00→value→0x00, 5ms pulse)")
print("=" * 50)

for i in range(10):
    # Protocol: reset → value → reset
    ser.write(b'\x00')
    time.sleep(0.002)
    ser.write(bytes([i]))
    ser.flush()
    time.sleep(0.005)
    ser.write(b'\x00')
    ser.flush()
    
    print(f"  SENT: 0x{i:02X}  dec={i:3d}  bin={i:08b}")
    time.sleep(1.0)  # observe device display

ser.close()
print(f"\n[OK] Done. What did Synamp show for each value?")
