class CaptionLine {
  const CaptionLine({
    required this.original,
    required this.translated,
    required this.confidence,
    required this.timestamp,
  });

  final String original;
  final String translated;
  final double confidence;
  final DateTime timestamp;
}
