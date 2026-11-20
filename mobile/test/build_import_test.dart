import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/services/build_import.dart';

void main() {
  test('imports desktop build slots, talents, attributes and attachments', () {
    final builds = parseDesktopBuildExport('''
      {"builds":[{"name":"Elmo DPS","specialization":"Technician","slots":{
        "Primary":{"name":"St. Elmo's Engine","talent":"Actum Est",
          "attrs":{"health_damage":10},
          "attachments":[{"slot":"Optics","name":"Conductor Rail","stats":"CHC +5%"}]}
      }}],"templates":[]}
    ''');

    expect(builds, hasLength(1));
    expect(builds.single['specialization'], 'Technician');
    final primary = builds.single['slots']['Primary'] as Map;
    expect(primary['talent'], 'Actum Est');
    expect(primary['attrs']['health_damage'], 10);
    expect(primary['attachments'].single['name'], 'Conductor Rail');
  });

  test('rejects malformed exports and oversized input', () {
    expect(
      () => parseDesktopBuildExport('{"builds":[]}'),
      throwsFormatException,
    );
    expect(
      () => parseDesktopBuildExport('x' * (2 * 1024 * 1024 + 1)),
      throwsFormatException,
    );
  });
}
