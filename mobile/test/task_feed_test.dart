import 'package:flutter_test/flutter_test.dart';
import 'package:td2_companion/services/task_feed.dart';

void main() {
  test('task feed IDs use stable IDs and ignore malformed entries', () {
    expect(
      taskFeedIds([
        {'id': 'task-1'},
        {'wiki_id': 'wiki-task-2'},
        {'id': ''},
        'invalid',
      ]),
      {'task-1', 'wiki-task-2'},
    );
    expect(taskFeedIds(null), isEmpty);
  });
}
