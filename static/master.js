"use strict"
function changeCheck(cb) {
    if(cb.checked == true) {
        cb.parentNode.parentNode.style.backgroundColor="rgba(255,0,0,0.3)";
    }else {
        cb.parentNode.parentNode.style.backgroundColor="rgba(0,255,0,0.3)";
    }
}
function changeHall(sel) {
    let dfd = new $.Deferred();
	let hallOpt = sel.options[sel.selectedIndex].value;

	$.ajax({
		url: `http://localhost:5000/api/v1/arcSchedule/${hallOpt}`,
		method: "GET"
    }).done(function(data) {
        console.log(data)
        displayDates(data)
        dfd.resolve();
    });

    return dfd;
}
function displayDates(data) {
    let d = [];
    for (let s of data["archive"]) {
        let str = "";
        str += ""
    }

}
function changeCalendar(data) {
    console.log(data);
    let raDict = {};
    for(let ra of data["raList"]) {
        raDict[ra[1]] = ra[0];
    }
    let tbl = document.getElementById("calendar");






    let thead = document.getElementsByTagName("thead")[0];
    let newRow = thead.insertRow(0);
    thead.deleteRow(0);
    for (let d of ["SAT","FRI","THU","WED","TUE","MON","SUN"]) {
        let newCell = newRow.insertCell(0);
        newCell.innerHTML = d;
    }

    //document.getElementsByClassName("month")[0].innerHTML = ;

    console.log(tbl.childNodes);
    console.log(thead);
    //console.log(cap);

    console.log(raDict)
}
