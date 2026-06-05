import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/entities/user.dart';
import '../../domain/repositories/profile_repository.dart';
import '../../domain/repositories/auth_repository.dart';
import 'auth_repository_impl.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepositoryImpl(
    dio: ref.watch(dioProvider),
    authRepository: ref.watch(authRepositoryProvider),
    secureStorage: ref.watch(secureStorageProvider),
  );
});

class ProfileRepositoryImpl implements ProfileRepository {
  final Dio dio;
  final AuthRepository authRepository;
  final FlutterSecureStorage secureStorage;

  ProfileRepositoryImpl({
    required this.dio,
    required this.authRepository,
    required this.secureStorage,
  });

  @override
  Future<Either<Failure, User>> getProfile() async {
    try {
      final response = await dio.get('/profile');
      if (response.statusCode == 200) {
        final user = User.fromJson(response.data);
        return Right(user);
      } else {
        return Left(ServerFailure(response.data['message'] ?? 'Failed to load profile'));
      }
    } on DioException catch (e) {
      if (e.response != null) {
        return Left(ServerFailure(e.response?.data['message'] ?? 'Failed to load profile'));
      }
      return const Left(NetworkFailure('Network connection failed'));
    } catch (e) {
      // Fallback to cached user if available
      return await authRepository.getCachedUser().then((result) => result.fold(
            (l) => const Left(ServerFailure('An unexpected error occurred')),
            (r) => r != null ? Right(r) : const Left(ServerFailure('No cached profile')),
          ));
    }
  }

  @override
  Future<Either<Failure, User>> updateProfile({
    required String name,
    required int age,
    required String gender,
  }) async {
    try {
      final response = await dio.put('/profile', data: {
        'name': name,
        'age': age,
        'gender': gender,
      });

      if (response.statusCode == 200) {
        final user = User.fromJson(response.data);
        
        // Update local cache as well
        await secureStorage.write(key: 'cached_user', value: '{"id":"${user.id}", "patientId":"${user.patientId}", "name":"${user.name}", "age":${user.age}, "gender":"${user.gender}", "email":"${user.email}"}');

        return Right(user);
      } else {
        return Left(ServerFailure(response.data['message'] ?? 'Failed to update profile'));
      }
    } on DioException catch (e) {
      if (e.response != null) {
        return Left(ServerFailure(e.response?.data['message'] ?? 'Failed to update profile'));
      }
      return const Left(NetworkFailure('Network connection failed'));
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }
}
