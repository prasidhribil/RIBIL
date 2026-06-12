-- Member 5 — Document Pipeline schema (Sprint 1, D-01)
-- Canonical migration for the 5 document/verification tables.
-- Requires the auth `users` table (Member 1) to exist first; for standalone
-- local development run migrations/000_dev_users_stub.sql before this file.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS postgis;

-- properties
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    survey_no TEXT,
    village TEXT,
    hobli TEXT,
    taluk TEXT,
    district TEXT,
    lat FLOAT,
    lng FLOAT,
    area_sqft FLOAT,
    cdp_zone TEXT,
    status VARCHAR CHECK (status IN ('pending','verifying','verified','failed')) DEFAULT 'pending',
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_properties_user ON properties(user_id);
CREATE INDEX idx_properties_geom ON properties USING GIST(geom);

-- property_documents
CREATE TABLE property_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    doc_type VARCHAR CHECK (doc_type IN
        ('rtc','pahani','mutation','ec','khata','sale_deed','sketch','tax_receipt','court_order','ngt_order','other'))
        DEFAULT 'other',
    source VARCHAR CHECK (source IN ('scraped','uploaded')) NOT NULL,
    s3_key TEXT NOT NULL,
    filename TEXT,
    file_size_bytes INT,
    mime_type VARCHAR,
    version_no INT DEFAULT 1,
    is_latest BOOLEAN DEFAULT true,
    scraped_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_property_documents_property ON property_documents(property_id);

-- doc_ocr_extracts
CREATE TABLE doc_ocr_extracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES property_documents(id) ON DELETE CASCADE,
    owner_name TEXT,
    survey_no TEXT,
    area_acres FLOAT,
    land_use TEXT,
    registration_date DATE,
    amount_rs BIGINT,
    parties JSONB,
    raw_extract TEXT,
    extracted_at TIMESTAMPTZ DEFAULT NOW()
);

-- verification_status (one row per check_type, 14 total)
CREATE TABLE verification_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    check_type VARCHAR CHECK (check_type IN
        ('rtc','pahani','mutation','ec','ecourts_district','ecourts_hc','ecourts_sc',
         'bda_acquisition','bda_layout','rera','bescom','bwssb','bbmp','cctns')) NOT NULL,
    status VARCHAR CHECK (status IN ('pending','running','passed','flagged','failed','skipped')) DEFAULT 'pending',
    result_summary TEXT,
    flag_details JSONB,
    checked_at TIMESTAMPTZ,
    source_url TEXT,
    UNIQUE (property_id, check_type)
);

CREATE INDEX idx_verification_status_property ON verification_status(property_id);

-- verification_reports
CREATE TABLE verification_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL UNIQUE REFERENCES properties(id) ON DELETE CASCADE,
    risk_score INT,
    risk_level VARCHAR CHECK (risk_level IN ('green','amber','red')),
    s3_key TEXT,
    download_url TEXT,
    url_expires_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    version INT DEFAULT 1
);
