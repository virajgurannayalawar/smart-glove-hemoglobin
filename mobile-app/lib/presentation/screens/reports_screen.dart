import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:collection/collection.dart';
import '../providers/history_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/patient_provider.dart';
import '../widgets/patient_selection_list.dart';
import '../../core/services/pdf_service.dart';
import '../../domain/entities/scan_result.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  String _formatDate(DateTime date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return '${date.day} ${months[date.month - 1]} ${date.year}';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyState = ref.watch(historyNotifierProvider);
    final user = ref.watch(authNotifierProvider).user;
    final patientState = ref.watch(patientNotifierProvider);
    final selectedPatient = patientState.selectedPatient;

    final scans = selectedPatient != null
        ? historyState.scans.where((s) => s.patientId == selectedPatient.id).toList()
        : const <ScanResult>[];

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(
          selectedPatient != null ? 'Reports: ${selectedPatient.name}' : 'Select Patient',
          style: const TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.bold),
        ),
        leading: selectedPatient != null
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => ref.read(patientNotifierProvider.notifier).clearSelection(),
              )
            : null,
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF0D47A1),
        elevation: 0,
      ),
      body: selectedPatient == null
          ? PatientSelectionList(
              onPatientSelected: (patient) {
                ref.read(patientNotifierProvider.notifier).selectPatient(patient);
              },
            )
          : scans.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.picture_as_pdf, size: 100, color: Colors.grey[300]),
                      const SizedBox(height: 24),
                      const Text(
                        'No reports available',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16.0),
                  itemCount: scans.length,
                  itemBuilder: (context, index) {
                    final scan = scans[index];
                    return Card(
                      elevation: 2,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  _formatDate(scan.date),
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
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
                              ],
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Hemoglobin: ${scan.hemoglobinLevel.toStringAsFixed(1)} g/dL',
                              style: const TextStyle(fontWeight: FontWeight.w500),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: double.infinity,
                              child: OutlinedButton.icon(
                                onPressed: () {
                                  if (user != null) {
                                    final pdfPatient = patientState.patients.firstWhereOrNull(
                                      (p) => p.id == scan.patientId,
                                    );
                                    PdfService.generateAndSharePdf(
                                      scanner: user,
                                      patient: pdfPatient ?? selectedPatient,
                                      scan: scan,
                                    );
                                  }
                                },
                                icon: const Icon(Icons.download),
                                label: const Text('Download PDF'),
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: const Color(0xFF0D47A1),
                                  side: const BorderSide(color: Color(0xFF0D47A1)),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
