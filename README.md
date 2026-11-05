# Do AI videos lack airplane Doppler curves?

**Leo Helfferich, 5 November 2026.**

A measurement of a rule that spread on X that month: *if a video has no low-frequency airplane Doppler curve, it is AI-generated.* [Adam Holter's thread](https://x.com/AdamHoltererer/status/2117703357536031204) on 120 AI videos says models do not generate airplane Dopplers. [Pierre Beyssac shared it](https://x.com/pbeyssac/status/2117974748281892884). The idea goes back to @0x45o's work geolocating videos through aircraft Doppler. Holter's own figure already says that a low-frequency curve alone does not establish a recorded aircraft. This repository is the detector, the counts, and the config, so the numbers can be checked or shown to be wrong.

The same results are laid out for reading in [`docs/index.html`](docs/index.html). To publish that page: GitHub → Settings → Pages → Deploy from a branch → `main` → `/docs`. The site is then `https://<user>.github.io/ai-video-doppler-check/`. After regenerating figures, `make pages` copies the three PNGs into `docs/figures/`.

## Result

The rule does not hold on this set.

| Set | Clips | Falling curve | Constant-ratio harmonics |
| --- | ---: | ---: | ---: |
| Grok Imagine, airplane asked for in the prompt | 10 | 4 | 1 |
| Grok Imagine, no airplane | 10 | 0 | 0 |
| ESC-50 airplane | 40 | 10 | 7 |
| ESC-50, no airplane, held out from tuning | 80 | 3 | 0 |

Read the way the rule reads ("no curve means AI"):

- 4 of 10 generated airplane clips would be called real.
- 30 of 40 real airplane clips would be called AI.
- 77 of 80 real clips with no airplane would be called AI. That is the rule's prediction for audio that has no airplane in it. A coin flip is the other baseline in `results/summary.json`.

The speed implied by f_start/f_end has median 15 m/s on the generated airplane curves, 20 m/s on the real airplane curves, and 5 m/s on the three real false positives. The fly-by fit has median 35 m/s on the generated curves and 67 m/s on 9 of the 10 real airplane curves. The remaining real airplane fit, and all three false positives, sat on the optimizer ceiling of 300 m/s. Those four are `v_fit_at_bound` and are left out of the median. The raw optimizer values stay in `results/per_clip.csv`.

Of the four generated hits, only `p01` has a harmonic pair whose frequency ratio stays put (about 2.00, coefficient of variation 0.006). `p10` clears the curve test with an implied speed of 9 m/s, under the 10 m/s floor in `config.toml`. That floor is a separate check and does not change the rule flag.

## What we measure

1. **Detector** (`doppler/detect.py`). Audio is decoded to mono at 44.1 kHz. The spectrogram runs from 20 to 250 Hz with a 50 ms hop. The FFT length is the next power of two at or above 44100/2.5, which is 32768, so the bin is **1.35 Hz**. Then spectral whitening, peak picking, and frame-to-frame ridge linking. A track counts as a Doppler curve when it
   - lasts at least 1.5 s,
   - falls monotonically (Spearman ρ ≤ −0.8, at least 70% non-rising steps),
   - drops by at least 3% from start to end, and
   - moves smoothly (jitter ≤ 0.4 Hz).
2. **Rule.** No curve means "AI", a curve means "real". The error counts are against two baselines: "always real", and a coin flip.
3. **Physics check** (`doppler/physics.py`).
   - **Harmonic consistency.** A moving source shifts every harmonic by the same factor, so f₂/f₁ stays constant over time.
   - **Speed estimate.** v = c(R−1)/(R+1), where R = f_start/f_end.
   - **Fly-by model fit.** A straight-line pass, fitted against a linear fit. Search range 0.5 to 300 m/s.

Every parameter lives in `config.toml`. `doppler/figures.py` draws the German post graphics (1080×1350). The page states the same numbers in English.

The panels are chosen by that file, so they are traceable:

- Hero: the longest generated airplane track, `p01.mp4`.
- Raster: the longest real airplane track, `1-43807-A-47.wav` (this is the real fit that sits on the 300 m/s ceiling), the first held-out wind clip `2-109371-A-16.wav`, the generated airplane hit with the highest fly-by R² after the hero (`p05.mp4`), and the first generated clip with no airplane (`n01.mp4`).

## Data

- **Real audio:** [ESC-50](https://github.com/karolpiczak/ESC-50) (K. J. Piczak, *ESC: Dataset for Environmental Sound Classification*, ACM MM 2015). The clips come from freesound.org and are licensed **CC BY-NC 3.0**. This repo does not redistribute any audio. `make fetch` downloads [commit `33c8ce9`](https://github.com/karolpiczak/ESC-50/commit/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6), which is the commit `master` pointed at on the measurement date. That commit only edits the upstream README relative to its parent. An older unpack at `data/ESC-50-master` is still picked up.
  - `airplane`: all 40 clips.
  - No-plane classes: wind, rain, sea_waves, crickets, chirping_birds, engine, train, thunderstorm, using files 11 to 20 of each class in sorted order (80 clips). Files 1 to 10 of each class were used to tune the detector and are left out of the evaluation.
- **AI audio:** 20 text-to-video clips from Grok Imagine (10 s, 480p), 10 with an airplane in the prompt and 10 without. `ai_clips/manifest.csv` lists each clip's prompt, generation date, sha256, and audio stream. `ai_clips/prompts.tsv` is the prompt list. The videos are not stored in git. Put the mp4 files in `data/ai/` under those names. `make verify` checks them against the checksums, and `make run` refuses to start if they differ.

## Reproduce

Python 3.11 or newer, plus `ffmpeg` and `ffprobe` on `PATH`.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# place the 20 mp4s in data/ai/, names as in ai_clips/manifest.csv
make all
```

`make all` downloads ESC-50 and writes `results/per_clip.csv`, `results/summary.json`, and `results/figures/`. `make manifest` rebuilds `ai_clips/manifest.csv` when the clips change, and keeps `generated_on` for a file that is already listed. Set `DOPPLER_DATA=/path/to/data` to use another data directory.

Checks that do not need the audio:

```
python -m unittest discover -s tests -v
```

## Limitations

- The sample is small: 20 AI clips from a single generator (Grok Imagine). This says nothing about Sora, Veo, or others.
- The airplane was asked for in the prompt. This is a best case for the generator, not a sample of videos found in the wild.
- ESC-50 clips are 5 s long and many airplanes in them are distant. That is why only 10 of 40 real airplane clips show a detectable curve.
- The detector was tuned by hand on a small tuning split. Other thresholds give other numbers, so the config is the experiment.
- The speed estimate from R uses only part of the pass and underestimates v. The fly-by fit is ill-posed for short tracks. In this run, four fits sat on the 300 m/s search limit and are not reported as speeds.

## Licence

Code: MIT (see `LICENSE`). ESC-50 audio is CC BY-NC 3.0 (Piczak 2015, Freesound) and is not included. Figures that contain ESC-50 spectrograms inherit CC BY-NC 3.0 and need attribution. The attribution line is on the figures.

## Cite

See `CITATION.cff`. Add `repository-code` there once the GitHub remote exists.
