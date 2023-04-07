const auth_title = document.getElementById("auth-form-title");
const login_input = document.getElementById("login");
const password_input = document.getElementById("password");
const password2_input = document.getElementById("password2");
const password2_div = document.getElementById("password2-div");
const btn_login = document.getElementById("btn_login");
const btn_register = document.getElementById("btn_register");

function toggleMode() {
    let login = auth_title.innerText.trim() === "Login";
    auth_title.innerText = login ? "Register" : "Login";
    password2_div.style.display = login ? "" : "none";
    btn_register.style.display = login ? "" : "none";
    btn_login.style.display = login ? "none" : "";
}

async function login() {
    let login = login_input.value.trim();
    let password = password_input.value.trim();
    // TODO: implement login
    alert(`Login button clicked!\n\nValues:\n  Login: ${login}\n  Password: ${password}`);
}

async function register() {
    let login = login_input.value.trim();
    let password = password_input.value.trim();
    let password2 = password2_input.value.trim();
    // TODO: implement register
    alert(`Register button clicked!\n\nValues:\n  Login: ${login}\n  Password: ${password}\n  Password2: ${password2}`);
}