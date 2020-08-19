"use strict"

function initCal( propObject ) {
    document.addEventListener('DOMContentLoaded', function() {
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, propObject);
        calendar.render();
    });
}

function initConflictCal() {
    initCal({
        initialView: 'dayGridMonth',
        dayMaxEventRows: true,
        moreLinkClick: "popover",
        dateClick: conflict_DateClick,
        customButtons: {
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
            left: 'prev,next today',
            center: 'title',
            right: 'conflictResetButton conflictSubmitButton'
        },
        //showNonCurrentDates: false,
    });
}

function initIndexCal() {
    initCal({
        initialView: 'dayGridMonth',
        dayMaxEventRows: true,
        moreLinkClick: "popover",
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: [
            { // This object will be "parsed" into an Event Object
                title: 'Tyler Conzett',
                start: '2020-08-01',
                end: '2020-08-02',
                color: '#000',
                textColor: '#FFF',
                id: 'RAID'
            },
            { // This object will be "parsed" into an Event Object
                title: 'Abigail Korenchan',
                start: '2020-08-01',
                end: '2020-08-02',
                color: '#FF1',
                textColor: '#000',
                id: 'RAID2'
            },
            { // This object will be "parsed" into an Event Object
                title: 'Teage Luther',
                start: '2020-08-01',
                end: '2020-08-02',
                color: '#ABABAB',
                textColor: '#FFF',
                id: 'RAID3'
            },
            { // This object will be "parsed" into an Event Object
                title: 'Austin Luther',
                start: '2020-08-01',
                end: '2020-08-02',
                color: '#0d1e76',
                textColor: '#FFF',
                id: 'RAID4'
            }
        ]
    });
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

function conflict_Submit() {
    // Submit the conflicts to the server
    appConfig.base.callAPI("enterConflicts/", Array.from(conSet), conflict_Reset, "POST");
    // ^ Running into CORS error
    // let f = document.getElementById("conflictForm");
    // let i;
    // for (let d of conSet) {
    //     i = document.createElement("input");
    //
    //     i.setAttribute("value", d);
    //     i.setAttribute("style", "display:none;");
    //
    //     f.appendChild(i);
    // }
    // f.submit();
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
