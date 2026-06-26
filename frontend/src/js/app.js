// let sessionId = null;
// let currentQuestionId = null;

// const API_BASE_URL = "http://127.0.0.1:8000";

// // call the header
// // document.addEventListener("DOMContentLoaded", () => {
// //     fetch("../components/navbar.html")
// //     .then(response => response.text())
// //     .then(data => {
// //         document.getElementById("header").innerHTML = data;
// //     })
// // });

// // header and logout login
// document.addEventListener("DOMContentLoaded", () => {

//     fetch("../../components/navbar.html")
//         .then(response => response.text())
//         .then(data => {

//             document.getElementById("header").innerHTML = data;

//             const join =
//                 document.getElementById("join");

//             const logoutBtn =
//                 document.getElementById("logoutBtn");

//             const token =
//                 localStorage.getItem(
//                     "access_token"
//                 );

//             if (token) {

//                 logoutBtn.style.display =
//                     "inline-block";

//                 join.style.display =
//                     "none";

//             } else {

//                 join.style.display =
//                     "inline-block";

//                 logoutBtn.style.display =
//                     "none";
//             }

//             logoutBtn.addEventListener(
//                 "click",
//                 () => {

//                     localStorage.removeItem(
//                         "access_token"
//                     );

//                     window.location.href =
//                         "../components/login.html";
//                 }
//             );

//         });

// });


// // login logout end

// function showLoading() {
//     document.getElementById("loading").classList.remove("hidden");
// }

// function hideLoading() {
//     document.getElementById("loading").classList.add("hidden");
// }

// function addMessage(sender, message) {
//     const chatBox = document.getElementById("chatBox");

//     const messageDiv = document.createElement("div");

//     if (sender === "ai") {
//         messageDiv.className = "bg-blue-100 p-4 rounded-xl";
//         messageDiv.innerHTML = `<strong>AI:</strong> ${message}`;
//     } else {
//         messageDiv.className = "bg-green-100 p-4 rounded-xl text-right";
//         messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
//     }

//     chatBox.appendChild(messageDiv);

//     chatBox.scrollTop = chatBox.scrollHeight;
// }

// function showEvaluation(evaluation) {
//     const feedback = `
//         Score: ${evaluation.score}/10<br>
//         Feedback: ${evaluation.feedback}
//     `;

//     addMessage("ai", feedback);
// }

// function showResumeSummary(resumeAnalysis, interviewPlan) {
//     const summaryDiv = document.getElementById("summary");

//     summaryDiv.classList.remove("hidden");

//     summaryDiv.innerHTML = `
//         <h2 class="text-2xl font-bold text-blue-600 mb-4">
//             Resume Analysis
//         </h2>

//         <p class="mb-2">
//             <strong>Score:</strong> ${resumeAnalysis.score}/100
//         </p>

//         <p class="mb-2">
//             <strong>Best Fit:</strong> ${resumeAnalysis.job_fit}
//         </p>

//         <p class="mb-2">
//             <strong>Candidate Level:</strong> ${interviewPlan.candidate_level}
//         </p>

//         <p class="mb-2">
//             <strong>Interview Difficulty:</strong> ${interviewPlan.difficulty}
//         </p>

//         <p class="mb-2">
//             <strong>Total Questions:</strong> ${interviewPlan.total_questions}
//         </p>

//         <p class="mb-2">
//             <strong>Skills To Test:</strong> ${interviewPlan.skills_to_test.join(", ")}
//         </p>
//     `;
// }

// async function startInterview() {
//     const fileInput = document.getElementById("resumeFile");
//     const file = fileInput.files[0];

//     if (!file) {
//         alert("Please upload a PDF resume");
//         return;
//     }

//     showLoading();

//     document.getElementById("summary").classList.add("hidden");
//     document.getElementById("chatSection").classList.add("hidden");
//     document.getElementById("finalReport").classList.add("hidden");
//     document.getElementById("chatBox").innerHTML = "";

//     const formData = new FormData();
//     formData.append("file", file);
//     formData.append("applicaion_id", APPLICATION_ID);

//     try {
//         const response = await fetch(`${API_BASE_URL}/interview/start`, {
//             method: "POST",
//             headers: {
//                 "Authorization": `Bearer ${localStorage.getItem("access_token")}`
//             },
//             body: formData
//         });

//         if (!response.ok) {
//             throw new Error("Failed to start interview");
//         }

//         const data = await response.json();

//         sessionId = data.session_id;
//         currentQuestionId = data.first_question.question_id;

//         hideLoading();

//         showResumeSummary(data.resume_analysis, data.interview_plan);

//         document.getElementById("chatSection").classList.remove("hidden");

//         addMessage("ai", data.first_question.question);

//     } catch (error) {
//         hideLoading();
//         console.error(error);
//         alert("Something went wrong while starting the interview");
//     }
// }

// async function submitAnswer() {
//     const answerInput = document.getElementById("answerInput");
//     const answer = answerInput.value.trim();

//     if (!answer) {
//         alert("Please type your answer");
//         return;
//     }

