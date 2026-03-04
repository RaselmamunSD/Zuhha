# JWT Authentication Documentation

## Overview
This project uses JWT (JSON Web Token) authentication with access and refresh tokens.

## Configuration
- **Access Token Lifetime**: 60 minutes (configurable via `ACCESS_TOKEN_LIFETIME` env var)
- **Refresh Token Lifetime**: 7 days (configurable via `REFRESH_TOKEN_LIFETIME` env var)
- **Token Rotation**: Enabled (new refresh token on each refresh)
- **Token Blacklisting**: Enabled (revoked tokens cannot be reused)

## API Endpoints

### 1. User Registration
**Endpoint**: `POST /api/auth/register/`

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 2. User Login
**Endpoint**: `POST /api/auth/login/`

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 3. Refresh Access Token
**Endpoint**: `POST /api/auth/refresh_token/`

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 4. User Logout (Blacklist Token)
**Endpoint**: `POST /api/auth/logout/`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "detail": "Successfully logged out. Token has been blacklisted."
}
```

---

### 5. Get Current User
**Endpoint**: `GET /api/auth/me/`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

---

### 6. Change Password
**Endpoint**: `POST /api/auth/change_password/`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "old_password": "OldPass123",
  "new_password": "NewPass123",
  "new_password_confirm": "NewPass123"
}
```

**Response**:
```json
{
  "detail": "Password changed successfully.",
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 7. Update Profile
**Endpoint**: `PUT /api/auth/update_profile/` or `PATCH /api/auth/update_profile/`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com"
}
```

**Response**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

---

### 8. Forgot Password
**Endpoint**: `POST /api/auth/forgot_password/`

**Request Body**:
```json
{
  "email": "john@example.com"
}
```

**Response**:
```json
{
  "detail": "If an account exists with this email, a reset link has been sent.",
  "reset_url": "http://localhost:3000/reset-password?uid=..&token=..",
  "email_sent": true
}
```

---

### 9. Reset Password
**Endpoint**: `POST /api/auth/reset_password/`

**Request Body**:
```json
{
  "uid": "MQ",
  "token": "abc123xyz",
  "new_password": "NewSecurePass123",
  "new_password_confirm": "NewSecurePass123"
}
```

**Response**:
```json
{
  "detail": "Password has been reset successfully.",
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 10. Delete Account
**Endpoint**: `DELETE /api/auth/delete_account/`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**: `204 No Content`

---

## Usage in Frontend

### 1. Store Tokens
```javascript
// After login/register
const response = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();
localStorage.setItem('access_token', data.tokens.access);
localStorage.setItem('refresh_token', data.tokens.refresh);
```

### 2. Use Access Token in Requests
```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('/api/some-endpoint/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. Handle Token Refresh
```javascript
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/auth/refresh_token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    return data.tokens.access;
  } else {
    // Refresh token expired, redirect to login
    localStorage.clear();
    window.location.href = '/login';
  }
}

// Axios interceptor example
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const newAccessToken = await refreshAccessToken();
      originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
      return axios(originalRequest);
    }
    
    return Promise.reject(error);
  }
);
```

### 4. Logout
```javascript
async function logout() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  
  await fetch('/api/auth/logout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  localStorage.clear();
  window.location.href = '/login';
}
```

---

## Security Best Practices

1. **Store tokens securely**: Use httpOnly cookies or secure localStorage
2. **Always use HTTPS** in production
3. **Implement token refresh logic** before access token expires
4. **Blacklist tokens on logout** to prevent reuse
5. **Set appropriate token lifetimes** based on your security requirements
6. **Validate tokens on the backend** for every protected route
7. **Never expose refresh tokens** in URLs or logs

---

## Environment Variables

Add these to your `.env` file:

```env
# JWT Settings
ACCESS_TOKEN_LIFETIME=60          # minutes
REFRESH_TOKEN_LIFETIME=7          # days
JWT_SIGNING_KEY=your-secret-key   # Leave empty to use SECRET_KEY

# Frontend URL for password reset emails
FRONTEND_BASE_URL=http://localhost:3000
```

---

## Testing with cURL

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "SecurePass123"}'
```

### Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <your_access_token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh_token/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```

### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```
