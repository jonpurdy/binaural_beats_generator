#!/usr/bin/env python3

import argparse
import array
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

DEFAULT_DURATION_SECONDS = 300.0
DEFAULT_SAMPLE_RATE = 44_100
DEFAULT_AMPLITUDE = 0.8
PCM_MAX = 32767


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a stereo binaural beat MP3."
    )
    parser.add_argument(
        "--low",
        "--base",
        dest="low",
        type=positive_float,
        required=True,
        help="Base frequency in Hz for the left channel.",
    )
    parser.add_argument(
        "--deviation",
        type=positive_float,
        required=True,
        help="Deviation in Hz added to the right channel.",
    )
    parser.add_argument(
        "--duration",
        type=positive_float,
        default=DEFAULT_DURATION_SECONDS,
        help=f"Output duration in seconds. Default: {DEFAULT_DURATION_SECONDS:g}.",
    )
    parser.add_argument(
        "--sample-rate",
        type=positive_int,
        default=DEFAULT_SAMPLE_RATE,
        help=f"Sample rate in Hz. Default: {DEFAULT_SAMPLE_RATE}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output MP3 path. Defaults to an auto-generated filename.",
    )
    return parser


def default_output_path(
    low: float,
    deviation: float,
    duration: float,
) -> Path:
    low_text = format_number(low)
    deviation_text = format_number(deviation)
    duration_text = format_duration_for_filename(duration)
    return Path(f"{deviation_text}hz-{low_text}-{duration_text}.mp3")


def next_available_output_path(path: Path) -> Path:
    if not path.exists():
        return path

    suffix = path.suffix
    stem = path.stem
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value).replace(".", "_")


def format_duration_for_filename(duration: float) -> str:
    if duration.is_integer():
        total_seconds = int(duration)
        minutes, seconds = divmod(total_seconds, 60)
        parts = []
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0:
            parts.append(f"{seconds}s")
        if not parts:
            parts.append("0s")
        return "".join(parts)

    return f"{format_number(duration)}s"


def generate_wave_samples(
    frequency: float,
    duration: float,
    sample_rate: int,
    amplitude: float,
) -> array.array:
    total_samples = int(duration * sample_rate)
    samples = array.array("h")

    for index in range(total_samples):
        cycle_position = (frequency * index / sample_rate) % 1.0
        sample_value = math.sin(2.0 * math.pi * cycle_position)
        sample = int(PCM_MAX * amplitude * sample_value)
        samples.append(sample)

    return samples


def interleave_stereo(left: array.array, right: array.array) -> array.array:
    if len(left) != len(right):
        raise ValueError("left and right channels must have the same length")

    frames = array.array("h")
    for left_sample, right_sample in zip(left, right):
        frames.append(left_sample)
        frames.append(right_sample)
    return frames


def write_wave_file(path: Path, frames: array.array, sample_rate: int) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames.tobytes())


def encode_mp3(wav_path: Path, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg is required to encode MP3 output but was not found on PATH."
        )

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(wav_path),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "320k",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"ffmpeg failed to encode MP3: {stderr}") from exc


def generate_binaural_mp3(
    low: float,
    deviation: float,
    duration: float,
    sample_rate: int,
    output_path: Path,
) -> None:
    right_frequency = low + deviation
    left_samples = generate_wave_samples(
        frequency=low,
        duration=duration,
        sample_rate=sample_rate,
        amplitude=DEFAULT_AMPLITUDE,
    )
    right_samples = generate_wave_samples(
        frequency=right_frequency,
        duration=duration,
        sample_rate=sample_rate,
        amplitude=DEFAULT_AMPLITUDE,
    )
    stereo_frames = interleave_stereo(left_samples, right_samples)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = Path(tmp_dir) / "intermediate.wav"
        write_wave_file(wav_path, stereo_frames, sample_rate)
        encode_mp3(wav_path, output_path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_path = args.output or next_available_output_path(
        default_output_path(
            args.low,
            args.deviation,
            args.duration,
        )
    )

    try:
        generate_binaural_mp3(
            low=args.low,
            deviation=args.deviation,
            duration=args.duration,
            sample_rate=args.sample_rate,
            output_path=output_path,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {output_path}")
    print(f"Left channel: {format_number(args.low)} Hz")
    print(f"Right channel: {format_number(args.low + args.deviation)} Hz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
