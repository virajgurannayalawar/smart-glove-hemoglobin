import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../presentation/providers/auth_provider.dart';
import '../../presentation/screens/login_screen.dart';
import '../../presentation/screens/signup_screen.dart';
import '../../presentation/screens/dashboard_screen.dart';
import '../../presentation/screens/main_layout.dart';
import '../../presentation/screens/history_screen.dart';
import '../../presentation/screens/profile_screen.dart';
import '../../presentation/screens/reports_screen.dart';
import '../../presentation/screens/connect_glove_screen.dart';
import '../../presentation/screens/patients_screen.dart';
import '../../presentation/screens/patient_form_screen.dart';
import '../../presentation/screens/check_scan_screen.dart';

class _RouterRefresh extends ChangeNotifier {
  _RouterRefresh(this.ref) {
    ref.listen(authNotifierProvider, (_, __) => notifyListeners());
  }

  final Ref ref;
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final refresh = _RouterRefresh(ref);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: refresh,
    redirect: (context, state) {
      final loggedIn = ref.read(authNotifierProvider).user != null;
      final location = state.matchedLocation;
      final isAuthRoute = location == '/login' || location == '/signup';

      if (!loggedIn && !isAuthRoute) return '/login';
      if (loggedIn && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (context, state) => const SignupScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) {
          return MainLayout(child: child);
        },
        routes: [
          GoRoute(
            path: '/dashboard',
            name: 'dashboard',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const DashboardScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
          GoRoute(
            path: '/history',
            name: 'history',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const HistoryScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const ProfileScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
          GoRoute(
            path: '/reports',
            name: 'reports',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const ReportsScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
          GoRoute(
            path: '/connect-glove',
            name: 'connect-glove',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const ConnectGloveScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return SlideTransition(
                  position: animation.drive(
                    Tween(begin: const Offset(1, 0), end: Offset.zero),
                  ),
                  child: child,
                );
              },
            ),
          ),
          GoRoute(
            path: '/patients',
            name: 'patients',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const PatientsScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
          GoRoute(
            path: '/add-patient',
            name: 'add-patient',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const PatientFormScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return SlideTransition(
                  position: animation.drive(
                    Tween(begin: const Offset(0, 1), end: Offset.zero),
                  ),
                  child: child,
                );
              },
            ),
          ),
          GoRoute(
            path: '/check-scan',
            name: 'check-scan',
            pageBuilder: (context, state) => CustomTransitionPage(
              key: state.pageKey,
              child: const CheckScanScreen(),
              transitionsBuilder: (context, animation, secondaryAnimation, child) {
                return FadeTransition(opacity: animation, child: child);
              },
            ),
          ),
        ],
      ),
    ],
  );
});
