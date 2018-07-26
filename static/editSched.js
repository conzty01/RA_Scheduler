"use strict"

function runScheduler() {
    let noDutyDays = prompt("Enter the days where no duties should be assigned separated by commas.\n\nFor example: 14,15,30");
    let monthNum = appConfig.calDate.getMonth();
    let year = appConfig.calDate.getFullYear();

    console.log("Running Scheduler for month: "+monthNum);
    console.log("  with no duties on: "+noDutyDays);

    document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI("runScheduler",{"monthNum":monthNum,"year":year,"noDuty":noDutyDays},reviewSched);
}

function reviewSched(resObject) {
    document.getElementById("loading").style.display = "none";

    applySchedule(resObject["schedule"]);
    updateRAs(resObject["raStats"]);

    document.getElementById("run").innerHTML = "Re-Run";
}

function editCalendar() {

}

function highlightRA(i) {
    let raNames = document.getElementsByClassName("name");
    for (let entry of raNames) {
        if (i == entry.id) {
            entry.style.boxShadow = "0px 0px 30px blue";
        } else {
            entry.style.boxShadow = "none";
        }
    }
}

function updateRAs(raList) {
    // Expecting a list containing objects with the following keys:
    //   id: id of the ra
    //   name: full name of the ra
    //   mPts: points the RA has in the current month

    let d = document.getElementById("raList");
    let newL = document.createElement("ul");

    for (let ra of raList) {
        // List entry
        let l = document.createElement("li");
        l.id = ra["id"];
        l.onclick = function () { highlightRA(ra["id"]); };

        // Div containing name
        let n = document.createElement("div");
        n.classList.add("tName");
        n.innerHTML = ra["name"];

        // Div containing points
        let p = document.createElement("div");
        p.classList.add("tPoints");
        p.innerHTML = ra["pts"];

        l.appendChild(n);
        l.appendChild(p);

        newL.appendChild(l);
    }

    d.removeChild(d.children[0]);
    d.appendChild(newL);
}
