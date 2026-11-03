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

### Phase 2 — Cloud foundation (in progress)

- ✅ D1 tables added (`schema.sql`): `mobile_pairings`, `mobile_devices`, `desktop_inbox`, `desktop_status`,
  `push_tokens`, `mobile_builds`, `account_deletions`.
- ✅ Endpoints implemented in `server/mobile.js`, wired into `worker.js`: pairing create/claim, dashboard,
  desktop inbox/events, allow-listed commands (`scan_start`/`scan_stop` only), build sync with revision
  conflict detection, push-token register/revoke, device revoke, account deletion (both from desktop
  `DELETE /v1/me` in `accounts.js` and from phone `DELETE /v1/mobile/me` in `mobile.js`).
- ✅ Pairing expires (5 min), one-time claims cannot be replayed (`claimed` flag + unique update), revoked
  devices lose access immediately, queued desktop commands stay allow-listed server-side.
- ✅ Account deletion is real, not just a flag: sessions/devices revoked immediately, then a 24h grace period,
  then `mobile.js::cleanup()` (called from `worker.js`'s `scheduled()`) actually deletes the account and all
  related rows (builds, inbox, status, push tokens, mobile devices, sessions, licenses, devices, accounts).
- ✅ 30 real, executed tests in `server/test_mobile.mjs` (`node server/test_mobile.mjs`) cover every endpoint,
  including the conflict/expiry/revocation/deletion edge cases. All existing server tests re-verified passing
  (no regressions).
- ✅ **Gap found and closed (2026-11-03):** the architecture doc's own requirement — "the user can see and revoke
  paired phones" — had no way to *see* them: `GET /v1/mobile/devices` (desktop session) now lists the account's
  active paired phones. Also closed: `mobile_builds.deleted` existed in the schema and in `listBuilds`'s response
  but nothing ever set it — `DELETE /v1/mobile/builds/{client_id}` now soft-deletes (tombstone) so other devices
  learn about the deletion on their next sync.
- ✅ **Third gap found and closed (2026-11-03):** a phone session that expired naturally (180-day TTL, never
  explicitly revoked via `revokeDevice`) was never cleaned up — its `mobile_devices` row and, if it had
  registered one, its `push_tokens` row stayed in D1 forever (an orphan, since only the explicit-revoke path
  deleted push tokens). `cleanup()` now also purges naturally-expired, non-revoked devices and their push
  tokens (7-day grace after expiry). `server/test_mobile.mjs`: 30 → 35 tests.
- ✅ **Android push delivery implemented (2026-11-03, Phase 4).** `sendPush()`/`fcmAccessToken()` in `mobile.js`
  now send real FCM HTTP v1 notifications: the Firebase Admin SDK service-account JSON (one Cloudflare secret,
  `FCM_SERVICE_ACCOUNT_JSON`) is used to build and RS256-sign a Google OAuth2 JWT assertion (Web Crypto
  `crypto.subtle`), exchange it for an access token (cached in-isolate until near expiry), then POST to
  `https://fcm.googleapis.com/v1/projects/{project_id}/messages:send` for each of the account's registered
  Android tokens. Triggered from `desktopEvent()` on `scan_result` events, best-effort (never blocks/fails the
  event response — fire-and-await inline in the test harness, `ctx.waitUntil` in the real Worker). A token FCM
  reports as `UNREGISTERED`/`NOT_FOUND`/`INVALID_ARGUMENT` is deleted automatically so it doesn't orphan. A new
  Firebase project (`td2-loot-advisor`) was created in the Firebase console and its Admin SDK service-account
  key generated and installed as the Cloudflare secret, via guided browser automation with the user's own Google
  sign-in — the key itself was never typed into chat or committed to the repo.
  `server/test_mobile.mjs`: 35 → 40 tests, including one that verifies the RS256 JWT signature against a real
  (test-only) RSA key pair rather than just asserting "a request happened".
- ✅ **iOS push code implemented (2026-11-03), not yet deployed.** `sendPush()`/`apnsProviderJwt()` in `mobile.js`
  now send real APNs HTTP/2 notifications using Apple's token-based auth: an ES256-signed provider JWT (Web
  Crypto `crypto.subtle`, `.p8` Auth Key, Team ID + Key ID) posted to `https://api.push.apple.com/3/device/{token}`
  with `apns-topic: <bundle id>`. A token APNs reports as `BadDeviceToken`/`Unregistered` (or HTTP 410) is deleted
  automatically. Fully symmetric with the Android path and independent of it — each platform is a no-op on its own
  if its own secrets aren't set. `server/test_mobile.mjs`: 40 → 44 tests, including a real ES256/P-256 signature
  check (IEEE P1363 raw r‖s format) against a test-only EC key pair via `node:crypto`.
  **Not deployed to production yet** — requires the user to complete the steps below first (a real Apple ID +
  paid enrollment, which the AI assistant must not do on the user's behalf) and supply the resulting credentials.
  **Status (2026-11-03): paused by the user.** They signed into developer.apple.com with their own Apple ID but
  have not paid for the Program membership yet — the free sign-in cannot create an APNs key (Apple's own
  restriction, confirmed when they tried). They chose to move on to other work for now; this step is parked,
  not blocked on anything from this side, and resumes whenever they complete the paid enrollment.

#### iOS push setup — steps the *user* must do (AI assistant cannot do these)

1. Enroll in the [Apple Developer Program](https://developer.apple.com/programs/enroll/) (~$99/year, requires a
   real Apple ID and a payment method — sign in with your own Apple ID, do not share the password with anyone).
2. In the [Apple Developer portal](https://developer.apple.com/account/resources/authkeys/list) → **Certificates,
   Identifiers & Profiles → Keys** → **+** to create a new key. Name it e.g. "TD2 Loot Advisor APNs", check
   **Apple Push Notifications service (APNs)**, then **Continue → Register**.
3. **Download the `.p8` key file immediately** — Apple only lets you download it once. Note the **Key ID** shown
   on the same page (10 characters, e.g. `ABC1234DEF`).
4. Find your **Team ID**: top-right of the Apple Developer portal (Membership details), also 10 characters.
5. Register an **App ID** (identifier) matching the Flutter app's bundle id, `com.federalturk.td2companion`
   (under **Identifiers**), with the **Push Notifications** capability enabled.
6. Hand the `.p8` file's contents, Key ID, and Team ID to whoever is running the deploy (never paste the `.p8`
   contents into a chat — pipe the file directly into `wrangler secret put`, same pattern as the FCM key):
   - `npx wrangler secret put APNS_AUTH_KEY_P8` (paste/pipe the whole `.p8` file content)
   - `npx wrangler secret put APNS_KEY_ID`
   - `npx wrangler secret put APNS_TEAM_ID`
   `APNS_BUNDLE_ID` is already set as a plain (non-secret) variable in `wrangler.toml`.
7. In Xcode, enable the **Push Notifications** capability for the Runner target (Signing & Capabilities tab) and
   add the Background Modes → Remote notifications capability if background delivery is wanted later.
8. Redeploy the Worker (`npx wrangler deploy`) so it picks up the new secrets, then test end-to-end on a real
   iOS device or TestFlight build (APNs does not work in the iOS Simulator).
- ✅ **Deployed to the live Cloudflare Worker (2026-11-03).** Run from the user's own PC (already authenticated
  Cloudflare session, explicit user approval before the production step): `npx wrangler d1 execute td2stats --remote
  --file schema.sql` (27 queries, 23 tables total, additive `IF NOT EXISTS`) then `npx wrangler deploy` (Version ID
  `278f119d-6683-4fc7-b8a4-c2d0a26e6a23`). Live at `https://td2-stats.td2loot.workers.dev`, `GET /v1/health` verified.
