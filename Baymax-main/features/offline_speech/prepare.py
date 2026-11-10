"""Explicit public-model download; never called by runtime or startup."""
import argparse
import json

from .bridge import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("tiny", "base"), required=True)
    args = parser.parse_args()
    from faster_whisper.utils import download_model
    settings = Settings(model=args.model)
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    download_model(args.model, output_dir=str(settings.model_dir))
    # Verify both native models now; runtime will never attempt a download.
    from .recognition import Recognizer
    recognizer = Recognizer(settings)
    print(json.dumps(dict(model=args.model, directory=str(settings.model_dir),
                          backend="CPU/int8", vad="Silero v6/ONNX", ready=recognizer is not None)))


if __name__ == "__main__":
    main()
