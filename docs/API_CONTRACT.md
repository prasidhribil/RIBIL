# RIBIL API Contracts

## Authentication

### POST /api/auth/register

Request

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}
```

Response

```json
{
  "success": true,
  "message": "User registered successfully"
}
```

---

### POST /api/auth/login

Request

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

Response

```json
{
  "success": true,
  "token": "jwt-token",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

### GET /api/auth/profile

Response

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}
```

---

## GIS

### POST /api/gis/detect-survey

Request

```json
{
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

Response

```json
{
  "surveyNumber": "47/3",
  "village": "Kadubeesanahalli"
}
```

---

### POST /api/gis/reverse-geocode

Request

```json
{
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

Response

```json
{
  "address": "Bangalore, Karnataka"
}
```

---

## Verification

### POST /api/verification/start

Request

```json
{
  "surveyNumber": "47/3"
}
```

Response

```json
{
  "verificationId": "VER-1001",
  "status": "started"
}
```

---

### GET /api/verification/status/:id

Response

```json
{
  "verificationId": "VER-1001",
  "status": "completed"
}
```

---

## Reports

### GET /api/reports/:id

Response

```json
{
  "reportId": 1,
  "reportName": "Land Verification Report"
}
```

---

### POST /api/reports/pdf

Response

```json
{
  "success": true,
  "downloadUrl": "/reports/report.pdf"
}
```

---

## Dashboard

### GET /api/dashboard

Response

```json
{
  "totalVerifications": 100,
  "pending": 12,
  "completed": 88
}
```
