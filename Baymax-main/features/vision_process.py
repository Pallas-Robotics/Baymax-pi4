"""Bounded camera inference in a child process, using the OS scheduler.

Only frames go in and plain landmarks come back. A hung model is stopped by
the watchdog; callers may restart CPU pose without blocking camera delivery.
The loading_model signal gives an explicitly selected CPU backend time to load.
"""
import collections
import os
import pickle
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Point = collections.namedtuple("Point", "x y z visibility presence")


def points(landmarks):
    """MediaPipe landmarks as plain tuples (x/y/z/visibility read like the originals)."""
    if landmarks is None:
        return None
    return [Point(p.x, p.y, p.z, p.visibility or 0.0, p.presence or 0.0) for p in landmarks]


_send = None   # in a vision child: main()'s reply, for loading_model()


def loading_model():
    """Called by a model in a vision child just before it loads another model during a
    frame (features.pose.backend.FallbackBackend switching from ONNX to MediaPipe:
    the ONNX child never imported MediaPipe, which can take seconds on the board). Remote
    then gives that call the start's limit (start_timeout) instead of a frame's, so the
    watchdog does not stop a child that is recovering. Does nothing anywhere else
    (benchmark.py, validate.py and tests run backends in their own process)."""
    if _send is not None:
        _send("loading", None)


class Stopped(RuntimeError):
    """The vision process is gone: it died, hung and was stopped by the watchdog, or sent
    an unreadable reply. Every later call fails the same way, so close the Remote (or
    start another). A model's own error in a frame is a plain RuntimeError instead, and
    the child goes on."""


class Remote:
    """`factory()` built and run in a child process, with the same detect(frame) call.

    A call still waiting for its reply after `timeout` seconds (`start_timeout` while the
    model loads, also when it says so mid-frame: loading_model) kills the child and raises
    Stopped (a RuntimeError), as if the child had died."""
    timeout = 5.0          # per frame; bounded per-frame inference wait
    start_timeout = 60.0   # imports and CPU model loading, at
                           # the start or mid-frame (loading_model); callers download models
                           # before starting the child
    tick = 0.5             # how often the watchdog looks
    deadline = None        # monotonic time the call in progress must be answered by
    expired = False        # the watchdog killed the child during the call in progress

    def __init__(self, factory, timeout=None):
        self.lock = threading.Lock()
        if timeout is not None:
            self.timeout = timeout
        self.closed = threading.Event()
        self.child = subprocess.Popen([sys.executable, "-m", "features.vision_process"], cwd=ROOT,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        threading.Thread(target=self._watch, name="vision-watchdog", daemon=True).start()
        try:
            self.device = self._call(factory, self.start_timeout)
        except Exception:
            self.close()
            raise

    def _watch(self):
        # Reads one attribute twice a second; a frame takes no lock or timer for it. Read
        # without a lock, a deadline can be acted on just after its call was answered, but
        # only for a call that took within a few ms of its timeout: the next call then fails
        # like a stopped process, and the caller restarts the child the same way.
        while not self.closed.wait(self.tick):
            deadline = self.deadline
            if deadline is not None and time.monotonic() > deadline:
                self.expired = True
                self.cancel()       # its pipes close, so the waiting call gets EOF or EPIPE

    def _call(self, item, timeout=None):
        limit = self.timeout if timeout is None else timeout
        with self.lock:
            self.expired = False
            self.deadline = time.monotonic() + limit
            try:
                pickle.dump(item, self.child.stdin, protocol=pickle.HIGHEST_PROTOCOL)
                self.child.stdin.flush()
                kind, value = pickle.load(self.child.stdout)
                while kind == "loading":    # loading_model(): a load inside this call, not a frame
                    limit = self.start_timeout
                    self.deadline = time.monotonic() + limit
                    kind, value = pickle.load(self.child.stdout)
            except (EOFError, OSError, pickle.UnpicklingError) as error:
                if self.expired:
                    raise Stopped(f"vision process hung: no reply in {limit:g} s, so it was stopped") from error
                raise Stopped(f"vision process stopped ({error or 'exited'})") from error
            except Exception as error:
                # Anything else on the reply pipe (e.g. text, which unpickles as a ValueError):
                # replies are out of step from here on, so callers close it as a stopped process.
                raise Stopped(f"vision process sent an unreadable reply ({type(error).__name__}: {error})") \
                    from error
            finally:
                self.deadline = None
        if kind == "error":
            raise RuntimeError(value)
        return value

    def detect(self, frame):
        landmarks, self.device = self._call(frame)
        return landmarks

    def cancel(self):
        """Kill the child now (the watchdog's way out of a hung call)."""
        if self.child.poll() is None:
            self.child.kill()

    def close(self):
        self.closed.set()             # the watchdog ends
        try:
            self.child.stdin.close()  # The child exits at end of input.
        except OSError:
            pass
        try:
            self.child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.child.kill()
            try:
                self.child.wait(timeout=1)   # reaped, unless it is stuck in a driver call
            except subprocess.TimeoutExpired:
                pass
        try:
            self.child.stdout.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()




def main():
    global _send
    requests = sys.stdin.buffer
    # Replies get their own copy of the pipe; descriptor 1 then points at stderr, so
    # native libraries writing to C stdout and
    # Python prints go to Ember's log instead of corrupting the reply pipe.
    replies = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    try:
        os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    except OSError:
        pass  # No usable stderr: native writes to fd 1 stay a risk, Python prints do not.
    sys.stdout = sys.stderr

    def reply(kind, value):
        pickle.dump((kind, value), replies, protocol=pickle.HIGHEST_PROTOCOL)
        replies.flush()
    _send = reply

    try:
        factory = pickle.load(requests)
        model = factory()
    except Exception as error:
        reply("error", f"{type(error).__name__}: {error}")
        return
    reply("ok", getattr(model, "device", None))
    try:
        while True:
            try:
                frame = pickle.load(requests)
            except EOFError:
                return
            try:
                landmarks = points(model.detect(frame))
                # Read after detect: an explicit ONNX CPU backend may fall back to MediaPipe.
                reply("ok", (landmarks, getattr(model, "device", None)))
            except Exception as error:
                reply("error", f"{type(error).__name__}: {error}")
    finally:
        try:
            if hasattr(model, "close"):
                model.close()  # release the model cleanly
        except Exception:
            pass


if __name__ == "__main__":
    # Run the imported module, not __main__, so Point pickles as features.vision_process.Point.
    from features.vision_process import main as serve
    serve()
