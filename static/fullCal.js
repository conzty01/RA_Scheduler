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
        //showNonCurrentDates: false
        fixedWeekCount: false
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
        lazyFetching: true,
        fixedWeekCount: false
    });
}

function initEditSchedCal() {
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
            },
            runSchedulerButton: {
                text: 'Run Scheduler',
                click: showRunModal
            },
            addEventButton: {
                text: 'Add Addtional Duty',
                click: showAddDutyModal
            }
        },
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: 'addEventButton runSchedulerButton'
        },
        events: {
            url: '/api/getSchedule',
            failure: function () {
                alert('there was an error while fetching events!');
            },
            extraParams: function () {
                return {
                    monthNum: appConfig.calDate.getMonth() + 1,
                    year: appConfig.calDate.getFullYear(),
                    allColors: true
                };
            }
        },
        lazyFetching: true,
        showNonCurrentDates: false,
        fixedWeekCount: false,
        eventClick: eventClicked
    });
}

function eventClicked(info) {
    //console.log(info);

    //console.log(info.event.start);
    //console.log(info.event.title);
    //console.log(info.event.backgroundColor);
    // Get the data clicked and make that the title of the modal
    // Get the name of the selected event (the ra on duty) and show that that
    // was the previous value.

    let modalTitle = document.getElementById("editModalLongTitle");
    modalTitle.innerHTML = info.event.start.toLocaleDateString();

    let prevRA = document.getElementById("editModalPrevRA");
    prevRA.innerHTML = info.event.title;

    let selector = document.getElementById("editModalNextRA");
    selector.value = info.event.backgroundColor;

    // Set the ID of the clicked element so that we can find the event later
    info.el.id = "lastEventSelected";

    // Hide any errors from previous event clicks
    let modal = document.getElementById("editModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    // Display the modal with RAs
    $('#editModal').modal('toggle');
}

function saveModal() {
    let selRAOption = document.getElementById("editModalNextRA").selectedOptions[0];

    let dateStr = document.getElementById("editModalLongTitle").textContent;

    let oldName = document.getElementById("editModalPrevRA").textContent;

    let newColor = selRAOption.value;
    let newName = selRAOption.text;
    // id = "selector_xxxxxx"
    // There are 9 characters before the id
    let newId = parseInt(selRAOption.id.slice(9));

    // If the new RA is different than the current RA,
    if (oldName !== newName) {
        // Save the changes
        console.log(dateStr+": Switching RA '"+oldName+"' for '"+newName+"'");

        let changeParams = {
            dateStr: dateStr,
            newId: newId,
            oldName: oldName
        }

        appConfig.base.callAPI("changeRAonDuty", changeParams, function(msg) {
            passModalSave('#editModal',msg)}, "POST",
            passModalSave("#runModal", {status:-1,msg:msg}));

    } else {
        // No change -- do nothing
        console.log(dateStr+": No change detected - Nothing to save");

    }
}

function passModalSave(modalId, msg, extraWork=() => {}) {

    //console.log(msg);

    let modal = document.getElementById(modalId);

    // If the status is '1', then the save was successful
    switch (msg.status) {
        case 1:
            // If the status is '1', then the save was successful

            // Refetch the current month's calendar
            calendar.currentData.calendarApi.refetchEvents();
            // Complete any additional work
            extraWork();
            // Hide the modal
            $(modalId).modal('toggle');

            // Ensure the respective errorDiv is hidden
            modal.getElementsByClassName("modalError")[0].style.display = "none";

            // TODO: update the points displayed
            break;

        case -1:
            // If the status is '-1', then there was an error

            // Log the Error
            console.error(msg.msg);

            // Continue to handle the unsuccessful save
        case 0:
            // If the status is '0', then the save was unsuccessful

            console.log(msg.msg);
            // Get the modal's errorDiv
            let errDiv = modal.getElementsByClassName("modalError")[0];

            // Update the errorDiv with the message
            errDiv.getElementsByClassName("msg")[0].innerHTML = msg.msg;
            // Display the errorDiv
            errDiv.style.display = "block";

            break;
    }
}

function showRunModal() {
    let title = document.getElementById("runModalLongTitle");

    title.textContent = appConfig.calDate.toLocaleString('default', { month: 'long' });

    // Hide any errors from previous scheduler runs
    let modal = document.getElementById("runModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    $('#runModal').modal('toggle');
}


function runScheduler() {
    let noDutyDays = document.getElementById("runNoDutyDates").value;
    let eligibleRAs = [];

    // Assemble list of RA ids that are eligible for the scheduler
    for (let li of document.getElementById("runRAList").getElementsByTagName("input")) {
        if (li.checked) {
            eligibleRAs.push(li.id);
        }
    }

    let monthNum = appConfig.calDate.getMonth();
    let year = appConfig.calDate.getFullYear();

    console.log("Running Scheduler for month: "+monthNum);
    console.log("  with no duties on: "+noDutyDays);
    console.log("  and RAs: "+eligibleRAs);

    // Indicate to user that scheduler is running
    document.getElementById("runButton").disabled = true;
    $("body").css("cursor", "wait");

    //document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI("runScheduler",
            {monthNum:monthNum, year:year, noDuty:noDutyDays, eligibleRAs:eligibleRAs},
            function(msg) {
                passModalSave("#runModal", msg, () => {
                    document.getElementById("runButton").disabled = false;
                    $("body").css("cursor", "auto");
                });
            }, "POST", passModalSave("#runModal", {status:-1,msg:msg}));
}

function showAddDutyModal() {
    // set the addDateDate input to point to the selected month with the appropriate range

    let datePicker = document.getElementById("addDateDate");

    // Format the min and max dates for the DatePicker

    let monthNum = appConfig.calDate.getMonth();
    let minDayNum = new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth(),1).getDate();
    let maxDayNum = new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth(),0).getDate();

    let month = monthNum + 1;
    if(month <= 9)
        month = '0' + month;

    if(minDayNum <= 9)
        minDayNum = '0' + minDayNum;

    let partialDateStr = appConfig.calDate.getFullYear() +'-'+ month +'-';

    //console.log(partialDateStr);
    //console.log(minDayNum);
    //console.log(maxDayNum);

    // Assign values to DatePicker
    datePicker.min = partialDateStr + minDayNum;
    datePicker.max = partialDateStr + maxDayNum;
    datePicker.value = partialDateStr + minDayNum;

    //console.log(datePicker);

    // Hide any errors from previous event clicks
    let modal = document.getElementById("addDutyModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    $('#addDutyModal').modal('toggle');
}

