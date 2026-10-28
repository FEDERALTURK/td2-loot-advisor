# TD2 Loot Advisor Mobile Companion

## Product direction

Build one Flutter app for iOS and Android that complements the existing Windows desktop app. The mobile app is a companion, not a port of the Tkinter interface or game-screen OCR.

Working name: **TD2 Loot Advisor Companion**. Launch the first store version free. Keep public game information usable without an account; ask for sign-in only for private builds, desktop pairing, sync, or notifications.

## MVP scope

1. **Game hub:** current tasks, official Division news, weekly vendor and targeted-loot information, with source and update time shown.
2. **Build library:** create and edit mobile builds; import/export a build through a QR code. Account sync can follow after the identity and deletion flows are in place.
3. **Desktop companion:** pair one Windows installation, show online/offline and scan status, receive the latest item scan result, and optionally ask the desktop to start or stop a scan. Pairing and remote control are explicitly enabled and revocable.
4. **Notifications:** opt-in alerts for a desktop scan result and chosen task/vendor updates. No notification permission is requested before the user enables an alert.

## Not in the first release

- Running OCR, capturing the game screen, reading game memory, or injecting input on the phone.
- Remote game control. Mobile commands may only call the desktop app's own documented scan controls.
- Premium sales, subscriptions, or external checkout. Keep the first store release free while the cross-platform entitlement and store billing design is resolved.
- Uploading screenshots, microphone recordings, or full desktop settings to the cloud.

## Existing project pieces

- The desktop app is Python/Tkinter. Its UI is not reusable as a mobile UI; item/build rules and JSON data can inform the mobile models.
- `companion.py` provides a separate, read-only LAN web view with a QR URL and random query token. Mobile Companion 0.1.2-beta can scan this QR and poll `/api/state`; it accepts only RFC1918 private IPv4 addresses and keeps the pairing token in memory.
- `localapi.py` is a separate loopback-first WebSocket/HTTP API with allow-listed desktop commands. It is not used by the mobile APK and must not be exposed to the public internet.
- `server/worker.js` and `server/accounts.js` run on Cloudflare Workers + D1. They currently handle community data, tasks, Discord-based desktop login, licensing, and account lookup. There is no mobile sync, pairing, push-token, or account-deletion endpoint yet.
- Desktop account state is protected using Windows DPAPI and a license entitlement can be bound to one device. A phone needs its own portable session and an explicit policy for which devices count against a license.

## Target architecture

```text
Flutter app (iOS / Android)
          │ HTTPS, short-lived device session
          ▼
Cloudflare Worker API ─── D1 (accounts, pairings, build sync, preferences)
          ▲                         │
          │ HTTPS outbound          └── APNs / FCM push delivery
          │
Windows desktop app ── local OCR and game-screen reading
```

The phone must not depend on a router port-forward or expose the desktop API to the public internet. The desktop keeps an outbound authenticated connection to the cloud relay. Pairing uses a short-lived, single-use code/QR and requires confirmation in the desktop app. The user can see and revoke paired phones. Desktop events are sent only after opt-in, with no image attached.

### Proposed API surface (versioned, to implement after review)

| Endpoint | Purpose |
|---|---|
| `POST /v1/mobile/pairings` | Desktop creates a short-lived pairing challenge. |
| `POST /v1/mobile/pairings/claim` | Authenticated phone claims a code and registers its device key. |
| `GET /v1/mobile/dashboard` | Paired desktop status and latest scan summary. |
| `GET /v1/mobile/desktop/inbox` | Desktop receives queued, allow-listed scan commands. |
| `POST /v1/mobile/desktop/events` | Desktop sends status and scan-result events. |
| `GET/PUT /v1/mobile/builds` | Optional, user-owned build synchronization with revision checks. |
| `PUT/DELETE /v1/mobile/push-tokens/{id}` | Register or revoke an APNs/FCM token and notification preferences. |
| `DELETE /v1/mobile/devices/{id}` | Revoke a phone session/pairing. |
| `DELETE /v1/me` | Request deletion of the account and eligible associated data. |

Public task/news/game-data endpoints should be reused where their schemas and caching behavior fit. The mobile API will use bearer authorization headers, TLS, rate limits, bounded payloads, idempotency keys for writes, and explicit schema versions. It will not put long-lived credentials in URLs.

## Delivery phases and exit gates

### Phase 1 — Scope and API contract

