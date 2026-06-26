// async function loadApplications() {
//   const response = await fetch("http://127.0.0.1:8000/candidate/applications");

//   const applications = await response.json();

//   const container = document.getElementById("applicationsContainer");

//   container.innerHTML = "";

//   applications.forEach((app) => {
//     container.innerHTML += `
// <div class="bg-white p-6 rounded-xl shadow">

//     <h2 class="text-xl font-bold">
//         ${app.job_title}
//     </h2>

//     <p class="mt-2">
//         Status: ${app.status}
//     </p>

//     <p>
//         Applied: ${app.applied_at}
//     </p>

//     <div class="mt-4 flex gap-3">

//         ${
//           app.status === "interview_pending"
//             ? `<button
//                 onclick="continueInterview(${app.application_id})"
//                 class="bg-blue-600 text-white px-4 py-2 rounded">
//                 Continue Interview
//             </button>`
//             : ""
//         }

//         ${
//           app.status === "interview_completed"
//             ? `<button
//                 onclick="viewReport(${app.application_id})"
//                 class="bg-green-600 text-white px-4 py-2 rounded">
//                 View Report
//             </button>`
//             : ""
//         }

//     </div>

// </div>
// `;
//   });
// }

// loadApplications();

// function continueInterview(applicationId){

//     window.location.href =
//         `interview.html?application_id=${applicationId}`;
// }

// function viewReport(applicationId){

//     window.location.href =
//         `report.html?application_id=${applicationId}`;
// }

async function loadApplications() {

    const token = localStorage.getItem("access_token")
    if (!token) {
        window.location.href = "../../components/login.html"
        return
    }

    const container = document.getElementById("applicationsContainer")

    try {
        const response = await fetch("http://127.0.0.1:8000/candidate/applications", {
            headers: { "Authorization": `Bearer ${token}` }   // ← FIXED: was missing
        })

        if (!response.ok) {
            const err = await response.json().catch(() => ({}))
            container.innerHTML = `<p class="text-red-500">Error: ${err.detail || "Failed to load applications"}</p>`
            return
        }

        const applications = await response.json()

        if (!applications.length) {
            container.innerHTML = `
                <div class="bg-white p-8 rounded-xl shadow text-center">
                    <p class="text-4xl mb-4">📋</p>
                    <p class="text-gray-500 text-lg">You haven't applied for any jobs yet.</p>
                    <a href="jobs.html" class="mt-4 inline-block bg-blue-600 text-white px-6 py-2 rounded-lg">Browse Jobs</a>
                </div>`
            return
        }

        container.innerHTML = ""

        applications.forEach(app => {

            const statusColors = {
                "applied":               "bg-gray-100 text-gray-700",
                "interview_pending":     "bg-blue-100 text-blue-700",
                "interview_in_progress": "bg-yellow-100 text-yellow-700",
                "interview_completed":   "bg-purple-100 text-purple-700",
                "shortlisted":           "bg-green-100 text-green-700",
                "hired":                 "bg-green-100 text-green-700",
                "rejected":              "bg-red-100 text-red-700",
            }
            const statusClass = statusColors[app.status] || "bg-gray-100 text-gray-700"
            const statusLabel = (app.status || "applied").replace(/_/g, " ")

            const appliedDate = app.applied_at
                ? new Date(app.applied_at).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })
                : "—"

            // Action buttons based on status
            let actionBtn = ""
            if (app.status === "interview_pending") {
                actionBtn = `
                    <a href="../interview.html?application_id=${app.application_id}&job_id=${app.job_id}"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition">
                        Start Interview →
                    </a>`
            } else if (app.status === "interview_completed" || app.status === "shortlisted" || app.status === "hired") {
                actionBtn = `
                    <a href="report.html?application_id=${app.application_id}"
                        class="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition">
                        View Report
                    </a>`
            }

            container.innerHTML += `
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div class="flex items-start justify-between">
                        <div>
                            <h2 class="text-xl font-bold text-gray-900">${app.job_title}</h2>
                            <p class="text-sm text-gray-400 mt-1">Applied: ${appliedDate}</p>
                        </div>
                        <span class="text-xs font-semibold px-3 py-1 rounded-full capitalize ${statusClass}">
                            ${statusLabel}
                        </span>
                    </div>
                    ${app.eligibility_status ? `
                    <div class="mt-3">
                        <span class="text-xs text-gray-500">Eligibility: </span>
                        <span class="text-xs font-medium ${app.eligibility_status === 'eligible' ? 'text-green-600' : 'text-red-500'}">
                            ${app.eligibility_status}
                        </span>
                    </div>` : ""}
                    ${actionBtn ? `<div class="mt-4">${actionBtn}</div>` : ""}
                </div>`
        })

    } catch (e) {
        container.innerHTML = `<p class="text-red-500">Cannot connect to server. Make sure the backend is running.</p>`
    }
}

loadApplications()