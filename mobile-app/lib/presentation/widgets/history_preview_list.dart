import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../domain/entities/scan_result.dart';

class HistoryPreviewList extends StatelessWidget {
  final List<ScanResult> recentScans;

  const HistoryPreviewList({
    super.key,
    required this.recentScans,
  });

  String _formatDate(DateTime date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return '${date.day} ${months[date.month - 1]} ${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Recent Scans',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                fontFamily: 'Poppins',
              ),
            ),
            TextButton(
              onPressed: () => context.go('/history'),
              child: const Text('View More'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (recentScans.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24.0),
            child: Center(
              child: Text(
                'No past scans available.',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          )
        else
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: recentScans.length > 3 ? 3 : recentScans.length,
            separatorBuilder: (context, index) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final scan = recentScans[index];
              return ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  _formatDate(scan.date),
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                subtitle: Text('Hb: ${scan.hemoglobinLevel.toStringAsFixed(1)} g/dL'),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: scan.isAnemic ? Colors.red.withOpacity(0.1) : Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    scan.statusText,
                    style: TextStyle(
                      color: scan.isAnemic ? Colors.red : Colors.green,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              );
            },
          ),
      ],
    );
  }
}
