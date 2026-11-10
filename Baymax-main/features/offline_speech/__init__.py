"""Optional local speech recognition. Feature author: natey."""
from .bridge import SpeechWorker

worker = SpeechWorker()


def tap(pcm, rate, time_info, enhancer):
    """Tap the existing cleaned stream; omit playback/failed-DSP audio, never open a mic."""
    if not worker.enabled:
        return
    worker.feed(pcm, rate, time_info=time_info, enhancer=enhancer,
                blocked=enhancer is None or bool(getattr(enhancer, "failed", False)))
