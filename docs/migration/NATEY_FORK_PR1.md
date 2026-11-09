# Archived draft PR: NateyKim/Baymax #1

This is a historical record, not current release evidence. The original fork is being retired in favor of Pallas-Robotics/Baymax-pi4. The reconciliation draft supersedes this review request.

- Title: Add opt-in offline fall check-ins and staged contribution protocol
- Author: NateyKim
- Original state: open; draft: True
- Head: `6eb21db2551c458f373752b1825746680e924065` (`archive/natey/offline-fall-checkin`)
- Base: `6056177f18bdd2df7f7f082fb41890dcef9df50a`
- Created: 2026-11-07T09:55:41Z
- Last updated: 2026-11-07T09:57:21Z

## Original description

Ember needs a clear contribution/release chain and owner opt-ins for experimental behavior. This adds local Vosk fall check-ins, independent language/offline feature opt-ins, and a documented software → chamber → physical → lead-approved release route. It preserves ordinary deploy/channel selection and does not promote this work to devices.

The README, CONTRIBUTING, AGENTS, PR template and testing protocol now state which repository/branch to use, who reviews/promotes, and what evidence is required. Graphify indexes those rules first, the agent query prints the protocol before code context, and CI rejects a stale or missing protocol map. The SD settings menu offers five named modes, preserving custom/current choices. Generated Graphify exports are marked as generated; caches and private runtime data are excluded.

Language adaptation and offline fall check-ins remain software-tested only. Their controls default off; existing explicit owner opt-ins persist. Local fall prompts accept explicit okay/fallen/help answers and repeat after 15-second listening windows while unresolved. No caregiver/emergency contact is made. Ordinary connected Gemini data flows and existing session recording remain in effect; this adds no local LLM or extra capture stream.

Validation on Windows / Python 3.12.15:
- `check_release.py`: core 548 tests, PASS, 7 platform/dependency skips; toolkit 263 tests, PASS.
- Graphify gate and eight regression checks: PASS. Protocol-first query exercised against the generated 1,713-node map.
- SD-image/configuration suite: 39 tests, PASS, 10 platform-dependent skips. Owner menu shell syntax and `git diff --check` checked.
- Corrected existing cross-platform test assumptions: portable cache path comparisons, explicit skips for unavailable Windows symlink/open-file fixture behavior, and bounded asynchronous TCP viewer cleanup. These do not assert physical-device success.
- Earlier isolated OPI4 software trial: five synthetic-landmark/synthesized-speech cases passed with real Vosk and Python network connections denied. This is software injection evidence, not chamber or physical validation.

Pending before release: review current GitHub CI; chamber/physical audio-video trials, board performance, real response accuracy, offline/reconnect/media scenarios, rollback/data compatibility and lead approval. The rollout checklist records automatic stable-sync PRs, required branch protection, owner health/version UI and fleet migration as pending. Manual CI runs were observed on the initial channels; automatic push-run records had not appeared during setup, so automatic execution is not claimed verified.

This is a draft for review. Do not merge/promote it on the strength of software tests alone. Runtime entry points, base Gemini models, sample rates and existing source/data locations are retained. Local speech needs prepared Vosk assets and espeak-ng; source control includes no model downloads, credentials or recordings.
