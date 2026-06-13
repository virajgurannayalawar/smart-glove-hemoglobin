class Patient {
  final String id;
  final String name;
  final int age;
  final String gender;
  final String contactNumber;
  final String email;
  final String? notes;
  final DateTime createdAt;

  Patient({
    required this.id,
    required this.name,
    required this.age,
    required this.gender,
    required this.contactNumber,
    required this.email,
    this.notes,
    required this.createdAt,
  });

  Patient copyWith({
    String? id,
    String? name,
    int? age,
    String? gender,
    String? contactNumber,
    String? email,
    String? notes,
    DateTime? createdAt,
  }) {
    return Patient(
      id: id ?? this.id,
      name: name ?? this.name,
      age: age ?? this.age,
      gender: gender ?? this.gender,
      contactNumber: contactNumber ?? this.contactNumber,
      email: email ?? this.email,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'PatientId': id,
      'name': name,
      'Name': name,
      'age': age,
      'Age': age,
      'gender': gender,
      'Gender': gender,
      'contactNumber': contactNumber,
      'ContactNumber': contactNumber,
      'email': email,
      'Email': email,
      'notes': notes,
      'Notes': notes,
      'createdAt': createdAt.toIso8601String(),
      'CreatedAt': createdAt.toIso8601String(),
    };
  }

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: (json['PatientId'] ??
              json['patient_id'] ??
              json['patientId'] ??
              json['id'] ??
              json['_id'] ??
              '')
          .toString(),
      name: (json['Name'] ?? json['name'] ?? '').toString(),
      age: ((json['Age'] ?? json['age'] ?? 0) as num).toInt(),
      gender: (json['Gender'] ?? json['gender'] ?? '').toString(),
      contactNumber:
          (json['ContactNumber'] ?? json['contactNumber'] ?? json['contact_number'] ?? '')
              .toString(),
      email: (json['Email'] ?? json['email'] ?? '').toString(),
      notes: (json['Notes'] ?? json['notes'])?.toString(),
      createdAt: json['CreatedAt'] != null
          ? DateTime.parse(json['CreatedAt'].toString())
          : json['createdAt'] != null
              ? DateTime.parse(json['createdAt'].toString())
              : DateTime.now(),
    );
  }

  @override
  String toString() => 'Patient(id: $id, name: $name, age: $age)';
}
