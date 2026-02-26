class Course {
  final int id;
  final String name;
  final String? description;
  final String? imageUrl;
  final String category;
  final String level;
  final double? durationHours;
  final String status;
  final double progress;
  final double? finalScore;
  final DateTime? enrollmentDate;
  final DateTime? completionDate;

  Course({
    required this.id,
    required this.name,
    this.description,
    this.imageUrl,
    required this.category,
    required this.level,
    this.durationHours,
    required this.status,
    required this.progress,
    this.finalScore,
    this.enrollmentDate,
    this.completionDate,
  });

  factory Course.fromJson(Map<String, dynamic> json) {
    return Course(
      id: json['id'] as int,
      name: json['name'] as String? ?? json['course_id']?[1] as String? ?? 'Unknown',
      description: json['description'] as String?,
      imageUrl: json['image_1920'] as String?,
      category: json['category_id']?[1] as String? ?? 'Unknown',
      level: json['level_id']?[1] as String? ?? 'Unknown',
      durationHours: (json['duration_hours'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'enrolled',
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      finalScore: (json['final_score'] as num?)?.toDouble(),
      enrollmentDate: json['enrollment_date'] != null
          ? DateTime.parse(json['enrollment_date'])
          : null,
      completionDate: json['completion_date'] != null
          ? DateTime.parse(json['completion_date'])
          : null,
    );
  }

  String get statusText {
    switch (status) {
      case 'enrolled':
        return 'Đã đăng ký';
      case 'in_progress':
        return 'Đang học';
      case 'completed':
        return 'Đã hoàn thành';
      default:
        return status;
    }
  }
}
