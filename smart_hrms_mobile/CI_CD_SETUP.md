# CI/CD Setup Guide - Smart HRMS Mobile

## Overview
Complete CI/CD pipeline setup using GitHub Actions for automated testing, building, and deployment of the Smart HRMS Flutter mobile application.

## Workflows

### 1. Test Suite Workflow (`test.yml`)
**Trigger**: On push to main/develop, on PR, daily schedule

**Jobs**:
- **test**: Run unit and integration tests
  - Checkout code
  - Setup Flutter (multiple versions)
  - Install dependencies
  - Analyze code quality
  - Format checking
  - Unit tests with coverage
  - Integration tests
  - Upload coverage to Codecov
  - Check coverage threshold (75%)

- **security-scan**: Security vulnerability scanning
  - Dependency checking
  - Secret scanning with Trufflehog
  - Vulnerability detection

- **performance**: Performance and size analysis
  - Run performance tests
  - Build APK for analysis
  - Analyze APK size (max 100MB)

- **build**: Build artifacts
  - Build APK and App Bundle
  - Upload artifacts to GitHub

- **notify**: Send notifications
  - Slack notifications on success/failure

### 2. Build Release Workflow (`build.yml`)
**Trigger**: On tag push (v*), manual workflow dispatch

**Jobs**:
- **build-android**: Android build
  - Build APK (arm64)
  - Build App Bundle
  - Sign APK
  - Upload to Firebase App Distribution

- **build-ios**: iOS build
  - Build iOS release
  - Sign with provisioning profile
  - Build IPA
  - Upload to TestFlight

- **test-build**: Test built APK
  - Start Android emulator
  - Install APK
  - Run integration tests

- **release**: Create GitHub Release
  - Create release notes
  - Upload binaries
  - Notify Slack

## Setup Instructions

### Prerequisites
- GitHub repository with Flutter project
- Flutter SDK installed locally
- Java 17+ installed
- Xcode for iOS builds (macOS)

### Step 1: Enable GitHub Actions
1. Go to repository Settings
2. Navigate to Actions > General
3. Enable GitHub Actions
4. Set workflow permissions to "Read and write permissions"

### Step 2: Configure Secrets
Add these secrets to GitHub repository (Settings > Secrets > Actions):

**Android Signing**
```
KEYSTORE_PROPERTIES - Content of keystore.properties file
RELEASE_KEYSTORE - Base64-encoded release.keystore file
```

**iOS Signing**
```
IOS_PROVISIONING_PROFILE - Base64-encoded .mobileprovision file
IOS_SIGNING_CERTIFICATE - Base64-encoded certificate.p12 file
IOS_CERTIFICATE_PASSWORD - Password for .p12 certificate
APPLE_ID - Apple Developer account email
APPLE_APP_SPECIFIC_PASSWORD - App-specific password
```

**Firebase**
```
FIREBASE_PROJECT_ID - Firebase project ID
FIREBASE_ANDROID_APP_ID - Android app ID
FIREBASE_TOKEN - Firebase CLI token
```

**Notifications**
```
SLACK_WEBHOOK - Slack webhook URL for notifications
```

### Step 3: Create Keystore (Android)
```bash
# Generate keystore
keytool -genkey -v -keystore ~/.android/release.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload -storepass password -keypass password

# Encode and add to GitHub Secrets
base64 ~/.android/release.keystore
```

### Step 4: Create Provisioning Profile (iOS)
1. Go to Apple Developer account
2. Create provisioning profile
3. Download .mobileprovision file
4. Encode and add to GitHub Secrets

### Step 5: Configure Workflows
1. Copy `.github/workflows/` files to repository
2. Update workflow file paths if needed
3. Configure job dependencies and triggers
4. Test with manual workflow dispatch

### Step 6: Setup Coverage Reporting
```bash
# Install coverage tools
flutter pub add --dev coverage

# Generate coverage locally
flutter test --coverage

# Check coverage
python3 scripts/check_coverage.py --threshold 75
```

## Running Workflows

### Manually Trigger Test Workflow
```bash
gh workflow run test.yml
```

### Manually Trigger Build Workflow
```bash
gh workflow run build.yml -f build_type=release
```

### View Workflow Runs
```bash
gh run list
gh run view <run-id>
```

## Test Execution

