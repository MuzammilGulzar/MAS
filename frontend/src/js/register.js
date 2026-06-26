// document
// .getElementById("registerForm")
// .addEventListener("submit", async (event) => {

// ```
// event.preventDefault();

// const message =
//     document.getElementById("message");

// try {

//     const response = await fetch(
//         "http://localhost:8000/register",
//         {
//             method: "POST",

//             headers: {
//                 "Content-Type":
//                 "application/json"
//             },

//             body: JSON.stringify({
//                 username:
//                     document.getElementById("username").value,

//                 email:
//                     document.getElementById("email").value,

//                 password:
//                     document.getElementById("password").value
//             })
//         }
//     );

//     const data = await response.json();

//     if (response.ok) {

//         message.className =
//             "text-green-600 text-sm mb-4 text-center";

//         message.textContent =
//             "Registration successful!";

//         setTimeout(() => {
//             window.location.href = "login.html";
//         }, 1500);

//     } else {

//         message.className =
//             "text-red-600 text-sm mb-4 text-center";

//         message.textContent =
//             data.detail || "Registration failed";
//     }

// } catch (error) {

//     message.className =
//         "text-red-600 text-sm mb-4 text-center";

//     message.textContent =
//         "Cannot connect to server";
// }
// ```

// });


document
.getElementById("registerForm")
.addEventListener("submit", async (event) => {

    event.preventDefault()

    const message = document.getElementById("message")

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/register",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: document.getElementById("username").value,
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value,
                    role: document.getElementById("role").value
                })
            }
        )

        const data = await response.json()

        if (response.ok) {
            message.className = "text-green-600 text-sm mb-4 text-center"
            message.textContent = "Registration successful! Redirecting..."
            setTimeout(() => {
                window.location.href = "login.html"
            }, 1500)
        } else {
            message.className = "text-red-600 text-sm mb-4 text-center"
            message.textContent = data.detail || "Registration failed"
        }

    } catch (error) {
        message.className = "text-red-600 text-sm mb-4 text-center"
        message.textContent = "Cannot connect to server"
    }

})
