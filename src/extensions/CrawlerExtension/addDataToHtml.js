function createRequestElement(content){
    var child = document.createElement("p");
    child.classList.add("Request");
    child.hidden = true;
    child.id = "URL_" + content.no;
    child.textContent = content.data.url;
    document.getElementById("contents").appendChild(child);
}

function createScriptElement(content, i){
    var child = document.createElement("p");
    child.classList.add("Script");
    child.hidden = true;
    child.id = "JSURL_" + i;
    child.textContent = content.url;
    document.getElementById("contents").appendChild(child);
}

function createDownloadElement(content){
    var child = document.createElement("p");
    child.classList.add("Download");
    child.hidden = true;
    child.id = "URL_" + content.no;
    child.textContent = content.data.url;
    document.getElementById("contents").appendChild(child);

    var child = document.createElement("p");
    child.classList.add("Download");
    child.hidden = true;
    child.id = "FileName_" + content.no;
    child.textContent = content.data.filename;
    document.getElementById("contents").appendChild(child);

    var child = document.createElement("p");
    child.classList.add("Download");
    child.hidden = true;
    child.id = "Referrer_" + content.no;
    child.textContent = content.data.referrer;
    document.getElementById("contents").appendChild(child);

    var child = document.createElement("p");
    child.classList.add("Download");
    child.hidden = true;
    child.id = "Mime_" + content.no;
    child.textContent = content.data.mime;
    document.getElementById("contents").appendChild(child);

    var child = document.createElement("p");
    child.classList.add("Download");
    child.hidden = true;
    child.id = "JsonData_" + content.no;
    var temp = new Date(content.data.startTime);
    child.textContent = JSON.stringify({"FileSize":content.data.fileSize, "TotalBytes": content.data.totalBytes,
    "Danger": content.data.danger, "StartTime": temp.toLocaleString()});
    document.getElementById("contents").appendChild(child);
}

function createHistoryElement(content){
    var child = document.createElement("p");
    child.classList.add("History");
    child.hidden = true;
    child.textContent = content.data.url;
    document.getElementById("contents").appendChild(child);
}

browser.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.description == "dataList"){
        message.request.forEach(function (value){
            // console.log("Request_" + value.no + " :" + value.data.url);
            // create element and add
            createRequestElement(value);
        });

        message.download.forEach(function (value){
            // console.log("Download_" + value.no + " :" + value.data);
            // create element and add
            createDownloadElement(value);
        });

        message.history.forEach(function (value){
            // console.log("History :" + value.data);
            // create element and add
            createHistoryElement(value);
        });

        var i = 0;
        message.js.forEach(function (value){
            i += 1;
            createScriptElement(value, i);
        });

        var child = document.createElement("p");
        child.id = "EndOfData";
        child.textContent = "End of data.";
        document.getElementById("contents").appendChild(child);
    }
});
