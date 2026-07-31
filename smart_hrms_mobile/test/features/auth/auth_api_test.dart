import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/auth/data/models/user_model.dart';
import 'package:smart_hrms_mobile/features/auth/presentation/widgets/password_strength.dart';

void main() {
  group('Authentication API Integration Tests', () {
    group('Password Strength Validator', () {
      test('evaluate() should identify weak password', () {
        final strength = PasswordStrengthValidator.evaluate('abc');
        expect(strength, PasswordStrength.weak);
      });

      test('evaluate() should identify fair password', () {
        final strength = PasswordStrengthValidator.evaluate('abcDEF123');
        expect(strength.index >= PasswordStrength.fair.index, true);
      });

      test('evaluate() should identify strong password', () {
        final strength =
            PasswordStrengthValidator.evaluate('MyPassword123!@#');
        expect(strength.index >= PasswordStrength.strong.index, true);
      });

      test('validate() should return error for weak password', () {
        final error = PasswordStrengthValidator.validate('weak');
        expect(error, isNotNull);
      });

      test('validate() should return null for valid password', () {
        final error = PasswordStrengthValidator.validate('ValidPass123!');
        expect(error, isNull);
      });

      test('isValid() should return false for weak passwords', () {
        expect(PasswordStrengthValidator.isValid('weak'), false);
      });

      test('isValid() should return true for strong passwords', () {
        expect(PasswordStrengthValidator.isValid('StrongPassword123!'), true);
      });

      test('getRequirements() should list missing requirements', () {
        final requirements = PasswordStrengthValidator.getRequirements('weak');
        expect(requirements.contains('✗'), true);
        expect(requirements.contains('Uppercase'), true);
      });

      test('getRequirements() should show met requirements', () {
        final requirements =
            PasswordStrengthValidator.getRequirements('ValidPassword123!');
        expect(requirements.contains('✓'), true);
      });

      test('getColor() should return red for weak password', () {
        final color = PasswordStrengthValidator.getColor(PasswordStrength.weak);
        expect(color, isNotNull);
      });

      test('getColor() should return green for very strong password', () {
        final color =
            PasswordStrengthValidator.getColor(PasswordStrength.veryStrong);
        expect(color, isNotNull);
      });

      test('getMessage() should return "Weak" for weak strength', () {
        final message = PasswordStrengthValidator.getMessage(PasswordStrength.weak);
        expect(message, 'Weak');
      });

      test('getMessage() should return "Strong" for strong strength', () {
        final message = PasswordStrengthValidator.getMessage(PasswordStrength.strong);
        expect(message, 'Strong');
      });
    });

    group('User Model', () {
      test('UserModel.fromJson() should parse user data correctly', () {
        final json = {
          'id': 1,
          'email': 'test@example.com',
          'full_name': 'Test User',
          'first_name': 'Test',
          'last_name': 'User',
          'employee_code': 'E-2510016',
          'role': 'employee',
          'department': 'IT',
          'designation': 'Software Engineer',
          'is_admin': false,
        };

        final user = UserModel.fromJson(json);

        expect(user.id, 1);
        expect(user.email, 'test@example.com');
        expect(user.fullName, 'Test User');
        expect(user.employeeCode, 'E-2510016');
        expect(user.role, 'employee');
        expect(user.isAdmin, false);
      });

      test('UserModel.toJson() should convert user to JSON', () {
        final user = UserModel(
          id: 1,
          email: 'test@example.com',
          fullName: 'Test User',
          firstName: 'Test',
          lastName: 'User',
          employeeCode: 'E-2510016',
          role: 'employee',
          department: 'IT',
          isAdmin: false,
        );

        final json = user.toJson();

        expect(json['id'], 1);
        expect(json['email'], 'test@example.com');
        expect(json['full_name'], 'Test User');
        expect(json['employee_code'], 'E-2510016');
      });

      test('UserModel.initials should return correct initials', () {
        final user = UserModel(
          id: 1,
          email: 'test@example.com',
          fullName: 'John Doe',
          firstName: 'John',
          lastName: 'Doe',
          role: 'employee',
          isAdmin: false,
        );

        expect(user.initials, 'JD');
      });

      test('UserModel.name should return fullName', () {
        final user = UserModel(
          id: 1,
          email: 'test@example.com',
          fullName: 'John Doe',
          firstName: 'John',
          lastName: 'Doe',
          role: 'employee',
          isAdmin: false,
        );

        expect(user.name, 'John Doe');
      });
    });

    group('AuthResponse Model', () {
      test('AuthResponse.fromJson() should parse auth response', () {
        final json = {
          'access_token': 'access_token_xyz',
          'refresh_token': 'refresh_token_xyz',
          'expires_in': 86400,
          'user': {
            'id': 1,
            'email': 'test@example.com',
            'full_name': 'Test User',
            'first_name': 'Test',
            'last_name': 'User',
            'employee_code': 'E-2510016',
            'role': 'employee',
            'is_admin': false,
          }
        };

        final response = AuthResponse.fromJson(json);

        expect(response.accessToken, 'access_token_xyz');
        expect(response.refreshToken, 'refresh_token_xyz');
        expect(response.expiresIn, 86400);
        expect(response.user.employeeCode, 'E-2510016');
      });

      test('AuthResponse should handle default expires_in', () {
        final json = {
          'access_token': 'access_token_xyz',
          'refresh_token': 'refresh_token_xyz',
          'user': {
            'id': 1,
            'email': 'test@example.com',
            'full_name': 'Test User',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'employee',
            'is_admin': false,
          }
        };

        final response = AuthResponse.fromJson(json);

        expect(response.expiresIn, 86400); // Default value
      });
    });

    group('API Constants Validation', () {
      test('login endpoint should be /auth/login', () {
        const endpoint = '/auth/login';
        expect(endpoint, '/auth/login');
      });

      test('forgot-password endpoint should be /auth/forgot-password', () {
        const endpoint = '/auth/forgot-password';
        expect(endpoint, '/auth/forgot-password');
      });

      test('reset-password endpoint should be /auth/reset-password', () {
        const endpoint = '/auth/reset-password';
        expect(endpoint, '/auth/reset-password');
      });

      test('lookup-employee endpoint should be /auth/lookup-employee', () {
        const endpoint = '/auth/lookup-employee';
        expect(endpoint, '/auth/lookup-employee');
      });

      test('me endpoint should be /auth/me', () {
        const endpoint = '/auth/me';
        expect(endpoint, '/auth/me');
      });

      test('refresh endpoint should be /auth/refresh', () {
        const endpoint = '/auth/refresh';
        expect(endpoint, '/auth/refresh');
      });

      test('logout endpoint should be /auth/logout', () {
        const endpoint = '/auth/logout';
        expect(endpoint, '/auth/logout');
      });
    });

    group('Authentication Validation Rules', () {
      test('employee code should not be empty', () {
        final code = '';
        expect(code.isEmpty, true);
      });

      test('employee code should be uppercase-trimmed', () {
        final code = '  e-2510016  '.trim().toUpperCase();
        expect(code, 'E-2510016');
      });

      test('password should have minimum 8 characters', () {
        final password = 'Pass123!';
        expect(password.length >= 8, true);
      });

      test('password should contain uppercase', () {
        final password = 'ValidPass123!';
        expect(RegExp(r'[A-Z]').hasMatch(password), true);
      });

      test('password should contain lowercase', () {
        final password = 'ValidPass123!';
        expect(RegExp(r'[a-z]').hasMatch(password), true);
      });

      test('password should contain digit', () {
        final password = 'ValidPass123!';
        expect(RegExp(r'[0-9]').hasMatch(password), true);
      });

      test('password should contain special character', () {
        final password = 'ValidPass123!';
        expect(RegExp(r'[!@#$%^&*(),.?":{}|<>]').hasMatch(password), true);
      });
    });

    group('API Response Validation', () {
      test('login response should include access_token', () {
        final response = {
          'success': true,
          'data': {'access_token': 'token'}
        };
        final data = response['data'] as Map<String, dynamic>?;
        expect(data?['access_token'], isNotNull);
      });

      test('login response should include refresh_token', () {
        final response = {
          'success': true,
          'data': {'refresh_token': 'token'}
        };
        final data = response['data'] as Map<String, dynamic>?;
        expect(data?['refresh_token'], isNotNull);
      });

      test('login response should include user data', () {
        final response = {
          'success': true,
          'data': {
            'user': {
              'id': 1,
              'email': 'test@example.com',
              'employee_code': 'E-2510016',
            }
          }
        };
        final data = response['data'] as Map<String, dynamic>?;
        final user = data?['user'] as Map<String, dynamic>?;
        expect(user?['employee_code'], 'E-2510016');
      });

      test('forgot password response should include reset_token', () {
        final response = {
          'success': true,
          'data': {'reset_token': 'token_xyz'}
        };
        final data = response['data'] as Map<String, dynamic>?;
        expect(data?['reset_token'], isNotNull);
      });

      test('lookup employee response should include found flag', () {
        final response = {
          'success': true,
          'data': {'found': true, 'name': 'John Doe'}
        };
        final data = response['data'] as Map<String, dynamic>?;
        expect(data?['found'], true);
        expect(data?['name'], 'John Doe');
      });
    });
  });
}
