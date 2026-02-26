class Progress {
  final List<ProgressItem> items;
  final double totalProgress;
  final double averageScore;
  final double totalStudyTime;

  Progress({
    required this.items,
    required this.totalProgress,
    required this.averageScore,
    required this.totalStudyTime,
  });

  factory Progress.fromJson(List<dynamic> json) {
    final items = json.map((item) => ProgressItem.fromJson(item)).toList();
    
    final totalProgress = items.isNotEmpty
        ? items.map((e) => e.progress).reduce((a, b) => a + b) / items.length
        : 0.0;
    
    final averageScore = items.isNotEmpty
        ? items.where((e) => e.quizScore != null)
            .map((e) => e.quizScore!)
            .reduce((a, b) => a + b) / items.where((e) => e.quizScore != null).length
        : 0.0;
    
    final totalStudyTime = items.map((e) => e.studyDuration).fold(0.0, (a, b) => a + b);

    return Progress(
      items: items,
      totalProgress: totalProgress,
      averageScore: averageScore,
      totalStudyTime: totalStudyTime,
    );
  }
}

class ProgressItem {
  final int id;
  final DateTime date;
  final String courseName;
  final String? lessonName;
  final double studyDuration;
  final double? quizScore;
  final String status;

  ProgressItem({
    required this.id,
    required this.date,
    required this.courseName,
    this.lessonName,
    required this.studyDuration,
    this.quizScore,
    required this.status,
  });

  factory ProgressItem.fromJson(Map<String, dynamic> json) {
    return ProgressItem(
      id: json['id'] as int,
      date: DateTime.parse(json['date'] as String),
      courseName: json['course_id']?[1] as String? ?? 'Unknown',
      lessonName: json['lesson_id']?[1] as String?,
      studyDuration: (json['study_duration'] as num?)?.toDouble() ?? 0.0,
      quizScore: (json['quiz_score'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'completed',
    );
  }

  double get progress => quizScore != null ? quizScore! / 100 : 0.0;
}
