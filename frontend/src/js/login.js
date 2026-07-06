// document
// .getElementById("loginForm")
// .addEventListener("submit", async function(event){

//     event.preventDefault();

//     const username =
//         document.getElementById("username").value;

//     const password =
//         document.getElementById("password").value;

//     const response = await fetch(
//         "http://127.0.0.1:8000/login",
//         {
//             method: "POST",

//             headers: {
//                 "Content-Type":
//                 "application/json"
//             },

//             body: JSON.stringify({
//                 username,
//                 password
//             })
//         }
//     );

//     const data = await response.json();

//     // Store JWT token in browser
//     localStorage.setItem(
//         "access_token",
//         data.access_token
//     );

//     alert("Login Successful");

//     // Move to dashboard
//     window.location.href = "../pages/shared/index.html";
// });

document
.getElementById("loginForm")
.addEventListener("submit", async function (event) {

    event.preventDefault();

    const message  = document.getElementById("message");
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("http://127.0.0.1:8000/login", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            message.className   = "text-red-600 text-sm mb-4 text-center";
            message.textContent = data.detail || "Login failed";
            return;
        }

        // Decode role from JWT payload (base64 middle part)
        const payload = JSON.parse(atob(data.access_token.split(".")[1]));

        // Persist auth info
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("username",     username);
        localStorage.setItem("role",         payload.role);

        // Redirect based on role
        if (payload.role === "hr") {
            window.location.href = "/frontend/pages/hr/hr_dashboard.html";
        } else {
            window.location.href = "/frontend/pages/candidate/candidate_dashboard.html";
        }

    } catch (error) {
        message.className   = "text-red-600 text-sm mb-4 text-center";
        message.textContent = "Cannot connect to server";
    }
});
