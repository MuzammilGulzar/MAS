const params =
    new URLSearchParams(
        window.location.search
    );

const applicationId =
    params.get("application_id");

function getToken() {
    return localStorage.getItem("access_token");
}

async function loadReport(){

    const token = getToken();
    if (!token) {
        document.getElementById("reportContainer").innerHTML =
            `<p class="text-red-600">You must be logged in to view this report.</p>`;
        return;
    }

    const response = await fetch(
        `http://127.0.0.1:8000/report/${applicationId}`,
        {
            headers: {
                "Authorization": `Bearer ${token}`,
            },
        }
    );

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        document.getElementById("reportContainer").innerHTML =
            `<p class="text-red-600">${err.detail || "Failed to load report."}</p>`;
        return;
    }

    const report =
        await response.json();

    document.getElementById(
        "reportContainer"
    ).innerHTML = `
        <h2 class="text-2xl font-bold mb-4">
            Score: ${report.overall_score}
        </h2>

        <p class="mb-2">
            <strong>Recommendation:</strong>
            ${report.recommendation}
        </p>

        <p class="mb-4">
            <strong>Why:</strong>
            ${report.score_reason || ""}
        </p>

        <h3 class="text-xl font-semibold mt-6 mb-2">Strengths</h3>
        <ul class="list-disc list-inside mb-4">
            ${(report.strengths || []).map(s => `<li>${s}</li>`).join("")}
        </ul>

        <h3 class="text-xl font-semibold mt-6 mb-2">Weaknesses</h3>
        <ul class="list-disc list-inside mb-4">
            ${(report.weaknesses || []).map(w => `<li>${w}</li>`).join("")}
        </ul>

        <h3 class="text-xl font-semibold mt-6 mb-2">Final Feedback</h3>
        <p>${report.final_feedback || ""}</p>
    `;
}

loadReport();