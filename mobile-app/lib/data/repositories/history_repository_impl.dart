import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'dart:convert';

import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/entities/scan_result.dart';
import '../../domain/repositories/history_repository.dart';

final historyRepositoryProvider = Provider<HistoryRepository>((ref) {
  return HistoryRepositoryImpl(dio: ref.watch(dioProvider));
});

class HistoryRepositoryImpl implements HistoryRepository {
  final Dio dio;
  static const String boxName = 'historyBox';
  static const String cacheKey = 'cached_history';

  HistoryRepositoryImpl({required this.dio});

  @override
  Future<Either<Failure, List<ScanResult>>> getHistory() async {
    try {
      final response = await dio.get('/history');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data;
        final results = data
            .map((json) => ScanResult.fromJson(Map<String, dynamic>.from(json)))
            .toList();

        // Cache the results for offline use
        try {
          final box = await Hive.openBox(boxName);
          await box.put(cacheKey, jsonEncode(data));
        } catch (e) {
          // Ignore Hive errors to not break the successful remote fetch
        }

        return Right(results);
      } else {
        return Left(ServerFailure(response.data['message'] ?? 'Failed to load history'));
      }
    } on DioException catch (e) {
      // Fallback to cache on network error
      return _getCachedHistory();
    } catch (e) {
      return _getCachedHistory();
    }
  }

  Future<Either<Failure, List<ScanResult>>> _getCachedHistory() async {
    try {
      final box = await Hive.openBox(boxName);
      final String? cachedData = box.get(cacheKey);
      
      if (cachedData != null) {
        final List<dynamic> data = jsonDecode(cachedData);
        final results = data
            .map((json) => ScanResult.fromJson(Map<String, dynamic>.from(json)))
            .toList();
        return Right(results);
      }
      return const Left(CacheFailure('No cached history available'));
    } catch (e) {
      return const Left(CacheFailure('Failed to load cached history'));
    }
  }
}
