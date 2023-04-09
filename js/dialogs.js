const dialogs = document.getElementById("dialogs");
const dialog_title = document.getElementById("dialog-title");
const messages = document.getElementById("messages");
const message_input = document.getElementById("message-input");

window.DIALOGS = {};
window.CURRENT_DIALOG = 0;
window._WS = null;

function updateDialog(dialog_id) {
    let dialog_obj = DIALOGS[dialog_id];
    let dialog = document.getElementById(`dialog-id-${dialog_id}`);
    if(!dialog || !dialog_obj) return;

    let username;
    for(let childNode of dialog.childNodes) {
        console.log(childNode.nodeName)
        if(childNode.nodeName === "SPAN") {
            username = childNode;
            break;
        }
    }
    console.log(username)
    if(!username) return;

    username.innerText = dialog_obj["username"];
    username.style.color = dialog_obj["new_messages"] ? "#ff0000" : "";
}

function addDialog(dialog_id, username, avatar_url, new_messages=true) {
    if(dialog_id in DIALOGS) {
        DIALOGS[dialog_id]["username"] = username;
        DIALOGS[dialog_id]["new_messages"] = new_messages;
        updateDialog(dialog_id);
        return;
    }
    DIALOGS[dialog_id] = {"username": username, "avatar_url": avatar_url, "dialog_id": dialog_id, "new_messages": new_messages};

    let dialog = document.createElement("li");
    dialog.classList.add("dialog");
    dialog.id = `dialog-id-${dialog_id}`;
    dialog.addEventListener("click", () => {selectDialog(dialog_id)});

    let avatar_img = document.createElement("img");
    avatar_img.src = avatar_url;
    avatar_img.width = 32;
    avatar_img.height = 32;

    let name = document.createElement("span");
    name.innerText = username;
    if(new_messages)
        name.style.color = "#ff0000";

    dialog.appendChild(avatar_img);
    dialog.innerHTML += "\n";
    dialog.appendChild(name);

    dialogs.appendChild(dialog);
}

function clearMessages() {
    messages.innerHTML = "";
}

function addMessage(dialog_id, message_id, type, text, time) {
    if(document.getElementsByClassName(`message-id-${message_id}`).length > 0)
        return;
    if(getSelectedDialog() !== dialog_id)
        return;

    let message = document.createElement("li");
    message.classList.add(`message-id-${message_id}`);
    message.classList.add(type === 0 ? "my-message" : "message");

    let date = new Date(time);
    let timestamp = document.createElement("span");
    timestamp.classList.add("message-time");
    timestamp.innerText = `[${padDate(date.getDate())}.${padDate(date.getMonth())}.${date.getFullYear()} ${padDate(date.getHours())}:${padDate(date.getMinutes())}]`;

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

function getSelectedDialog() {
    let selected_dialogs = document.getElementsByClassName("dialog-selected");
    if(selected_dialogs.length > 0) {
        return parseInt(selected_dialogs[0].id.replace("dialog-id-", ""));
    }
    return CURRENT_DIALOG;
}

async function sendMessage() {
    let text = message_input.value.trim();
    if(!text)
        return;

    let resp = await fetch("https://127.0.0.1:8000/api/v1/chat/messages", {
        method: "POST",
        headers: {
            "Authorization": localStorage.getItem("token"),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"dialog_id": getSelectedDialog(), "text": text})
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    if(resp.status >= 400 && resp.status < 405) {
        let jsonResp = await resp.json();
        alert(jsonResp.message);
        return;
    }

    message_input.value = "";
}

message_input.addEventListener("keyup", ({key}) => {
    if(key === "Enter") {
        sendMessage().then();
    }
});

async function fetchDialogs() {
    let resp = await fetch("https://127.0.0.1:8000/api/v1/chat/dialogs", {
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    for(let dialog of await resp.json()) {
        addDialog(dialog["id"], dialog["username"], "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNMafj/HwAGFwLkTJBHPQAAAABJRU5ErkJggg==");
    }
}

async function fetchMessages(dialog_id) {
    let resp = await fetch(`https://127.0.0.1:8000/api/v1/chat/messages?dialog_id=${dialog_id}`, {
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    for(let message of await resp.json()) {
        addMessage(dialog_id, message["id"], message["type"], message["text"], message["time"]);
    }
}

function selectDialog(dialog_id) {
    if(!(dialog_id in DIALOGS)) return;

    let dialog_to_sel = document.getElementById(`dialog-id-${dialog_id}`);
    if(!dialog_to_sel) return;

    for(let dialog of document.getElementsByClassName("dialog-selected")) {
        dialog.classList.remove("dialog-selected");
    }

    dialog_to_sel.classList.add("dialog-selected");
    dialog_title.innerText = DIALOGS[dialog_id].username;
    clearMessages();

    CURRENT_DIALOG = dialog_id;
    fetchMessages(dialog_id).then();
}

async function newDialog() {
    let username = prompt("Username:").trim();
    if(!username) return;

    let resp = await fetch("https://127.0.0.1:8000/api/v1/chat/dialogs", {
        method: "POST",
        headers: {
            "Authorization": localStorage.getItem("token"),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"username": username})
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    let jsonResp = await resp.json();

    if(resp.status >= 400 && resp.status < 405) {
        alert(jsonResp.message);
        return;
    }

    addDialog(jsonResp["id"], jsonResp["username"], "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNMafj/HwAGFwLkTJBHPQAAAABJRU5ErkJggg==");
}

window.addEventListener("DOMContentLoaded", async () => {
    await fetchDialogs();

}, false);

function _ws_handle_1(data) {
    let dialog = data["dialog"];
    addDialog(dialog["id"], dialog["username"], "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNMafj/HwAGFwLkTJBHPQAAAABJRU5ErkJggg==");

    let message = data["message"];
    addMessage(dialog["id"], message["id"], message["type"], message["text"], message["time"]);
}

window.WS_HANDLERS = {
    1: _ws_handle_1
}

function initWs() {
    window._WS = ws = new WebSocket("wss://127.0.0.1:8000/ws");

    ws.addEventListener("open", (event) => {
        ws.send(JSON.stringify({
            "op": 0,
            "d": {
                "token": localStorage.getItem("token")
            }
        }));
    });

    ws.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        if(data["op"] in WS_HANDLERS) {
            WS_HANDLERS[data["op"]](data["d"])
        }
    });

    ws.addEventListener("close", (event) => {
        if(event.code === 4001) {
            localStorage.removeItem("token");
            location.href = "/auth.html";
            return;
        }
        setTimeout(initWs, 1000);
    });
}

window.addEventListener("DOMContentLoaded", () => {
    initWs();
}, false);