// Production enviroment
window.API_ENDPOINT = "https://idkchat-api.pepega.ml/api/v1";
window.WS_ENDPOINT = "wss://idkchat-api.pepega.ml/ws";

// Local enviroment
/*window.API_ENDPOINT = "https://127.0.0.1:8000/api/v1";
window.WS_ENDPOINT = "wss://127.0.0.1:8000/ws";*/


// Solution to not working DOMContentLoaded on Cloudflare when both HTML Minify and Rocker Loader are on.
// https://dev.to/hollowman6/solution-to-missing-domcontentloaded-event-when-enabling-both-html-auto-minify-and-rocket-loader-in-cloudflare-5ch8
let inCloudFlare = true;
window.addEventListener("DOMContentLoaded", function () {
    inCloudFlare = false;
});
if (document.readyState === "loading") {
    window.addEventListener("load", function () {
        if (inCloudFlare) window.dispatchEvent(new Event("DOMContentLoaded"));
    });
}