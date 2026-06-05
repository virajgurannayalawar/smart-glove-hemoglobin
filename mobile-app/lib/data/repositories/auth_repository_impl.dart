import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';

import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    dio: ref.watch(dioProvider),
    secureStorage: ref.watch(secureStorageProvider),
  );
});

class AuthRepositoryImpl implements AuthRepository {
  final Dio dio;
  final FlutterSecureStorage secureStorage;

  AuthRepositoryImpl({required this.dio, required this.secureStorage});

  @override
  Future<Either<Failure, User>> login(String email, String password) async {
    try {
      final response = await dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });

      if (response.statusCode == 200) {
        final token = response.data['token'];
        final userData = response.data['user'];

        await secureStorage.write(key: 'jwt_token', value: token);
        await secureStorage.write(key: 'cached_user', value: jsonEncode(userData));

        return Right(User.fromJson(userData));
      } else {
        return Left(ServerFailure(response.data['message'] ?? 'Login failed'));
      }
    } on DioException catch (e) {
      if (e.response != null) {
        return Left(ServerFailure(e.response?.data['message'] ?? 'Login failed'));
      }
      return const Left(NetworkFailure('Network connection failed'));
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      await secureStorage.delete(key: 'jwt_token');
      await secureStorage.delete(key: 'cached_user');
      return const Right(null);
    } catch (e) {
      return const Left(CacheFailure('Failed to clear cache'));
    }
  }

  @override
  Future<Either<Failure, User?>> getCachedUser() async {
    try {
      final userStr = await secureStorage.read(key: 'cached_user');
      if (userStr != null) {
        return Right(User.fromJson(jsonDecode(userStr)));
      }
      return const Right(null);
    } catch (e) {
      return const Left(CacheFailure('Failed to read cached user'));
    }
  }

  @override
  Future<Either<Failure, User>> register({
    required String name,
    required String email,
    required String password,
    required int age,
    required String gender,
  }) async {
    try {
      final response = await dio.post('/auth/register', data: {
        'name': name,
        'email': email,
        'password': password,
        'age': age,
        'gender': gender,
      });

      if (response.statusCode == 200 || response.statusCode == 201) {
        return Right(User.fromJson(response.data));
      } else {
        return Left(ServerFailure(response.data['detail'] ?? 'Registration failed'));
      }
    } on DioException catch (e) {
      if (e.response != null) {
        return Left(ServerFailure(e.response?.data['detail'] ?? 'Registration failed'));
      }
      return const Left(NetworkFailure('Network connection failed'));
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }
}
