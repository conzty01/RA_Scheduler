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
        determineNavigationButtonStatus();
    });
}

function moveNext() {
    console.log("Change Month: Next");

    // Check to see if the 'next' button has been disabled
    if (!$('.fc-customNextButton-button').prop('disabled')) {
        // If not, then move the calendar view to the next month.
        appConfig.calDate.setMonth(appConfig.calDate.getMonth() + 1);
        console.log(appConfig.calDate);
        calendar.currentData.calendarApi.next();

        // Enable and disable the appropriate buttons
        determineNavigationButtonStatus();
    }

}

function movePrev() {
    console.log("Change Month: Prev");

    // Check to see if the 'previous' button has been disabled
    if (!$('.fc-customPrevButton-button').prop('disabled')) {
        // If not, then move the calendar view to the previous month.
        appConfig.calDate.setMonth(appConfig.calDate.getMonth() - 1);
        console.log(appConfig.calDate);
        calendar.currentData.calendarApi.prev();

        // Enable and disable the appropriate buttons
        determineNavigationButtonStatus();
    }

}

function moveToday() {
    console.log("Change Month: Today");

    appConfig.calDate.setMonth(appConfig.curDate.getMonth());
    appConfig.calDate.setFullYear(appConfig.curDate.getFullYear());
    calendar.currentData.calendarApi.today();

    // Enable and disable the appropriate buttons
    determineNavigationButtonStatus();
}

function determineNavigationButtonStatus() {
    // Determine which of the navigation buttons should be
    //  enabled and disabled based on the current month view.

    let disablePrev = false;
    let disableNext = false;

    // If the current month is the first month of the school
    //  year or earlier...
    if (appConfig.calDate.getFullYear() <= schoolYearStart.getFullYear() &&
            appConfig.calDate.getMonth() <= schoolYearStart.getMonth()) {
        // Then disable the 'prev' and enable the 'next' buttons
        disablePrev = true;

    } else if (appConfig.calDate.getFullYear() >= schoolYearEnd.getFullYear() &&
            appConfig.calDate.getMonth() >= schoolYearEnd.getMonth()) {
        // Otherwise, if the current month is the last month of
        //  the school year or later...

        // Then disable the 'next' and enable the 'prev' buttons
        disableNext = true;

    }

    // Otherwise, both buttons remain enabled
    $(".fc-customPrevButton-button").prop('disabled', disablePrev);
    $(".fc-customNextButton-button").prop('disabled', disableNext);

}