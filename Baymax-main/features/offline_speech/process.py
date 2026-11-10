"""Private speech subprocess protocol: shared PCM in, local speech events out."""
import argparse
import os
import pickle
import sys
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("tiny", "base"), required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--language")
    args = parser.parse_args()
    requests = sys.stdin.buffer
    replies = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    lock = threading.Lock()

    def emit(event):
        with lock:
            pickle.dump(event, replies, protocol=pickle.HIGHEST_PROTOCOL)
            replies.flush()

    pipeline = None
    try:
        from .bridge import Settings
        from .recognition import Pipeline, Recognizer
        recognizer = Recognizer(Settings(args.model, args.threads, args.language))
        pipeline = Pipeline(recognizer, emit)
        emit(dict(kind="ready"))
        last_heartbeat = 0
        while not pipeline.stop_event.is_set():
            packet = pickle.load(requests)
            if time.monotonic() - packet["captured_at"] > 1:
                emit(dict(kind="dropped", scope="packet"))
                continue
            pipeline.accept(packet)
            if time.monotonic() - last_heartbeat >= 1:
                emit(dict(kind="heartbeat"))
                last_heartbeat = time.monotonic()
    except EOFError:
        pass
    except Exception as error:
        emit(dict(kind="error", message=f"Offline speech failed: {type(error).__name__}: {error}"))
    finally:
        if pipeline is not None:
            pipeline.close()
        replies.close()


if __name__ == "__main__":
    main()
