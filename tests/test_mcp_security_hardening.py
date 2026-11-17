"""Unit and stdio transport isolation tests for flstudio-mcp security hardening."""

from __future__ import annotations

import io
import json
import struct
import subprocess
import sys
import tomllib
from contextlib import asynccontextmanager
from pathlib import Path
from unittest import mock

import pytest

import mcp_server

REPO_ROOT = Path(__file__).resolve().parent.parent


def _minimal_wav_bytes(sample_rate: int = 48000, channels: int = 2, bits_per_sample: int = 16) -> bytes:
    """Build a minimal 44-byte RIFF/WAVE PCM header with zero payload samples."""
    block_align = channels * (bits_per_sample // 8)
    byte_rate = sample_rate * block_align
    data_size = 0
    chunk_size = 36 + data_size
    return (
        b"RIFF"
        + struct.pack("<I", chunk_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        + b"data"
        + struct.pack("<I", data_size)
    )


def test_pyproject_pins_mcp_major_v1() -> None:
    pyproject_data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject_data["project"]["dependencies"]
    mcp_specs = [d for d in deps if d.startswith("mcp")]
    assert mcp_specs == ["mcp>=1.2.0,<2"]


@pytest.mark.parametrize(
    "payload",
    [
        "12-tet; touch /tmp/pwn",
        "12-tet && id",
        "$(whoami)",
        "12-tet | cat /etc/passwd",
        "",
        "   ",
        "unsupported-scale",
    ],
)
def test_generate_scala_tunings_rejects_untrusted_temperament(payload: str) -> None:
    with mock.patch.object(mcp_server.subprocess, "run") as mock_run:
        res = mcp_server.fl_generate_scala_tunings(payload)

    assert res.startswith("Error:")
    mock_run.assert_not_called()


def test_generate_scala_tunings_invokes_argv_without_shell(tmp_path: Path) -> None:
    fake_script = tmp_path / "scala_generator.py"
    fake_script.write_text("# stub\n", encoding="utf-8")
    tuning_dir = tmp_path / "Tuning"

    with (
        mock.patch.object(mcp_server, "SKILLS_SCRIPTS", tmp_path),
        mock.patch.object(mcp_server, "FL_TUNING", tuning_dir),
        mock.patch.object(mcp_server.subprocess, "run") as mock_run,
    ):
        res = mcp_server.fl_generate_scala_tunings(" 12-TET ")

    assert "compiled and deployed" in res
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert isinstance(args[0], list)
    assert args[0] == [
        sys.executable,
        str(fake_script),
        "--temperament",
        "12-tet",
        "--output-dir",
        str(tuning_dir),
    ]
    assert kwargs.get("shell", False) is False
    assert kwargs.get("check") is True
    assert kwargs.get("capture_output") is True


@pytest.mark.parametrize(
    "bad_name",
    [
        "../escape.py",
        "../../etc/passwd",
        "nested/script.py",
        "nested\\script.py",
        ".hidden.py",
        "foo..bar.py",
        "",
        "   ",
        "bad\x00name.py",
    ],
)
def test_deploy_piano_roll_script_rejects_traversal_and_bad_names(
    tmp_path: Path, bad_name: str
) -> None:
    pr_dir = tmp_path / "Piano roll scripts"
    valid_code = "def createScore():\n    pass\n"

    with mock.patch.object(mcp_server, "FL_PIANOROLL", pr_dir):
        res = mcp_server.fl_deploy_custom_piano_roll_script(bad_name, valid_code, overwrite=True)

    assert "Invalid" in res
    assert not pr_dir.exists()


def test_deploy_piano_roll_script_rejects_symlink_target(tmp_path: Path) -> None:
    pr_dir = tmp_path / "Piano roll scripts"
    pr_dir.mkdir(parents=True)
    outside = tmp_path / "outside.py"
    outside.write_text("# original\n", encoding="utf-8")
    symlink_target = pr_dir / "trap.py"
    symlink_target.symlink_to(outside)

    valid_code = "def createScore():\n    return 1\n"
    with mock.patch.object(mcp_server, "FL_PIANOROLL", pr_dir):
        res = mcp_server.fl_deploy_custom_piano_roll_script("trap.py", valid_code, overwrite=True)

    assert "symlink" in res.lower()
    assert outside.read_text(encoding="utf-8") == "# original\n"


def test_deploy_piano_roll_script_writes_confined_valid_script(tmp_path: Path) -> None:
    pr_dir = tmp_path / "Piano roll scripts"
    valid_code = "def createScore():\n    return None\n"

    with mock.patch.object(mcp_server, "FL_PIANOROLL", pr_dir):
        res = mcp_server.fl_deploy_custom_piano_roll_script("safe_compas", valid_code)

    deployed = pr_dir / "safe_compas.py"
    assert "Successfully deployed 'safe_compas.py'" in res
    assert deployed.is_file()
    assert deployed.read_text(encoding="utf-8") == valid_code


def test_binary_and_media_tools_reject_outside_paths_and_symlinks(tmp_path: Path) -> None:
    allowed_dir = tmp_path / "samples"
    allowed_dir.mkdir()
    outside_secret = tmp_path / "secret.wav"
    outside_secret.write_bytes(_minimal_wav_bytes())
    escape_link = allowed_dir / "escape.wav"
    escape_link.symlink_to(outside_secret)
    traversal_arg = str(allowed_dir / ".." / "secret.wav")

    with mock.patch.object(mcp_server, "SAMPLES_DIR", allowed_dir):
        for candidate in ("/etc/passwd", "../../etc/passwd", traversal_arg, str(escape_link)):
            hdr = mcp_server.fl_inspect_binary_header(candidate)
            spec = mcp_server.fl_analyze_audio_spectrum(candidate)
            decomp = mcp_server.fl_decompile_binary_preset(candidate)
            with mock.patch.object(mcp_server.subprocess, "run") as mock_open_run:
                open_res = mcp_server.fl_open_project_or_midi(candidate)
                mock_open_run.assert_not_called()

            assert "error" in hdr
            assert "error" in spec
            assert "error" in decomp
            assert "Access denied" in open_res


def test_inspect_binary_header_reads_valid_file_inside_patched_root(tmp_path: Path) -> None:
    allowed_dir = tmp_path / "samples"
    allowed_dir.mkdir()
    wav_file = allowed_dir / "synthetic_test.wav"
    wav_file.write_bytes(_minimal_wav_bytes(sample_rate=48000, channels=2, bits_per_sample=16))

    with mock.patch.object(mcp_server, "SAMPLES_DIR", allowed_dir):
        missing = mcp_server.fl_inspect_binary_header(str(allowed_dir / "missing.wav"))
        hdr = mcp_server.fl_inspect_binary_header(str(wav_file))

    assert "File does not exist" in missing["error"]
    assert hdr["file_type"] == "RIFF WAVE Audio Stem"
    assert hdr["sample_rate_hz"] == 48000
    assert hdr["bits_per_sample"] == 16
    assert hdr["channels"] == 2


def test_main_redirects_stdout_to_stderr_while_preserving_protocol_stream() -> None:
    protocol_buf = io.BytesIO()
    fake_stdout = io.TextIOWrapper(protocol_buf, encoding="utf-8")
    fake_stderr = io.StringIO()
    captured: dict[str, object] = {}

    @asynccontextmanager
    async def fake_stdio_server(stdin=None, stdout=None):
        captured["stdout_arg"] = stdout
        print("stray print must hit stderr")
        if stdout is not None:
            await stdout.write('{"jsonrpc":"2.0","id":1,"result":{}}\n')
            await stdout.flush()
        yield (None, None)

    async def fake_mcp_run(*args, **kwargs):
        return None

    with (
        mock.patch.object(sys, "stdout", fake_stdout),
        mock.patch.object(sys, "stderr", fake_stderr),
        mock.patch.object(mcp_server, "stdio_server", fake_stdio_server),
        mock.patch.object(mcp_server.mcp._mcp_server, "run", fake_mcp_run),
    ):
        mcp_server.main()
        # Simulate detach cleanup cleanly before closing fake_stdout
        assert sys.stdout is fake_stderr

    assert captured["stdout_arg"] is not None
    assert protocol_buf.getvalue() == b'{"jsonrpc":"2.0","id":1,"result":{}}\n'
    assert "stray print must hit stderr" in fake_stderr.getvalue()
    assert not protocol_buf.closed


def test_stdio_subprocess_emits_only_valid_jsonrpc_on_stdout() -> None:
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest-stdio-smoke", "version": "1.0.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "fl_generate_scala_tunings",
                "arguments": {"temperament": "12-tet; echo pwn"},
            },
        },
    ]
    stdin_payload = "\n".join(json.dumps(m) for m in messages) + "\n"

    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "mcp_server.py")],
        input=stdin_payload,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )

    assert proc.returncode == 0
    assert "Starting FL Studio SOTA MCP Server" in proc.stderr

    stdout_lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(stdout_lines) >= 2
    parsed = [json.loads(line) for line in stdout_lines]
    assert all(item.get("jsonrpc") == "2.0" for item in parsed)
    by_id = {item.get("id"): item for item in parsed if "id" in item}
    assert 1 in by_id and "result" in by_id[1]
    assert 2 in by_id and "Unsupported temperament" in json.dumps(by_id[2])
