class Roadmap {
  final int id;
  final String name;
  final String state;
  final String? recommendationMethod;
  final int totalCourses;
  final DateTime? createDate;

  Roadmap({
    required this.id,
    required this.name,
    required this.state,
    this.recommendationMethod,
    required this.totalCourses,
    this.createDate,
  });

  factory Roadmap.fromJson(Map<String, dynamic> json) {
    return Roadmap(
      id: json['id'] as int,
      name: json['name'] as String? ?? 'Roadmap',
      state: json['state'] as String? ?? 'suggested',
      recommendationMethod: json['recommendation_method'] as String?,
      totalCourses: json['total_courses'] as int? ?? 0,
      createDate: json['create_date'] != null
          ? DateTime.parse(json['create_date'])
          : null,
    );
  }

  String get stateText {
    switch (state) {
      case 'suggested':
        return 'Đã đề xuất';
      case 'approved':
        return 'Đã phê duyệt';
      case 'locked':
        return 'Đã khóa';
      case 'rejected':
        return 'Đã từ chối';
      default:
        return state;
    }
  }
}
