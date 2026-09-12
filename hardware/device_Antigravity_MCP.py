# name=Antigravity MCP Controller
# deviceNameMatches=Antigravity MCP Out, Antigravity*
# url=https://github.com/borjamoskv/antigravity-mcp-flstudio
#
# Antigravity SOTA MCP Bi-Directional Controller for FL Studio 2025 (v7.5)
# Comprehensive Hardware & AI Telemetry Engine supporting 125 mixer tracks,
# Direct Sidechain Routing, Track Focus & Arming, Window Navigation,
# Channel Rack, Pattern & Marker Navigation, Transport, and Macro Modulation.

import mixer
import channels
import patterns
import transport
import general
import ui
import device
import plugins
import midi

VERSION = "7.5-SOTA"

def OnInit():
    print("==================================================================")
    print(f"  ANTIGRAVITY SOTA MCP CONTROLLER INITIALIZED (v{VERSION})")
    print("  Bidirectional Telemetry: Active | 125 Mixer Tracks | Direct Routing")
    print("==================================================================")
    device.setHasMeters()
    ui.setHintMsg(f"Antigravity MCP {VERSION} Connected")

def OnDeInit():
    print(f"[Antigravity MCP] Controller Deinitialized (v{VERSION})")
    ui.setHintMsg("Antigravity MCP Disconnected")

def OnRefresh(flags):
    """Called by FL Studio when internal state changes (faders, mutes, tempo)."""
    pass

def OnUpdateBeatIndicator(value):
    """Called on each beat/bar tick for visual tempo alignment."""
    pass

def OnIdle():
    """Heartbeat callback invoked during FL Studio idle loop."""
    pass

