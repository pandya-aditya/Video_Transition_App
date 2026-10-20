# Local demo script

Start `./scripts/run.sh`, open http://127.0.0.1:8765. All media/inference is local. Use the small prepared public-source collection; attribution is in the footer and `samples-manifest.json`.

1. Show the source strip: sports, archival film, everyday movement and rotation. Explain the personal editing goal.
2. Select **Jump shot**. Pick a moment at or after 2.1 seconds; move one actual source frame with the arrow control. The timestamp and integer PTS are visible.
3. Click **Find the next shot**. Explain that DINOv2 retrieves visual/spatial neighbors, then ordered flow and available pose evidence rank them. Results are genuine model outputs, not hand-authored pairs.
4. Play a candidate. It is two seconds on each side, muted, with a hard cut. A similar still image is not automatically a good transition: watch the movement across the cut.
5. Adjust outgoing/incoming frames, rebuild the preview, toggle padding/crop, then export a 1080p MP4. Play the resulting file.
6. Switch to the appearance-only baseline, compare its suggestions, and open inference evidence. Show measured timings, never promise every query will be fast.
7. In the review section, watch blind A/B examples, save useful preferences, and show a miss. Explain that user labels will fine-tune a small part of the pretrained encoder; do not show an adapted comparison until a checkpoint has actually been trained and evaluated.

A successful final creative demo needs three user-approved exports and at least one keepable result in the top six for half of 8–10 queries. This script and technical exports alone do not satisfy that subjective gate. Record a walkthrough after reviewing the actual suggestions; retain source credits and share-alike obligations in the recording/export package.
