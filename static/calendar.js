"use strict"

// Dev stuff
//document.cookie = "username=conzty01; hall=Brandt;";

function getCurSchedule() {
    // Get the schedule for the current month
    console.log("Getting Current Schedule: ",appConfig.curDate);
    appConfig.calDate.setMonth(appConfig.curDate.getMonth());
    appConfig.calDate.setYear(appConfig.curDate.getFullYear());
    getSchedule(appConfig.curDate.getMonth()+1,appConfig.curDate.getFullYear());
    // The +1 accounts for the 0 indexing ---^
}

function getSchedule(monthNum,year) {
    // Get the schedule for the given month and year
    console.log("Getting Schedule for month: ",monthNum, year);
    document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI("getSchedule",{"monthNum":monthNum,"year":year},applySchedule);
}

function applySchedule(sched) {
    // Apply the given schedule to the calendar
    console.log("Applying Schedule: ",sched);

    clearCalendar();
    document.getElementById("current-month").innerHTML = sched["month"];
    let cal = document.getElementById("calendar");

    for (let week of sched["dates"]) {
        let w = document.createElement("div");
        w.className = "calendar__week";
        cal.appendChild(w); // Append "calendar__week" div to "calendar" div

        let dayNum = 0;
        for (let day of week) {
            let pts;
            if (dayNum in [0,1,2,3,4]) {
                pts = 1;
            } else {
                pts = 2;
            }
            let d = document.createElement("div");
            let dDate = document.createElement("div");
            dDate.className = "date";

            d.appendChild(dDate);   // Append the "date" div to the "calendar__day" div
            w.appendChild(d);   // Append the "calendar__day" div to the "calendar__week" div

            d.className = "calendar__day day";

            if (day["date"] !== 0) {
                dDate.innerHTML = day["date"];
                d.id = "d" + day["date"];
                for (let ra of day["ras"]) {
                    let r = document.createElement("div");
                    r.className = "name";
                    r.setAttribute("style","background-color:"+ra["bgColor"]+";border-color:"+ra["bdColor"]);
                    r.innerHTML = ra["name"];
                    r.id = ra["id"];
                    d.appendChild(r);
                }
            }
            d.setAttribute("data-points",pts);
            dayNum++;
            if (dayNum >= 7) {
                dayNum = 0;
            }
        }
    }
    document.getElementById("loading").style.display = "none";

}

function clearCalendar() {
    // Clear the calendar of all RAs
    let w = document.getElementsByClassName("calendar__week");
    let loopTimes = w.length;
    // This is needed because .length updates each time a div is removed.

    for (let i = 0; i < loopTimes; i++) {
        //console.log("Removing RA: ",ras[0]);
        w[0].remove();
    }
}

function changeMonth(i) {
    // This function should change the calendar to show either the previous
    //  or next month depending on the integer that is passed as a parameter.
    //   1  indicates the next month
    //  -1  indicates the previous month

    console.log("Change Month: ",i);
    appConfig.calDate.setMonth(appConfig.calDate.getMonth() + i);
    getSchedule(appConfig.calDate.getMonth()+1,appConfig.calDate.getFullYear());
}

function resetForm() {
    console.log("Reset Form");
    let days = document.getElementsByClassName("checkLabel");
    for (let d of days) {
        d.setAttribute("style","background-color:rgba(0,255,0,0.3)");
    }
    document.getElementById("conflictForm").reset();
}
function submitForm() {
    console.log("Submit Form");
    let inputBox = document.getElementById("monthInfo");
    let d = appConfig.calDate;
    inputBox.value = d.getMonth().toString()+"/"+d.getFullYear().toString();
    document.getElementById("conflictForm").submit();
}

window.onload = getCurSchedule();
