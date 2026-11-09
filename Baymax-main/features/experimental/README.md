# Experimental features

Experimental features are **off by default**. The device owner opts in separately
to each feature in Ember Setup, saves, and restarts Ember. A test-channel choice
does not enable experiments. Existing explicit per-feature settings are retained.

The folders record the highest completed testing stage; implementation stays at
its established import path. Promoting an entry never requires moving runtime
code. `FEATURES` in `__init__.py` supplies the stage and owner setting to Setup.

| Folder | Meaning |
|---|---|
| [tested_in_software](tested_in_software/README.md) | Source tests, synthetic inputs and direct data injection have been exercised; chamber and hardware validation remain pending |
| [tested_in_sim](tested_in_sim/README.md) | The chamber replayed known video and audio through Ember's real capture paths, with recorded expected outcomes |
| [tested_in_hardware](tested_in_hardware/README.md) | Controlled real-world physical trials passed on a named board/peripheral configuration |

Language adaptation and offline fall check-ins are currently **tested in
software only**. Running synthetic landmarks/PCM directly on an Orange Pi is
software evidence, not chamber simulation or physical sensor validation.

## Owner opt-in

In Setup, use the **Experimental features** checkboxes. For managed configuration,
the corresponding private `.env` settings are:

```dotenv
BAYMAX_LANGUAGE_ADAPTATION_ENABLED=0
BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED=0
```

Set the individual value to `1` to opt in. No other value enables it. The language
switch controls the added language-adaptation instructions; Gemini's underlying
multilingual ability is unchanged. The offline switch controls local fall
check-ins and does not itself enable camera fall detection. Follow that feature's
setup/dependency guide too. No imports start capture, providers or workers.

## Advancement policy

For every stage, record the exact source commit, tester/date, board/OS, model and
peripheral versions, scenarios, expected/actual outcomes, failures and evidence.
Maintain one entry per experiment; update its stage in `FEATURES`, move its entry
to the next folder, and update Setup's stage wording. An unsuccessful test does
not count as completed. A behavior-changing revision needs new evidence for the
affected stage; old results do not automatically validate new code.

The chamber stage should cover distance, lighting, occlusion, noise, speech
variants, speaker echo, lost connectivity, repeated prompts, reconnect and stop.
Hardware trials add actual cameras/microphones/speakers, placement, thermals,
resource use and safe real-world scenarios on each supported board. Do not ask a
person to perform an unsafe fall. Hardware-tested is not automatic deployment
approval: the lead approves a board-specific release separately.

See [update channels and repository policy](../../../docs/UPDATE_CHANNELS.md).