### Running Tests Locally
```bash
# Unit tests
flutter test

# Integration tests
flutter test integration_test/

# With coverage
flutter test --coverage

# Specific test file
flutter test test/features/leave/data/models/leave_model_test.dart
```

### Coverage Report
```bash
# Generate coverage
flutter test --coverage

# View HTML report
open coverage/index.html
```

## Build Artifacts

### APK Output Locations
- Release APK: `build/app/outputs/apk/release/app-release.apk`
- Split APKs: `build/app/outputs/apk/release/*-arm64-v8a.apk`
- App Bundle: `build/app/outputs/bundle/release/app-release.aab`

### IPA Output Locations
- IPA: `build/ios_build/ipa/Smart HRMS.ipa`

## Performance Monitoring

### APK Size Analysis
- Target: < 100MB
- Measured in release build
- Reported in workflow logs

### Test Performance
- Unit tests: < 5 minutes
- Integration tests: < 10 minutes
- Overall pipeline: < 30 minutes

## Security Considerations

### Secrets Management
- Use GitHub Secrets for sensitive data
- Never commit .keystore or certificates
- Rotate signing certificates regularly
- Use environment-specific secrets

### Secret Scanning
- Trufflehog scans for exposed credentials
- Prevents accidental secret commits
- Runs on every push

### Dependency Checking
- Scans for known vulnerabilities
- Updates pubspec.lock regularly
- Reviews security advisories

## Troubleshooting

### Common Issues

**Test Failures**
```bash
# Clear pub cache
flutter clean
flutter pub cache repair

# Reinstall dependencies
flutter pub get

# Run specific test for debugging
flutter test -v test/path/to/test.dart
```

**Coverage Not Generated**
```bash
# Ensure coverage tool is available
flutter pub add --dev coverage

# Run with coverage flag
flutter test --coverage --no-pub
```

**APK Signing Failure**
- Verify keystore file format
- Check password is correct
- Ensure Java 17+ installed

**iOS Build Failure**
- Verify Xcode version (14+)
- Check provisioning profile validity
- Ensure certificate is in keychain

### View Workflow Logs
1. Go to repository Actions tab
2. Select workflow run
3. Click failed job
4. Expand step logs

## Best Practices

### Commit Strategy
- Use semantic versioning (v1.2.3)
- Create tags for releases
- Add descriptive commit messages
- Squash commits for clean history

### Testing
- Write tests before code (TDD)
- Maintain 75%+ coverage
- Test edge cases
- Mock external dependencies

### Code Quality
- Run analyzer regularly
- Format code consistently
- Use lints
- Review PRs thoroughly

### Release Process
1. Update version in pubspec.yaml
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. Monitor GitHub Actions for build
6. Review release notes
7. Publish to app stores

## Continuous Integration Checklist

Before production release, verify:
- [ ] All tests passing (75%+ coverage)
- [ ] Code analysis clean
- [ ] Security scan passed
- [ ] APK size < 100MB
- [ ] Performance benchmarks met
- [ ] Integration tests passing
- [ ] Artifacts generated
- [ ] Release notes complete
- [ ] Slack notification received
- [ ] Manual testing on staging device

## Monitoring and Alerts

### Slack Notifications
Workflow notifications include:
- Test results (pass/fail)
- Build status
- Release announcements
- Coverage reports

### Email Notifications
- Configured in GitHub
- Sent for workflow failures
- Sent for manual reviews

### Metrics to Track
- Build success rate
- Average test duration
- Code coverage trend
- APK size trend
- Release frequency

## Advanced Configuration

### Matrix Testing
Test on multiple Flutter versions:
```yaml
matrix:
  flutter-version: [ 3.19.0, 3.22.0 ]
```

### Conditional Jobs
Run jobs based on conditions:
```yaml
if: startsWith(github.ref, 'refs/tags/')
```

### Custom Actions
Create reusable actions:
```yaml
- uses: ./github/actions/test-coverage
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Flutter Testing Guide](https://flutter.dev/docs/testing)
- [Codecov Integration](https://docs.codecov.io/docs)
- [Firebase App Distribution](https://firebase.google.com/docs/app-distribution)
- [TestFlight Documentation](https://developer.apple.com/testflight/)

## Support

For issues or questions:
1. Check workflow logs
2. Review troubleshooting section
3. Consult Flutter documentation
4. Open GitHub issue
5. Contact team lead
