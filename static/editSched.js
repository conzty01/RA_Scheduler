"use strict"

var editCal = {};

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
}

function editSched(raList) {
    console.log(raList);
    for (let i of raList) {
        editCal[i.name] = i.id;
    }
    updateRAs(raList);

    let names = document.getElementsByClassName("name");

    for (let nameDiv of names) {
        let s = document.createElement("select");
        s.setAttribute("onChange","tallyPoints()");
        let rID = nameDiv.id;
        let rName = nameDiv.innerHTML;

        let curSel = document.createElement("option");
        curSel.text = rName;
        s.add(curSel);
        let spacer = document.createElement("option");
        spacer.text = "----";
        s.add(spacer);

        for (let ra of raList) {

            if (rID != ra.id) {
                let o = document.createElement("option");
                o.text = ra.name;
                s.add(o);
            }
        }

        nameDiv.innerHTML = "";
        nameDiv.appendChild(s);
    }

    let eb = document.getElementById("edit");
    eb.innerHTML = "Submit Changes";
    eb.setAttribute("onclick","updateSchedule()");
    let rs = document.getElementById("run");
    rs.disabled = true;
    document.getElementById("loading").style.display = "none";
}

function getEditInfo() {
    let monthNum = appConfig.calDate.getMonth();
    let year = appConfig.calDate.getFullYear();

    console.log("Editing Schedule for month: "+monthNum);

    document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI("getEditInfo",{"monthNum":monthNum,"year":year},editSched);
}

function tallyPoints() {
    let sels = document.getElementsByTagName("select");
    let resDict = {};
    for (let i of sels) {
        let raName = i.value;
        if (raName in resDict) {
            resDict[raName] += parseInt(i.parentNode.parentNode.dataset.points);
        } else {
            resDict[raName] = parseInt(i.parentNode.parentNode.dataset.points);
        }
    }
    for (let raKey in resDict) {
        let i = editCal[raKey];
        let ptsDiv = document.getElementById("list_points_"+i);
        ptsDiv.innerHTML = resDict[raKey];
    }
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
        l.id = "list_"+ra["id"];
        l.onclick = function () { highlightRA(ra["id"]); };

        // Div containing name
        let n = document.createElement("div");
        n.classList.add("tName");
        n.innerHTML = ra["name"];
        n.id = "list_name_"+ra["id"];

        // Div containing points
        let p = document.createElement("div");
        p.classList.add("tPoints");
        p.innerHTML = ra["points"];
        p.id = "list_points_"+ra["id"];

        l.appendChild(n);
        l.appendChild(p);

        newL.appendChild(l);
    }

    d.removeChild(d.children[0]);
    d.appendChild(newL);
}
