#!/usr/bin/env python3
"""
Unit and integration tests for Antigravity FL Studio Native MCP Server (v7.5 SOTA).
Validates MIDI dispatch, AST safety verification, binary header reverse engineering,
centralized bounce cataloging, and self-test attestation.
"""

import sys
import time
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

    def test_20_generate_fsc_score(self):
        """Verifies native FL Studio Piano Roll Score (.fsc) binary generation."""
        res = mcp_server.fl_generate_fsc_score(bars=2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("total_notes"), 24)
        self.assertTrue(Path(res.get("file")).exists())

    def test_21_slice_audio_transients(self):
        """Verifies audio transient slicing into zero-crossing chops and MIDI/FSC triggers."""
        preview_wav = mcp_server.MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        if preview_wav.exists():
            res = mcp_server.fl_slice_audio_transients(input_wav=str(preview_wav))
            self.assertEqual(res.get("status"), "SUCCESS")
            self.assertGreater(res.get("total_slices", 0), 0)
            self.assertTrue(Path(res.get("trigger_midi")).exists())
            self.assertTrue(Path(res.get("trigger_fsc")).exists())

    def test_22_generate_midi_cc_automation(self):
        """Verifies continuous high-resolution 14-bit pitch bend and CC automation generation."""
        res = mcp_server.fl_generate_midi_cc_automation(curve_type="all", bars=2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("vibrato_pitch_bend", res.get("exported_files", {}))
        self.assertIn("sidechain_ducking", res.get("exported_files", {}))

    def test_23_generate_sytrus_microtonal_preset(self):
        """Verifies microtonal Scala tunings and Sytrus/Harmor presets generation."""
        res = mcp_server.fl_generate_sytrus_microtonal_preset()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_installed", 0), 0)
        self.assertTrue(Path(res.get("centralized_mirror")).exists())

    def test_24_live_cockpit_server(self):
        """Verifies live bidirectional HTTP/SSE Cockpit server start, health check, and stop."""
        start_res = mcp_server.fl_start_cockpit_server(port=8855)
        self.assertIn(start_res.get("status"), ("STARTED", "ALREADY_RUNNING"))
        time.sleep(0.3)
        stop_res = mcp_server.fl_stop_cockpit_server()
        self.assertIn(stop_res.get("status"), ("STOPPED", "NOT_RUNNING"))

    def test_25_causal_mix_transaction(self):
        """Verifies ACID transactional mutation on mixer routing DAG."""
        res = mcp_server.fl_commit_causal_mix_transaction(
            mutations=[
                {"track": 1, "volume": 0.60, "pan": 0.0},
                {"track": 2, "volume": 0.35, "add_send": 1}
            ],
            execute_midi=False
        )
        self.assertEqual(res.get("status"), "COMMITTED")
        self.assertEqual(res.get("mutations_applied"), 2)
        self.assertIsNotNone(res.get("transaction_id"))

    def test_26_shm_telemetry(self):
        """Verifies zero-copy POSIX shared memory ring telemetry read."""
        res = mcp_server.fl_audit_shm_telemetry()
        self.assertIn(res.get("status"), ("SHM_ONLINE", "SHM_OFFLINE"))
        if res.get("status") == "SHM_ONLINE":
            self.assertTrue(res.get("is_consistent"))
            self.assertGreater(res.get("monitored_tracks", 0), 0)

    def test_27_diagnose_daw_health_kernel(self):
        """Verifies Mach thread and kernel duty cycle diagnostics without -c flag."""
        res = mcp_server.fl_diagnose_daw_health_kernel()
        self.assertIn("status", res)
        self.assertIn(res.get("status"), ("DAW_ONLINE_KERNEL_VALIDATED", "DAW_OFFLINE"))

    def test_28_transcribe_audio_to_score(self):
        """Verifies monophonic audio transcription via fast YIN algorithm into .fsc."""
        bass_wav = mcp_server.MUSIC_BOUNCES_DIR / "Stems" / "Dark_Cyber_Flamenco_Stems_16Bars" / "03_Rolling_Cyber_Bass.wav"
        if bass_wav.exists():
            res = mcp_server.fl_transcribe_audio_to_score(str(bass_wav))
            self.assertEqual(res.get("status"), "SUCCESS")
            self.assertGreater(res.get("total_notes_detected", 0), 0)
            self.assertTrue(Path(res.get("exported_fsc")).exists())

    def test_29_rearrange_slices_generative(self):
        """Verifies algorithmic slice breakbeat and compás rearrangement."""
        res = mcp_server.fl_rearrange_slices_generative(style="bulerias_cyber_drill", bars=2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_notes", 0), 0)
        self.assertTrue(Path(res.get("exported_fsc")).exists())

    def test_30_render_tui_cockpit(self):
        """Verifies rendering of ASCII ANSI terminal dashboard."""
        hud_str = mcp_server.fl_render_tui_cockpit()
        self.assertIn("ANTIGRAVITY FL STUDIO COCKPIT", hud_str)
        self.assertIn("MIXER MATRIX METERS", hud_str)

    def test_31_calculate_microtonal_retuning(self):
        """Verifies cent-level retuning calculation for Just Intonation and Flamenco Hijaz."""
        res = mcp_server.fl_calculate_microtonal_retuning("just_intonation_5limit")
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(len(res.get("matrix", [])), 12)
        self.assertTrue(Path(res.get("exported_json")).exists())

    def test_32_compile_flp_project(self):
        """Verifies pure Python binary FL Studio (.flp) project compiler."""
        res = mcp_server.fl_compile_flp_project()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("channels_count"), 5)
        self.assertEqual(res.get("bpm"), 112.0)
        self.assertTrue(Path(res.get("project_file")).exists())
        self.assertGreater(res.get("file_size_bytes", 0), 0)

    def test_33_carve_psychoacoustic_masking(self):
        """Verifies 24 Bark critical band psychoacoustic spectral masking analysis."""
        res = mcp_server.fl_carve_psychoacoustic_masking()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("parametric_eq_carving_curve", res)
        self.assertIn("overall_masking_verdict", res)
        self.assertTrue(Path(res.get("report_file")).exists())

    def test_34_synthesize_neuroacoustic_entrainment(self):
        """Verifies 40 Hz Gamma and 6 Hz Theta neuroacoustic brainwave synthesizer."""
        # Fast test with short duration (2.0 seconds) to ensure quick test execution
        res = mcp_server.fl_synthesize_neuroacoustic_entrainment(
            wave_type="gamma_40hz",
            duration_sec=2.0,
            carrier_freq_hz=146.83
        )
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("entrainment_freq_hz"), 40.0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_35_encode_ambisonics_bformat(self):
        """Verifies 1st-order Ambisonics B-format (ambiX ACN-SN3D) 4-channel encoding."""
        res = mcp_server.fl_encode_ambisonics_bformat(azimuth_deg=45.0, elevation_deg=15.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("format"), "ambiX_ACN_SN3D_4CH")
        self.assertEqual(len(res.get("channels", [])), 4)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_36_spatialize_binaural_3d(self):
        """Verifies Woodworth spherical head model binaural 3D spatializer."""
        res = mcp_server.fl_spatialize_binaural_3d(azimuth_deg=30.0, elevation_deg=10.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("itd_left_usec", res)
        self.assertIn("iacc_inter_aural_correlation", res)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_37_separate_harmonic_percussive(self):
        """Verifies FitzGerald 2D STFT median-filtering HPSS demixing."""
        res = mcp_server.fl_separate_harmonic_percussive()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertTrue(Path(res.get("harmonic_stem")).exists())
        self.assertTrue(Path(res.get("percussive_stem")).exists())
        self.assertGreater(res.get("energy_ratio_harmonic", 0), 0)
        self.assertGreater(res.get("energy_ratio_percussive", 0), 0)

    def test_38_compile_playlist_arrangement(self):
        """Verifies full 64-bar song arrangement compilation to native .flp binary."""
        res = mcp_server.fl_compile_playlist_arrangement()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("total_bars"), 64)
        self.assertGreater(res.get("total_notes", 0), 500)
        self.assertTrue(Path(res.get("flp_project_file")).exists())
        self.assertTrue(Path(res.get("json_manifest_file")).exists())

    def test_39_verify_mixer_gain_staging(self):
        """Verifies formal gain-staging and Linear Programming headroom optimization."""
        res = mcp_server.fl_verify_mixer_gain_staging()
        self.assertIn(res.get("status"), ("VERIFIED_SAFE", "HEADROOM_VIOLATION_REMEDIATED"))
        self.assertIn("coherent_headroom_db", res)
        self.assertIn("remediated_safe_faders", res)

    def test_40_synthesize_granular_cloud(self):
        """Verifies Curtis Roads stochastic granular cloud synthesis."""
        res = mcp_server.fl_synthesize_granular_cloud(output_duration_sec=2.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_grains_rendered", 0), 10)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_41_convolve_acoustic_space(self):
        """Verifies physical Sabine convolution reverb with physical RIR synthesis."""
        res = mcp_server.fl_convolve_acoustic_space(room_profile="alhambra_flamenco_cave", wet_mix=0.20)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("sabine_rt60_sec"), 1.8)
        self.assertTrue(Path(res.get("output_file")).exists())
        self.assertTrue(Path(res.get("ir_file")).exists())

    def test_42_master_audio_ebu_r128(self):
        """Verifies EBU R128 mastering pass with true-peak limiting and mono sub-bass."""
        res = mcp_server.fl_master_audio_ebu_r128(target_lufs=-14.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertAlmostEqual(res.get("target_integrated_lufs"), -14.0)
    def test_43_morph_spectral_cross_synthesis(self):
        """Verifies STFT non-stationary spectral morphing and cross-synthesis vocoder."""
        res = mcp_server.fl_morph_spectral_cross_synthesis(morph_factor=0.45)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("morph_factor"), 0.45)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_44_decorrelate_spatial_ambisonics(self):
        """Verifies multi-channel orthogonal Schroeder all-pass lattice spatial decorrelator."""
        res = mcp_server.fl_decorrelate_spatial_ambisonics(diffuse_amount=0.35)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("diffuse_amount"), 0.35)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_45_humanize_groove_causal(self):
        """Verifies Bulerías 12-beat compás micro-timing and Voss-Clarke 1/f pink noise drift humanization."""
        res = mcp_server.fl_humanize_groove_causal(style="bulerias_flamenco", groove_depth=0.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_notes_humanized", 0), 0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_46_calibrate_spectral_match_eq(self):
        """Verifies LTAS Welch PSD spectral matching EQ calibrator against 1/f pink noise."""
        res = mcp_server.fl_calibrate_spectral_match_eq(target_curve="pink_noise_1overf")
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("spectral_error_after_db", res)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_47_synthesize_waveguide_flute(self):
        """Verifies Julius O. Smith digital waveguide physical modeling acoustic Ney/flute synthesis."""
        res = mcp_server.fl_synthesize_waveguide_flute(pitch_midi=62, duration_sec=1.2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("pitch_midi"), 62)
        self.assertAlmostEqual(res.get("base_freq_hz"), 293.66, places=1)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_48_demix_multitrack_nmf_blind(self):
        """Verifies unsupervised NMF & Wiener ratio masking blind audio source separation into 4 stems."""
        res = mcp_server.fl_demix_multitrack_nmf_blind(num_components=4, nmf_iterations=10)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(len(res.get("separated_stems", {})), 4)
        for stem_name, stem_path in res.get("separated_stems", {}).items():
            self.assertTrue(Path(stem_path).exists(), f"Stem {stem_name} does not exist")

    def test_49_optimize_tonnetz_voice_leading(self):
        """Verifies Neo-Riemannian Tonnetz torus progression & parsimonious voice-leading minimization."""
        res = mcp_server.fl_optimize_tonnetz_voice_leading(bars=2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_chords", 0), 0)
        self.assertIn("parsimonious_voice_leading_cost", res)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_50_saturate_audio_wdf_analog(self):
        """Verifies Wave Digital Filter (WDF) analog diode/triode saturation and 3-band RC tone stack."""
        res = mcp_server.fl_saturate_audio_wdf_analog(drive_db=6.0, tube_bias=0.20)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("drive_db"), 6.0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_51_synthesize_spectral_freeze_drone(self):
        """Verifies STFT spectral frame freeze & stochastic phase diffusion drone synthesis."""
        res = mcp_server.fl_synthesize_spectral_freeze_drone(freeze_time_sec=1.5, output_duration_sec=2.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("output_duration_sec"), 2.0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_52_shape_multiband_transients(self):
        """Verifies 3-band Linkwitz-Riley crossover multiband transient and sustain shaper."""
        res = mcp_server.fl_shape_multiband_transients(high_transient_db=2.0, low_sustain_db=1.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("gains_applied_db", res)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_53_compile_multitrack_stems_flp(self):
        """Verifies autopoietic native binary .flp compilation with audio clip samplers and mixer routing."""
        res = mcp_server.fl_compile_multitrack_stems_flp()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_stem_channels", 0), 0)
        self.assertTrue(Path(res.get("flp_file")).exists())
        self.assertTrue(Path(res.get("manifest_file")).exists())

    def test_54_simulate_binaural_room_acoustics(self):
        """Verifies Image-Source Method (ISM) 3D binaural room impulse response simulation & convolution."""
        res = mcp_server.fl_simulate_binaural_room_acoustics(reflection_order=1)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertGreater(res.get("total_virtual_image_sources", 0), 0)
        self.assertTrue(Path(res.get("brir_impulse_file")).exists())
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_55_synthesize_shepard_risset_glissando(self):
        """Verifies Shepard-Risset infinite glissando and 3D barberpole binaural spatialization."""
        res = mcp_server.fl_synthesize_shepard_risset_glissando(duration_sec=2.0, direction="ascending")
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("direction"), "ascending")
        self.assertEqual(res.get("duration_sec"), 2.0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_56_extract_harmonic_perceptual_features(self):
        """Verifies psychoacoustic MIR Chroma, K-S 24-key detection, and spectral flux BPM estimation."""
        res = mcp_server.fl_extract_harmonic_perceptual_features()
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("detected_key", res)
        self.assertIn("estimated_bpm", res)
        self.assertIn("chroma_pitch_class_profile", res)
        self.assertTrue(Path(res.get("report_file")).exists())

    def test_57_synthesize_formant_vocal_tract(self):
        """Verifies Chiba-Kajiyama acoustic vocal tract physical modeling with Liljencrants-Fant glottal pulse."""
        res = mcp_server.fl_synthesize_formant_vocal_tract(vowel="A", duration_sec=1.5, pitch_midi=57.0)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("vowel"), "A")
        self.assertEqual(res.get("pitch_midi"), 57.0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_58_compose_algorithmic_modal_counterpoint(self):
        """Verifies Johann Joseph Fux First-Species modal counterpoint and dual-voice .fsc & .mid export."""
        res = mcp_server.fl_compose_algorithmic_modal_counterpoint(cantus_firmus_mode="dorian", bars=12)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("mode"), "Dorian")
        self.assertEqual(res.get("total_bars"), 12)
        self.assertEqual(res.get("total_notes"), 24)
        self.assertTrue(Path(res.get("fsc_score_file")).exists())
        self.assertTrue(Path(res.get("midi_file")).exists())

    def test_59_apply_psychoacoustic_noise_shaping_dither(self):
        """Verifies Lipshitz-Vanderkooy psychoacoustically noise-shaped TPDF dithering and noise floor shaping."""
        res = mcp_server.fl_apply_psychoacoustic_noise_shaping_dither(target_bit_depth=16, noise_shaping=True, max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("target_bit_depth"), 16)
        self.assertTrue(res.get("noise_shaping_enabled"))
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_60_synthesize_modal_plate_resonator(self):
        """Verifies 2D Kirchhoff-Love thin plate physical modeling and Chladni modal synthesis."""
        res = mcp_server.fl_synthesize_modal_plate_resonator(material="bronze", duration_sec=1.5, max_modes=24)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("material"), "bronze")
        self.assertGreater(res.get("total_modes_synthesized", 0), 0)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_61_deconvolve_homomorphic_cepstrum(self):
        """Verifies Oppenheim homomorphic real cepstrum deconvolution and formant envelope shaping."""
        res = mcp_server.fl_deconvolve_homomorphic_cepstrum(quefrency_cutoff_ms=2.8, max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("quefrency_cutoff_ms"), 2.8)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_62_align_multitrack_stems_phase(self):
        """Verifies sub-sample cross-correlation lag estimation and fractional delay phase alignment."""
        res = mcp_server.fl_align_multitrack_stems_phase(max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertIn("delay_offset_ms", res)
        self.assertIn("aligned_phase_correlation", res)
        self.assertTrue(Path(res.get("output_sum_mix_file")).exists())
        self.assertTrue(Path(res.get("aligned_secondary_file")).exists())

    def test_63_encode_higher_order_ambisonics_hoa3(self):
        """Verifies 3rd-Order 16-channel Higher-Order Ambisonics encoding and 3D binaural decoding."""
        res = mcp_server.fl_encode_higher_order_ambisonics_hoa3(azimuth_deg=45.0, elevation_deg=15.0, max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("ambisonics_order"), 3)
        self.assertEqual(res.get("total_spherical_harmonic_channels"), 16)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_64_synthesize_chaotic_attractor_oscillator(self):
        """Verifies Duffing / Van der Pol / Lorenz non-linear chaotic attractor synthesis via RK4."""
        res = mcp_server.fl_synthesize_chaotic_attractor_oscillator(attractor_type="duffing", duration_sec=1.2)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("attractor_type"), "duffing")
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_65_saturate_volterra_kernel_analog(self):
        """Verifies multi-order discrete Volterra series non-linear analog transformer and tape saturation."""
        res = mcp_server.fl_saturate_volterra_kernel_analog(drive_db=4.0, max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("volterra_kernel_length"), 32)
        self.assertTrue(Path(res.get("output_file")).exists())

    def test_66_denoise_wavelet_packet_transform(self):
        """Verifies Daubechies 4 multi-scale discrete wavelet transform denoising and transient preservation."""
        res = mcp_server.fl_denoise_wavelet_packet_transform(levels=3, max_duration_sec=1.5)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("wavelet_family"), "Daubechies 4 (db4)")
        self.assertEqual(res.get("decomposition_levels"), 3)
        self.assertTrue(Path(res.get("output_file")).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)



