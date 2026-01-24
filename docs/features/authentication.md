# Authentication Feature

The authentication system provides secure user account management, login/logout functionality, and optional two-factor authentication.

---

## Overview

Mnemosyne uses **JWT (JSON Web Token)** authentication. When users log in, they receive a token that must be included in subsequent requests to access protected resources.

---

## Features

### Account Management

| Feature | Description |
|---------|-------------|
| Registration | Create new accounts with email verification |
| Login | Authenticate and receive JWT token |
| Password Change | Change password while logged in |
| Password Reset | Reset forgotten password via email |
| Profile Management | Update display name and preferences |

### Security Features

| Feature | Description |
|---------|-------------|
| Two-Factor Authentication (2FA) | TOTP-based secondary verification |
| Account Lockout | Automatic lockout after failed attempts |
| Session Management | Track and revoke active sessions |
| Secure Password Storage | bcrypt hashing with salt |

---

## User Registration

### Requirements

- **Username**: 3-50 characters, alphanumeric and underscores
- **Email**: Valid email format, unique per account
- **Password**: Minimum 8 characters with:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

### Registration Flow

```
1. User submits registration form
2. System validates input
3. Password is hashed with bcrypt
4. User record created
5. JWT token returned
6. User is logged in
```

### Rate Limit

**5 registrations per hour** per IP address

---

## Authentication (Login)

### Login Flow

```
1. User submits credentials (username/email + password)
2. System finds user by identifier
3. Password verified against hash
4. If 2FA enabled:
   a. Prompt for TOTP code
   b. Verify code
5. JWT token generated
6. Token returned to client
```

### Token Format

```json
{
  "sub": "username",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Token Usage

Include the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Rate Limit

**10 login attempts per minute** per IP address

---

## Password Security

### Password Hashing

Passwords are never stored in plain text. Mnemosyne uses **bcrypt** with:
- Cost factor of 12 (configurable)
- Automatic salt generation
- Constant-time comparison

### Password Reset

```
1. User requests reset via email
2. System generates secure token (32 bytes)
3. Token emailed to user (expires in 1 hour)
4. User clicks link with token
5. User enters new password
6. Token invalidated, password updated
```

---

## Two-Factor Authentication (2FA)

### Setup Process

```
1. User requests 2FA setup
2. System generates TOTP secret
3. QR code displayed for authenticator app
4. User scans code with app (Google Authenticator, etc.)
5. User enters verification code
6. 2FA enabled
7. Backup codes provided (8 codes)
```

### Login with 2FA

```
1. User enters username and password
2. If valid, prompt for TOTP code
3. User enters 6-digit code from app
4. Code verified (30-second window)
5. JWT token issued
```

### Backup Codes

- 8 backup codes generated on 2FA setup
- Each code can only be used once
- Codes are hashed before storage
- Regenerate codes if needed

---

## Account Lockout

### Trigger Conditions

- **5 failed login attempts** within 30 minutes

### Lockout Duration

- **30 minutes** automatic unlock
- Manual unlock available via admin

### Lockout Flow

```
1. Failed login attempt recorded
2. Counter incremented
3. If counter >= 5:
   a. Account locked
   b. Lockout time recorded
4. On next attempt:
   a. Check if locked
   b. Check if lockout expired
   c. If expired, reset counter
```

---

## Session Management

### Active Sessions

Users can view all active sessions:
- Device/browser information
- IP address
- Last activity time
- Login time

### Session Revocation

Users can revoke any active session:
- Individual session logout
- "Log out all devices" option

---

## API Endpoints

### Registration

```http
POST /register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Login

```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecurePass123!
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /me
Authorization: Bearer <token>
```

Response:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Change Password

```http
POST /change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### Setup 2FA

```http
POST /2fa/setup
Authorization: Bearer <token>
```

Response:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/Mnemosyne:johndoe?secret=..."
}
```

### Enable 2FA

```http
POST /2fa/enable
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "123456"
}
```

Response:
```json
{
  "success": true,
  "backup_codes": ["abc123", "def456", ...]
}
```

---

## Error Responses

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid credentials |
| 403 | Forbidden - Account locked |
| 409 | Conflict - Username/email exists |
| 422 | Validation Error - Input failed validation |
| 429 | Too Many Requests - Rate limit exceeded |

---

## Security Best Practices

### For Users

1. Use a strong, unique password
2. Enable 2FA for additional security
3. Store backup codes securely
4. Log out on shared devices
5. Review active sessions regularly

### For Administrators

1. Keep SECRET_KEY secure and unique per environment
2. Use HTTPS in production
3. Monitor failed login attempts
4. Regularly rotate JWT secrets
5. Keep dependencies updated
