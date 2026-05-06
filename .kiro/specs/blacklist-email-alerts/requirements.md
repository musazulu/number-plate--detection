# Requirements Document

## Introduction

This feature adds real-time email alerting to the existing ANPR backend. Whenever the `/detect` endpoint identifies a licence plate that appears on the blacklist, the system sends an email notification to a configured recipient. The email includes the plate number, detection timestamp, confidence score, and the saved snapshot image as an attachment. Alert delivery failures must not interrupt the normal detection response.

## Glossary

- **ANPR_API**: The existing Flask REST API defined in `api.py` that accepts image uploads, runs YOLO detection, performs OCR, and stores results in `plates.db`.
- **Blacklist**: The in-memory list of licence plate strings that are flagged as vehicles of interest.
- **Alert_Service**: The new component responsible for composing and sending email notifications when a blacklisted plate is detected.
- **SMTP_Config**: The externalized configuration (host, port, sender address, credentials, recipient address) required to connect to an SMTP server.
- **Detection_Event**: A single successful plate recognition result produced by the `/detect` endpoint, including plate text, confidence score, timestamp, and snapshot image path.
- **Snapshot**: The cropped JPEG image of the detected licence plate saved to the `snapshots/` directory.

## Requirements

### Requirement 1: Send Email Alert on Blacklisted Plate Detection

**User Story:** As a security operator, I want to receive an email whenever a blacklisted plate is detected, so that I can respond to the vehicle of interest in real time.

#### Acceptance Criteria

1. WHEN the ANPR_API detects a plate whose text matches an entry in the Blacklist, THE Alert_Service SHALL send an email notification to the configured recipient address.
2. WHEN the ANPR_API detects a plate whose text does not match any entry in the Blacklist, THE Alert_Service SHALL NOT send an email notification.
3. WHEN the ANPR_API detects the same blacklisted plate in multiple separate Detection_Events, THE Alert_Service SHALL send one email notification per Detection_Event.

---

### Requirement 2: Email Content

**User Story:** As a security operator, I want the alert email to contain all relevant detection details, so that I can assess the situation without logging into the dashboard.

#### Acceptance Criteria

1. THE Alert_Service SHALL include the detected plate text in the email subject line.
2. THE Alert_Service SHALL include the plate text, confidence score, and detection timestamp in the email body.
3. WHEN a Snapshot file exists for the Detection_Event, THE Alert_Service SHALL attach the Snapshot image to the email.
4. IF the Snapshot file does not exist at the expected path, THEN THE Alert_Service SHALL send the email without an attachment and SHALL log a warning indicating the missing file path.

---

### Requirement 3: SMTP Configuration

**User Story:** As a developer, I want SMTP settings to be read from environment variables, so that credentials are not hardcoded in source code and can be changed without modifying the codebase.

#### Acceptance Criteria

1. THE Alert_Service SHALL read SMTP host, port, sender address, sender password, and recipient address from environment variables at application startup.
2. IF a required SMTP environment variable is not set at startup, THEN THE ANPR_API SHALL log an error message identifying the missing variable and SHALL disable email alerting for the session.
3. WHERE TLS is enabled via configuration, THE Alert_Service SHALL establish the SMTP connection using STARTTLS.

---

### Requirement 4: Alert Delivery Fault Tolerance

**User Story:** As a system operator, I want a failed email delivery to not affect the plate detection response, so that the core ANPR functionality remains available even when the mail server is unreachable.

#### Acceptance Criteria

1. IF the Alert_Service fails to deliver an email due to an SMTP error, THEN THE ANPR_API SHALL still return a valid JSON detection response to the caller.
2. IF the Alert_Service fails to deliver an email, THEN THE Alert_Service SHALL log the error message and the plate text associated with the failed alert.
3. THE ANPR_API SHALL complete the detection response within 5 seconds regardless of Alert_Service delivery outcome.