function addDuty() {
    // Get the selected date and RA from the addDutyModal and pass it to the server

    let dateVal = document.getElementById("addDateDate").value;
    let selRAOption = document.getElementById("addDateRASelect").selectedOptions[0];

    // id = "selector_xxxxxx"
    // There are 9 characters before the id
    let newId = parseInt(selRAOption.id.slice(9));

    let newParams = {
        id: newId,
        dateStr: dateVal
    }

    // Pass the parameters to the server and send results to passNewDutyModal
    appConfig.base.callAPI("addNewDuty", newParams, function(msg) {
        passModalSave('#addDutyModal',msg)}, "POST",
        passModalSave("#runModal", {status:-1,msg:msg}));

}

function deleteDuty() {
    // Get the RA that is assigned to the duty and the date and send to API

    let dateStr = document.getElementById("editModalLongTitle").textContent;
    let oldName = document.getElementById("editModalPrevRA").textContent;

    let changeParams = {
        dateStr: dateStr,
        raName: oldName
    }

    appConfig.base.callAPI("deleteDuty", changeParams,
            function(msg) {passModalSave('#editModal',msg)}, "POST",
            passModalSave("#runModal", {status:-1,msg:msg}));

}

function passNewDutyModal() {
    // Check if hanlded expection occurred or if the save was successful.
    //  If successful, hide the modal. If not, inform user.

    // TODO: Check if save succeeded and inform user if unsuccessful

    calendar.currentData.calendarApi.refetchEvents();
    $('#addDutyModal').modal('toggle');
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
