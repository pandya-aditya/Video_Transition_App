# Prompt to give Codex

I want you to plan and build a proof of concept for **Match Cut**, a personal creative application that uses ML inference to discover satisfying transitions between videos.

Read `MATCH_CUT_DESIGN.md` in this workspace first. Treat it as a design brief with proposed defaults and open questions, not as a finalized specification. Follow applicable repository instructions. The existing folder name does not mean the project must focus on basketball.

My priorities are:

- A project that feels creative and personally interesting.
- Meaningful ML inference at the center of the experience.
- An end-to-end result that is easy to demonstrate visually.
- Minimal cost and no dependency on lengthy third-party access or approvals.
- Interesting, evidence-backed architecture decisions and documentation.

**Start by ideating the plan with me.** Ask all the questions in the brief's planning interview, in small, coherent batches of roughly 3–5 questions. Ask the creative purpose and first-workflow questions first. As the plan develops, cover footage, hardware, spending, inference, timing, output, evaluation, and completion criteria. Inspect facts you can learn safely yourself rather than making me retrieve them. Offer recommended answers with tradeoffs, and let me delegate decisions. Do not silently skip unresolved questions or substitute your preferences for my answers.

Keep an answer/decision log in `docs/planning-decisions.md`, marking each interview item answered, delegated, or unresolved. Do not wait for the whole interview before doing useful independent work: inspect the workspace, hardware, and available tooling, and research feasible models using current primary documentation. Do not access unrelated personal files, download large model weights, spend money, or upload footage while those choices remain unresolved.

Once the necessary answers are available, produce a concise implementation plan and record it in `docs/poc-plan.md`. Include:

1. The precise user workflow and agreed scope.
2. The architecture, data flow, and minimal storage/job design.
3. Model candidates, why they fit, and how you will compare them on my hardware.
4. A feasibility experiment that tests actual match usefulness before a large UI investment.
5. Milestones with observable completion criteria.
6. An evaluation approach, resource budgets, risks, and fallback options.
7. A short proposed demo sequence.

Explain the plan and proceed with implementation once the material choices are answered or explicitly delegated. I am authorizing the local POC build; do not require a separate routine approval after the planning interview. Ask follow-ups when a new consequential decision needs my input, while continuing independent work.

Prefer a small local architecture and real pretrained inference. Treat model choice and motion-analysis method as hypotheses to test. Separate cheap candidate retrieval from more expensive temporal ranking. Evaluate ordered transitions, account for source timestamps and preview/export alignment, and cache derived features with model/configuration versions.

The initial technical milestone should be a working pipeline from selected outgoing timestamp to retrieved candidates, temporal ranking, and playable previews. If the results are poor, investigate the failure and improve the matching approach before expanding the UI. Do not replace genuine inference with random or fabricated outputs, and clearly identify fixtures or precomputed examples.

Build toward an application that imports approved footage, shows processing progress, returns diverse matches, supports preview and cut-point adjustment, and exports a playable transition, subject to the scope we agree on. Include meaningful tests, real performance measurements, a small quality comparison, setup documentation, and a demo script. Record limitations honestly.

Keep me updated on findings and tradeoffs. Finish with the runnable result, how to use it, what you tested, measured limitations, and the most worthwhile next experiment.
