#!/usr/bin/env python3

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate whether a stereo audio file contains a binaural beat."
    )
    parser.add_argument(
        "inputs",
        metavar="input",
        nargs="+",
        type=Path,
        help="One or more audio files to inspect.",
    )
    return parser


def decode_to_wav_path(input_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if input_path.suffix.lower() == ".wav":
        return input_path, None

    tmp_dir = tempfile.TemporaryDirectory()
    wav_path = Path(tmp_dir.name) / "decoded.wav"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(wav_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        tmp_dir.cleanup()
        raise RuntimeError("ffmpeg is required to verify non-WAV files.") from exc
    except subprocess.CalledProcessError as exc:
        tmp_dir.cleanup()
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"ffmpeg failed to decode audio: {stderr}") from exc

    return wav_path, tmp_dir


def load_stereo_channels(path: Path) -> tuple[int, np.ndarray, np.ndarray]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()
        frames = wav_file.readframes(frame_count)

    if channels != 2:
        raise RuntimeError(f"expected a stereo file, found {channels} channel(s)")

    dtype_by_width = {
        1: np.uint8,
        2: np.int16,
        4: np.int32,
    }
    dtype = dtype_by_width.get(sample_width)
    if dtype is None:
        raise RuntimeError(f"unsupported sample width: {sample_width} bytes")

    data = np.frombuffer(frames, dtype=dtype)
    if sample_width == 1:
        data = data.astype(np.int16) - 128

    data = data.reshape(-1, channels)
    left = data[:, 0].astype(np.float64)
    right = data[:, 1].astype(np.float64)
    return sample_rate, left, right


def dominant_frequency(samples: np.ndarray, sample_rate: int) -> float:
    # Remove DC offset and apply a Hann window so the peak estimate is steadier.
    centered = samples - np.mean(samples)
    windowed = centered * np.hanning(len(centered))
    fft = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(len(windowed), 1 / sample_rate)
    return float(freqs[np.argmax(np.abs(fft))])


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    had_error = False

    for index, input_path in enumerate(args.inputs):
        if index > 0:
            print()

        print(f"File:  {input_path}")

        if not input_path.exists():
            print(f"Error: file not found: {input_path}", file=sys.stderr)
            had_error = True
            continue

        temp_dir = None
        try:
            wav_path, temp_dir = decode_to_wav_path(input_path)
            sample_rate, left, right = load_stereo_channels(wav_path)
            left_freq = dominant_frequency(left, sample_rate)
            right_freq = dominant_frequency(right, sample_rate)
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            had_error = True
            continue
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

        beat = abs(right_freq - left_freq)

        print(f"Left:  {left_freq:.2f} Hz")
        print(f"Right: {right_freq:.2f} Hz")
        print(f"Beat:  {beat:.2f} Hz")

    print("Note: this checks for dominant-frequency separation between channels.")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
