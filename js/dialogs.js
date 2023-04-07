const dialogs = document.getElementById("dialogs");
const messages = document.getElementById("messages");
const message_input = document.getElementById("message-input");

function addDialog(username, avatar_url) {
    let dialog = document.createElement("li");
    dialog.classList.add("dialog");
    let avatar_img = document.createElement("img");
    avatar_img.src = avatar_url;
    avatar_img.width = 32;
    avatar_img.height = 32;
    let name = document.createElement("span");
    name.innerText = username;
    dialog.appendChild(avatar_img);
    dialog.innerHTML += "\n";
    dialog.appendChild(name);
    dialogs.appendChild(dialog);
}
function clearMessages() {
    messages.innerHTML = "";
}

function addMessage(type, text, time) {
    let message = document.createElement("li");
    message.classList.add(type === 0 ? "my-message" : "message");
    let date = new Date(time);
    let timestamp = document.createElement("span");
    timestamp.classList.add("message-time");
    timestamp.innerText = `[${padDate(date.getDay())}.${padDate(date.getMonth())}.${date.getFullYear()} ${padDate(date.getHours())}:${padDate(date.getMinutes())}]`;
    let message_text = document.createElement("span");
    message_text.innerText = text;
    message.appendChild(type === 0 ? message_text : timestamp);
    message.innerHTML += "\n";
    message.appendChild(type === 0 ? timestamp : message_text);
    messages.appendChild(message);
    messages.scrollTo(0, messages.scrollHeight);
}

function padDate(d) {
    return ("0"+d).slice(-2)
}

async function sendMessage() {
    let text = message_input.value.trim();
    if(!text)
        return;
    // TODO: Send message to server
    // But for now simply add message
    addMessage(0, text, Date.now());
    message_input.value = "";
}

message_input.addEventListener("keyup", ({key}) => {
    if(key === "Enter") {
        sendMessage();
    }
});

for(let i = 0; i < 30; i++) {
    addDialog(`Username ${i}`, "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNMafj/HwAGFwLkTJBHPQAAAABJRU5ErkJggg==");
}

for(let i = 0; i < 200; i++) {
    addMessage(1, "Text asd qwe ", 1680859800000);
}