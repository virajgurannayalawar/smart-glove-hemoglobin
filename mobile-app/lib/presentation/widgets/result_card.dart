import 'package:flutter/material.dart';
import '../../domain/entities/scan_result.dart';
import 'severity_slider.dart';

class ResultCard extends StatelessWidget {
  final ScanResult? latestResult;
  final VoidCallback onCheckPressed;
  final bool isScanning;

  const ResultCard({
    super.key,
    required this.latestResult,
    required this.onCheckPressed,
    this.isScanning = false,
  });

  @override
  Widget build(BuildContext context) {
    if (latestResult == null) {
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
              _buildCheckButton(),
            ],
          ),
        ),
      );
    }

    final isAnemic = latestResult!.isAnemic;
    final statusColor = isAnemic ? Colors.red : Colors.green;
    final statusText = isAnemic ? 'ANEMIC' : 'NON-ANEMIC';

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
              'Hemoglobin (Hb) ${latestResult!.hemoglobinLevel.toStringAsFixed(1)} g/dL',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF0D47A1),
              ),
            ),
            const SizedBox(height: 32),
            SeveritySlider(hbValue: latestResult!.hemoglobinLevel),
            const SizedBox(height: 32),
            _buildCheckButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildCheckButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: isScanning ? null : onCheckPressed,
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
