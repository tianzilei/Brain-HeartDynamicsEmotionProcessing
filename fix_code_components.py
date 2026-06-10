"""
Fix alignment marker code in all .psyexp files.
Removes 0x00 resets, changes sendMessage -> com.write, gap 0.3 -> 1.0.
"""
import re
import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

PSYEXP_DIR = Path(r"C:\Users\Charlie\Desktop\Psychopy")

OLD_GAP = "gap = 0.3"
NEW_GAP = "gap = 1.0"

def fix_code(code):
    """Fix alignment marker Python code. Code uses &#10; for newlines."""
    if not code or 'sendMessage' not in code:
        return code
    
    # Fix gap
    code = code.replace('gap = 0.3', 'gap = 1.0')
    
    NL = '&#10;'
    
    # Replace the for-loop body: remove 0x00 lines, change sendMessage to com.write
    old_block = (
        'for b in seq:' + NL
        + '    serialPort.sendMessage(chr(0))' + NL
        + '    clock.time.sleep(0.003)' + NL
        + '    serialPort.sendMessage(chr(b))' + NL
        + '    clock.time.sleep(0.005)' + NL
        + '    serialPort.sendMessage(chr(0))' + NL
        + '    clock.time.sleep(gap)'
    )
    new_block = (
        'for b in seq:' + NL
        + '    serialPort.com.write(bytes([b]))' + NL
        + '    clock.time.sleep(gap)'
    )
    code = code.replace(old_block, new_block)
    
    return code


def process_psyexp(filepath):
    """Process one .psyexp file."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    changed = 0
    
    for code_comp in root.iter('CodeComponent'):
        name_el = code_comp.find(".//Param[@name='name']")
        name = name_el.get('val') if name_el is not None else '?'
        
        # Only fix Python code sections (not JS)
        for param in code_comp.findall("Param"):
            pname = param.get('name', '')
            if pname in ('Begin Routine', 'End Routine'):
                old_val = param.get('val', '')
                new_val = fix_code(old_val)
                if new_val != old_val:
                    param.set('val', new_val)
                    changed += 1
                    print(f"  [{name}] {pname}: fixed")
    
    if changed > 0:
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        print(f"[OK] {filepath.name}: {changed} sections fixed")
    else:
        print(f"[--] {filepath.name}: no changes needed")
    
    return changed


def main():
    files = sorted(PSYEXP_DIR.glob("*.psyexp"))
    total = 0
    for f in files:
        total += process_psyexp(f)
    print(f"\nTotal fixes: {total}")


if __name__ == "__main__":
    main()
