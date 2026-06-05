// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'scan_result.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ScanResultImpl _$$ScanResultImplFromJson(Map<String, dynamic> json) =>
    _$ScanResultImpl(
      id: json['id'] as String,
      date: DateTime.parse(json['date'] as String),
      hemoglobinLevel: (json['hemoglobinLevel'] as num).toDouble(),
      isAnemic: json['isAnemic'] as bool,
      statusText: json['statusText'] as String,
    );

Map<String, dynamic> _$$ScanResultImplToJson(_$ScanResultImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'date': instance.date.toIso8601String(),
      'hemoglobinLevel': instance.hemoglobinLevel,
      'isAnemic': instance.isAnemic,
      'statusText': instance.statusText,
    };
