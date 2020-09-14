/////////////////////////////////////////////
/*  Functions for the conflicts.html page  */
/////////////////////////////////////////////

function initConflictCal() {
    initCal({
        height: "75%",
        initialView: 'dayGridMonth',
        dayMaxEventRows: true,
        moreLinkClick: "popover",
        dateClick: conflict_DateClick,
        customButtons: {
            customPrevButton: {
                text: '<',
                click: conflictPrev
            },
            customNextButton: {
                text: '>',
                click: conflictNext
            },
            customTodayButton: {
                text: 'Today',
                click: conflictToday
            },
            conflictSubmitButton: {
              text: 'Submit',
              click: conflict_Submit
            },
            conflictResetButton: {
              text: 'Reset',
              click: conflict_Reset
            },
        },
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: 'conflictResetButton conflictSubmitButton'
        },
        //showNonCurrentDates: false
        fixedWeekCount: false
    });
}

function conflictNext() {
    console.log("Change Month: Next");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() + 1);
    console.log(appConfig.calDate);

    getPrevConflicts();

    calendar.currentData.calendarApi.next();
}

function conflictPrev() {
    console.log("Change Month: Prev");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() - 1);
    console.log(appConfig.calDate);

    getPrevConflicts();

    calendar.currentData.calendarApi.prev();
}

function conflictToday() {
    console.log("Change Month: Today");

    appConfig.calDate.setMonth(appConfig.curDate.getMonth());

    getPrevConflicts();

    calendar.currentData.calendarApi.today();
}

function conflict_DateClick(info) {
    console.log(info);
    //alert('Clicked on: ' + info.dateStr);
    //alert('Coordinates: ' + info.jsEvent.pageX + ',' + info.jsEvent.pageY);
    //alert('Current view: ' + info.view.type);

    // If the selected day is not part of the month
    if (!(info.dayEl.classList.contains("fc-day-other"))) {

        // change the day's background color
        if (info.dayEl.classList.contains("selected")) {
            // Remove the selected date from the conSet
            conSet.delete(info.dateStr);
            // Remove the 'selected' class from the date
            info.dayEl.classList.remove("selected");

        } else {
            // Add the selected date to the conSet
            conSet.add(info.dateStr);
            // Add the 'selected' class to the date
            info.dayEl.classList.add("selected");
        };
    };
}

function getPrevConflicts() {
    console.log("Fetching Previously Entered Conflicts");

    let data = {
        // Convert from js zero-based numbering
        monthNum: appConfig.calDate.getMonth(),
        year: appConfig.calDate.getFullYear()
    }

    appConfig.base.callAPI("getConflicts", data, showPrevConflicts, "GET");
}

function showPrevConflicts(conRes) {
    console.log(conRes.conflicts.length+" Conflicts Received");
    console.log(conRes);

    let conList = conRes.conflicts;

    let dayList = document.querySelectorAll("[data-date]");

    for (let dayEl of dayList) {

        // If the dayElement's date is in the conList
        if (conList.includes(dayEl.dataset.date)) {

            // Mark the dayElement as selected
            dayEl.classList.add("selected");
            // And add the date to the conSet
            conSet.add(dayEl.dataset.date);
        }
    }

}
