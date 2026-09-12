#!/usr/bin/env python3
"""
Unit and integration tests for Antigravity FL Studio Native MCP Server (v7.5 SOTA).
Validates MIDI dispatch, AST safety verification, binary header reverse engineering,
centralized bounce cataloging, and self-test attestation.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import mcp_server


class TestFLStudioMCPServer(unittest.TestCase):

    def test_01_health_check(self):
        """Verifies health check runs and outputs diagnostic lines."""
        report = mcp_server.fl_health_check()
        self.assertIn("FL Studio MCP SOTA Health Check", report)
        self.assertIn("CoreMIDI Port", report)
        self.assertIn("FL Studio App", report)

    def test_02_transport_control(self):
        """Verifies transport commands and input validation."""
        res_play = mcp_server.fl_transport_control("play")
        self.assertIn("PLAY", res_play)
        
        res_invalid = mcp_server.fl_transport_control("nonexistent_action")
        self.assertIn("Invalid action", res_invalid)

    def test_03_set_tempo(self):
        """Verifies tempo range clamping between 60 and 187 BPM."""
        res_normal = mcp_server.fl_set_tempo(124.0)
        self.assertIn("124 BPM", res_normal)

        res_low = mcp_server.fl_set_tempo(40.0)
        self.assertIn("60 BPM", res_low)

        res_high = mcp_server.fl_set_tempo(250.0)
        self.assertIn("187 BPM", res_high)

    def test_04_mixer_controls(self):
        """Verifies track volume, pan, mute, solo, and stereo separation."""
        v_res = mcp_server.fl_set_mixer_volume(1, 0.8)
        self.assertIn("Mixer track 1 volume set to 0.80", v_res)

        p_res = mcp_server.fl_set_mixer_pan(2, -0.5)
        self.assertIn("panning set to -0.50", p_res)

        m_res = mcp_server.fl_mute_track(3, True)
        self.assertIn("Muted", m_res)

        s_res = mcp_server.fl_solo_track(4, True)
        self.assertIn("Soloed", s_res)

        sep_res = mcp_server.fl_set_mixer_stereo_separation(5, 0.5)
        self.assertIn("stereo separation", sep_res)

    def test_05_sidechain_and_select(self):
        """Verifies sidechain routing and track selection."""
        sc_res = mcp_server.fl_setup_sidechain(1, 2)
        self.assertIn("Track 01 ===> Track 02", sc_res)

        sel_res = mcp_server.fl_select_mixer_track(10)
        self.assertIn("track 10 selected", sel_res)

    def test_06_window_toggle(self):
        """Verifies window toggling for mixer, playlist, piano roll, channel rack."""
        w_res = mcp_server.fl_toggle_window("mixer")
        self.assertIn("window 'mixer' focus/toggle executed", w_res)

        w_inv = mcp_server.fl_toggle_window("invalid_window")
        self.assertIn("Unknown window", w_inv)

    def test_07_binary_header_inspector(self):
        """Verifies binary header parser for RIFF WAV files."""
        wav_file = mcp_server.SAMPLES_DIR / "orbital_kick.wav"
        if wav_file.exists():
            hdr = mcp_server.fl_inspect_binary_header(str(wav_file))
            self.assertEqual(hdr["file_type"], "RIFF WAVE Audio Stem")
            self.assertEqual(hdr["sample_rate_hz"], 44100)
            self.assertIn("duration_sec", hdr)

        # Test non-existent file handling
        missing = mcp_server.fl_inspect_binary_header("/nonexistent/file.wav")
        self.assertIn("error", missing)

    def test_08_sensory_dissonance(self):
        """Verifies Sethares / Plomp-Levelt roughness index calculation."""
        res = mcp_server.fl_calculate_sensory_dissonance(440.0, 466.16)
        self.assertIn("Sensory Dissonance between 440.0Hz and 466.2Hz", res)

    def test_09_music_bounces_catalog(self):
        """Verifies cataloging of ~/Music/FL Studio Bounces/."""
        catalog = mcp_server.fl_catalog_music_bounces(follow_symlinks=True)
        self.assertIn("catalog_root", catalog)
        self.assertIn("assets", catalog)
        self.assertGreaterEqual(catalog["total_files"], 1)

    def test_10_piano_roll_script_ast_validation(self):
        """Verifies AST safety checks reject syntactically invalid scripts."""
        bad_code = "def syntax_error(:\n    pass"
        res = mcp_server.fl_deploy_custom_piano_roll_script("bad_script", bad_code)
        self.assertIn("SyntaxError", res)

    def test_11_run_self_test(self):
        """Verifies system-wide automated self test returns ALL_SYSTEMS_GO."""
        test_summary = mcp_server.fl_run_self_test()
        self.assertEqual(test_summary["overall_status"], "ALL_SYSTEMS_GO")
        self.assertEqual(test_summary["tests"]["coremidi_port"], "ONLINE")
        self.assertIn("PASSED", test_summary["tests"]["binary_inspector"])
        self.assertIn("PASSED", test_summary["tests"]["dissonance_calculator"])
        self.assertIn("PASSED", test_summary["tests"]["bounces_catalog"])

    def test_12_headless_audio_preview(self):
        """Verifies pure Python headless audio preview synthesis."""
        res = mcp_server.fl_render_headless_audio_preview()
        self.assertIn("Rendered 16-bar Headless Audio Preview", res)
        out_wav = mcp_server.MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        self.assertTrue(out_wav.exists())
        self.assertGreater(out_wav.stat().st_size, 1024 * 1024)

    def test_13_apply_exergic_mixer_matrix(self):
        """Verifies injection of complete 7-track mixing matrix via MIDI."""
        res = mcp_server.fl_apply_exergic_mixer_matrix()
        self.assertIn("Successfully applied C5-REAL Exergic Mixer Matrix", res)
        self.assertIn("Maceo Kick DSP", res)
        self.assertIn("Minimoog Sub-Bass", res)

    def test_14_live_telemetry(self):
        """Verifies closed-loop telemetry retrieval or fallback."""
        telem = mcp_server.fl_get_live_telemetry()
        self.assertIn("status", telem)
        self.assertIn("telemetry_source", telem)
        self.assertIn("timestamp", telem)

    def test_15_render_multitrack_stems_pack(self):
        """Verifies discrete multitrack stems generation and manifest."""
        manifest = mcp_server.fl_render_multitrack_stems_pack()
        self.assertIn("stems", manifest)
        self.assertEqual(manifest["total_stems"], 5)
        self.assertGreater(len(manifest["stems"]), 0)

    def test_16_analyze_audio_spectrum(self):
        """Verifies ITU-R BS.1770 / EBU R128 spectral and exergy analysis."""
        test_wav = mcp_server.MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        if test_wav.exists():
            report = mcp_server.fl_analyze_audio_spectrum(str(test_wav))
            self.assertIn("metrics", report)
            self.assertIn("peak_dbfs", report["metrics"])
            self.assertIn("crest_factor_db", report["metrics"])
            self.assertIn("exergy_rating_21000", report)

    def test_17_generate_euclidean_rhythm(self):
        """Verifies Bjorklund Euclidean polyrhythm MIDI generation."""
        res = mcp_server.fl_generate_euclidean_rhythm(pulses=5, steps=8, bars=4, bpm=112.0)
        self.assertIn("Generated Euclidean MIDI E(5,8)", res)

    def test_18_export_web_audio_hud(self):
        """Verifies HTML5 Web Audio cockpit generation."""
        res = mcp_server.fl_export_web_audio_hud()
        self.assertIn("Exported standalone Cyber HUD", res)
        hud_file = mcp_server.MUSIC_BOUNCES_DIR / "fl_studio_cyber_hud.html"
        self.assertTrue(hud_file.exists())

    def test_19_decompile_binary_preset(self):
        """Verifies binary preset decompiler error handling on non-existent or invalid file."""
        res = mcp_server.fl_decompile_binary_preset("/nonexistent/preset.fst")
        self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
