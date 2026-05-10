from __future__ import annotations

import threading


class TextToSpeech:
    def __init__(self) -> None:
        self._engine = None
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        if not text.strip():
            return

        with self._lock:
            if self._engine is None:
                import pyttsx3

                self._engine = pyttsx3.init()

            self._engine.say(text)
            self._engine.runAndWait()

    def speak_async(self, text: str) -> None:
        import threading

        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
