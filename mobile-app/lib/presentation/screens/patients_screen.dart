import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../domain/entities/patient.dart';
import '../providers/patient_provider.dart';

class PatientsScreen extends ConsumerStatefulWidget {
  const PatientsScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<PatientsScreen> createState() => _PatientsScreenState();
}

class _PatientsScreenState extends ConsumerState<PatientsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(patientNotifierProvider.notifier).loadPatients();
    });
  }

  void _handleAddPatient() {
    context.push('/add-patient').then((result) {
      if (result == true) {
        // Patient added successfully, refresh list
        ref.read(patientNotifierProvider.notifier).loadPatients();
      }
    });
  }

  void _handleDeletePatient(Patient patient) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Patient'),
        content: Text('Are you sure you want to delete ${patient.name}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _deletePatient(patient.id);
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  Future<void> _deletePatient(String patientId) async {
    final success = await ref.read(patientNotifierProvider.notifier).deletePatient(patientId);
    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Patient deleted successfully')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to delete patient'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(patientNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Patients'),
        elevation: 0,
      ),
      body: state.isLoading && state.patients.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : state.patients.isEmpty
              ? _buildEmptyState()
              : _buildPatientList(state),
      floatingActionButton: FloatingActionButton(
        onPressed: _handleAddPatient,
        backgroundColor: Colors.blue,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.people_outline,
            size: 80,
            color: Colors.grey.shade300,
          ),
          const SizedBox(height: 16),
          Text(
            'No Patients Yet',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: Colors.grey.shade600,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Add a patient to get started',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey.shade500,
                ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _handleAddPatient,
            icon: const Icon(Icons.add),
            label: const Text('Add Patient'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPatientList(PatientState state) {
    return RefreshIndicator(
      onRefresh: () => ref.read(patientNotifierProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.patients.length,
        itemBuilder: (ctx, idx) => _buildPatientCard(state.patients[idx]),
      ),
    );
  }

  Widget _buildPatientCard(Patient patient) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade200),
        borderRadius: BorderRadius.circular(12),
        color: Colors.white,
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          radius: 28,
          backgroundColor: Colors.blue.shade100,
          child: Text(
            patient.name.substring(0, 1).toUpperCase(),
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 18,
              color: Colors.blue,
            ),
          ),
        ),
        title: Text(
          patient.name,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('Age: ${patient.age} • ${patient.gender.capitalize()}'),
            const SizedBox(height: 2),
            Text(patient.contactNumber, style: const TextStyle(fontSize: 12)),
            Text(patient.email, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        isThreeLine: true,
        trailing: PopupMenuButton(
          itemBuilder: (ctx) => [
            PopupMenuItem(
              child: const Row(
                children: [
                  Icon(Icons.delete, size: 20),
                  SizedBox(width: 8),
                  Text('Delete'),
                ],
              ),
              onTap: () => _handleDeletePatient(patient),
            ),
          ],
        ),
      ),
    );
  }
}

extension StringCapitalize on String {
  String capitalize() => '${this[0].toUpperCase()}${substring(1)}';
}
