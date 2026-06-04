# RIBIL API Contract

## Authentication

POST /auth/register
POST /auth/login
GET /auth/profile

## GIS

POST /gis/detect-survey
POST /gis/reverse-geocode

## Verification

POST /verification/start
GET /verification/status/:id

## Reports

GET /reports/:id
POST /reports/pdf

## Dashboard

GET /dashboard