# Public sample footage research

Updated 2026-10-19 (America/Toronto). The user authorized the agent to find reusable public samples and delegated collection sizing. No footage has been downloaded or visually inspected yet. Descriptions below are discovery leads, not validated matches.

## Working collection choice

Start with 12–16 mostly single-shot clips totaling approximately 2–4 minutes. Prefer 720p/1080p, retain native frame timing, and include a few portrait/square clips. Smaller/lower-resolution footage can be used if it supplies a valuable movement or failure case, with its resolution reported. Exporting it in a 1080p frame does not recover source detail.

Aim for several examples in each of these groups:

- Sports: jumps, reaches, turns, dribbling, running.
- Film: short self-contained shots from an openly licensed film, selected after inspecting actual scene boundaries.
- Everyday movement: walking, cycling, gestures, objects moving across frame, approximating the eventual personal-recording workflow.
- Distractors: similar colors or subjects with incompatible motion, different subject placement, and static scenes.

Choose clips for coverage of these categories before examining model rankings. Track the parent recording for every excerpt; all excerpts/encodes from one parent remain in the same tuning/evaluation group. Separate curated demo queries from held-out evaluation. Do not present a hand-picked successful pair as automatically discovered until the pipeline actually retrieves it.

## Candidate sources

| Candidate | Why inspect it | Current verification |
| --- | --- | --- |
| [Basketball shot types, PLOS supplement s001](https://commons.wikimedia.org/wiki/File:Basketball-Shot-Types-and-Shot-Success-in-Different-Levels-of-Competitive-Basketball-pone.0128885.s001.ogv) | Small full-HD example for shot posture; related supplements may offer alternate actions. | CC BY 4.0, Frane Erčulj and Erik Štrumbelj; [publisher article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0128885) confirms attribution licensing and supplemental videos. 2,312,988 bytes, 1920×1080, 3.921 seconds. Inspect actual action and context before selection. |
| [Basketball: Basic Types of Dribbling](https://commons.wikimedia.org/wiki/File:Basketball-Basic_Types_of_Dribbling.webm) | Repetitive movement and ball handling; potentially useful as a difficult timing case. | Uploader Mart570 identifies own work under CC BY-SA 3.0; ~59 seconds, 960×540, ~11.44 MB. Share-alike affects shared edited footage; prefer simpler licensed alternatives when available. |
| [Person 04 biking 01](https://commons.wikimedia.org/wiki/File:Person_04_biking_01.ogg) | Lateral subject motion and bicycle shape; short 720p source. | Commons imageinfo API confirms uploader Vctrung, own work, CC BY-SA 4.0, 8,082,066 bytes, 1280×720, 9.528 seconds. Playback pending. |
| [Vaulting gymnastics](https://commons.wikimedia.org/wiki/File:Vaulting-gymnastics.webm) | Jump trajectory, pose change, and square framing. | Uploader Lionel Aubert, own work, CC BY-SA 4.0, 2,960,809 bytes, 1080×1080, 8.08 seconds. Playback pending. |
| [Elzhana Taniyeva clubs handling](https://commons.wikimedia.org/wiki/File:Elzhana_Taniyeva_2024_Sofia_World_Cup_clubs_handling.webm) | Rotational movement and visible body pose; short full-HD source. | Commons imageinfo API confirms uploader FloweringDagwood, own work, CC BY 4.0, 2,269,409 bytes, 1920×1080, 6.621 seconds. Playback pending. |
| [Tears of Steel, official release on Commons](https://commons.wikimedia.org/wiki/File:Tears_of_Steel_in_4k_-_Official_Blender_Foundation_release.webm) | Actual live-action/CGI film shots for cross-domain matching. | Commons records CC BY 3.0 and attribution/change-notice requirements. The [creator's project page](https://mango.blender.org/about/) independently identifies CC BY 3.0. Prefer a small rendition or bounded excerpts; do not download the 4K master by default. |
| [Running water](https://commons.wikimedia.org/wiki/File:RunningWater.webm) | Everyday scene or motion distractor. | Uploader Patjos.scot provides CC0; only ~3.4 seconds, so likely a short-context diagnostic/distractor rather than a main demonstration source. |

## Sources screened out of the initial collection

Mixkit has suitable-looking sports and cinematic clips, but its [User Terms](https://mixkit.co/terms/) incorporate an [Acceptable Use Policy](https://help.elements.envato.com/hc/en-us/articles/31035788503321-Acceptable-Use-Policy) restricting unauthorized use for developing or enhancing AI/ML algorithms and a [Fair Use Policy](https://help.elements.envato.com/hc/en-us/articles/360000621743-Fair-Use-Policy) restricting automated access/downloads. Avoid relying on these assets for this reproducible inference-development experiment. No Mixkit footage was downloaded.

Pexels permits many creative uses, but its [Terms of Service](https://www.pexels.com/terms-of-service/) restrict unauthorized automated extraction, including for machine learning. Prefer sources with straightforward downloadable, explicitly licensed artifacts rather than introducing an account/API or access negotiation. No Pexels footage was downloaded.

These are source-selection decisions for this project, not a general legal conclusion about every use of either service.

## Before adding an asset

Record the creator, exact source page, license URL/version, selected rendition, original filename, byte size, SHA-256, source family, and any extraction/encoding changes. Probe dimensions, rotation, duration, actual PTS sequence, frame-rate behavior, and existing cuts. Review playback and remove unsuitable or unusable clips. Keep model results and user quality labels out of the acquisition metadata.

For the eventual download manifest, use only the selected small set and keep original media outside source control. Provide attribution with the demo and exported examples as required. The user accepted a 10 GB total working footprint, a 2 GB model-weight cap, and $0 paid services. Prefer CC BY/CC0 inputs for the initial demo; if using BY-SA, carry the required terms with shared adapted outputs.
