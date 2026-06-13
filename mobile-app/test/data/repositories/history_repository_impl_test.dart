import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:dartz/dartz.dart';
import 'dart:io';

import 'package:hive/hive.dart';

import 'package:smart_glove/core/error/failures.dart';
import 'package:smart_glove/data/repositories/history_repository_impl.dart';
import 'package:smart_glove/domain/entities/scan_result.dart';

@GenerateMocks([Dio])
import 'history_repository_impl_test.mocks.dart';

void main() {
  late HistoryRepositoryImpl repository;
  late MockDio mockDio;

  setUpAll(() async {
    final dir = await Directory.systemTemp.createTemp('hive_history_test');
    Hive.init(dir.path);
    await Hive.openBox(HistoryRepositoryImpl.boxName);
  });

  tearDownAll(() async {
    await Hive.close();
  });

  setUp(() async {
    mockDio = MockDio();
    repository = HistoryRepositoryImpl(dio: mockDio);
    final box = await Hive.openBox(HistoryRepositoryImpl.boxName);
    await box.clear();
  });

  group('getHistory', () {
    final tScanListJson = [
      {
        'id': 'scan_1',
        'date': '2025-05-20T10:00:00.000Z',
        'hemoglobinLevel': 13.2,
        'isAnemic': false,
        'statusText': 'Normal',
      },
      {
        'id': 'scan_2',
        'date': '2025-05-18T10:00:00.000Z',
        'hemoglobinLevel': 8.5,
        'isAnemic': true,
        'statusText': 'Anemic',
      }
    ];

    test('should return List<ScanResult> when call to remote source is successful (200)', () async {
      when(mockDio.get(any)).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/history'),
          statusCode: 200,
          data: tScanListJson,
        ),
      );

      final result = await repository.getHistory();

      expect(result.isRight(), true);
      result.fold((_) => fail('expected success'), (scans) {
        expect(scans.length, 2);
        expect(scans.first.hemoglobinLevel, 13.2);
        expect(scans.last.isAnemic, true);
      });
      verify(mockDio.get('/history')).called(1);
    });

    test('should return ServerFailure when call to remote source fails', () async {
      when(mockDio.get(any)).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/history'),
          statusCode: 500,
          data: {'message': 'Server Error'},
        ),
      );

      final result = await repository.getHistory();

      result.fold(
        (failure) => expect(failure.message, 'Server Error'),
        (_) => fail('expected failure'),
      );
    });

    test('should fallback to cache when DioException occurs (simulated network failure)', () async {
      when(mockDio.get(any)).thenThrow(
        DioException(requestOptions: RequestOptions(path: '/history')),
      );

      final result = await repository.getHistory();

      expect(result.isLeft(), true);
      result.fold((failure) {
        expect(failure, isA<CacheFailure>());
      }, (_) => fail('expected cache failure'));
    });
  });
}
