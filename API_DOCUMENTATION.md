# Salahtime API Documentation

## Table of Contents
- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [API Root](#api-root)
  - [Authentication](#authentication-1)
  - [Prayer Times](#prayer-times)
  - [Locations](#locations)
  - [Users](#users)
  - [Subscriptions](#subscriptions)
  - [Mosques](#mosques)
- [Models](#models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

The Salahtime API provides a comprehensive RESTful interface for managing prayer times, locations, user accounts, subscriptions, and mosque information. This API uses JSON for request and response bodies and implements JWT (JSON Web Token) authentication.

---

## Base URL

```
http://localhost:8000/
```

For production, replace `localhost:8000` with your actual server domain.

---

## Authentication

This API uses **JWT (JSON Web Token)** authentication via SimpleJWT.

### Authentication Header

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

### Obtaining Tokens

1. **Register**: Create a new user account
2. **Login**: Get access and refresh tokens
3. **Refresh**: Use refresh token to get new access token

### Token Endpoints

| Token Type | Lifetime |
|------------|----------|
| Access Token | 60 minutes |
| Refresh Token | 1 day |

---

## API Endpoints

### API Root

**GET** `/`

Returns API information and available endpoints.

**Response:**
```json
{
    "message": "Welcome to Salahtime API",
    "version": "1.0",
    "endpoints": {
        "auth": "/api/auth/",
        "prayer_times": "/api/prayer-times/",
        "locations": "/api/locations/",
        "users": "/api/users/",
        "subscribe": "/api/subscribe/",
        "mosques": "/api/mosques/",
        "api": "/api/"
    },
    "documentation": "Use Django Admin at /admin/ or DRF browsable API for more details"
}
```

---

### Authentication

Base URL: `/api/auth/`

#### Register User

**POST** `/api/auth/register/`

Register a new user account.

**Request Body:**
```json
{
    "username": "string",
    "email": "user@example.com",
    "password": "string",
    "first_name": "string",
    "last_name": "string"
}
```

**Response (201 Created):**
```json
{
    "user": {
        "id": 1,
        "username": "string",
        "email": "user@example.com",
        "first_name": "string",
        "last_name": "string"
    },
    "tokens": {
        "refresh": "eyJ...",
        "access": "eyJ..."
    }
}
```

---

#### Login

**POST** `/api/auth/login/`

Authenticate user and receive tokens.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "string",
        "email": "user@example.com",
        "first_name": "string",
        "last_name": "string"
    },
    "tokens": {
        "refresh": "eyJ...",
        "access": "eyJ..."
    }
}
```

---

#### Logout

**POST** `/api/auth/logout/`

Logout current user. Note: JWT is stateless, client should discard tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "detail": "Successfully logged out. Please discard your tokens."
}
```

---

#### Refresh Token

**POST** `/api/auth/refresh_token/`

Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ..."
}
```

**Response (200 OK):**
```json
{
    "tokens": {
        "access": "eyJ...",
        "refresh": "eyJ..."
    }
}
```

---

#### Get Current User

**GET** `/api/auth/me/`

Get authenticated user's information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "string",
    "email": "user@example.com",
    "first_name": "string",
    "last_name": "string"
}
```

---

#### Change Password

**POST** `/api/auth/change_password/`

Change user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "old_password": "string",
    "new_password": "string"
}
```

**Response (200 OK):**
```json
{
    "detail": "Password changed successfully.",
    "tokens": {
        "refresh": "eyJ...",
        "access": "eyJ..."
    }
}
```

---

#### Update Profile

**PUT/PATCH** `/api/auth/update_profile/`

Update user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "first_name": "string",
    "last_name": "string",
    "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "string",
    "email": "user@example.com",
    "first_name": "string",
    "last_name": "string"
}
```

---

#### Delete Account

**DELETE** `/api/auth/delete_account/`

Delete user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content):**
```json
{
    "detail": "Account deleted successfully."
}
```

---

### Prayer Times

Base URL: `/api/prayer-times/`

#### List All Prayer Times

**GET** `/api/prayer-times/`

Get all prayer time records.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by date |
| ordering | string | Order by date or created_at |
| page | integer | Page number for pagination |

**Response (200 OK):**
```json
{
    "count": 365,
    "next": "http://localhost:8000/api/prayer-times/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "date": "2024-01-01",
            "fajr": "05:30:00",
            "sunrise": "06:45:00",
            "dhuhr": "12:30:00",
            "asr": "15:45:00",
            "maghrib": "18:30:00",
            "isha": "19:45:00",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

---

#### Get Today's Prayer Times

**GET** `/api/prayer-times/today/`

Get prayer times for today.

**Response (200 OK):**
```json
{
    "id": 1,
    "date": "2024-01-15",
    "fajr": "05:30:00",
    "sunrise": "06:45:00",
    "dhuhr": "12:30:00",
    "asr": "15:45:00",
    "maghrib": "18:30:00",
    "isha": "19:45:00",
    "created_at": "2024-01-15T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z"
}
```

---

#### Get Prayer Times by Date

**GET** `/api/prayer-times/by_date/?date=2024-01-15`

Get prayer times for a specific date.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date | string | Yes | Date in YYYY-MM-DD format |

**Response (200 OK):**
```json
{
    "id": 1,
    "date": "2024-01-15",
    "fajr": "05:30:00",
    "sunrise": "06:45:00",
    "dhuhr": "12:30:00",
    "asr": "15:45:00",
    "maghrib": "18:30:00",
    "isha": "19:45:00",
    "created_at": "2024-01-15T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z"
}
```

---

#### Monthly Prayer Times

**GET** `/api/prayer-times/monthly/`

Get monthly prayer times.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| city | integer | Filter by city ID |
| year | integer | Filter by year |
| month | integer | Filter by month (1-12) |
| search | string | Search by city name |
| ordering | string | Order by year, month, day |

**Response (200 OK):**
```json
{
    "count": 30,
    "results": [
        {
            "id": 1,
            "city": 1,
            "year": 2024,
            "month": 1,
            "day": 1,
            "fajr": "05:30:00",
            "sunrise": "06:45:00",
            "dhuhr": "12:30:00",
            "asr": "15:45:00",
            "maghrib": "18:30:00",
            "isha": "19:45:00"
        }
    ]
}
```

---

#### Get Current Month Prayer Times

**GET** `/api/prayer-times/monthly/current_month/?city=1`

Get current month's prayer times for a city.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| city | integer | Yes | City ID |

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "city": 1,
        "year": 2024,
        "month": 1,
        "day": 1,
        "fajr": "05:30:00",
        "sunrise": "06:45:00",
        "dhuhr": "12:30:00",
        "asr": "15:45:00",
        "maghrib": "18:30:00",
        "isha": "19:45:00"
    }
]
```

---

#### Prayer Time Adjustments

**GET** `/api/prayer-times/adjustments/`

Get prayer time adjustments.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| city | integer | Filter by city ID |
| is_active | boolean | Filter by active status |
| search | string | Search by city name or prayer name |
| prayer_name | string | Filter by prayer name (fajr, sunrise, dhuhr, asr, maghrib, isha) |

**Response (200 OK):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "prayer_name": "fajr",
            "adjustment_minutes": 5,
            "city": 1,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

---

### Locations

Base URL: `/api/locations/`

#### List Countries

**GET** `/api/locations/countries/`

Get all countries.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by name or code |
| is_active | boolean | Filter by active status |
| ordering | string | Order by name or code |

**Response (200 OK):**
```json
{
    "count": 195,
    "results": [
        {
            "id": 1,
            "name": "Bangladesh",
            "code": "BGD",
            "phone_code": "+880",
            "currency": "BDT",
            "currency_symbol": "৳",
            "is_active": true
        }
    ]
}
```

---

#### List Cities

**GET** `/api/locations/cities/`

Get all cities.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| country | integer | Filter by country ID |
| is_active | boolean | Filter by active status |
| is_capital | boolean | Filter by capital cities |
| search | string | Search by city or country name |
| ordering | string | Order by name or country |

**Response (200 OK):**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "name": "Dhaka",
            "country": 1,
            "country_name": "Bangladesh",
            "latitude": "23.810300",
            "longitude": "90.412500",
            "timezone": "Asia/Dhaka",
            "elevation": 23,
            "is_active": true,
            "is_capital": true
        }
    ]
}
```

---

#### Search Cities

**GET** `/api/locations/cities/search/?q=Dhaka`

Search cities by name.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query (min 2 characters) |

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Dhaka",
        "country": 1,
        "country_name": "Bangladesh",
        "latitude": "23.810300",
        "longitude": "90.412500",
        "timezone": "Asia/Dhaka",
        "is_capital": true
    }
]
```

