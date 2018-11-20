// send message to background.js
function sendToBackground(message){
    browser.runtime.sendMessage(message);
}

// start watching
function sendStart(){
    var s = new Object({description: "start_watching"});
    sendToBackground(s);
}
//function getURLs(){
//    var message = new Object({description: "give_URLs"});
//    sendToBackground(message);
//}
// stop watching
function sendStop(){
    var s = new Object({description: "stop_watching"});
    sendToBackground(s);
}
//create New blank Tab
function createTab(){
    browser.tabs.create({url: "about:blank"});
}
function clearContents(){
    var element = document.getElementById("contents");
    var clone = element.cloneNode(false);
    element.parentNode.replaceChild(clone, element);
}

//function onGot(info){
//    currentTab = info;
//    var elem = document.createElement("p");
//    elem.id = "currentTab";
//    elem.textContent = "CurrentTab info has got.";
//    document.getElementById("button").appendChild(elem);
//}
//function onError(error){
//    console.log("Error : ${error}")
//}
function attachJsToButton(){
//    var gettingCurrent = browser.tabs.getCurrent();
//    gettingCurrent.then(onGot, onError);
    var element = document.getElementById("start");
    element.onclick = sendStart;
//    element = document.getElementById("getURLs");
//    element.onclick = getURLs;
    element = document.getElementById("stop");
    element.onclick = sendStop;
    element = document.getElementById("createBlankTab");
    element.onclick = createTab;
    element = document.getElementById("clearContents");
    element.onclick = clearContents;
    element = document.createElement("p");
    element.id = "DoneAttachJS";
    element.textContent = "Attaching javascript has done.";
    element.hidden = true;
    document.getElementById("notice").appendChild(element);
}

window.addEventListener("DOMContentLoaded", attachJsToButton, false);