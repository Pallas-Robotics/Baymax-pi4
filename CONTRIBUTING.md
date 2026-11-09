# Contributing to Ember

Start with the [working protocol](docs/WORKING_PROTOCOL.md). Humans and LLMs use
the same branch, evidence and review rules.

- Published authority: **Pallas-Robotics/Baymax-pi4**. Runtime owners use `deploy`; a draft PR
  is for review/bench checkout and is not a deployment recommendation.
- Branch from this fork's current `main`; push a focused feature branch here and
  open a draft PR targeting `main`. Never push feature work into channel branches.
- Run `python devops/graphify/query.py "<question>"` before architecture/code work.
- Run the [testing protocol](Baymax-main/TESTING_PROTOCOL.md), including software,
  chamber simulation and physical stages. Record failures/skips honestly.
- Keep experiments off unless the owner opts in. Preserve deployed behavior,
  preferences and data compatibility; test changes before asking for promotion.
- Update feature evidence, CHANGELOG, documentation and Graphify. Open a PR with
  concise results and pending work; the lead approves deployment separately.

The PR template describes the evidence expected. Channel synchronization,
required-review protection and fleet recovery work must not be assumed complete
because channel branches exist. Read [update policy](docs/UPDATE_CHANNELS.md).
