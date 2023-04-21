const dialogs = document.getElementById("dialogs");
const dialog_title = document.getElementById("dialog-title");
const messages = document.getElementById("messages");
const message_input = document.getElementById("message-input");
const crypt = new OpenCrypto();

window.DIALOGS = {};
window.MESSAGES = [];
window.MESSAGES_CACHE = {};
window.CURRENT_DIALOG = 0;
window._WS = null;

async function encryptMessage(text, publicKey) {
    let buffer = new TextEncoder().encode(text);
    let chunkSize = publicKey.algorithm.modulusLength/8-2;
    switch(publicKey.algorithm.hash.name.toLowerCase()) {
        case "sha-512":
        case "sha-384":
            chunkSize -= 64 * 2; break;
        case "sha-256":
            chunkSize -= 32 * 2; break;
        case "sha-1":
            chunkSize -= 20 * 2; break;
    }
    let outBuffers = [];
    for (let i = 0; i < buffer.length; i += chunkSize) {
        let chunk = buffer.slice(i, i + chunkSize);
        let encryptedChunk = await window.crypto.subtle.encrypt({"name": "RSA-OAEP"}, publicKey, chunk)
        outBuffers.push(new Uint8Array(encryptedChunk));
    }
    return crypt.encodeAb(concatUint8Arrays(outBuffers));
}

async function decryptMessage(message, privKey) {
    message = new Uint8Array(crypt.decodeAb(message));
    let chunkSize = privKey.algorithm.modulusLength/8;
    let out = "";
    console.log(message)
    for (let i = 0; i < message.length; i += chunkSize) {
        let chunk = message.slice(i, i + chunkSize);
        let decryptedChunk = await window.crypto.subtle.decrypt({"name": "RSA-OAEP"}, privKey, chunk);
        console.log(decryptedChunk)
        out += new TextDecoder("utf8").decode(decryptedChunk);
    }
    return out;
}

function updateDialog(dialog_id) {
    let dialog_obj = DIALOGS[dialog_id];
    let dialog = document.getElementById(`dialog-id-${dialog_id}`);
    if(!dialog || !dialog_obj) return;

    let username, avatar;
    for(let childNode of dialog.childNodes) {
        if(childNode.nodeName === "SPAN") {
            username = childNode;
        }
        if(childNode.nodeName === "IMG") {
            avatar = childNode;
        }
        if(username && avatar) break;
    }
    if(!username || !avatar) return;

    username.innerText = dialog_obj["username"];
    username.style.color = dialog_obj["new_messages"] ? "#ff0000" : "";

    avatar.src = dialog_obj["avatar"] ? avatarUrl(dialog_obj["user_id"], dialog_obj["avatar"]) : DEFAULT_AVATAR;
    ensureImageLoaded(avatar, DEFAULT_AVATAR);
}

function ensureImageLoaded(image_element, default_src) {
    image_element.dataset.load_tries = "0";
    image_element.onerror = () => {
        setTimeout(() => {
            if(+image_element.dataset.load_tries > 5) {
                image_element.dataset.load_tries = "0";
                image_element.src = default_src;
                return;
            }
            image_element.dataset.load_tries = (+image_element.dataset.load_tries+1).toString();
            image_element.src = image_element.src+(image_element.src.includes("?") ? "&" : "?")+`_C=${new Date().getTime()}`;
        }, 500);
    }
    image_element.onload = () => {
        image_element.dataset.load_tries = "0";
    }
}

function addDialog(dialog_id, username, avatar_url, new_messages, public_key) {
    if(!(dialog_id in MESSAGES_CACHE)) {
        MESSAGES_CACHE[dialog_id] = {"messages": [], "message_ids": []};
    }
    if(dialog_id in DIALOGS) {
        DIALOGS[dialog_id]["username"] = username;
        DIALOGS[dialog_id]["new_messages"] = new_messages;
        DIALOGS[dialog_id]["publicKey"] = public_key ? public_key : DIALOGS[dialog_id]["publicKey"];
        updateDialog(dialog_id);
        return;
    }
    DIALOGS[dialog_id] = {"username": username, "avatar_url": avatar_url, "dialog_id": dialog_id, "new_messages": new_messages, "publicKey": public_key};

    let dialog = document.createElement("li");
    dialog.classList.add("dialog");
    dialog.id = `dialog-id-${dialog_id}`;
    dialog.addEventListener("click", () => {selectDialog(dialog_id)});

    let avatar_img = document.createElement("img");
    avatar_img.src = avatar_url;
    avatar_img.width = 32;
    avatar_img.height = 32;
    ensureImageLoaded(avatar_img, DEFAULT_AVATAR);

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
    if(!MESSAGES_CACHE[dialog_id]["message_ids"].includes(message_id)) {
        MESSAGES_CACHE[dialog_id]["message_ids"].push(message_id);
        MESSAGES_CACHE[dialog_id]["messages"].push({"id": message_id, "type": type, "text": text, "time": time});
    }
    if(getSelectedDialog() !== dialog_id)
        return;
    if(document.getElementById(`message-id-${message_id}`))
        return;

    if(!text) return;

    let idx = sortedIndex(MESSAGES, message_id);
    MESSAGES.splice(idx, 0, message_id);

    let message = document.createElement("li");
    message.id = `message-id-${message_id}`;
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

    let insertLast = idx === MESSAGES.length-1;
    let before = MESSAGES[idx+1];
    before = document.getElementById(`message-id-${before}`);
    if(insertLast || !before)
        messages.appendChild(message);
    else {
        messages.insertBefore(message, before);
    }

    if(insertLast)
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
    return window.CURRENT_DIALOG;
}

