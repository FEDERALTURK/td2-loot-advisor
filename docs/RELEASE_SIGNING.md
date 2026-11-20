# Release manifest signing

Installer and source updates from `v9.1.5.53` onward require an Ed25519-signed
`TD2_RELEASE_MANIFEST.json`. The manifest binds the release tag and version to
the installer/portable SHA-256 values and the GitHub source ZIP SHA-256. Older
releases remain on the existing checksum path so currently installed versions
can update to the first signed release.

## Add the GitHub Actions secret

The private key is generated outside the repository at:

```text
%LOCALAPPDATA%\TD2LootAdvisor\release-signing\release-signing-private.pem
```

In PowerShell, copy its Base64-encoded PEM to the clipboard without printing
the secret in the terminal:

```powershell
$keyPath = Join-Path $env:LOCALAPPDATA 'TD2LootAdvisor\release-signing\release-signing-private.pem'
[Convert]::ToBase64String([IO.File]::ReadAllBytes($keyPath)) | Set-Clipboard
```

In the GitHub repository, open **Settings → Secrets and variables → Actions →
New repository secret** and create:

```text
Name:  TD2_RELEASE_SIGNING_KEY_BASE64
Value: paste from clipboard
```

Do not print or commit the key. Keep a protected offline backup; losing the
private key requires a coordinated public-key rotation in a future application
version. The matching public key is embedded in `updater.py`.

The Windows release workflow fails at **Sign release manifest** if the secret
is absent or invalid. Non-release branch builds do not need the secret. Verify
the secret is configured before creating a release tag or dispatching a release
build. No secret value is required in a pull request.
