function initNavbar() {
    const token    = localStorage.getItem("access_token");
    const role     = localStorage.getItem("role");
    const username = localStorage.getItem("username");

    if (token) {
        document.getElementById("loginLink").style.display  = "none";
        document.getElementById("logoutBtn").style.display  = "inline-flex";

        if (username) {
            const el = document.getElementById("navUsername");
            el.textContent   = "Hi, " + username;
            el.style.display = "inline";
        }

        if (role === "hr") {
            document.getElementById("hrNav").style.display        = "flex";
            document.getElementById("navLogo").href = "/frontend/pages/hr/hr_dashboard.html";
        } else {
            document.getElementById("candidateNav").style.display = "flex";
            document.getElementById("navLogo").href = "/frontend/pages/candidate/jobs.html";
        }
    }

    document.getElementById("logoutBtn").addEventListener("click", function () {
        localStorage.clear();
        window.location.href = "/frontend/components/login.html";
    });
}

function loadNavbar(relativePath) {
    // relativePath: path from the current page to navbar.html
    // e.g. "../../components/navbar.html" or "../components/navbar.html"
    fetch(relativePath)
        .then(r => r.text())
        .then(html => {
            document.getElementById("navbar").innerHTML = html;
            initNavbar();  // run AFTER html is injected into DOM
        });
}
