# Postman — RIBIL Auth (Sprint 1)

## Files
- `RIBIL_Auth_Sprint1.postman_collection.json` — all 9 auth endpoints + negative/edge cases.
- `RIBIL_Auth_Sprint1.postman_environment.json` — `baseUrl`, `token`, `adminToken`, `userId`.

## Usage
1. In Postman: **Import** both files.
2. Select the **RIBIL Auth - Local** environment.
3. Start the API: `cd backend && npm run dev` (defaults to `http://localhost:3000`).
4. Run **Auth → Register**, then **Auth → Login** — the login test script saves the JWT into the
   `{{token}}` variable automatically. Run **Login (admin)** with an admin account to populate
   `{{adminToken}}`.
5. Run the **Protected** and **Admin & Users** requests; they send `Authorization: Bearer {{token}}`
   (or `{{adminToken}}`) automatically.

> To create an admin, register normally then `UPDATE users SET role='admin' WHERE email='...';`
> (`/register` always assigns `role = 'user'`).
