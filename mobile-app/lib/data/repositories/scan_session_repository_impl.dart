import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/entities/scan_result.dart';
import '../../domain/repositories/scan_session_repository.dart';

final scanSessionRepositoryProvider = Provider<ScanSessionRepository>((ref) {
  return ScanSessionRepositoryImpl(
    dio: ref.watch(dioProvider),
    longPollDio: ref.watch(longPollDioProvider),
    scanBox: Hive.box('scanBox'),
  );
});

class ScanSessionRepositoryImpl implements ScanSessionRepository {
  final Dio dio;
  final Dio longPollDio;
  final Box<dynamic> scanBox;

  ScanSessionRepositoryImpl({
    required this.dio,
    required this.longPollDio,
    required this.scanBox,
  });

  @override
  Future<Either<Failure, String>> createSession({
    required String patientId,
    required bool isPregnant,
  }) async {
    try {
      final response = await dio.post(
        '/scan/sessions',
        data: {
          'PatientId': patientId,
          'IsPregnant': isPregnant,
        },
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final scanId = (data['ScanId'] ??
                data['scan_id'] ??
                data['scanId'] ??
                data['id'] ??
                '')
            .toString();

        if (scanId.isEmpty) {
          return const Left(ServerFailure('Empty scan ID received'));
        }

        await scanBox.put('session_$scanId', {
          'scan_id': scanId,
          'patient_id': patientId,
          'is_pregnant': isPregnant,
          'created_at': DateTime.now().toIso8601String(),
          'status': 'active',
        });

        return Right(scanId);
      }

      return const Left(ServerFailure('Failed to create scan session'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to create scan session');
    } catch (e) {
      return Left(ServerFailure('Error: $e'));
    }
  }

  @override
  Future<Either<Failure, ScanPollResponse>> pollResult({
    required String scanId,
    int timeoutSeconds = 60,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await longPollDio.get(
        '/scan/sessions/$scanId/result',
        queryParameters: {'timeout_seconds': timeoutSeconds},
        cancelToken: cancelToken,
      );

      if (response.statusCode == 200) {
        final data = Map<String, dynamic>.from(response.data as Map);
        final status = (data['Status'] ?? data['status'] ?? 'pending').toString();

        if (status == 'pending') {
          return Right(ScanPollResponse(status: status));
        }

        if (status == 'completed') {
          final result = ScanResult.fromJson({
            ...data,
            'ScanId': scanId,
            'ReadingId': data['ReadingId'] ?? data['reading_id'],
          });

          await scanBox.put('result_$scanId', result.toJson());
          final session = scanBox.get('session_$scanId') as Map?;
          if (session != null) {
            session['status'] = 'completed';
            await scanBox.put('session_$scanId', session);
          }

          return Right(ScanPollResponse(status: status, result: result));
        }

        final error = (data['Error'] ?? data['error'] ?? 'Scan $status').toString();
        return Right(ScanPollResponse(status: status, error: error));
      }

      return const Left(ServerFailure('Failed to fetch scan result'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to fetch scan result');
    } catch (e) {
      return Left(ServerFailure('Error: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> cancelScan(String scanId) async {
    try {
      // Backend has no DELETE endpoint; cancel locally only.
      final session = scanBox.get('session_$scanId') as Map?;
      if (session != null) {
        session['status'] = 'cancelled';
        await scanBox.put('session_$scanId', session);
      }
      return const Right(null);
    } catch (e) {
      return Left(ServerFailure('Error: $e'));
    }
  }

  @override
  Future<Either<Failure, List<ScanResult>>> getScanHistory(
    String patientId,
  ) async {
    try {
      final cachedResults = scanBox.get('history_$patientId') as List?;
      if (cachedResults != null && cachedResults.isNotEmpty) {
        return Right(
          cachedResults
              .map((item) => ScanResult.fromJson(Map<String, dynamic>.from(item)))
              .toList(),
        );
      }

      final response = await dio.get(
        '/history',
        queryParameters: {'PatientId': patientId},
      );

      if (response.statusCode == 200) {
        final resultList = response.data as List;
        final results = resultList
            .map((item) => ScanResult.fromJson(Map<String, dynamic>.from(item)))
            .toList();

        await scanBox.put(
          'history_$patientId',
          results.map((r) => r.toJson()).toList(),
        );

        return Right(results);
      }

      return const Left(ServerFailure('Failed to fetch scan history'));
    } on DioException catch (e) {
      final cachedResults = scanBox.get('history_$patientId') as List?;
      if (cachedResults != null && cachedResults.isNotEmpty) {
        return Right(
          cachedResults
              .map((item) => ScanResult.fromJson(Map<String, dynamic>.from(item)))
              .toList(),
        );
      }
      return _mapDioError(e, 'Failed to fetch scan history');
    } catch (e) {
      return Left(ServerFailure('Error: $e'));
    }
  }

  Either<Failure, T> _mapDioError<T>(DioException e, String fallback) {
    if (e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionTimeout) {
      return Left(NetworkFailure('$fallback: timeout'));
    }
    if (e.response != null) {
      final detail = e.response?.data;
      final message = detail is Map
          ? (detail['detail'] ?? detail['message'] ?? fallback).toString()
          : fallback;
      return Left(ServerFailure(message));
    }
    return Left(NetworkFailure('$fallback: network error'));
  }
}
