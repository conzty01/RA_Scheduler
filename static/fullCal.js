"use strict"


/////////////////////////////////////////////
/* Functions for the initializing calendar */
/////////////////////////////////////////////

function initCal( propObject ) {
    document.addEventListener('DOMContentLoaded', function() {
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, propObject);
        //console.log(calendar);
        window.calendar = calendar;
        calendar.render();
    });
}

function moveNext() {
    console.log("Change Month: Next");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() + 1);
    console.log(appConfig.calDate);
    calendar.currentData.calendarApi.next();
}

function movePrev() {
    console.log("Change Month: Prev");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() - 1);
    console.log(appConfig.calDate);
    calendar.currentData.calendarApi.prev();
}

function moveToday() {
    console.log("Change Month: Today");

    appConfig.calDate.setMonth(appConfig.curDate.getMonth());
    calendar.currentData.calendarApi.today();
}