---

#### Find City by Coordinates

**GET** `/api/locations/cities/by_coordinates/?latitude=23.8103&longitude=90.4125`

Find nearest city by coordinates.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| latitude | number | Yes | Latitude coordinate |
| longitude | number | Yes | Longitude coordinate |

**Response (200 OK):**
```json
{
    "id": 1,
    "name": "Dhaka",
    "country": 1,
    "country_name": "Bangladesh",
    "latitude": "23.810300",
    "longitude": "90.412500",
    "timezone": "Asia/Dhaka",
    "elevation": 23,
    "is_active": true,
    "is_capital": true
}
```

---

### Users

Base URL: `/api/users/`

#### List Users

**GET** `/api/users/`

Get all users (Admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by username, email, first_name, last_name |
| ordering | string | Order by username or date_joined |

**Response (200 OK):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
    ]
}
```

---

#### Get Current User

**GET** `/api/users/me/`

Get authenticated user's information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

---

#### User Profiles

**GET** `/api/users/profile/`

Get user profiles.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "count": 1,
    "results": [
        {
            "id": 1,
            "user": 1,
            "bio": "string",
            "phone": "+1234567890",
            "timezone": "Asia/Dhaka",
            "preferred_language": "en",
            "notifications_enabled": true
        }
    ]
}
```

