import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/services/companion_release.dart';

void main() {
  test('companion release comparison only accepts newer semantic versions', () {
    expect(isNewerVersion('0.1.5', '0.1.4'), isTrue);
    expect(isNewerVersion('0.2.0', '0.1.99'), isTrue);
    expect(isNewerVersion('0.1.4', '0.1.4'), isFalse);
    expect(isNewerVersion('0.1.3', '0.1.4'), isFalse);
    expect(isNewerVersion('beta', '0.1.4'), isFalse);
  });
}
