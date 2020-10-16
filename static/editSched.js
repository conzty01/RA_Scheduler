"use strict"

///////////////////////////////////////////
/* Functions for the editSched.html page */
///////////////////////////////////////////

function initEditSchedCal() {
    initCal({
        height: "75%",
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
        dateClick: showAddDutyModal,
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: 'addEventButton runSchedulerButton'
        },
        eventSources: [
            {
                url: '/api/getSchedule',
                failure: function () {
                    alert('there was an error while fetching Regular Duties!');
                },
                extraParams: function () {
                    return {
                        monthNum: appConfig.calDate.getMonth() + 1,
                        year: appConfig.calDate.getFullYear(),
                        allColors: true
                    };
                },
            },
            {
                url: '/api/getBreakDuties',
                failure: function () {
                    alert('there was an error while fetching Break Duties!');
                },
                extraParams: function () {
                    return {
                        monthNum: appConfig.calDate.getMonth() + 1,
                        year: appConfig.calDate.getFullYear(),
                        allColors: false
                    };
                },
                eventDataTransform: makeBackgroundEvent
            }
        ],
        lazyFetching: true,
        showNonCurrentDates: false,
        fixedWeekCount: false,
        eventClick: eventClicked
    });
}

function makeBackgroundEvent(event) {
    // Add the display: background attributed to each event

    let tmp = {};

    tmp.id = event.id;
    tmp.title = "Break Duty";
    tmp.display = "background";
    tmp.start = event.start;

    return tmp;
}

function eventClicked(info) {
    //console.log(info);

    //console.log(info.event.start);
    //console.log(info.event.title);
    //console.log(info.event.backgroundColor);
    //console.log(info.event.extendedProps);
    // Get the data clicked and make that the title of the modal
    // Get the name of the selected event (the ra on duty) and show that that
    // was the previous value.

    let modalTitle = document.getElementById("editModalLongTitle");
    modalTitle.innerHTML = info.event.start.toLocaleDateString();

    let prevRA = document.getElementById("editModalPrevRA");
    prevRA.value = info.event.title;

    let selector = document.getElementById("editModalNextRA");
    selector.value = info.event.backgroundColor;

    switch (info.event.extendedProps.dutyType) {
        case "std":
            // If the duty clicked is a normal duty, then activate the del and save buttons
            document.getElementById("editDelButt").disabled = false;
            document.getElementById("editSavButt").disabled = false;

            // Also hide the break duty message
            document.getElementById("breakDutyWarning").style.display = "none";

            break;

        case "brk":
            // If it is a break duty, disable the del and save buttons
            document.getElementById("editDelButt").disabled = true;
            document.getElementById("editSavButt").disabled = true;

            // Also hide the break duty message
            document.getElementById("breakDutyWarning").style.display = "block";

            break;

        default:
            console.log("Reached Default State for dutyType: ", info.event.extendedProps.dutyType);

            // Disable del and sav buttons
            document.getElementById("editDelButt").disabled = true;
            document.getElementById("editSavButt").disabled = true;

            // Hide the break duty msesage
            document.getElementById("breakDutyWarning").style.display = "none";

    }

    // Set the ID of the clicked element so that we can find the event later
    info.el.id = "lastEventSelected";

    // Hide any errors from previous event clicks
    let modal = document.getElementById("editModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    // Display the modal with RAs
    $('#editModal').modal('show');
}

function saveModal() {
    let selRAOption = document.getElementById("editModalNextRA").selectedOptions[0];

    let dateStr = document.getElementById("editModalLongTitle").textContent;

    let oldName = document.getElementById("editModalPrevRA").selectedOptions[0].value;

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

        appConfig.base.callAPI("changeRAonDuty", changeParams,
            function(msg) {
                passModalSave('#editModal',msg);
            }, "POST",
            function(msg) {passModalSave("#editModal", {status:-1,msg:msg})});

    } else {
        // No change -- do nothing
        console.log(dateStr+": No change detected - Nothing to save");

    }
}

function passModalSave(modalId, msg, extraWork=() => {}) {

    //console.log(msg);

    let modal = document.getElementById(modalId.slice(1));

    // If the status is '1', then the save was successful
    switch (msg.status) {
        case 1:
            // If the status is '1', then the save was successful

            // Refetch the current month's calendar
            calendar.currentData.calendarApi.refetchEvents();
            // Get the updated points
            getPoints();
            // Complete any additional work
            extraWork();
            // Hide the modal
            $(modalId).modal('hide');

            // Ensure the respective errorDiv is hidden
            modal.getElementsByClassName("modalError")[0].style.display = "none";

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

        default:
            console.error("REACHED DEFAULT STATE: ",msg);
            break;
    }
}

function showRunModal() {
    let title = document.getElementById("runModalLongTitle");

    title.textContent = appConfig.calDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    // Hide any errors from previous scheduler runs
    let modal = document.getElementById("runModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    $('#runModal').modal('show');
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

    console.log("Running Scheduler for month: "+(monthNum+1));
    console.log("  with no duties on: "+noDutyDays);
    console.log("  and RAs: "+eligibleRAs);

    // Indicate to user that scheduler is running
    document.getElementById("runButton").disabled = true;
    $("body").css("cursor", "wait");

    //document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI("runScheduler",
            {monthNum:monthNum+1, year:year, noDuty:noDutyDays, eligibleRAs:eligibleRAs},
            function(msg) {
                passModalSave("#runModal", msg, () => {
                    document.getElementById("runButton").disabled = false;
                    $("body").css("cursor", "auto");
                });
            }, "POST", function(msg) {passModalSave("#runModal", {status:-1,msg:msg})});
}