//     if (!sessionId) {
//         alert("Interview session not found");
//         return;
//     }

//     addMessage("user", answer);

//     answerInput.value = "";

//     const sendButton = document.getElementById("sendButton");
//     sendButton.disabled = true;
//     sendButton.innerText = "Checking...";

//     try {
//         const response = await fetch(`${API_BASE_URL}/interview/answer`, {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             },
//             body: JSON.stringify({
//                 session_id: sessionId,
//                 answer: answer
//             })
//         });

//         if (!response.ok) {
//             throw new Error("Failed to submit answer");
//         }

//         const data = await response.json();

//         showEvaluation(data.evaluation);

//         if (data.type === "completed") {
//             addMessage("ai", "Interview completed.");

//             showFinalReport(data.final_report);

//             sendButton.disabled = true;
//             answerInput.disabled = true;
//             sendButton.innerText = "Completed";

//             return;
//         }

//         currentQuestionId = data.next_question.question_id;

//         addMessage("ai", data.next_question.question);

//         sendButton.disabled = false;
//         sendButton.innerText = "Send";

//     } catch (error) {
//         console.error(error);
//         alert("Something went wrong while submitting your answer");

//         sendButton.disabled = false;
//         sendButton.innerText = "Send";
//     }
// }

// function showFinalReport(report) {
//     const finalReportDiv = document.getElementById("finalReport");

//     finalReportDiv.classList.remove("hidden");

//     if (!report) {
//         finalReportDiv.innerHTML = `
//             <h2 class="text-2xl font-bold text-blue-600 mb-4">
//                 Final Report
//             </h2>
//             <p>Interview completed. Final report is not connected yet.</p>
//         `;
//         return;
//     }

//     finalReportDiv.innerHTML = `
//         <h2 class="text-2xl font-bold text-blue-600 mb-4">
//             Final Report
//         </h2>

//         <p class="mb-2">
//             <strong>Overall Score:</strong> ${report.overall_score}/10
//         </p>

//         <p class="mb-2">
//             <strong>Recommendation:</strong> ${report.recommendation}
//         </p>

//         <div class="mt-4">
//             <h3 class="text-xl font-semibold mb-2">Skill Scores</h3>
//             <ul class="list-disc ml-6">
//                 ${Object.entries(report.skill_scores).map(([skill, score]) =>
//                     `<li>${skill}: ${score}</li>`
//                 ).join("")}
//             </ul>
//         </div>

//         <div class="mt-4">
//             <h3 class="text-xl font-semibold mb-2">Strengths</h3>
//             <ul class="list-disc ml-6">
//                 ${report.strengths.map(item =>
//                     `<li>${item}</li>`
//                 ).join("")}
//             </ul>
//         </div>

//         <div class="mt-4">
//             <h3 class="text-xl font-semibold mb-2">Weaknesses</h3>
//             <ul class="list-disc ml-6">
//                 ${report.weaknesses.map(item =>
//                     `<li>${item}</li>`
//                 ).join("")}
//             </ul>
//         </div>

//         <div class="mt-4">
//             <h3 class="text-xl font-semibold mb-2">Final Feedback</h3>
//             <p class="text-gray-700 leading-relaxed">
//                 ${report.final_feedback}
//             </p>
//         </div>
//     `;
// }




// app.js v2 — updated
let sessionId = null;
let currentQuestionId = null;

const API_BASE_URL = "http://127.0.0.1:8000";

// ── Read application_id from URL or localStorage ──────────────────
const urlParams = new URLSearchParams(window.location.search);
const APPLICATION_ID = urlParams.get("application_id") || localStorage.getItem("application_id");

// ── Safe header loader (only runs if #header exists on this page) ─
document.addEventListener("DOMContentLoaded", () => {
    const headerEl = document.getElementById("header");
    if (headerEl) {
        fetch("../../components/navbar.html")
            .then(r => r.text())
            .then(html => { headerEl.innerHTML = html; })
            .catch(() => {});
    }
});

// ── Helpers ───────────────────────────────────────────────────────
function getToken() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You are not logged in. Redirecting to login.");
        window.location.href = "../../components/login.html";
        return null;
    }
    return token;
}

function showLoading() {
    document.getElementById("loading").classList.remove("hidden");
}

function hideLoading() {
    document.getElementById("loading").classList.add("hidden");
}

function addMessage(sender, message) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement("div");

    if (sender === "ai") {
        messageDiv.className = "bg-blue-100 p-4 rounded-xl";
        messageDiv.innerHTML = `<strong>AI:</strong> ${message}`;
    } else {
        messageDiv.className = "bg-green-100 p-4 rounded-xl text-right";
        messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
    }

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showEvaluation(evaluation) {
    const feedback = `Score: ${evaluation.score}/10 — ${evaluation.feedback}`;
    addMessage("ai", feedback);
}

