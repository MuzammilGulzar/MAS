const params =
    new URLSearchParams(
        window.location.search
    );

const applicationId =
    params.get("application_id");

async function loadReport(){

    const response = await fetch(
        `http://127.0.0.1:8000/report/${applicationId}`
    );

    const report =
        await response.json();

    document.getElementById(
        "reportContainer"
    ).innerHTML = `
        <h2 class="text-2xl font-bold mb-4">
            Score: ${report.overall_score}
        </h2>

        <p>
            Recommendation:
            ${report.recommendation}
        </p>
    `;
}

loadReport();