---

#### Get Current User's Profile

**GET** `/api/users/profile/me/`

Get current user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "user": 1,
    "bio": "string",
    "phone": "+1234567890",
    "timezone": "Asia/Dhaka",
    "preferred_language": "en",
    "notifications_enabled": true
}
```

---

#### User Locations

**GET** `/api/users/locations/`

Get user's saved locations.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by city name or label |

**Response (200 OK):**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "user": 1,
            "city": 1,
            "label": "Home",
            "is_default": true
        }
    ]
}
```

---

#### Get Default Location

**GET** `/api/users/locations/default/`

Get user's default location.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "user": 1,
    "city": 1,
    "label": "Home",
    "is_default": true
}
```

---

### Subscriptions

Base URL: `/api/subscribe/`

#### Create Subscription

**POST** `/api/subscribe/`

Create a new subscription.

**Request Body:**
```json
{
    "email": "user@example.com",
    "phone": "+1234567890",
    "subscription_type": "daily",
    "city": 1
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "phone": "+1234567890",
    "subscription_type": "daily",
    "city": 1,
    "is_active": false,
    "activation_token": "abc123..."
}
```

---

#### List Subscriptions

**GET** `/api/subscribe/`

Get all subscriptions (Admin) or user's subscriptions.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "email": "user@example.com",
            "phone": "+1234567890",
            "subscription_type": "daily",
            "city": 1,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

---

#### Activate Subscription

**POST** `/api/subscribe/activate/`

Activate a subscription using token.

**Request Body:**
```json
{
    "token": "abc123..."
}
```

**Response (200 OK):**
```json
{
    "detail": "Subscription activated successfully."
}
```

---

#### Unsubscribe

**POST** `/api/subscribe/unsubscribe/`

Unsubscribe using email.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
    "detail": "Unsubscribed successfully."
}
```

---

#### Subscription Logs

**GET** `/api/subscribe/logs/`

Get subscription notification logs.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "subscription": 1,
            "sent_at": "2024-01-15T05:30:00Z",
            "status": "sent",
            "message": "Prayer times for today"
        }
    ]
}
```

---

### Mosques

Base URL: `/api/mosques/`

#### List Mosques

**GET** `/api/mosques/`

Get all mosques.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| city | integer | Filter by city ID |
| country | integer | Filter by country ID |
| is_verified | boolean | Filter by verified status |
| is_active | boolean | Filter by active status |
| has_parking | boolean | Filter by parking availability |
| has_jumuah | boolean | Filter by Jumuah prayer availability |
| search | string | Search by name, address, city, country |
| ordering | string | Order by name or created_at |

**Response (200 OK):**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "name": "Baitur Mukarram",
            "address": "Dhaka, Bangladesh",
            "city": 1,
            "latitude": "23.7365",
            "longitude": "90.4054",
            "phone": "+880-2-123456",
            "capacity": 5000,
            "has_parking": true,
            "has_jumuah": true,
            "is_verified": true,
            "is_active": true
        }
    ]
}
```

---

#### Get Mosque Details

**GET** `/api/mosques/{id}/`

Get detailed mosque information.

**Response (200 OK):**
```json
{
    "id": 1,
    "name": "Baitur Mukarram",
    "address": "Dhaka, Bangladesh",
    "city": 1,
    "latitude": "23.7365",
    "longitude": "90.4054",
    "phone": "+880-2-123456",
    "email": "info@mosque.org",
    "website": "https://mosque.org",
    "capacity": 5000,
    "has_parking": true,
    "has_jumuah": true,
    "facilities": ["prayer_hall", "women_prayer_area", "library"],
    "services": ["quran_classes", "islamic_school"],
    "is_verified": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
}
```

---

#### Find Nearby Mosques

**GET** `/api/mosques/nearby/?latitude=23.8103&longitude=90.4125&radius=5`