function showResumeSummary(resumeAnalysis, interviewPlan) {
    const summaryDiv = document.getElementById("summary");
    summaryDiv.classList.remove("hidden");
    summaryDiv.innerHTML = `
        <h2 class="text-2xl font-bold text-blue-600 mb-4">Resume Analysis</h2>
        <p class="mb-2"><strong>Score:</strong> ${resumeAnalysis.score}/100</p>
        <p class="mb-2"><strong>Best Fit:</strong> ${resumeAnalysis.job_fit}</p>
        <p class="mb-2"><strong>Candidate Level:</strong> ${interviewPlan.candidate_level}</p>
        <p class="mb-2"><strong>Interview Difficulty:</strong> ${interviewPlan.difficulty}</p>
        <p class="mb-2"><strong>Total Questions:</strong> ${interviewPlan.total_questions}</p>
        <p class="mb-2"><strong>Skills To Test:</strong> ${interviewPlan.skills_to_test.join(", ")}</p>
    `;
}

// ── Start Interview ───────────────────────────────────────────────
async function startInterview() {
    const token = getToken();
    if (!token) return;

    const fileInput = document.getElementById("resumeFile");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please upload your resume to start the interview.");
        return;
    }

    if (!APPLICATION_ID) {
        alert("Application ID not found. Please go back and check eligibility first.");
        window.location.href = "./candidate/jobs.html";
        return;
    }

    showLoading();
    document.getElementById("summary").classList.add("hidden");
    document.getElementById("chatSection").classList.add("hidden");
    document.getElementById("finalReport").classList.add("hidden");
    document.getElementById("chatBox").innerHTML = "";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("application_id", APPLICATION_ID);

    try {
        const response = await fetch(`${API_BASE_URL}/interview/start`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "Failed to start interview");
        }

        const data = await response.json();

        sessionId = data.session_id;
        currentQuestionId = data.first_question.question_id;

        hideLoading();
        showResumeSummary(data.resume_analysis, data.interview_plan);
        document.getElementById("chatSection").classList.remove("hidden");
        addMessage("ai", data.first_question.question);

    } catch (error) {
        hideLoading();
        console.error(error);
        alert("Error starting interview: " + error.message);
    }
}

// ── Submit Answer ─────────────────────────────────────────────────
async function submitAnswer() {
    const answerInput = document.getElementById("answerInput");
    const answer = answerInput.value.trim();

    if (!answer) {
        alert("Please type your answer");
        return;
    }

    if (!sessionId) {
        alert("Interview session not found");
        return;
    }

    addMessage("user", answer);
    answerInput.value = "";

    const sendButton = document.getElementById("sendButton");
    sendButton.disabled = true;
    sendButton.innerText = "Checking...";

    try {
        const response = await fetch(`${API_BASE_URL}/interview/answer`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_id: sessionId,
                answer: answer
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "Failed to submit answer");
        }

        const data = await response.json();

        showEvaluation(data.evaluation);

        if (data.type === "completed") {
            addMessage("ai", "🎉 Interview completed!");
            showFinalReport(data.final_report);
            sendButton.disabled = true;
            answerInput.disabled = true;
            sendButton.innerText = "Completed";
            localStorage.removeItem("application_id");
            return;
        }

        currentQuestionId = data.next_question.question_id;
        addMessage("ai", data.next_question.question);
        sendButton.disabled = false;
        sendButton.innerText = "Send";

    } catch (error) {
        console.error(error);
        alert("Something went wrong: " + error.message);
        sendButton.disabled = false;
        sendButton.innerText = "Send";
    }
}

// ── Final Report ──────────────────────────────────────────────────
function showFinalReport(report) {
    const finalReportDiv = document.getElementById("finalReport");
    finalReportDiv.classList.remove("hidden");

    if (!report) {
        finalReportDiv.innerHTML = `<p>Report not available.</p>`;
        return;
    }

    finalReportDiv.innerHTML = `
        <h2 class="text-2xl font-bold text-blue-600 mb-4">Final Report</h2>
        <p class="mb-2"><strong>Overall Score:</strong> ${report.overall_score}/10</p>
        <p class="mb-2"><strong>Recommendation:</strong> ${report.recommendation}</p>
        <div class="mt-4">
            <h3 class="text-xl font-semibold mb-2">Skill Scores</h3>
            <ul class="list-disc ml-6">
                ${Object.entries(report.skill_scores).map(([skill, score]) =>
                    `<li>${skill}: ${score}</li>`
                ).join("")}
            </ul>
        </div>
        <div class="mt-4">
            <h3 class="text-xl font-semibold mb-2">Strengths</h3>
            <ul class="list-disc ml-6">
                ${report.strengths.map(item => `<li>${item}</li>`).join("")}
            </ul>
        </div>
        <div class="mt-4">
            <h3 class="text-xl font-semibold mb-2">Weaknesses</h3>
            <ul class="list-disc ml-6">
                ${report.weaknesses.map(item => `<li>${item}</li>`).join("")}
            </ul>
        </div>
        <div class="mt-4">
            <h3 class="text-xl font-semibold mb-2">Final Feedback</h3>
            <p class="text-gray-700 leading-relaxed">${report.final_feedback}</p>
        </div>
    `;

    finalReportDiv.scrollIntoView({ behavior: "smooth" });
}