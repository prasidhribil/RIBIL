# Authentication Testing Checklist

## Registration

### TC-01 Valid Registration

Expected:

* User created
* OTP generated
* Status 201

### TC-02 Duplicate Email

Expected:

* Status 409

### TC-03 Weak Password

Expected:

* Status 422

### TC-04 Invalid Phone Number

Expected:

* Status 422

---

## OTP Verification

### TC-05 Correct OTP

Expected:

* User verified
* Status 200

### TC-06 Incorrect OTP

Expected:

* Status 401

### TC-07 Expired OTP

Expected:

* Status 401

### TC-08 OTP Reuse

Expected:

* Status 401

---

## Login

### TC-09 Correct Credentials

Expected:

* Access Token
* Refresh Token
* Status 200

### TC-10 Wrong Password

Expected:

* Status 401

### TC-11 Unverified User

Expected:

* Status 403

---

## JWT Middleware

### TC-12 Missing Token

Expected:

* Status 401

### TC-13 Invalid Token

Expected:

* Status 401

### TC-14 Expired Token

Expected:

* Status 401

### TC-15 Valid Token

Expected:

* Request Allowed

---

## Role Authorization

### TC-16 Admin Route with Buyer Token

Expected:

* Status 403

### TC-17 Admin Route with Admin Token

Expected:

* Status 200
