class ScanResult {
  final String id;
  final String? scanId;
  final DateTime date;
  final double hemoglobinLevel;
  final bool isAnemic;
  final String statusText;
  final String? imageUrl;
  final DateTime? trueTimestamp;

  ScanResult({
    required this.id,
    this.scanId,
    required this.date,
    required this.hemoglobinLevel,
    required this.isAnemic,
    required this.statusText,
    this.imageUrl,
    this.trueTimestamp,
  });

  ScanResult copyWith({
    String? id,
    String? scanId,
    DateTime? date,
    double? hemoglobinLevel,
    bool? isAnemic,
    String? statusText,
    String? imageUrl,
    DateTime? trueTimestamp,
  }) {
    return ScanResult(
      id: id ?? this.id,
      scanId: scanId ?? this.scanId,
      date: date ?? this.date,
      hemoglobinLevel: hemoglobinLevel ?? this.hemoglobinLevel,
      isAnemic: isAnemic ?? this.isAnemic,
      statusText: statusText ?? this.statusText,
      imageUrl: imageUrl ?? this.imageUrl,
      trueTimestamp: trueTimestamp ?? this.trueTimestamp,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'scanId': scanId,
      'scan_id': scanId,
      'date': date.toIso8601String(),
      'hemoglobinLevel': hemoglobinLevel,
      'hemoglobin_level': hemoglobinLevel,
      'isAnemic': isAnemic,
      'is_anemic': isAnemic,
      'statusText': statusText,
      'status_text': statusText,
      'imageUrl': imageUrl,
      'image_url': imageUrl,
      'trueTimestamp': trueTimestamp?.toIso8601String(),
      'true_timestamp': trueTimestamp?.toIso8601String(),
    };
  }

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    final timestamp = _parseDateTime(
      json['trueTimestamp'] ??
          json['true_timestamp'] ??
          json['TrueTimestamp'] ??
          json['date'] ??
          json['Date'],
    );

    final hb = json['hemoglobinLevel'] ??
        json['hemoglobin_level'] ??
        json['HemoglobinLevel'] ??
        0;

    return ScanResult(
      id: (json['id'] ??
              json['readingId'] ??
              json['reading_id'] ??
              json['ReadingId'] ??
              '')
          .toString(),
      scanId: (json['scanId'] ?? json['scan_id'] ?? json['ScanId'])?.toString(),
      date: timestamp ?? DateTime.now(),
      hemoglobinLevel: (hb is num) ? hb.toDouble() : double.tryParse('$hb') ?? 0,
      isAnemic: json['isAnemic'] ?? json['is_anemic'] ?? json['IsAnemic'] ?? false,
      statusText: (json['statusText'] ??
              json['status_text'] ??
              json['StatusText'] ??
              'Unknown')
          .toString(),
      imageUrl: (json['imageUrl'] ?? json['image_url'] ?? json['ImageUrl'])?.toString(),
      trueTimestamp: timestamp,
    );
  }

  static DateTime? _parseDateTime(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    return DateTime.tryParse(value.toString());
  }

  @override
  String toString() =>
      'ScanResult(id: $id, hb: $hemoglobinLevel, anemic: $isAnemic)';
}
