# ── Alignment END Marker ──
# Paste into Code Component > End Routine (at end of recording block)
# 5-byte coded sequence: 0x04→0x02→0x01→0x02→0x04
# fNIRS: CH2→CH1→CH0→CH1→CH2 | Synamp: 208→224→160→224→208
serialPort = deviceManager.getDevice('COM')
seq = [0x04, 0x02, 0x01, 0x02, 0x04]
gap = 0.3
for b in seq:
    serialPort.sendMessage(0)
    clock.time.sleep(0.003)
    serialPort.sendMessage(b)
    clock.time.sleep(0.005)
    serialPort.sendMessage(0)
    clock.time.sleep(gap)
