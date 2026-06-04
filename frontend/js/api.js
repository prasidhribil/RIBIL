const API_BASE_URL = "http://localhost:3000";

async function getHealth() {
    const response = await fetch(
        `${API_BASE_URL}/health`
    );

    return await response.json();
}

async function startVerificationAPI() {

    const response = await fetch(
        `${API_BASE_URL}/api/verification/start`
    );

    return await response.json();
}