- Confirm the free companion MVP above and publish the API/data contracts.
- Define account linking for Discord and platform sign-in, portable device sessions, license/device limits, data retention, and deletion semantics.
- Exit when pairing, sync, privacy, and billing decisions are written down; no production secrets are needed for this phase.

### Phase 2 — Cloud foundation

- Add database migrations for mobile devices, pairing challenges, desktop relay state, build revisions, and push registrations.
- Add authenticated endpoints and account deletion; never return admin credentials to a client.
- Implement desktop outbound relay and revocation/expiry behavior. Do not expose `localapi.py` to the internet.
- Exit when pairing expires, one-time claims cannot be replayed, revoked devices lose access, and queued commands remain allow-listed.

### Phase 3 — Flutter MVP

- A separate Flutter `mobile/` app now contains the game hub, task tracker, local build library, news feed, and Android QR pairing to the existing read-only desktop companion.
- Desktop pairing is same-LAN only and uses the desktop's current HTTP QR token. It is a beta bridge, not the proposed TLS cloud relay. Mobile remote control, commands, account sync, cloud auth, push, and phone-token management remain out of scope.
- Use secure platform storage for mobile credentials, native push integrations, offline cache, and accessible loading/error/empty states.
- The current local beta does not persist the desktop token; it drops it when the app closes or disconnects. Real-device validation on Android and iOS remains an exit gate.

### Phase 4 — Beta and store readiness

- Test real devices, slow/lost networks, expired sessions, revoked devices, sync conflicts, accessibility, battery impact, and notification opt-in.
- Add privacy policy, support/contact page, accurate data-safety disclosures, store screenshots, and an App Review demo account/mode.
- TestFlight and Play internal testing first; then closed testing and staged production.
- Exit when critical defects are fixed, privacy disclosures match observed network traffic, and review credentials/backend are live.

### Phase 5 — First public release and follow-up

- Publish the free companion to App Store and Google Play, monitor crashes and API health, and roll out gradually.
- Add AI voice, broader build sync, and paid features only after usage feedback and store billing rules are settled.

## Store and build constraints

- iOS Flutter builds require macOS and Xcode. This Windows checkout can host shared Dart source and Android work, but a Mac/macOS CI runner is required for signed iOS builds and release submission.
- Apple membership is required for App Store distribution. Apple may require an equivalent privacy-preserving login option when a third-party social login is used as the primary account login; account creation requires in-app account deletion.
- Google Play requires its billing system for most digital in-app purchases. New personal developer accounts may need a closed test with 12 continuously opted-in testers for 14 days before production access. New Play submissions currently need Android 16 / API 36 or higher as of August 31, 2026.
- If account creation is enabled, provide an in-app deletion path and the required external deletion request resource for Play. Keep the account optional for public game information.
- Check The Division marks, logos, screenshots, and source-data redistribution permissions before submitting store art or listings.

## Current local development readiness

- The Windows workspace has user-local Flutter 3.47.8, Dart 3.13.7, Java 21, and Android SDK 36 toolchains. They are invoked by explicit paths and need not be on global `PATH`.
- Android Companion 0.1.2-beta fixes an Android launcher/Kotlin `MainActivity` package mismatch. Static APK checks confirm the manifest's launcher class now exists in DEX, Flutter analysis and the first-frame widget smoke test pass, and both APK and AAB build on this Windows host. A real HONOR Android 16 device retest and Google Play upload signing remain outstanding.
- iOS project files are present, but no iOS archive, signing, physical-device check, or App Store submission has been completed; these require macOS/Xcode and Apple developer signing.
- The proposed Cloudflare mobile API above is still a future design, not a live backend or the transport used by this local beta.

## Official references

- [Flutter platform setup](https://docs.flutter.dev/install/custom) and [iOS setup](https://docs.flutter.dev/platform-integration/ios/setup)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple account deletion requirement](https://developer.apple.com/support/offering-account-deletion-in-your-app/)
- [Google Play account deletion requirement](https://support.google.com/googleplay/android-developer/answer/13327111)
- [Google Play payments policy](https://support.google.com/googleplay/android-developer/answer/10281818)
- [Google Play target API requirement](https://support.google.com/googleplay/android-developer/answer/11926878)
- [Google Play testing requirement for new personal developer accounts](https://support.google.com/googleplay/android-developer/answer/14151465)
- [Apple Developer Program enrollment](https://developer.apple.com/programs/) and [Google Play distribution options](https://support.google.com/android-developer-console/answer/16640817)
