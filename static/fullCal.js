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
        customButtons: {
            customPrevButton: {
                text: '<',
                click: movePrev
            },
            customNextButton: {
                text: '>',
                click: moveNext
            },
            customTodayButton: {
                text: 'Today',
                click: moveToday
            }
        },
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: ''
        },
        events: {
            url: '/api/getSchedule',
            failure: function () {
                alert('there was an error while fetching events!');
            },
            extraParams: function () {
                return {
                    monthNum: appConfig.calDate.getMonth() + 1,
                    year: appConfig.calDate.getFullYear()
                };
            }
        },
        lazyFetching: true
    });
}

function moveNext() {
    console.log("Change Month: Next");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() + 1);
    calendar.currentData.calendarApi.next();
}

function movePrev() {
    console.log("Change Month: Prev");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() - 1);
    calendar.currentData.calendarApi.prev();
}

function moveToday() {
    console.log("Change Month: Today");

    appConfig.calDate.setMonth(appConfig.curDate.getMonth());
    calendar.currentData.calendarApi.today();
}



///////////////////////////////////////////
/*   Functions for the index.html page   */
///////////////////////////////////////////

function addSchedule( dutyList ){
    console.log(dutyList);

    for (let duty of dutyList) {
        // duty : ('Lue', 'Girardin', '#66CDAA', 3, '2020-08-01')

        console.log(1);
        addSingleEvent(duty[3], duty[0] + ' ' + duty[1], duty[4], duty[2]);
    }
    calendar.rerender

}

function addSingleEvent( id, title, startStr, colorStr, allDay = true ) {
    var date = new Date(startStr + 'T00:00:00'); // will be in local time

    if (!isNaN(date.valueOf())) { // valid?
        calendar.addEvent({
            id: id,
            title: title,
            start: date,
            color: colorStr,
            allDay: allDay
        });
    } else {
        console.log('Invalid date: ' + startStr + ' -> ' + date);
    }
}



/////////////////////////////////////////////
/*  Functions for the conflicts.html page  */
/////////////////////////////////////////////

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
