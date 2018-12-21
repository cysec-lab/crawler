
var running = false;
var currentTab = null;
var request_num = 0;
var download_num = 0;
var request_list = [];
var download_list = [];
var history_list = [];

function onCreated(tab){
    currentTab = tab;
    console.log(currentTab);
}
function onError(error){
    console.log("Error : ${error}");
}
// create new tab to communicate with python
var creating = browser.tabs.create({url: "Watcher.html"});
creating.then(onCreated, onError);

// send message to current tab
function send_message(message){
    browser.tabs.sendMessage(currentTab.id, message, function() {});
}

// receive message from Watcher.html
browser.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    //console.log("receiving data's description in background : " + message.description);
    if (message.description == "start_watching"){
        running = true;
    }
    else if (message.description == "stop_watching"){
        if (running == true){
            running = false;
            var message = new Object({description: "dataList", request: request_list, download: download_list, history: history_list});
            send_message(message);
            request_num = 0;
            download_num = 0;
            request_list = [];
            download_list = [];
            history_list = [];
        }
    }
});

// Watching Request
browser.webRequest.onBeforeRequest.addListener(
    function (details) {
        if (running){
            // console.log(details.url);
            request_num++;
            if (details.url.indexOf("data:") != 0){
                var message = new Object({no: request_num, data: details});
                request_list.push(message);
    //            console.log("details");
    //            console.log(details);
    //            let filter = browser.webRequest.filterResponseData(details.requestId);
    //            filter.ondata = event => {
    //                console.log("data");
    //                console.log(event.data);
    //                console.log("event")
    //                console.log(event)
    //                filter.write(event.data);
    //                filter.disconnect();
    //            }
            }
        }
    },
    {urls: ['<all_urls>']},
    []
    //["blocking"]
);
// Watching File-Download
browser.downloads.onCreated.addListener(
    function (item) {
        if (running){
            // console.log(item)
            download_num++;
            var message = new Object({no: download_num, data: item});
            download_list.push(message);
        }
    }
);
// Watching Visited-WebPage
browser.history.onVisited.addListener(
    function (historyItem) {
        if (running){
            // console.log(historyItem)
            var message = new Object({data: historyItem});
            history_list.push(message);
        }
    }
);
