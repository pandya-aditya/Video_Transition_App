# Part 1 shot list: product showcase (about 75 s)

Example: **Eye close-up**, outgoing frame 50 (2.083 s, PTS 25600), **Appearance baseline**, collection *My targeted clips*. Every image and video below is real app output.

## Regenerate the media

With the app running (`./scripts/run.sh`):

```sh
.venv/bin/python scripts/demo_capture.py                                   # frames, preview + 1080p MP4, results.json
uv run --no-project --with playwright python scripts/demo_screenshots.py   # 1920x1080 UI stills + walkthrough.webm
uv run --no-project --with playwright python scripts/demo_render_html.py demo/part1/cards.html demo/part1/captures/cards
```

Everything lands in `demo/part1/captures/`, which is git-ignored because the iStock clips are not licensed for redistribution. Results can shift slightly between runs (for example, the engine time). `results.json` is the source of truth for any numbers you put on screen.

## Shots

| # | Time | Visual (file in `captures/`) | Narration |
| --- | --- | --- | --- |
| 1 | 0:00–0:05 | `cards/01-title.png` | "This is Match Cut, a tool I built that finds the next shot for a match cut." |
| 2 | 0:05–0:14 | `cards/02-problem.png` | "A great match cut, like a pupil becoming an eclipse, depends on shape and motion lining up at one exact frame. Editors usually find these from memory. I wanted to search for them." |
| 3 | 0:14–0:20 | `ui/01-library.png`, slow push-in on the clip row | "I import my footage. Everything is decoded, indexed and searched locally on this laptop." |
| 4 | 0:20–0:28 | `cards/03-pick-a-moment.png`, then `ui/03-outgoing-panel.png` | "I choose the last frame of the outgoing shot: the eye close-up, frame 50. The app tracks real decoded frames and timestamps, so I can step one frame at a time." |
| 5 | 0:28–0:34 | `ui/03b-mode-appearance-baseline.png` (zoom on the dropdown) | "For this example I use the appearance baseline, which ranks candidates purely by DINOv2 visual similarity." |
| 6 | 0:34–0:38 | `ui/04a-searching.png` | "Find the next shot." |
| 7 | 0:38–0:48 | `ui/04-results.png`, then `cards/04-appearance-baseline.png` | "About a second later I get six candidates, one per source clip. The top match is a solar eclipse, the same dark circle in a bright ring." |
| 8 | 0:48–0:54 | `ui/05-inference-evidence.png` | "The evidence panel shows every score, so the ranking is never a black box." |
| 9 | 0:54–1:04 | `ui/06-editor-preview.png`, then cut to full-screen `export-1080p.mp4` | "I pick it and get a frame-exact preview: two seconds on each side and a hard cut." |
| 10 | 1:04–1:10 | `cards/05-the-cut.png` | "The search also nudged the outgoing frame half a second later, to frame 62, where the pupil lines up best." |
| 11 | 1:10–1:15 | `ui/07-export.png` | "One click exports a 1080p MP4 that's ready to drop into an edit." |
| 12 | 1:15–1:20 | `cards/06-credits.png` | "Next: how it works, and how it's designed to scale." |

## Other assets

- `walkthrough.webm`: an unedited 1920x1080 recording of the scripted session. Use it as B-roll, or speed-ramp it as a single take.
- `ui/08-full-page.png`: a tall full-page capture, useful for a slow vertical pan.
- `preview.mp4` (360p) and `export-1080p.mp4`: the real renders of the pupil-to-eclipse cut.
- `candidate-NN.jpg` and `outgoing.jpg`: raw frames for custom overlays.

## Editing notes

- Play the export at least twice: once at normal speed, and once slowed to about 25% around the cut (2.0 s in).
- Keep the iStock watermark visible. Don't crop it out.
- Use the stated numbers from `results.json`, not round guesses. The appearance score is cosine similarity, not a probability.
