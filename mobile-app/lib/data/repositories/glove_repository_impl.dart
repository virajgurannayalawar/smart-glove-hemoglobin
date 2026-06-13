import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/repositories/glove_repository.dart';

final gloveRepositoryProvider = Provider<GloveRepository>((ref) {
  return GloveRepositoryImpl(dio: ref.watch(dioProvider));
});

class GloveRepositoryImpl implements GloveRepository {
  final Dio dio;

  GloveRepositoryImpl({required this.dio});

  @override
  Future<Either<Failure, String>> fetchOwnerId() async {
    try {
      final response = await dio.get('/scan/OwnerId');

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final ownerId = (data['OwnerId'] ??
                data['owner_id'] ??
                data['ownerId'] ??
                '')
            .toString();
        if (ownerId.isEmpty) {
          return const Left(ServerFailure('Empty owner ID received'));
        }
        return Right(ownerId);
      }

      return const Left(ServerFailure('Failed to fetch owner ID'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to fetch owner ID');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, String>> fetchGloveKey() async {
    try {
      final response = await dio.get('/scan/glove-key');

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final gloveKey = (data['GloveApiKey'] ??
                data['glove_key'] ??
                data['gloveKey'] ??
                '')
            .toString();
        if (gloveKey.isEmpty) {
          return const Left(ServerFailure('Empty glove key received'));
        }
        return Right(gloveKey);
      }

      return const Left(ServerFailure('Failed to fetch glove key'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to fetch glove key');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, String>> rotateGloveKey() async {
    try {
      final response = await dio.post('/scan/glove-key/rotate');

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final newKey = (data['GloveApiKey'] ??
                data['glove_key'] ??
                data['gloveKey'] ??
                '')
            .toString();
        if (newKey.isEmpty) {
          return const Left(ServerFailure('Empty new key received'));
        }
        return Right(newKey);
      }

      return const Left(ServerFailure('Failed to rotate glove key'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to rotate glove key');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  Either<Failure, String> _mapDioError(DioException e, String fallback) {
    if (e.type == DioExceptionType.receiveTimeout) {
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
