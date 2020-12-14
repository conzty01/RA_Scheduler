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
              text: 'Clear',
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
        monthNum: appConfig.calDate.getMonth() + 1,
        year: appConfig.calDate.getFullYear()
    }

    appConfig.base.callAPI("getConflicts", data, showPrevConflicts, "GET");
}

function showPrevConflicts(conRes) {
    console.log(conRes.conflicts.length+" Conflicts Received");
    console.log(conRes);

    let conList = conRes.conflicts;

    let dayList = document.querySelectorAll("[data-date]");

    conSet = new Set();
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

function toggleColorBlind() {
    // Toggle the color of the custGreen and custRed

    let toggle = document.getElementById("cbToggle");

    // If the toggle is checked, then change colors for colorblindness
    if (toggle.checked) {
        document.documentElement.style.setProperty("--custGreen", "var(--cbGreen)");
        document.documentElement.style.setProperty("--custRed", "var(--cbRed)");

        document.documentElement.style.setProperty("--custGreenTxt", "var(--cbGreenTxt)");
        document.documentElement.style.setProperty("--custRedTxt", "var(--cbRedTxt)");

    } else {
        // Otherwise, set everything back to regular
        document.documentElement.style.setProperty("--custGreen", "var(--rgGreen)");
        document.documentElement.style.setProperty("--custRed", "var(--rgRed)");

        document.documentElement.style.setProperty("--custGreenTxt", "var(--rgGreenTxt)");
        document.documentElement.style.setProperty("--custRedTxt", "var(--rgRedTxt)");
    }
}

function conflict_Submit() {
    // Submit the conflicts to the server

    // disable the button until receive an ack from the server
    let butt = document.getElementsByClassName("fc-conflictSubmitButton-button")[0];
    butt.disabled = true;

    data = {
        conflicts: Array.from(conSet),
        monthNum: appConfig.calDate.getMonth() + 1,
        year: appConfig.calDate.getFullYear()
    };

    appConfig.base.callAPI("enterConflicts/", data, (res) => {
        let butt = document.getElementsByClassName("fc-conflictSubmitButton-button")[0]
        butt.disabled = false

        if (res.status != 1) {
            console.log(res.msg);
        } else {
            getPrevConflicts();
        }
    }, "POST");
}

function conflict_Reset() {
    // Reset the calendar and clear the conSet

    let days = document.getElementsByClassName("selected");
    let dayLen = days.length;
    //console.log(days);

    // Since getElementsByClassName returns an array-like object
    //  when a for-of loop iterates over and the class is removed,
    //  the object is actually removed from the array which
    //  skrews up the iterator. This is a simple workaround.
    for (let i = 0; i < dayLen; i++) {
        days[0].classList.remove("selected");
    }

    conSet = new Set();
}

var conSet = new Set();
