import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/services/image_compression_service.dart';
import '../../data/models/attendance_model.dart';
import '../../data/repository/attendance_repository.dart';

// ── Today's Attendance Provider ────────────────────────────────────
final todayAttendanceProvider =
    FutureProvider.autoDispose<TodayAttendance>((ref) async {
  final repo = ref.read(attendanceRepositoryProvider);
  final result = await repo.getTodayAttendance();
  return result.fold(
    (failure) => throw failure.message,
    (attendance) => attendance,
  );
});

// ── Office Settings Provider ───────────────────────────────────────
final officeSettingsProvider =
    FutureProvider.autoDispose<OfficeSettings>((ref) async {
  final repo = ref.read(attendanceRepositoryProvider);
  final result = await repo.getOfficeSettings();
  return result.fold(
    (failure) => throw failure.message,
    (settings) => settings,
  );
});

// ── Attendance History Provider ────────────────────────────────────
final attendanceHistoryProvider = FutureProvider.autoDispose
    .family<List<AttendanceRecord>, Map<String, dynamic>>((ref, params) async {
  final repo = ref.read(attendanceRepositoryProvider);
  final result = await repo.getAttendanceHistory(
    page: params['page'] ?? 1,
    perPage: params['perPage'] ?? 20,
    startDate: params['startDate'],
    endDate: params['endDate'],
    status: params['status'],
    sortBy: params['sortBy'],
    sortOrder: params['sortOrder'],
  );

  return result.fold(
    (failure) => throw failure.message,
    (paginatedResult) => paginatedResult.items,
  );
});

// ── Check-In/Out State ─────────────────────────────────────────────
class CheckInOutState {
  final bool isLoading;
  final String? error;
  final String? successMessage;
  final String? photoPath;

  const CheckInOutState({
    this.isLoading = false,
    this.error,
    this.successMessage,
    this.photoPath,
  });

  CheckInOutState copyWith({
    bool? isLoading,
    String? error,
    String? successMessage,
    String? photoPath,
  }) {
    return CheckInOutState(
      isLoading: isLoading ?? this.isLoading,
      error: error,
      successMessage: successMessage,
      photoPath: photoPath ?? this.photoPath,
    );
  }
}

final checkInOutProvider =
    StateNotifierProvider<CheckInOutNotifier, CheckInOutState>((ref) {
  return CheckInOutNotifier(ref);
});

class CheckInOutNotifier extends StateNotifier<CheckInOutState> {
  final Ref _ref;

  CheckInOutNotifier(this._ref) : super(const CheckInOutState());

  // ── Upload Photo with Compression ─────────────────────────────────
  Future<bool> uploadPhoto(File imageFile, {required bool isCheckIn}) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      // Compress image before upload
      final compressedFile = await ImageCompressionService.compressImage(imageFile);

      final repo = _ref.read(attendanceRepositoryProvider);
      final result = isCheckIn
          ? await repo.uploadCheckInPhoto(compressedFile)
          : await repo.uploadCheckOutPhoto(compressedFile);

      return result.fold(
        (failure) {
          state = state.copyWith(
            isLoading: false,
            error: failure.message,
          );
          return false;
        },
        (photoPath) {
          state = state.copyWith(
            isLoading: false,
            photoPath: photoPath,
            successMessage: 'Photo uploaded successfully',
          );
          return true;
        },
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to compress/upload photo: $e',
      );
      return false;
    }
  }

  // ── Check In ───────────────────────────────────────────────────────
  Future<bool> checkIn({
    required double latitude,
    required double longitude,
    String? photoPath,
  }) async {
    state = state.copyWith(isLoading: true, error: null, successMessage: null);

    try {
      final repo = _ref.read(attendanceRepositoryProvider);
      
      // If photo provided, compress and upload it first
      if (photoPath != null) {
        final photoFile = File(photoPath);
        final compressedFile = await ImageCompressionService.compressImage(photoFile);
        await repo.uploadCheckInPhoto(compressedFile);
      }

      final result = await repo.checkIn(
        latitude: latitude,
        longitude: longitude,
      );

      return result.fold(
        (failure) {
          state = state.copyWith(
            isLoading: false,
            error: failure.message,
          );
          return false;
        },
        (response) {
          state = state.copyWith(
            isLoading: false,
            successMessage: response['message'] ?? 'Checked in successfully',
          );
          // Invalidate today's attendance to refresh
          _ref.invalidate(todayAttendanceProvider);
          return true;
        },
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Check-in failed: $e',
      );
      return false;
    }
  }

  // ── Check Out ──────────────────────────────────────────────────────
  Future<bool> checkOut({
    required double latitude,
    required double longitude,
    String? photoPath,
  }) async {
    state = state.copyWith(isLoading: true, error: null, successMessage: null);

    try {
      final repo = _ref.read(attendanceRepositoryProvider);
      
      // If photo provided, compress and upload it first
      if (photoPath != null) {
        final photoFile = File(photoPath);
        final compressedFile = await ImageCompressionService.compressImage(photoFile);
        await repo.uploadCheckOutPhoto(compressedFile);
      }

      final result = await repo.checkOut(
        latitude: latitude,
        longitude: longitude,
      );

      return result.fold(
        (failure) {
          state = state.copyWith(
            isLoading: false,
            error: failure.message,
          );
          return false;
        },
        (response) {
          state = state.copyWith(
            isLoading: false,
            successMessage: response['message'] ?? 'Checked out successfully',
          );
          // Invalidate today's attendance to refresh
          _ref.invalidate(todayAttendanceProvider);
          return true;
        },
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Check-out failed: $e',
      );
      return false;
    }
  }

  void clearMessages() {
    state = state.copyWith(error: null, successMessage: null);
  }

  void clearPhotoPath() {
    state = state.copyWith(photoPath: null);
  }
}
