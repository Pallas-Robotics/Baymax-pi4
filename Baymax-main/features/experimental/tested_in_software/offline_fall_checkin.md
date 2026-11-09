# Offline fall check-ins

Stage: **tested_in_software**. Chamber simulation: pending. Hardware trials: pending.

Implementation and dependencies: [offline fall guide](../../toolkits/OFFLINE_FALL.md)
and [offline_fall.py](../../toolkits/offline_fall.py).
Owner setting: `BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED=1`; default off. Setup exposes
the same opt-in. The camera detector must also be enabled and dependencies prepared.

Fixed local prompts and Vosk accept explicit okay/fallen/help responses. Silence
and unclear speech remain unresolved; each 15-second listening window ends with
another prompt until an explicit answer or shutdown/failure. Confirming a fall
does not confirm safety. No caregiver/emergency contact is made by this feature.

On 2026-11-07, an isolated Orange Pi 4 Pro software run used real Vosk, synthetic
pose landmarks and synthesized speech. Five cases passed: okay, fallen, help,
negative safety and continuing silence. Python network connects were blocked in
that test process. Its synthetic data bypassed physical camera/mic/speaker paths;
therefore this is software testing, not the planned chamber simulation. The live
release and normal service were unchanged. Confidence remains >=0.85 per word;
duplicate ok/okay grammar spellings were removed after the test exposed a split.

Next: chamber fall/non-fall video through the actual camera plus audio replay
through the mic, including negatives, accents, echo, noise, disconnection and
reconnect. Then safe physical scenarios on named boards/peripherals. No
real-video accuracy, human-speech accuracy or hardware approval is recorded.
