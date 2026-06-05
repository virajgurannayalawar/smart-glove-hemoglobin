import 'package:dartz/dartz.dart';
import '../../core/error/failures.dart';
import '../entities/user.dart';

abstract class AuthRepository {
  Future<Either<Failure, User>> login(String email, String password);
  Future<Either<Failure, void>> logout();
  Future<Either<Failure, User?>> getCachedUser();
  Future<Either<Failure, User>> register({
    required String name,
    required String email,
    required String password,
    required int age,
    required String gender,
  });
}
