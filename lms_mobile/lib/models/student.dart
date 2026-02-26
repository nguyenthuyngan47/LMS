class Student {
  final int id;
  final String name;
  final String email;
  final String? phone;
  final String currentLevel;
  final String? learningGoals;
  final String? desiredSkills;
  final int totalCourses;
  final int completedCourses;
  final double? averageScore;
  final bool isActive;
  final int? userId; // Link với res.users

  Student({
    required this.id,
    required this.name,
    required this.email,
    this.phone,
    required this.currentLevel,
    this.learningGoals,
    this.desiredSkills,
    required this.totalCourses,
    required this.completedCourses,
    this.averageScore,
    required this.isActive,
    this.userId,
  });

  factory Student.fromJson(Map<String, dynamic> json) {
    return Student(
      id: json['id'] as int,
      name: json['name'] as String,
      email: json['email'] as String? ?? '',
      phone: json['phone'] as String?,
      currentLevel: json['current_level'] as String? ?? 'beginner',
      learningGoals: json['learning_goals'] as String?,
      desiredSkills: json['desired_skills'] as String?,
      totalCourses: json['total_courses'] as int? ?? 0,
      completedCourses: json['completed_courses'] as int? ?? 0,
      averageScore: (json['average_score'] as num?)?.toDouble(),
      isActive: json['is_active'] as bool? ?? true,
      userId: json['user_id'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'phone': phone,
      'current_level': currentLevel,
      'learning_goals': learningGoals,
      'desired_skills': desiredSkills,
      'total_courses': totalCourses,
      'completed_courses': completedCourses,
      'average_score': averageScore,
      'is_active': isActive,
      'user_id': userId,
    };
  }
}
