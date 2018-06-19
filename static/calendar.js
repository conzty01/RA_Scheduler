"use strict"

// Dev stuff
document.cookie = "username=conzty01; hall=Brandt;";

function getCurSchedule() {
    getSchedule();
}

function getSchedule(month) {
    appConfig.base.callAPI("getSchedule")
}

function applySchedule(sched) {

}

function clearCalendar() {
    let ras = document.getElementsByClassName("name");
    let loopTimes = ras.length;
    // This is needed because .length updates each time a div is removed.

    for (let i = 0; i < loopTimes; i++) {
        //console.log("Removing RA: ",ras[0]);
        ras[0].remove();
    }
}

function changeMonth(i) {
    // This function should change the calendar to show either the previous
    //  or next month depending on the integer that is passed as a parameter.
    //   1  indicates the next month
    //  -1  indicates the previous month

    console.log("Change Month: ",i);
}
