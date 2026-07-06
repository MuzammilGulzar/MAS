// Auth Guard — protects pages that require login or a specific role

function getToken() {
    return localStorage.getItem("access_token")
}

// function getRole() {
//     const token = getToken()
//     if (!token) return null
//     try {
//         // JWT payload is the second segment, base64-encoded
//         const payload = JSON.parse(atob(token.split(".")[1]))
//         return payload.role || null
//     } catch (e) {
//         return null
//     }
// }

function getRole() {
    const token = getToken();
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        console.log("JWT Payload:", payload);
        console.log("Role:", payload.role);
        return payload.role || null;
    } catch (e) {
        console.error(e);
        return null;
    }
}

function requireLogin() {
    if (!getToken()) {
        window.location.href = "/components/login.html"
    }
}

export function requireHR() {
    const role = getRole()
    if (!getToken() || role !== "hr") {
        window.location.href = "frontend/components/login.html"
    }
}

export function requireCandidate() {
    const role = getRole()
    if (!getToken() || role !== "candidate") {
        window.location.href = "/components/login.html"
    }
}