Find mosques near a location.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| latitude | number | Yes | Latitude coordinate |
| longitude | number | Yes | Longitude coordinate |
| radius | number | No | Search radius in km (default: 10) |

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Baitur Mukarram",
        "address": "Dhaka, Bangladesh",
        "city": 1,
        "latitude": "23.7365",
        "longitude": "90.4054",
        "phone": "+880-2-123456",
        "capacity": 5000,
        "has_parking": true,
        "has_jumuah": true,
        "is_verified": true,
        "is_active": true,
        "distance_km": 1.5
    }
]
```

---

#### Mosque Images

**GET** `/api/mosques/{mosque_id}/images/`

Get mosque images.

**Response (200 OK):**
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "mosque": 1,
            "image": "/media/mosques/image1.jpg",
            "is_primary": true,
            "caption": "Main entrance",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

---

### API (General)

Base URL: `/api/`

#### Prayer Times CRUD

**GET** `/api/prayertimes/`

**POST** `/api/prayertimes/`

**GET** `/api/prayertimes/{id}/`

**PUT/PATCH** `/api/prayertimes/{id}/`

**DELETE** `/api/prayertimes/{id}/`

---

#### Locations CRUD

**GET** `/api/locations/`

**POST** `/api/locations/`

**GET** `/api/locations/{id}/`

**PUT/PATCH** `/api/locations/{id}/`

**DELETE** `/api/locations/{id}/`

---

#### User Preferences CRUD

**GET** `/api/preferences/`

**POST** `/api/preferences/`

**GET** `/api/preferences/{id}/`

**PUT/PATCH** `/api/preferences/{id}/`

**DELETE** `/api/preferences/{id}/`

---

## Models

### PrayerTime
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| date | date | Date for prayer times |
| fajr | time | Fajr prayer time |
| sunrise | time | Sunrise time |
| dhuhr | time | Dhuhr prayer time |
| asr | time | Asr prayer time |
| maghrib | time | Maghrib prayer time |
| isha | time | Isha prayer time |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### MonthlyPrayerTime
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| city | foreign key | Reference to City |
| year | integer | Year |
| month | integer | Month (1-12) |
| day | integer | Day (1-31) |
| fajr-sunset | time | Prayer times |

### Country
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| name | string | Country name |
| code | string | ISO 3166-1 alpha-3 code |
| phone_code | string | International phone code |
| currency | string | Currency code |
| currency_symbol | string | Currency symbol |
| is_active | boolean | Active status |

### City
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| name | string | City name |
| country | foreign key | Reference to Country |
| latitude | decimal | Latitude coordinate |
| longitude | decimal | Longitude coordinate |
| timezone | string | Timezone name |
| elevation | integer | Elevation in meters |
| is_active | boolean | Active status |
| is_capital | boolean | Capital city flag |

### Mosque
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| name | string | Mosque name |
| address | string | Full address |
| city | foreign key | Reference to City |
| latitude | decimal | Latitude coordinate |
| longitude | decimal | Longitude coordinate |
| phone | string | Contact phone |
| email | string | Contact email |
| website | string | Website URL |
| capacity | integer | Worshipper capacity |
| has_parking | boolean | Parking availability |
| has_jumuah | boolean | Jumuah prayer availability |
| is_verified | boolean | Verified status |
| is_active | boolean | Active status |

### Subscription
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| email | string | Subscriber email |
| phone | string | Subscriber phone |
| subscription_type | string | Type: daily, weekly, monthly |
| city | foreign key | Reference to City |
| is_active | boolean | Active status |
| activation_token | string | Activation token |

---

## Error Handling

The API uses standard HTTP status codes to indicate success or failure.

### Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no content to return |
| 400 | Bad Request - Invalid request parameters |
| 401 | Unauthorized - Authentication required or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

### Error Response Format

```json
{
    "detail": "Error message description"
}
```

For validation errors:
```json
{
    "field_name": [
        "Error message"
    ]
}
```

---

## Rate Limiting

Currently, there is no rate limiting configured. For production deployment, consider implementing rate limiting using Django REST Framework's throttling features or a reverse proxy like Nginx.

---

## Testing

A Postman collection is available at `salahtime.postman_collection.json` in the project root directory. Import this file into Postman to test all API endpoints.

---

## Technology Stack

- **Framework**: Django 4.2.27
- **API Framework**: Django REST Framework 3.14.0
- **Authentication**: SimpleJWT 5.3.0
- **Caching**: Redis
- **Task Queue**: Celery
- **Database**: SQLite3 (default) / PostgreSQL (recommended for production)

---

## Version History

- **1.0.0** - Initial release
  - User authentication (JWT)
  - Prayer times management
  - Location management (countries, cities)
  - User profiles and preferences
  - Subscription management
  - Mosque directory

---

*Last updated: 2024*

