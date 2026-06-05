import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dartz/dartz.dart';

import 'package:smart_glove/core/error/failures.dart';
import 'package:smart_glove/data/repositories/auth_repository_impl.dart';
import 'package:smart_glove/domain/entities/user.dart';

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
      'Id': 'mongo-id',
      'OwnerId': 'owner-uuid',
      'Name': 'John Doe',
      'Age': 25,
      'Gender': 'Male',
      'Email': tEmail,
    };
    final tUser = User.fromJson(tUserJson);

    test('should return User when login is successful (200)', () async {
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

      final result = await repository.login(tEmail, tPassword);

      expect(result.isRight(), true);
      result.fold((_) => fail('expected success'), (user) {
        expect(user.patientId, 'owner-uuid');
        expect(user.name, 'John Doe');
      });
      verify(mockSecureStorage.write(key: 'jwt_token', value: 'test_jwt_token')).called(1);
    });

    test('should return ServerFailure when login fails (401)', () async {
      when(mockDio.post(any, data: anyNamed('data'))).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 401,
          data: {'message': 'Invalid credentials'},
        ),
      );

      final result = await repository.login(tEmail, tPassword);

      result.fold(
        (failure) => expect(failure.message, 'Invalid credentials'),
        (_) => fail('expected failure'),
      );
      verifyNever(mockSecureStorage.write(key: anyNamed('key'), value: anyNamed('value')));
    });

    test('should return NetworkFailure when DioException occurs', () async {
      when(mockDio.post(any, data: anyNamed('data'))).thenThrow(
        DioException(requestOptions: RequestOptions(path: '/auth/login')),
      );

      final result = await repository.login(tEmail, tPassword);

      result.fold(
        (failure) => expect(failure.message, 'Network connection failed'),
        (_) => fail('expected failure'),
      );
    });
  });
}
