import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/roadmap_provider.dart';
import '../models/roadmap.dart';

class RoadmapScreen extends StatelessWidget {
  const RoadmapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lộ trình học tập'),
      ),
      body: Consumer<RoadmapProvider>(
        builder: (context, roadmapProvider, child) {
          if (roadmapProvider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (roadmapProvider.errorMessage != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(roadmapProvider.errorMessage!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => roadmapProvider.loadRoadmaps(),
                    child: const Text('Thử lại'),
                  ),
                ],
              ),
            );
          }

          if (roadmapProvider.roadmaps.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.map_outlined, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  Text(
                    'Chưa có roadmap nào',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Hãy tạo roadmap mới để bắt đầu học tập',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => roadmapProvider.loadRoadmaps(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: roadmapProvider.roadmaps.length,
              itemBuilder: (context, index) {
                final roadmap = roadmapProvider.roadmaps[index];
                return _RoadmapCard(roadmap: roadmap);
              },
            ),
          );
        },
      ),
    );
  }
}

class _RoadmapCard extends StatelessWidget {
  final Roadmap roadmap;

  const _RoadmapCard({required this.roadmap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    roadmap.name,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Chip(
                  label: Text(roadmap.stateText),
                  backgroundColor: _getStateColor(roadmap.state).withOpacity(0.2),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.school, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(
                  '${roadmap.totalCourses} khóa học',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (roadmap.recommendationMethod != null) ...[
                  const SizedBox(width: 16),
                  Icon(Icons.auto_awesome, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    roadmap.recommendationMethod!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ],
            ),
            if (roadmap.createDate != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.calendar_today, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    'Tạo ngày: ${_formatDate(roadmap.createDate!)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getStateColor(String state) {
    switch (state) {
      case 'approved':
        return Colors.green;
      case 'suggested':
        return Colors.blue;
      case 'locked':
        return Colors.orange;
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
