function make_link(){
	var link3 = document.createElement("a");
	document.body.appendChild(link3);
	link3.id = "download";
	link3.href = "#";
	link3.download = "restart.bat";
}
function handleDownload() {
    // -r を入れると再起動
	// var content = 'shutdown.exe -r -t 60';
	var content = 'start notepad.exe';
	var blob = new Blob([ content ], { "type" : "application/octet-stream" });

	if (window.navigator.msSaveBlob) {
	    window.navigator.msSaveBlob(blob, "restart.bat");

	    // msSaveOrOpenBlobの場合はファイルを保存せずに開ける
	    window.navigator.msSaveOrOpenBlob(blob, "restart.bat");
	} else {
	    document.getElementById("download").href = window.URL.createObjectURL(blob);
	}
}
function click_dl(){
    var link3 = document.getElementById("download");
	link3.click();
	document.body.removeChild(link3);
}

// MIME-typeを適当に入れられるとダウンロード検知できない
function make_link_2(){
	var link3 = document.createElement("a");
	document.body.appendChild(link3);
	link3.id = "download";
	link3.href = "#";
	link3.download = "mimeHirose.bat";
}
function handleDownload_2() {
    // -r を入れると再起動
	// var content = 'shutdown.exe -r -t 60';
	var content = 'start notepad.exe';
	var blob = new Blob([ content ], { "type" : "test/hirose" });

	if (window.navigator.msSaveBlob) {
	    window.navigator.msSaveBlob(blob, "mimeHirose.bat");

	    // msSaveOrOpenBlobの場合はファイルを保存せずに開ける
	    window.navigator.msSaveOrOpenBlob(blob, "mimeHirose.bat");
	} else {
	    document.getElementById("download").href = window.URL.createObjectURL(blob);
	}
}