async function sendMessage() {
    let text = message_input.value.trim();
    if(!text) return;
    if(!getSelectedDialog()) return;

    let pubKey = DIALOGS[getSelectedDialog()]["publicKey"];
    text = await encryptMessage(text, pubKey);

    let resp = await fetch(`${window.API_ENDPOINT}/chat/messages`, {
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
    let resp = await fetch(`${window.API_ENDPOINT}/chat/dialogs`, {
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    for(let dialog of await resp.json()) {
        addDialog(
            dialog["id"],
            dialog["username"],
            dialog["avatar"] ? avatarUrl(dialog["user_id"], dialog["avatar"]) : DEFAULT_AVATAR,
            dialog["new_messages"],
            await crypt.pemPublicToCrypto(dialog["public_key"], { name: 'RSA-OAEP' })
        );
        Object.assign(DIALOGS[dialog["id"]], dialog);
    }
}

async function fetchMessages(dialog_id) {
    let resp = await fetch(`${window.API_ENDPOINT}/chat/messages?dialog_id=${dialog_id}`, {
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    });
    if(resp.status === 401) {
        localStorage.removeItem("token");
        location.href = "/auth.html";
    }

    let privKey = await crypt.decryptPrivateKey(localStorage.getItem("encPrivKey"), localStorage.getItem("KEY"), { name: 'RSA-OAEP' });
    for(let message of await resp.json()) {
        addMessage(dialog_id, message["id"], message["type"], await decryptMessage(message["text"], privKey), message["time"]);
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
    window.MESSAGES = [];
    clearMessages();

    window.CURRENT_DIALOG = dialog_id;
    for(let message of MESSAGES_CACHE[dialog_id]["messages"]) {
        addMessage(dialog_id, message["id"], message["type"], message["text"], message["time"]);
    }
    fetchMessages(dialog_id).then();

    if(DIALOGS[dialog_id]["new_messages"]) {
        window._WS.send(JSON.stringify({
            "op": 2,
            "d": {
                "dialog_id": getSelectedDialog(),
                "message_id": -1
            }
        }));
    }
}

async function newDialog() {
    let username = prompt("Username:").trim();
    if(!username) return;

    let resp = await fetch(`${window.API_ENDPOINT}/chat/dialogs`, {
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

    addDialog(
        jsonResp["id"],
        jsonResp["username"],
        jsonResp["avatar"] ? avatarUrl(jsonResp["user_id"], jsonResp["avatar"]) : DEFAULT_AVATAR,
        jsonResp["new_messages"],
        await crypt.pemPublicToCrypto(jsonResp["public_key"], { name: 'RSA-OAEP' })
    );
}

if (document.readyState !== 'loading') {
    fetchDialogs().then();
} else {
    window.addEventListener("DOMContentLoaded", async () => {
        await fetchDialogs();
    }, false);
}

async function _ws_handle_new_message(data) {
    let dialog = data["dialog"];
    addDialog(
        dialog["id"],
        dialog["username"],
        data["avatar"] ? avatarUrl(data["user_id"], data["avatar"]) : DEFAULT_AVATAR,
        dialog["new_messages"],
        await crypt.pemPublicToCrypto(dialog["public_key"], { name: 'RSA-OAEP' })
    );

    let message = data["message"];
    let privKey = await crypt.decryptPrivateKey(localStorage.getItem("encPrivKey"), localStorage.getItem("KEY"), { name: 'RSA-OAEP' });
    addMessage(dialog["id"], message["id"], message["type"], await decryptMessage(message["text"], privKey), message["time"]);

    if(message["type"] !== 0) {
        if(getSelectedDialog() === dialog["id"])
            window._WS.send(JSON.stringify({
                "op": 2,
                "d": {
                    "dialog_id": dialog["id"],
                    "message_id": message["id"]
                }
            }));
    }
}

async function _ws_handle_dialog_update(data) {
    let dialog_id = data["id"];
    Object.assign(DIALOGS[dialog_id], data);
    updateDialog(dialog_id);
}

window.WS_HANDLERS = {
    1: _ws_handle_new_message,
    3: _ws_handle_dialog_update
}

function initWs() {
    let ws = window._WS = new WebSocket(window.WS_ENDPOINT);

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
            WS_HANDLERS[data["op"]](data["d"]).then();
        }
    });

    ws.addEventListener("close", (event) => {
        if(event.code === 4001) {
            localStorage.removeItem("token");
            location.href = "/auth.html";
            return;
        }
        setTimeout(() => {
            fetchDialogs().then();
            initWs();
        }, 1000);
    });
}

if (document.readyState !== 'loading') {
    initWs();
} else {
    window.addEventListener("DOMContentLoaded", () => {
        initWs();
    }, false);
}