CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- properties
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    survey_no TEXT,
    village TEXT,
    hobli TEXT,
    taluk TEXT,
    district TEXT,
    lat FLOAT,
    lng FLOAT,
    area_sqft FLOAT,
    cdp_zone TEXT,
    status VARCHAR CHECK(status IN ('pending','verifying','verified','failed')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- property_documents
CREATE TABLE property_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    doc_type VARCHAR DEFAULT 'other',
    source VARCHAR NOT NULL,
    s3_key TEXT NOT NULL,
    filename TEXT,
    file_size_bytes INT,
    mime_type VARCHAR,
    version_no INT DEFAULT 1,
    is_latest BOOLEAN DEFAULT true,
    scraped_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

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

-- verification_status
CREATE TABLE verification_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    check_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    result_summary TEXT,
    flag_details JSONB,
    checked_at TIMESTAMPTZ,
    source_url TEXT,
    UNIQUE(property_id, check_type)
);

-- verification_reports
CREATE TABLE verification_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) UNIQUE,
    risk_score INT,
    risk_level VARCHAR,
    s3_key TEXT,
    download_url TEXT,
    url_expires_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    version INT DEFAULT 1
);