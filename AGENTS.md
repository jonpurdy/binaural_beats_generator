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
  - Uses Web Audio API for stereo playback and in-browser MP3 export.
  - Uses `new.css` from CDN plus the Inter font stylesheet.
  - Embeds `lamejs` directly in the page so MP3 export works locally without server-side processing.
  - Current UI terminology uses `carrier frequency` and `beat` in the browser, while preserving the same underlying left/right channel mapping as the CLI.
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
  - carrier frequency dropdown with preset options plus an `Other` custom numeric input
  - beat dropdown with preset options plus an `Other` custom numeric input
  - duration input where `0` means infinite playback
  - volume control with default `100%`
  - play / stop controls
  - MP3 export control for finite-duration audio
  - live waveform canvas with a waveform-mode dropdown
  - live-updating controls that apply immediately during playback without requiring a manual restart
- Browser export behavior:
  - export runs entirely in the browser using embedded `lamejs`
  - export should preserve the same audio semantics as playback and the CLI
  - export should use the current carrier frequency, beat, duration, and volume settings
  - export is only available for finite durations; `0` still means infinite playback only
  - export should use the CLI-style default filename shape `DEVIATIONhz-LOW-DURATION.mp3`
  - export UI should provide visible in-progress feedback without causing the control row to jump around
- The current waveform behavior intentionally mirrors `binaural-old.html`:
  - use the analyser-based continuous-line visualizer as the source of truth
  - prefer `getFloatTimeDomainData()` for waveform sampling so the sine trace stays visually smooth on modern displays
  - use the same direct analyser sampling model rather than a buffered slowdown or history-scrolling visualizer unless the user explicitly asks for that
  - preserve the current combined and overlay modes
  - keep the waveform and center line at the current thin-stroke treatment
  - if you change waveform behavior, compare against `binaural-old.html` unless the user explicitly asks for a different visualizer model
  - keep the retina/high-DPI canvas support in `binaural.html`
- The browser app should keep the current compact single-page layout unless the user explicitly asks for a larger or more segmented layout.
- Maintain the same channel invariant as the CLI:
  - left = `low`
  - right = `low + deviation`
- When editing browser copy or controls, preserve the user-facing terminology shift:
  - `low` is presented as `carrier frequency`
  - `deviation` is presented as `beat`
- Keep the UI simple and semantic so it works well with `new.css`.
- Prefer stable form layouts that keep each control grouped with its related custom field instead of allowing optional fields to push unrelated controls out of alignment.

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
