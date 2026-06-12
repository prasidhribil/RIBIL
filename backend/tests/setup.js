// Ensure required env exists before app modules load (they fail-fast otherwise).
process.env.JWT_SECRET = process.env.JWT_SECRET || "test-secret";
process.env.NODE_ENV = "test";
