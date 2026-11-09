# Language adaptation

Stage: **tested_in_software**. Chamber simulation: pending. Hardware trials: pending.

Implementation: [persona.py](../../persona.py), `LANGUAGE_GUIDANCE` and `apply()`.
The guidance comes from the existing `opi4-chat-timing` language work; it is now
added only when the owner explicitly enables `BAYMAX_LANGUAGE_ADAPTATION_ENABLED=1`.
Setup exposes that same switch. Default: off.

The guidance tells Gemini to follow the person's language, switches and mixed
speech, without English internal system messages changing the conversation
language. It is prompt guidance, not proof of recognition or pronunciation
accuracy. Existing conversation data still goes to Gemini; this experiment adds
no new provider, capture stream, local language model or recording.

Software evidence includes the existing language evaluation work in
`opi4-chat-timing` and local regression checks of opt-in/default-off behavior and
preservation of the base persona. Earlier software runs, even on the Pi, do not
meet the chamber or physical-hardware stage. New gated integration needs the
same behavioral evaluation before promotion.

Next: chamber replay of single-language, switched-language and mixed-language
speech; then live speakers and actual room/peripheral conditions. Record
languages, model/version, source commit, expected/actual response language,
latency, misses, false switches and failures. No sim/hardware approval recorded.
