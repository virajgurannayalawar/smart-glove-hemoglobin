import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String patientId,
    required String name,
    required int age,
    required String gender,
    required String email,
  }) = _User;

  /// Supports backend PascalCase (OwnerId, Name) and legacy camelCase JSON.
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['Id'] ?? json['id'] ?? json['_id'] ?? '').toString(),
      patientId: (json['OwnerId'] ??
              json['ownerId'] ??
              json['patientId'] ??
              json['PatientId'] ??
              '')
          .toString(),
      name: (json['Name'] ?? json['name'] ?? '').toString(),
      age: ((json['Age'] ?? json['age'] ?? 0) as num).toInt(),
      gender: (json['Gender'] ?? json['gender'] ?? '').toString(),
      email: (json['Email'] ?? json['email'] ?? '').toString(),
    );
  }
}
