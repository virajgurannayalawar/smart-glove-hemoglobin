import 'package:flutter_test/flutter_test.dart';
import 'package:smart_glove/domain/entities/patient.dart';
import 'package:smart_glove/domain/entities/scan_result.dart';
import 'package:smart_glove/domain/entities/user.dart';

void main() {
  group('ScanResult.fromJson', () {
    test('parses backend PascalCase scan result payload', () {
      final result = ScanResult.fromJson({
        'ScanId': 'scan-123',
        'ReadingId': 'read-456',
        'HemoglobinLevel': 11.2,
        'IsAnemic': true,
        'StatusText': 'Anemic',
        'TrueTimestamp': '2026-06-05T10:00:00.000Z',
        'ImageUrl': 'https://example.com/image.jpg',
        'Status': 'completed',
      });

      expect(result.id, 'read-456');
      expect(result.scanId, 'scan-123');
      expect(result.hemoglobinLevel, 11.2);
      expect(result.isAnemic, true);
      expect(result.statusText, 'Anemic');
      expect(result.imageUrl, 'https://example.com/image.jpg');
    });

    test('parses history camelCase payload', () {
      final result = ScanResult.fromJson({
        'id': 'mongo-id',
        'readingId': 'read-789',
        'hemoglobinLevel': 14.0,
        'isAnemic': false,
        'statusText': 'Normal',
        'date': '2026-06-05T10:00:00.000Z',
      });

      expect(result.hemoglobinLevel, 14.0);
      expect(result.isAnemic, false);
      expect(result.statusText, 'Normal');
    });
  });

  group('User.fromJson', () {
    test('parses backend OwnerId field', () {
      final user = User.fromJson({
        'Id': 'mongo-id',
        'OwnerId': 'owner-uuid',
        'Name': 'Jane Owner',
        'Age': 40,
        'Gender': 'female',
        'Email': 'owner@example.com',
      });

      expect(user.patientId, 'owner-uuid');
      expect(user.name, 'Jane Owner');
    });
  });

  group('Patient.fromJson', () {
    test('parses backend PatientId field', () {
      final patient = Patient.fromJson({
        'PatientId': 'patient-uuid',
        'Name': 'Jane Doe',
        'Age': 30,
        'Gender': 'female',
        'ContactNumber': '1234567890',
        'Email': 'jane@example.com',
        'CreatedAt': '2026-06-05T10:00:00.000Z',
      });

      expect(patient.id, 'patient-uuid');
      expect(patient.name, 'Jane Doe');
      expect(patient.age, 30);
    });
  });
}
