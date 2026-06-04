const API_BASE = "http://localhost:3000";

async function testBackend() {

    const result = document.getElementById("result");

    try {

        const response = await fetch(`${API_BASE}/health`);

        const data = await response.json();

        result.innerHTML = `
            <h3>Backend Connected</h3>
            <p>Status: ${data.status}</p>
            <p>Service: ${data.service}</p>
        `;

    } catch (error) {

        console.error(error);

        result.innerHTML = `
            <h3>Connection Failed</h3>
        `;
    }
}

async function startVerification() {

    const result = document.getElementById("result");

    try {

        const response = await fetch(
            `${API_BASE}/api/verification/start`
        );

        const data = await response.json();

        result.innerHTML = `
            <h3>Verification Started</h3>

            <p><b>Survey Number:</b> ${data.surveyNumber}</p>

            <p><b>Village:</b> ${data.village}</p>

            <p><b>Status:</b> ${data.status}</p>
        `;

    } catch (error) {

        console.error(error);

        result.innerHTML = `
            <h3>Verification Failed</h3>
        `;
    }
}