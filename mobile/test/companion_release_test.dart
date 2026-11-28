import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/services/companion_release.dart';

void main() {
  test(
    'release links are restricted to the Companion repository asset path',
    () {
      expect(
        isTrustedReleaseUrl(
          'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.10/TD2LootAdvisor_Companion_0.1.10.apk',
          asset: true,
          tag: 'companion-v0.1.10',
        ),
        isTrue,
      );
      expect(
        isTrustedReleaseUrl('https://attacker.example/file.apk', asset: true),
        isFalse,
      );
      expect(
        isTrustedReleaseUrl(
          'https://github.com/FEDERALTURK/other/releases/tag/companion-v0.1.10',
        ),
        isFalse,
      );
    },
  );
  test('download progress is bounded and handles unknown content length', () {
    expect(downloadProgress(25, 100), 0.25);
    expect(downloadProgress(150, 100), 1);
    expect(downloadProgress(25, null), 0);
  });

  test('shared companion user agent follows the installed version', () {
    expect(companionVersion, '0.1.12');
    expect(companionUserAgent, 'TD2-Loot-Advisor-Companion/$companionVersion');
    expect(companionUserAgent, isNot(contains('0.1.5')));
  });

  test('companion release comparison only accepts newer semantic versions', () {
    expect(isNewerVersion('0.1.5', '0.1.4'), isTrue);
    expect(isNewerVersion('0.1.4.1', '0.1.4'), isTrue);
    expect(isNewerVersion('0.1.4', '0.1.4.1'), isFalse);
    expect(isNewerVersion('0.2.0', '0.1.99'), isTrue);
    expect(isNewerVersion('0.1.4', '0.1.4'), isFalse);
    expect(isNewerVersion('0.1.3', '0.1.4'), isFalse);
    expect(isNewerVersion('beta', '0.1.4'), isFalse);
  });

  test('update check is throttled but runs when no check exists', () {
    final now = DateTime(2026, 11, 7, 12);
    expect(isUpdateCheckDue(null, now: now), isTrue);
    expect(
      isUpdateCheckDue(
        now.subtract(const Duration(hours: 5, minutes: 59)),
        now: now,
      ),
      isFalse,
    );
    expect(
      isUpdateCheckDue(now.subtract(const Duration(hours: 6)), now: now),
      isTrue,
    );
  });

  test('companion release selects the newest direct APK asset', () {
    final release = parseLatestCompanionRelease([
      {
        'tag_name': 'v9.9.9',
        'html_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/v9.9.9',
      },
      {
        'tag_name': 'companion-v0.1.4.1-beta',
        'html_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/companion-v0.1.4.1-beta',
        'assets': [
          {
            'name': 'SHA256SUMS.sha256',
            'browser_download_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/SHA256SUMS.sha256',
          },
          {
            'name': 'TD2LootAdvisor_Companion_0.1.4.1-beta.apk',
            'browser_download_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/TD2LootAdvisor_Companion_0.1.4.1-beta.apk',
          },
          {
            'name': 'SHA256SUMS.sha256',
            'browser_download_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/SHA256SUMS.sha256',
          },
        ],
      },
    ]);

    expect(release?.version, '0.1.4.1');
    expect(release?.apkUrl, endsWith('.apk'));
    expect(release?.sha256Url, contains('SHA256SUMS.sha256'));
  });
}
