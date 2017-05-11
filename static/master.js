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
        displayDates(data)
        dfd.resolve();
    });

    return dfd;
}
function displayDates(data) {
    // data contains archive date list, hallID int, and raList Dictionary
    let datesDiv = document.getElementById("dates");
    let datesUl = document.createElement("ul");

    for (let s of data["archive"]) {
        let l = document.createElement("li")
        l.innerHTML = s;
        l.className = "arcDates";
        let a = "getSchedule(this,"+data["hallID"].toString()+")";
        l.setAttribute("onclick",a);
        datesUl.appendChild(l);
    }

    datesDiv.appendChild(datesUl);

}
function getSchedule(li, id) {
    let dfd = new $.Deferred();

    let qStr = li.innerText +"_"+ id.toString()
    $.ajax({
		url: `http://localhost:5000/api/v1/arcRetrieve/${qStr}`,
		method: "GET"
    }).done(function(data) {
        changeCalendar(data)
        dfd.resolve();
    });

    return dfd
}
function changeCalendar(data) {
    document.getElementsByTagName("caption")[0].innerHTML = data["schedule"][2].split(" ")[2];
    console.log(data);
    let sch = data["schedule"].splice(0,2);

    let tbl = document.getElementById("calendar");

    for (let i = tbl.rows.length; i > 1; i--) {
        tbl.deleteRow(1);
    }

    for (let week of data["cal"]) {
        let tr = document.createElement("tr");

        for (let date of week) {
            let td = document.createElement("td");
            if (date[0] === 0) {
                tr.appendChild(td);
            } else {
                let div = document.createElement("div");
                div.className = "day";
                div.innerHTML = date[0];

                let d0 = date[0];

                if (data["schedule"][d0]) {
                    for (let ra in data["raList"]) {
                        if (data["schedule"][d0].indexOf(data["raList"][ra]) >= 0) {
                            let raDiv = document.createElement("div");
                            raDiv.innerHTML = ra;
                            td.appendChild(raDiv);
                        }
                    }
                }

                td.appendChild(div);
                tr.appendChild(td);
            }
        }
        tbl.appendChild(tr);
    }

}
function indexchangeHall(sel) {
    let dfd = new $.Deferred();
	let hallOpt = sel.options[sel.selectedIndex].value;

	$.ajax({
		url: `http://localhost:5000/api/v1/curSchedule/${hallOpt}`,
		method: "GET"
    }).done(function(data) {
        changeCalendar(data)
        dfd.resolve();
    });

    return dfd;

}
function conflictChangeSelect(sel) {
    let dfd = new $.Deferred();
	let hallOpt = sel.options[sel.selectedIndex].value;

	$.ajax({
		url: `http://localhost:5000/api/v1/getRAs/${hallOpt}`,
		method: "GET"
    }).done(function(data) {
        console.log(data);
        changeSelect(data)
        dfd.resolve();
    });

    return dfd
}
function changeSelect(data) {
    let sel = document.getElementById("raList");
    for (let i; i < sel.options.length; i++) {
        sel.removeChild(0);
    }
    for (let o of data) {
        let opt = document.createElement("option");
        opt.value = o[0];
        opt.innerHTML = o[1];
        sel.appendChild(opt);
    }
}
