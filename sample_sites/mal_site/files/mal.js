function changeTitle(){
	var obj = document.getElementById("header");
	obj.innerHTML = "<h1> changed Title </h1>";
}
function jumpRitsu(){
    var link2 = document.createElement("a");
    document.body.appendChild(link2);
	link2.href = "http://www.ritsumei.ac.jp/top/";
	link2.click();
	document.body.removeChild(link2);
}
function jumpMe(){
    var link2 = document.createElement("a");
    document.body.appendChild(link2);
	link2.href = "#";
	link2.click();
	document.body.removeChild(link2);
}
function autoDownLoad_js(){
	var link3 = document.createElement("a");
	document.body.appendChild(link3);
	link3.href = "data/fromAtag.txt";
	link3.download = "fromAtag.txt";
	link3.click();
	document.body.removeChild(link3);
}