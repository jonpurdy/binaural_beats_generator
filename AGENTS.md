# AGENTS.md

This repository has two user-facing surfaces:

- `binaural_generator.py`: Python CLI that generates stereo binaural-beat MP3 files.
- `binaural.html`: single-file browser app for in-browser playback.

Use this guide when making changes so behavior stays consistent across both.

## Project Layout

- `binaural_generator.py`
  - Owns command-line generation, filename formatting, WAV staging, and MP3 encoding through `ffmpeg`.
  - Current audio synthesis is fixed to sine-wave output.
- `binaural.html`
  - Owns the self-serve browser experience.
  - Uses Web Audio API for stereo playback only.
  - Uses `new.css` from CDN plus the Inter font stylesheet.
- `README.md`
  - Documents the Python CLI usage and filename behavior.

## Python CLI Guidance

- Keep the CLI dependency-light. Prefer Python standard library plus the existing `ffmpeg` encode step.
- Treat left and right channel mapping as a core invariant:
  - left = `low`
  - right = `low + deviation`
- Preserve current filename conventions unless explicitly asked to change them:
  - default shape is `DEVIATIONhz-LOW-DURATION.mp3`
  - examples:
    - `2hz-150-10m.mp3`
    - `10hz-200-5m30s.mp3`
- Duration formatting rules for filenames:
  - whole minutes only: `5m`
  - minutes + seconds: `5m30s`
  - non-integer durations fall back to a seconds-based token
- If a default output filename already exists, append `-2`, `-3`, etc. before `.mp3`.
- If you change output naming, update both code and `README.md`.

## Web App Guidance

- Keep `binaural.html` self-contained in behavior. The page should remain a single-file app with inline JavaScript.
- Current browser features:
  - low frequency input
  - deviation input
  - duration input where `0` means infinite playback
  - volume control with default `100%`
  - play / stop controls
  - deviation guide block
- The browser app should stay waveform-free in the UI unless the user explicitly asks to reintroduce waveform options.
- Maintain the same channel invariant as the CLI:
  - left = `low`
  - right = `low + deviation`
- Keep the UI simple and semantic so it works well with `new.css`.

## Consistency Rules

- When changing audio semantics, update both the CLI and web app if the change applies to both surfaces.
- When changing naming or user-facing terminology, also update `README.md`.
- Do not introduce extra build steps, bundlers, or backend requirements unless explicitly requested.
- Avoid adding heavyweight Python or JavaScript dependencies for straightforward changes.

## Verification

- For Python changes:
  - run `python3 -m py_compile binaural_generator.py`
  - run a short generation smoke test when practical
- For HTML changes:
  - run a lightweight HTML parse check
  - inspect key IDs and script wiring after UI edits
- If you cannot do a browser runtime check, say so clearly.

## Common Commands

- Python compile check:
  - `python3 -m py_compile binaural_generator.py`
- Example short MP3 generation:
  - `python3 binaural_generator.py --low 200 --deviation 10 --duration 2`

