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
            addEventButton: {
                text: 'Add Break Duty',
                click: showAddDutyModal
            }
        },
        dateClick: showAddDutyModal,
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: 'addEventButton'
        },
        events: {
            url: 'api/getBreakDuties',
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
    prevRA.value = info.event.title;

    let selector = document.getElementById("editModalNextRA");
    selector.value = info.event.title;

    // Load the duty's point value
    document.getElementById("editDatePts").value = info.event.extendedProps.pts;

    // Set the ID of the clicked element so that we can find the event later
    info.el.id = "lastEventSelected";

    // Hide any errors from previous event clicks
    let modal = document.getElementById("editModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    // Display the modal with RAs
    $('#editModal').modal('show');
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

function addBreakDuty() {
    // Get the selected date and RA from the addDutyModal and pass it to the server.

    let dateVal = document.getElementById("addDateDate").value;
    let selRAOption = document.getElementById("addDateRASelect").selectedOptions[0];
    let ptVal = document.getElementById("addDatePts").value;

    console.log("Adding Break Duty:" + dateVal);

    // id = "selector_xxxxxx"
    // There are 9 characters before the id
    let newId = parseInt(selRAOption.id.slice(9));

    let newParams = {
        id: newId,
        dateStr: dateVal,
        pts: ptVal
    }

    // Pass the parameters to the server and send results passModalSave
    appConfig.base.callAPI("addBreakDuty", newParams, function(msg) {
        passModalSave('#addDutyModal',msg)}, "POST",
        function(msg) {passModalSave("#addDutyModal", {status:-1,msg:msg})});


}

function deleteBreakDuty() {
    // Get the RA that is assigned to the break duty and the date and send to API

    let dateStr = document.getElementById("editModalLongTitle").textContent;
    let oldName = document.getElementById("editModalPrevRA").selectedOptions[0].value;

    let changeParams = {
        dateStr: dateStr,
        raName: oldName
    }

    appConfig.base.callAPI("deleteBreakDuty", changeParams,
            function(msg) {passModalSave('#editModal',msg)}, "POST",
            function(msg) {passModalSave("#editModal", msg)});
}

function getBreakCount() {
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

    appConfig.base.callAPI("getRABreakStats", params, updateBDCount, "GET");
}

function updateBDCount(bkDict) {
    // PointDict is expected to be as follows:
    // { raId: {name: x, pts: x}, ... }
    console.log(bkDict);

    let raListDiv = document.getElementById("raList");

    for (let idKey in bkDict) {
        // Get the Div containing the points for the respective RA
        let bkDiv = document.getElementById("list_points_" + idKey);

        if (bkDiv == null) {
            // If the RA is not currently in the raList
            //  then create a new entry for them.

            let newLi = document.createElement("li");
            newLi.id = "list_" + idKey;

            let newNameDiv = document.createElement("div");
            newNameDiv.id = "list_name_" + idKey;
            newNameDiv.classList.add("tName");
            newNameDiv.innerHTML = pointDict[idKey].name;

            let newCountDiv = document.createElement("div");
            newCountDiv.id = "list_points_" + idKey;
            newCountDiv.classList.add("tPoints");
            newCountDiv.innerHTML = pointDict[idKey].count;

            newLi.appendChild(newNameDiv);
            newLi.appendChild(newCountDiv);
            raListDiv.getElementsByTagName("ul")[0].appendChild(newLi);

        } else {
            // Else update the point value
            bkDiv.innerHTML = bkDict[idKey].count;
        }
    }
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
    let pts = parseInt(document.getElementById("editDatePts").value);

    // If the new RA is different than the current RA,
    if (typeof selRAOption !== "undefined") {
        // Save the changes
        console.log(dateStr+": Switching RA '"+oldName+"' for '"+newName+"'");

        let changeParams = {
            dateStr: dateStr,
            newId: newId,
            oldName: oldName,
            pts: pts
        }

        appConfig.base.callAPI("changeBreakDuty", changeParams,
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
            // Get the updated break duties
            getBreakCount();
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
