Set<String> taskFeedIds(dynamic value) => value is List
    ? value
          .whereType<Map>()
          .map((task) => '${task['id'] ?? task['wiki_id'] ?? ''}')
          .where((id) => id.isNotEmpty)
          .toSet()
    : <String>{};
