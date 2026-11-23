# Ember app link: messages, dashboard reminders, about the person

Connects the robot to the Ember app on tadashirobotics.com. Off unless the unit
has `BAYMAX_DEVICE_KEY` (and `EMBER_FAMILY_ENABLED` isn't `0`).

Every ~15 s `link.py` reads `GET /api/device/inbox` and reports through
`POST /api/device/sync` (15 rows of a kind per request, repeated until done):

| From the app | On the robot |
|---|---|
| A message | Kept in `toolkit_family.sqlite3`. At the next quiet moment (same rule as reminders) Ember reads it out, says who it's from and offers to reply. A reply is read back and sent only after the person confirms (`send_reply`). |
| A reminder, one-time or repeating | Added to the everyday reminder store, labelled "dashboard" with the sender's name. One the store refuses (e.g. a time in the past) is reported back with the reason. |
| A cancellation | Applied to that reminder, whether it was set on the app or by voice. |
| Notes about the person | Summarised by Gemini (`gemini-3.5-flash`, as session summaries are) into a short profile. It goes into Ember's instructions as `[ABOUT THE PERSON]` at every connection, is sent mid-conversation when it changes (at the next quiet moment, like messages: a note sent while Ember is replying could cut the reply off; on Gemini 3 not until that note is checked live, so the next session's instructions carry it), and goes back to the app so the owner sees exactly what Ember uses. |

What goes back up: reminder definitions, states and next times; each
announcement with its check-in answer; which messages were read out; replies;
the profile summary; the robot's timezone. **Transcripts are never sent.**
Message text, replies, reminder text and the notes do go to the app's database
(the owner's choice, 2026-10-22).

Offline, everything waits in the local databases and syncs when the link is
back. Tests: `tests/test_toolkit_family.py` (fake site) and
`tests/test_toolkit_reminder_repeats.py`.

Joe Kojima's quiet-profile guard (ee940fa) is extended in the OPI4 candidate:
quietness is checked again after loading the profile, and failed/cancelled or
deferred deliveries stay pending. An edit arriving during a send remains pending
for the next poll. This is a local best-effort quiet check, not an atomic
guarantee about remote generation. No additional data or provider is introduced.

## Settings from the app: microphone, camera, speaker volume

Ported from the LattePanda line (JoeKojima/Baymax `mvp-v10`, James). The app's Settings
tab is the only place these change; they arrive in the inbox and what is in force goes
back in every sync (`features/device_settings.py`, saved in `device_settings.json` under
`BAYMAX_DATA_DIR`, so a switch stays as set across restarts).

| Setting | On the robot |
|---|---|
| Microphone off | The capture callback drops every block first: nothing reaches Gemini, the recorder, voice recognition or the wake words. Ember can still speak. |
| Camera off | The camera thread releases the camera and closes the pose process: no fall detection, no MJPEG stream, no video to Gemini, no face recognition. On again, it starts over. |
| Volume, 10-100% | The whole speaker, through PipeWire (`wpctl` or `pactl`). Never silent: alerts must be heard. |

Ember says out loud who switched the camera or microphone off or on. With **both** off
Ember sends Gemini nothing, so Gemini closes the idle session about every 2 minutes.
Ember then stays disconnected until one is back on, or a reminder or family message is
due. A connection that can't resume gets the last two hours of this run's turns back
as a note (`session.recap`, RAM only). Tests: `tests/test_device_settings.py`,
`tests/test_session.py`, `tests/test_v10_runtime.py` (the camera thread, the mic
callback, and `run()` staying disconnected).

## Daily reports for the family

`reports.py`, ported with the settings above. Each evening at `report_time` (app
setting, default 20:00 robot time) Ember writes a short summary of the day's
conversations with Gemini Flash, with cautious concern flags (a clear or repeated sign,
never a passing remark; up to two quotes that must appear in the transcript). A strict
check after each conversation catches urgent things (self-harm, chest pain, a fall, a
scam in progress). "Write a report now" in the app asks for a preview.

- Data: raw transcript lines stay in a robot-only journal (`toolkit_reports.sqlite3`,
  pruned after 14 days). Only the reports and alerts go to the site, through this link.
  The transcript goes to Gemini Flash for the summary, as it already does for memory.
- Off: `reports` or `report_flags` in the app, not at the robot. With reports off
  nothing is journalled. Ember tells the person about the reports once.
- Tests: `tests/test_family_reports.py`.
