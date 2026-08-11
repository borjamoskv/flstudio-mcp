#!/usr/bin/env python3
"""
FL Studio Deep Binary Protocol Decompiler & Event Decoder
Decodes FLdt variable-length byte streams, event IDs, plugin strings, and parameter values.
"""

import sys
import os
import struct

# Known FL Studio Binary Event IDs
FL_EVENTS = {
    0: ("Byte", "Enabled / Active State"),
    2: ("Byte", "Mixer Volume"),
    3: ("Byte", "Mixer Pan"),
    4: ("Short", "Pitch / Detune"),
    6: ("DWord", "Track / Channel Color (RGB)"),
    10: ("Short", "MIDI Channel Number"),
    19: ("DWord", "Delay / Reverb Send Level"),
    21: ("Byte", "Cutoff Frequency"),
    22: ("Byte", "Resonance"),
    128: ("Text", "Channel / Plugin Name"),
    129: ("Text", "Sample / Audio File Path"),
    130: ("Text", "Plugin Generator Name"),
    131: ("Text", "Mixer Track Label"),
    136: ("Text", "Author / Project Comment")
}

def decode_fl_events(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    if data[:4] != b'FLhd':
        return {"error": "Invalid FLhd header"}

    pos = 14  # Skip 14-byte FLhd header
    events_found = []

    while pos < len(data):
        if data[pos:pos+4] == b'FLdt':
            chunk_len = struct.unpack('<I', data[pos+4:pos+8])[0]
            pos += 8
            end_pos = pos + chunk_len

            while pos < end_pos and pos < len(data):
                event_id = data[pos]
                pos += 1

                if event_id < 64:  # Byte events (0..63)
                    val = data[pos]
                    pos += 1
                    event_info = FL_EVENTS.get(event_id, ("Byte", f"Event_{event_id}"))
                    events_found.append({"id": event_id, "name": event_info[1], "value": val})

                elif event_id < 128:  # Short/Word events (64..127)
                    val = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    event_info = FL_EVENTS.get(event_id, ("Short", f"Event_{event_id}"))
                    events_found.append({"id": event_id, "name": event_info[1], "value": val})

                elif event_id < 192:  # Variable-length Text/String events (128..191)
                    # Read VarInt length
                    length = 0
                    shift = 0
                    while True:
                        b = data[pos]
                        pos += 1
                        length |= (b & 0x7F) << shift
                        if (b & 0x80) == 0:
                            break
                        shift += 7
                    
                    text_bytes = data[pos:pos+length]
                    pos += length
                    text_str = text_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    event_info = FL_EVENTS.get(event_id, ("Text", f"Event_{event_id}"))
                    events_found.append({"id": event_id, "name": event_info[1], "value": text_str})

                else:  # DWord / Data block events (192..255)
                    pos += 4
        else:
            pos += 1

    return events_found

if __name__ == "__main__":
    fst_file = "/Users/borjafernandezangulo/Documents/Image-Line/Downloads/FL Studio Mobile Factory Data/Synth Presets2/3xOsc/Bells/Bell.fst"
    events = decode_fl_events(fst_file)
    print(f"=== DECOMPILED {len(events)} EVENTS FROM FL BINARY ===")
    for ev in events[:15]:
        print(f" -> Event [{ev['id']:>3}]: {ev['name']:<30} = {ev['value']}")
