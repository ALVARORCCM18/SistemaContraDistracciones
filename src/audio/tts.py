from __future__ import annotations

import threading


class TextToSpeech:
    def __init__(self) -> None:
        self._engine = None
        self._lock = threading.Lock()
        self._configured = False

    def speak(self, text: str) -> None:
        if not text.strip():
            return

        with self._lock:
            if self._engine is None:
                import pyttsx3

                self._engine = pyttsx3.init()

            if not self._configured:
                try:
                    voices = self._engine.getProperty("voices")
                    chosen = None
                    for v in voices:
                        vname = (getattr(v, "name", "") or "").lower()
                        langs = "".join(getattr(v, "languages", [])).lower() if getattr(v, "languages", None) else ""
                        if "spanish" in vname or "es_" in vname or "es-" in vname or "es" in langs:
                            chosen = getattr(v, "id", None)
                            break
                    if chosen:
                        self._engine.setProperty("voice", chosen)
                except Exception:
                    # ignore voice selection errors
                    pass

                try:
                    self._engine.setProperty("rate", 150)
                    self._engine.setProperty("volume", 1.0)
                except Exception:
                    pass

                self._configured = True

            self._engine.say(text)
            self._engine.runAndWait()

    def speak_async(self, text: str) -> None:
        import threading

        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