- Exit gate still open: desktop outbound relay is the simple poll-based inbox above, not a persistent
  WebSocket/long-poll relay — good enough for low-frequency commands, revisit if latency matters.

### Phase 3 — Flutter MVP

- A separate Flutter `mobile/` app now contains the game hub, task tracker, local build library, news feed, and Android QR pairing to the existing read-only desktop companion.
- Desktop pairing (LAN/QR) is same-LAN only and uses the desktop's current HTTP QR token. It is a beta bridge, not the cloud relay. It is untouched by the cloud work below and keeps working independently.
- ✅ **Cloud pairing wired in (2026-11-03).** `mobile/lib/services/cloud_api.dart` (HTTP client for every `server/mobile.js` phone-side endpoint) and `cloud_link.dart` (`CloudLinkModel`: pairing-code claim, device token in `shared_preferences`, dashboard polling, build sync with revision tracking, account deletion). `main.dart` gained an independent "Bulut eşleştirmesi" card/page (code entry, not QR — the desktop now has a "Pair a phone" button in its Account panel, `account.py::create_mobile_pairing()` + `app.py`, that shows an 8-char code). Build create/delete push/tombstone to the cloud automatically (best-effort) when paired; a manual "sync" button pulls and reconciles. Account deletion has a prominent warning that it deletes the whole linked account, not just the phone.
- ⚠️ **Not yet validated**: no Flutter/Dart SDK was available in the sandbox that wrote this, so `flutter analyze`/`flutter test`/a build have not been run. The code was reviewed by hand (brace balance, type checks, class boundaries) but needs `flutter analyze` and a real run on the Windows dev machine (Flutter 3.47.8) before being trusted end-to-end.
- Push notifications, phone-initiated remote commands beyond `scan_start`/`scan_stop`, and push-token registration UI remain out of scope for this pass.
- Use secure platform storage for mobile credentials, native push integrations, offline cache, and accessible loading/error/empty states.
- The LAN/QR beta still does not persist the desktop token; it drops it when the app closes or disconnects. Real-device validation on Android and iOS remains an exit gate.

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
