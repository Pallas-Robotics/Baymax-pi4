"""Exercise the real speech subprocess with a WAV file; never opens audio devices."""
import argparse
import json
import os
import time
import wave

from .bridge import SpeechWorker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wav", required=True, help="Public/synthetic mono PCM16 WAV, 16 or 48 kHz")
    parser.add_argument("--model", choices=("tiny", "base"), default="tiny")
    parser.add_argument("--expect", help="Optional expected text fragment (case insensitive)")
    args = parser.parse_args()
    with wave.open(args.wav, "rb") as audio:
        rate = audio.getframerate()
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or rate not in (16000, 48000):
            parser.error("WAV must be mono PCM16 at 16000 or 48000 Hz")
        pcm = audio.readframes(audio.getnframes()) + b"\0\0" * (rate // 2)
    os.environ.update(EMBER_OFFLINE_SPEECH="1", EMBER_OFFLINE_SPEECH_MODEL=args.model)
    results = []
    worker = SpeechWorker(on_result=results.append)
    try:
        worker.start()
        deadline = time.monotonic() + 60
        while worker.state == "loading" and time.monotonic() < deadline:
            time.sleep(0.05)
        if worker.state != "running":
            raise RuntimeError(worker.detail)
        start = time.monotonic()
        for offset in range(0, len(pcm), 2048):
            captured_at = start + offset / (2 * rate)
            time.sleep(max(0, captured_at - time.monotonic()))
            worker.feed(pcm[offset:offset + 2048], rate, captured_at=captured_at)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and worker.state != "error":
            # Wait for the final decoder result, not just its queue insertion.
            if results and results[-1]["ended_at"] >= start + len(pcm) / (2 * rate) - 1:
                break
            time.sleep(0.05)
        snapshot = worker.snapshot()
        print(json.dumps(snapshot, ensure_ascii=False))
        text = " ".join(result["text"] for result in results)
        if worker.state == "error" or not text or (args.expect and args.expect.lower() not in text.lower()):
            raise SystemExit(1)
    finally:
        worker.stop()


if __name__ == "__main__":
    main()
