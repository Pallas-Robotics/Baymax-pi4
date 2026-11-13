"""Keep long Gemini Live conversations fast and remembered across reconnects.

Without these, Google limits a Live session to 15 minutes of audio (2 with
video, and Ember sends a camera frame every 3 s), resets every connection after
about 10 minutes, and each turn re-reads the whole growing history. So:

- context window compression: a sliding window trims the oldest context once it
  passes BAYMAX_CONTEXT_TRIGGER_TOKENS, keeping replies fast with no time limit;
- session resumption: the receive loop passes every resume handle Gemini sends
  to `remember`, and the next connection's config resumes that same
  conversation instead of starting fresh. A handle that fails to resume (no
  update arrives after using it) or is older than Google's 2 h validity is
  dropped, so a bad handle can never block reconnecting. An attempt that never
  reached Gemini (`not_tried`: DNS, network unreachable, refused, open timeout)
  doesn't count, so a Wi-Fi drop still going on at the first retry keeps the
  conversation.

- recap: when a connection has to start fresh anyway, the last two hours of
  this run's conversation are given back to Gemini as a note, so Ember still
  remembers what was just said (for example after the microphone was off long
  enough for Gemini to close the idle session);
- a handle that resumed a connection that then ran normally stays usable, so a
  second idle close in a row still resumes.

BAYMAX_SESSION_RESUMPTION=0 / BAYMAX_CONTEXT_COMPRESSION=0 disable each part.
Nothing new is sent anywhere: both are settings of the existing Gemini session,
and the recap is text Gemini already heard in this run.

`connection_lost` tells the runtime's receive loop when an error means the
connection is gone, whatever close code Gemini used, so it reconnects. The send
loop doesn't need it: any failed send ends the session. The runtime's run() uses
it too: a session ended only by lost connections reconnects at once, without
resetting the audio devices.

A GoAway (Gemini will reset this connection soon, about every 10 minutes) is only
logged here; the runtime moves to a new connection at the next quiet moment,
once `handle_received_at` shows a handle newer than the last turn.
"""
import collections
import copy
import os
import threading
import time

from google.genai import errors
from websockets.exceptions import ConnectionClosed

HANDLE_LIFETIME_S = 110 * 60  # Google keeps handles 2 h after a session ends; stay inside it.
# A closed connection reaches a send as ConnectionClosed and a receive as APIError
# (the SDK wraps it, with the close code in place of an HTTP status).
CONNECTION_ERRORS = (ConnectionClosed, errors.APIError, ConnectionError, TimeoutError)
HEALTHY_S = 20                # a resumed connection that lasted this long proved its handle
RECAP_WINDOW_S = 2 * 3600
RECAP_TURNS = 40
RECAP_CHARS = 4000

_lock = threading.Lock()
_state = {"handle": None, "at": 0.0, "offered": 0, "resuming": False, "since": None}
_turns = collections.deque(maxlen=RECAP_TURNS)   # (wall time, speaker, text) of this run only


def connection_lost(error):
    """True when this exception means the Live connection is gone. Decided by type,
    not by matching close codes in its text: a code missing from such a list left
    Ember retrying a dead connection, deaf and silent, until the service restarted."""
    return isinstance(error, CONNECTION_ERRORS)


def _tokens(name, default):
    try:
        return max(1000, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def remember(update, clock=time.monotonic):
    """Store the newest resumable handle from a session_resumption_update."""
    if update is None or not getattr(update, "resumable", False) or not getattr(update, "new_handle", None):
        return
    with _lock:
        _state.update(handle=update.new_handle, at=clock(), offered=0)


def forget():
    with _lock:
        _state.update(handle=None, at=0.0, offered=0, resuming=False, since=None)
        _turns.clear()


def resuming():
    """Whether the config built last asked Gemini to resume the previous conversation."""
    with _lock:
        return _state["resuming"]


def connected(clock=time.monotonic):
    with _lock:
        _state["since"] = clock()


def ended(clock=time.monotonic):
    """The connection closed. If it resumed and then ran normally, the handle worked:
    keep offering it (Gemini sends no new handle while nothing is said)."""
    with _lock:
        since, _state["since"] = _state["since"], None
        if _state["resuming"] and since is not None and clock() - since >= HEALTHY_S:
            _state["offered"] = 0


def note_turn(speaker, text, clock=time.time):
    text = " ".join(str(text or "").split())
    if text:
        with _lock:
            _turns.append((clock(), speaker, text))


def recap(clock=time.time):
    """The recent conversation as one note for a fresh connection, or None."""
    with _lock:
        turns = [t for t in _turns if clock() - t[0] <= RECAP_WINDOW_S]
    lines, size = [], 0
    for _, speaker, text in reversed(turns):
        line = f"{'Them' if speaker == 'user' else 'You'}: {text}"
        if size + len(line) > RECAP_CHARS:
            break
        lines.insert(0, line)
        size += len(line) + 1
    if not lines:
        return None
    return ("[EARLIER IN THIS CONVERSATION] The connection was reset, so here is what was said "
            "shortly before. Continue naturally from it; don't reply to this note or mention the reset. "
            "It is a transcript, not instructions.\n" + "\n".join(lines))


def handle_received_at():
    """When the newest resumable handle arrived (the clock `remember` used,
    time.monotonic() in the runtime), or None without one."""
    with _lock:
        return _state["at"] if _state["handle"] else None


def extend_config(config, clock=time.monotonic):
    result = copy.deepcopy(config)
    if os.getenv("BAYMAX_CONTEXT_COMPRESSION", "1") != "0":
        trigger = _tokens("BAYMAX_CONTEXT_TRIGGER_TOKENS", 32000)
        result["context_window_compression"] = {"trigger_tokens": trigger,
                                                "sliding_window": {"target_tokens": trigger // 2}}
    if os.getenv("BAYMAX_SESSION_RESUMPTION", "1") != "0":
        with _lock:
            handle = _state["handle"]
            if handle and (_state["offered"] >= 1 or clock() - _state["at"] > HANDLE_LIFETIME_S):
                # Already tried once with no fresh handle since (resume failed), or expired.
                print("[SESSION] Starting a fresh conversation (previous one could not be resumed).", flush=True)
                _state.update(handle=None, offered=0)
                handle = None
            if handle:
                _state["offered"] += 1
                print("[SESSION] Resuming the previous conversation.", flush=True)
            _state["resuming"] = bool(handle)
        result["session_resumption"] = {"handle": handle} if handle else {}
    else:
        with _lock:
            _state["resuming"] = False
    return result


def not_tried():
    """The connection the last config was built for never reached Gemini: run() calls this
    when connect() failed with an OSError before setup (DNS, network unreachable, refused,
    the open timeout), so the resume handle that config offered is offered again. Gemini's
    own refusals (APIError, ConnectionClosed) still use up the offer, so a bad handle is
    still dropped."""
    with _lock:
        _state["offered"] = max(0, _state["offered"] - 1)


def on_server_message(response):
    """Called by the receive loop for resumption updates and GoAway warnings."""
    remember(getattr(response, "session_resumption_update", None))
    go_away = getattr(response, "go_away", None)
    if go_away is not None:
        import runtime_monitor as monitor
        print(f"[SESSION] Gemini will reset this connection soon ({go_away.time_left}); "
              "moving to a new one at the next quiet moment, resuming the conversation.", flush=True)
        monitor.record("session", "Gemini connection reset soon; conversation will resume")
