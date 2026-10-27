# 6.0.2 validation

The local validation run passed 18 test groups: item policy, bounded workers, performance policy, animation policy, application integration, translation integrity, local API backpressure, launcher, OCR serialization, core, live translation, autoscan, local API, screen state, service, overlay, tasks and hidden Tk widget construction.

Two real OCR card samples at four resolutions passed eight checks. This is a limited sample, not a claim of universal OCR accuracy. Hidden widget construction does not verify visible layout or in-game behavior.

Personal configuration and progress files were unchanged in before/after SHA-256 checks.

The release workflow additionally gates publication on regression tests, installer creation, installed executable startup, packaged OCR/translation runtime checks, and an update over a tray-running application. See GitHub Actions for the result of each release run.

Actual performance on an 8 GB computer without a discrete GPU, and in-game CPU/RAM/GPU/FPS effects, remain unverified. No percentage speedup is claimed.
