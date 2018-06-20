"use strict"

// Dev stuff
document.cookie = "username=conzty01; hall=Brandt;";

function getCurSchedule() {
    // Get the schedule for the current month
    console.log("Getting Current Schedule: ",appConfig.curDate);
    getSchedule(appConfig.curDate.getMonth(),appConfig.curDate.getFullYear());
}

function getSchedule(monthNum,year) {
    // Get the schedule for the given month and year
    console.log("Getting Schedule for month: ",monthNum, year);
    appConfig.base.callAPI("getSchedule",[monthNum,year],applySchedule);
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

        for (let day of week) {
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
                    d.appendChild(r);
                }
            }
        }
    }

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
    getSchedule(appConfig.calDate.getMonth(),appConfig.appDate.getFullYear());
}
