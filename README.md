# Binaural Generator

Small Python CLI for generating stereo binaural beat MP3 files.

## Requirements

- Python 3
- `ffmpeg` available on `PATH`

## Usage

```bash
python3 binaural_generator.py --low 200 --deviation 10 --duration 300 --output out.mp3
```

This produces:

- left channel: `200 Hz`
- right channel: `210 Hz`
- MP3 output encoded at `320 kbps`

If `--output` is omitted, the script writes a predictable filename such as:

```text
150-10hz-300s.mp3
```

If that filename already exists, the script appends a numeric suffix:

```text
150-10hz-300s-2.mp3
```

## Options

- `--low` / `--base`: base frequency for the left channel
- `--deviation`: amount added to the right channel
- `--duration`: output length in seconds
- `--sample-rate`: sample rate in Hz, default `44100`
- `--output`: output MP3 path
