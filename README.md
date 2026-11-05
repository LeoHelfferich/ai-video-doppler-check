# Do AI videos lack airplane Doppler curves? A measurement

**Draft. Not yet published.**

In early November 2026 a rule went viral on X: *if a video has no low-frequency airplane Doppler curve, it is AI-generated.* Adam Holter ran an analysis of 120 AI videos ([thread](https://x.com/AdamHoltererer/status/2117703357536031204)) and wrote that "models do NOT generate airplane Dopplers". Pierre Beyssac shared it ([post](https://x.com/pbeyssac/status/2117974748281892884)), and the idea goes back to @0x45o's work geolocating videos through aircraft Doppler. Those threads inspired this repo. Holter's own figure already carries the caveat "Low-frequency curves alone do not establish a recorded aircraft". This repo tests the rule with a transparent detector, so anyone can check our numbers or prove them wrong.

## What we measure
1. **Detector** (`doppler/detect.py`): spectrogram from 20 to 250 Hz (about 2.7 Hz bins, 50 ms hop), spectral whitening, peak picking, and frame-to-frame ridge linking. A track counts as a *Doppler curve* when it
   - lasts at least 1.5 s,
   - falls monotonically (Spearman ρ ≤ −0.8, at least 70 % non-rising steps),
   - drops by at least 3 % from start to end, and
   - moves smoothly (jitter ≤ 0.4 Hz).
2. **Rule**: no Doppler curve means "AI", a curve means "real". We report the error counts against two baselines: "always real" and a coin flip.
3. **Physics check** (`doppler/physics.py`):
   - **Harmonic consistency.** A moving source shifts every harmonic by the same factor, so f₂/f₁ stays constant over time.
   - **Speed estimate.** v = c(R−1)/(R+1), where R = f_start/f_end.
   - **Fly-by model fit.** A straight-line pass, fitted against a linear fit.

Every parameter lives in `config.toml`.

## Data
- **Real audio:** [ESC-50](https://github.com/karolpiczak/ESC-50) (K. J. Piczak, *ESC: Dataset for Environmental Sound Classification*, ACM MM 2015). The clips come from freesound.org and are licensed **CC BY-NC 3.0**. This repo does **not** redistribute any audio. `make fetch` downloads the dataset from its original source.
  - `airplane`: all 40 clips.
  - No-plane classes: wind, rain, sea_waves, crickets, chirping_birds, engine, train, thunderstorm, using files 11 to 20 of each class in sorted order (80 clips). Files 1 to 10 of each class were used to tune the detector and are left out of the evaluation.
- **AI audio:** 20 text-to-video clips from Grok Imagine (10 s, 480p), 10 with an airplane in the prompt and 10 without. `ai_clips/manifest.csv` lists each clip's prompt, generation date, sha256 and audio stream info. The videos are not stored in git. Put them into `data/ai/` together with `ai_clips/prompts.tsv` and check them against the checksums.

## Reproduce
```
pip install -r requirements.txt   # also needs ffmpeg/ffprobe on PATH
make all                          # fetch ESC-50, rebuild manifest, compute everything
```
`make run` writes `results/per_clip.csv`, `results/summary.json` and `results/figures/*.png`. Set `DOPPLER_DATA=/path/to/data` to use another data directory.

## Limitations
- The sample is small: 20 AI clips from a single generator (Grok Imagine). This says nothing about Sora, Veo or others.
- The airplane was asked for in the prompt. This is a best case for the generator, not a sample of videos found in the wild.
- ESC-50 clips are 5 s long and many airplanes in them are distant. That is why only 10 of 40 real airplane clips show a detectable curve.
- The detector was tuned by hand on a small tuning split. Other thresholds give other numbers, so the config is the experiment.
- The speed estimate from R uses only part of the pass and underestimates v. The fly-by fit is ill-posed for short tracks.

## Licence
Code: MIT (see `LICENSE`). ESC-50 audio is CC BY-NC 3.0 (Piczak 2015, Freesound) and is not included. Figures contain spectrograms of ESC-50 audio, so they inherit CC BY-NC 3.0 and need attribution.