def OnMidiMsg(event):
    if event.handled:
        return

    status_type = event.status & 0xF0
    mid_chan = event.status & 0x0F
    cc_num = event.data1
    val = event.data2

    # Handle Control Change (0xB0)
    if status_type == midi.MIDI_CONTROLCHANGE:
        
        # ─────────────────────────────────────────────────────────────
        # CH 1 (0): Mixer Track Volume (CC 0 = Master, 1..125 = Tracks)
        # ─────────────────────────────────────────────────────────────
        if mid_chan == 0:
            track_id = min(cc_num, 125)
            vol_norm = val / 127.0
            mixer.setTrackVolume(track_id, vol_norm)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 2 (1): Mixer Track Panning (-1.0 to 1.0, 64 center)
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 1:
            track_id = min(cc_num, 125)
            pan_norm = (val - 64) / 64.0
            mixer.setTrackPan(track_id, pan_norm)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 3 (2): Mixer Track Mute
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 2:
            track_id = min(cc_num, 125)
            mixer.muteTrack(track_id, 1 if val > 64 else 0)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 4 (3): Mixer Track Solo
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 3:
            track_id = min(cc_num, 125)
            mixer.soloTrack(track_id, 1 if val > 64 else 0)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 5 (4): Mixer Track Stereo Separation (-1.0 to 1.0)
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 4:
            track_id = min(cc_num, 125)
            sep_norm = (val - 64) / 64.0
            mixer.setStereoSep(track_id, sep_norm)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 6 (5): Focused Plugin Macros & TB-303 Cutoff/Resonance
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 5:
            cur_chan = channels.channelNumber()
            param_idx = cc_num
            val_norm = val / 127.0
            plugins.setParamValue(val_norm, param_idx, cur_chan)
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 7 (6): Channel Rack Control (Select, Mute, Solo)
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 6:
            chan_count = channels.channelCount()
            if cc_num < chan_count:
                # CC 0..15: Select and focus channel
                channels.selectOneChannel(cc_num)
                event.handled = True
            elif 16 <= cc_num < 16 + chan_count:
                # CC 16..31: Mute channel
                c_idx = cc_num - 16
                channels.muteChannel(c_idx, 1 if val > 64 else 0)
                event.handled = True
            elif 32 <= cc_num < 32 + chan_count:
                # CC 32..47: Solo channel
                c_idx = cc_num - 32
                channels.soloChannel(c_idx, 1 if val > 64 else 0)
                event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 8 (7): Pattern & Arrangement Marker Navigation
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 7:
            if cc_num == 1:
                # Jump to previous marker
                transport.markerJump(-1)
                event.handled = True
            elif cc_num == 2:
                # Jump to next marker
                transport.markerJump(1)
                event.handled = True
            elif cc_num == 3:
                # Toggle Pattern vs Song Mode (0 = Pattern, 127 = Song)
                transport.setLoopMode()
                event.handled = True
            elif cc_num == 4:
                # Select Pattern index
                target_pat = max(1, min(val, 999))
                patterns.jumpToPattern(target_pat)
                event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 9 (8): Direct Sidechain Routing (CC = Source, Val = Target)
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 8:
            src_track = min(cc_num, 125)
            dst_track = min(val, 125)
            # Route as sidechain (value 2 = sidechain send, value 1 = normal send)
            mixer.setRouteTo(src_track, dst_track, 2)
            ui.setHintMsg(f"Sidechain Send: Track {src_track} -> Track {dst_track}")
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 10 (9): Mixer Track Focus & Arming (CC = Track ID)
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 9:
            track_id = min(cc_num, 125)
            if val == 0:
                mixer.setTrackNumber(track_id)
                ui.setHintMsg(f"Selected Mixer Track {track_id}")
            elif val > 64:
                mixer.armTrack(track_id)
                ui.setHintMsg(f"Armed Mixer Track {track_id}")
            event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 11 (10): DAW Window Visibility & Navigation
        # CC 0 = Mixer, CC 1 = Channel Rack, CC 2 = Playlist, CC 3 = Piano Roll, CC 4 = Browser
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 10:
            wid_map = {
                0: midi.widMixer,
                1: midi.widChannelRack,
                2: midi.widPlaylist,
                3: midi.widPianoRoll,
                4: midi.widBrowser,
            }
            if cc_num in wid_map:
                target_wid = wid_map[cc_num]
                ui.showWindow(target_wid)
                ui.setFocused(target_wid)
                event.handled = True

        # ─────────────────────────────────────────────────────────────
        # CH 16 (15): Global Master Transport, Undo & Routing
        # ─────────────────────────────────────────────────────────────
        elif mid_chan == 15:
            if cc_num == 10:  # Play / Pause
                if val > 64:
                    transport.start()
                else:
                    transport.stop()
                event.handled = True
            elif cc_num == 11:  # Absolute Stop
                transport.stop()
                event.handled = True
            elif cc_num == 12:  # Record Arm Toggle
                transport.record()
                event.handled = True
            elif cc_num == 13:  # Loop Mode Toggle
                transport.setLoopMode()
                event.handled = True
            elif cc_num == 14:  # Metronome
                transport.globalTransport(midi.FPT_Metronome, 1)
                event.handled = True
            elif cc_num == 15:  # BPM Setting: val + 60 (e.g. 60 + 56 = 116 BPM)
                bpm_val = (val + 60) * 1000
                general.setBPM(bpm_val)
                ui.setHintMsg(f"BPM set to {val + 60}")
                event.handled = True
            elif cc_num == 16:  # Undo
                general.undo()
                ui.setHintMsg("Undo")
                event.handled = True
            elif cc_num == 17:  # Redo
                general.undoUp()
                ui.setHintMsg("Redo")
                event.handled = True
            elif cc_num == 18:  # Sidechain Routing (Legacy fallback): data2 = send track, focused track = source
                cur_track = mixer.trackNumber()
                target_track = val
                mixer.setRouteTo(cur_track, target_track, 2)
                ui.setHintMsg(f"Sidechain Send: Track {cur_track} -> Track {target_track}")
                event.handled = True
            elif cc_num == 19:  # Project Save
                transport.globalTransport(midi.FPT_Save, 1)
                ui.setHintMsg("Project Saved")
                event.handled = True
