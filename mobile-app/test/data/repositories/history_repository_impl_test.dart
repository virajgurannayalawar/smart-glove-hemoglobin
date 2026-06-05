import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:dartz/dartz.dart';

import '../../../lib/core/error/failures.dart';
import '../../../lib/data/repositories/history_repository_impl.dart';
import '../../../lib/domain/entities/scan_result.dart';

@GenerateMocks([Dio])
import 'history_repository_impl_test.mocks.dart';

void main() {
  late HistoryRepositoryImpl repository;
  late MockDio mockDio;

  setUp(() {
    mockDio = MockDio();
    repository = HistoryRepositoryImpl(dio: mockDio);
  });

  group('getHistory', () {
    final tScanListJson = [
      {
        'id': 'scan_1',
        'date': '2025-05-20T10:00:00Z',
        'hemoglobinLevel': 13.2,
        'isAnemic': false,
        'statusText': 'NON-ANEMIC',
      },
      {
        'id': 'scan_2',
        'date': '2025-05-18T10:00:00Z',
        'hemoglobinLevel': 8.5,
        'isAnemic': true,
        'statusText': 'ANEMIC',
      }
    ];

    final tScanList = tScanListJson.map((json) => ScanResult.fromJson(json)).toList();

    test('should return List<ScanResult> when call to remote source is successful (200)', () async {
      // arrange
      when(mockDio.get(any)).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/history'),
          statusCode: 200,
          data: tScanListJson,
        ),
      );

      // act
      final result = await repository.getHistory();

      // assert
      expect(result, equals(Right(tScanList)));
      verify(mockDio.get('/history')).called(1);
    });

    test('should return ServerFailure when call to remote source fails', () async {
      // arrange
      when(mockDio.get(any)).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/history'),
          statusCode: 500,
          data: {'message': 'Server Error'},
        ),
      );

      // act
      final result = await repository.getHistory();

      // assert
      expect(result, equals(const Left(ServerFailure('Server Error'))));
    });

    test('should fallback to cache when DioException occurs (simulated network failure)', () async {
      // arrange
      when(mockDio.get(any)).thenThrow(
        DioException(requestOptions: RequestOptions(path: '/history')),
      );

      // act
      final result = await repository.getHistory();

      // assert
      // Note: Because Hive is not mocked here, it will return CacheFailure due to Hive not being initialized in tests.
      // This verifies the fallback logic was entered.
      expect(result, equals(const Left(CacheFailure('Failed to load cached history'))));
    });
  });
}
