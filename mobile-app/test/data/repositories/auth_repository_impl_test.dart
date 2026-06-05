import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dartz/dartz.dart';

// Since this is in a separate root directory, we use absolute imports or relative imports.
import '../../../lib/core/error/failures.dart';
import '../../../lib/data/repositories/auth_repository_impl.dart';
import '../../../lib/domain/entities/user.dart';

@GenerateMocks([Dio, FlutterSecureStorage])
import 'auth_repository_impl_test.mocks.dart';

void main() {
  late AuthRepositoryImpl repository;
  late MockDio mockDio;
  late MockFlutterSecureStorage mockSecureStorage;

  setUp(() {
    mockDio = MockDio();
    mockSecureStorage = MockFlutterSecureStorage();
    repository = AuthRepositoryImpl(
      dio: mockDio,
      secureStorage: mockSecureStorage,
    );
  });

  group('login', () {
    const tEmail = 'test@example.com';
    const tPassword = 'password123';
    
    final tUserJson = {
      'id': '1',
      'patientId': 'P123456',
      'name': 'John Doe',
      'age': 25,
      'gender': 'Male',
      'email': tEmail,
    };
    final tUser = User.fromJson(tUserJson);

    test('should return User when login is successful (200)', () async {
      // arrange
      when(mockDio.post(any, data: anyNamed('data'))).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 200,
          data: {
            'token': 'test_jwt_token',
            'user': tUserJson,
          },
        ),
      );
      
      when(mockSecureStorage.write(key: anyNamed('key'), value: anyNamed('value')))
          .thenAnswer((_) async => Future.value());

      // act
      final result = await repository.login(tEmail, tPassword);

      // assert
      expect(result, equals(Right(tUser)));
      verify(mockSecureStorage.write(key: 'jwt_token', value: 'test_jwt_token')).called(1);
    });

    test('should return ServerFailure when login fails (401)', () async {
      // arrange
      when(mockDio.post(any, data: anyNamed('data'))).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 401,
          data: {'message': 'Invalid credentials'},
        ),
      );

      // act
      final result = await repository.login(tEmail, tPassword);

      // assert
      expect(result, equals(const Left(ServerFailure('Invalid credentials'))));
      verifyNever(mockSecureStorage.write(key: anyNamed('key'), value: anyNamed('value')));
    });

    test('should return NetworkFailure when DioException occurs', () async {
      // arrange
      when(mockDio.post(any, data: anyNamed('data'))).thenThrow(
        DioException(requestOptions: RequestOptions(path: '/auth/login')),
      );

      // act
      final result = await repository.login(tEmail, tPassword);

      // assert
      expect(result, equals(const Left(NetworkFailure('Network connection failed'))));
    });
  });
}