function showAddDutyModal(info=null) {
    // set the addDateDate input to point to the selected month with the appropriate range
    //console.log(info.type, info);
    let datePicker = document.getElementById("addDateDate");

    // Format the min and max dates for the DatePicker

    let monthNum = appConfig.calDate.getMonth();
    let minDayNum = new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth(),1).getDate();
    let maxDayNum = new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth()+1,0).getDate();

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

    //console.log(datePicker.min, datePicker.max);

    // If called from clicking a date
    if (info.type === "click") {
        // Set the value to the date selected
        //console.log("BUTTON CLICK",info.dateStr);
        datePicker.value = partialDateStr + minDayNum;

    } else {
        // Set the value to the first day of the month
        //console.log("CALENDER CLICK",partialDateStr + minDayNum);
        datePicker.value = info.dateStr;
    }

    //console.log(datePicker);

    // Hide any errors from previous event clicks
    let modal = document.getElementById("addDutyModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    $('#addDutyModal').modal('show');
}

function addDuty() {
    // Get the selected date and RA from the addDutyModal and pass it to the server

    let dateVal = document.getElementById("addDateDate").value;
    let selRAOption = document.getElementById("addDateRASelect").selectedOptions[0];
    let ptVal = document.getElementById("addDatePts").value;

    // id = "selector_xxxxxx"
    // There are 9 characters before the id
    let newId = parseInt(selRAOption.id.slice(9));

    let newParams = {
        id: newId,
        dateStr: dateVal,
        pts: ptVal
    }

    // Pass the parameters to the server and send results passModalSave
    appConfig.base.callAPI("addNewDuty", newParams, function(msg) {
        passModalSave('#addDutyModal',msg)}, "POST",
        function(msg) {passModalSave("#addDutyModal", {status:-1,msg:msg})});

}

function deleteDuty() {
    // Get the RA that is assigned to the duty and the date and send to API

    let dateStr = document.getElementById("editModalLongTitle").textContent;
    let oldName = document.getElementById("editModalPrevRA").selectedOptions[0].value;

    let changeParams = {
        dateStr: dateStr,
        raName: oldName
    }

    appConfig.base.callAPI("deleteDuty", changeParams,
            function(msg) {passModalSave('#editModal',msg)}, "POST",
            function(msg) {passModalSave("#editModal", {status:-1,msg:msg})});

}

var editCal = {};

function getPoints() {

    // In order to determine what school year the user is currently in
    //  we need to get the current date and determine if its between
    //  08-01 and 06-01

    let curMonNum = appConfig.curDate.getMonth();
    let startYear;
    let endYear;

    if (curMonNum >= 7) {
        // If the current month is August or later
        //  then the current year is the startYear

        startYear = appConfig.curDate.getFullYear();
        endYear = appConfig.curDate.getFullYear() + 1;

    } else {
        // If the current month is earlier than August
        //  then the current year is the endYear

        startYear = appConfig.curDate.getFullYear() - 1;
        endYear = appConfig.curDate.getFullYear();
    }

    let params = {
        start: startYear.toString() + '-08-01',
        end: endYear.toString() + '-06-01'
    }

    appConfig.base.callAPI("getStats", params, updatePoints, "GET");

}

function updatePoints(pointDict) {
    // PointDict is expected to be as follows:
    // { raId: {name: x, pts: x}, ... }
    console.log(pointDict);

    let raListDiv = document.getElementById("raList");

    for (let idKey in pointDict) {
        // Get the Div containing the points for the respective RA
        let ptDiv = document.getElementById("list_points_" + idKey);

        if (ptDiv == null) {
            // If the RA is not currently in the raList
            //  then create a new entry for them.

            let newLi = document.createElement("li");
            newLi.id = "list_" + idKey;

            let newNameDiv = document.createElement("div");
            newNameDiv.id = "list_name_" + idKey;
            newNameDiv.classList.add("tName");
            newNameDiv.innerHTML = pointDict[idKey].name;

            let newPtsDiv = document.createElement("div");
            newPtsDiv.id = "list_points_" + idKey;
            newPtsDiv.classList.add("tPoints");
            newPtsDiv.innerHTML = pointDict[idKey].pts;

            newLi.appendChild(newNameDiv);
            newLi.appendChild(newPtsDiv);
            raListDiv.getElementsByTagName("ul")[0].appendChild(newLi);

        } else {
            // Else update the point value
            ptDiv.innerHTML = pointDict[idKey].pts;
        }
    }
}


function highlightRA(i) {
    let raNames = document.getElementsByClassName("name");
    for (let entry of raNames) {
        if (i == entry.id) {
            entry.style.boxShadow = "0px 0px 30px blue";
        } else {
            entry.style.boxShadow = "none";
        }
    }
}
