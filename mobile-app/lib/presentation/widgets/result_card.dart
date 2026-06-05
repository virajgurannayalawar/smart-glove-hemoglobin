import 'package:flutter/material.dart';
import '../../domain/entities/scan_result.dart';
import 'severity_slider.dart';

class ResultCard extends StatelessWidget {
  final ScanResult? latestResult;
  final ScanResult? result; // Alternative parameter for check_scan_screen
  final VoidCallback? onCheckPressed;
  final bool isScanning;

  const ResultCard({
    super.key,
    this.latestResult,
    this.onCheckPressed,
    this.result,
    this.isScanning = false,
  });

  @override
  Widget build(BuildContext context) {
    // Use result if provided, otherwise latestResult (for backwards compatibility)
    final scanResult = result ?? latestResult;

    if (scanResult == null) {
      return Card(
        elevation: 4,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const Icon(Icons.show_chart, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              const Text(
                'No recent scans found.',
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 24),
              if (onCheckPressed != null) _buildCheckButton(),
            ],
          ),
        ),
      );
    }

    final isAnemic = scanResult.isAnemic;
    final statusColor = isAnemic ? Colors.red : Colors.green;
    final statusText = scanResult.statusText.toUpperCase();

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            Text(
              statusText,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: statusColor,
                fontFamily: 'Poppins',
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Hemoglobin (Hb) ${scanResult.hemoglobinLevel.toStringAsFixed(1)} g/dL',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF0D47A1),
              ),
            ),
            const SizedBox(height: 12),
            // Show additional metadata if available
            if (scanResult.scanId != null || scanResult.trueTimestamp != null)
              Column(
                children: [
                  const Divider(),
                  const SizedBox(height: 8),
                  if (scanResult.trueTimestamp != null)
                    Text(
                      'Scanned: ${_formatTime(scanResult.trueTimestamp!)}',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  if (scanResult.scanId != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        'ID: ${scanResult.scanId!.substring(0, 8)}...',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                    ),
                  const SizedBox(height: 8),
                ],
              ),
            const SizedBox(height: 24),
            SeveritySlider(hbValue: scanResult.hemoglobinLevel),
            const SizedBox(height: 24),
            if (onCheckPressed != null) _buildCheckButton(),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    final diff = now.difference(dateTime);

    if (diff.inSeconds < 60) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  Widget _buildCheckButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: isScanning ? null : (onCheckPressed ?? () {}),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF0D47A1),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: isScanning
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
              )
            : const Text(
                'Anemia Check',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
      ),
    );
  }
}
