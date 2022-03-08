"use strict"

///////////////////////////////////////////
/* Functions for the editSched.html page */
///////////////////////////////////////////

// Calendar button configurations to be passed
//  into the initialization function.
var schedButtons = {
    customPrevButton: {
        text: '<',
        click: editSchedMovePrev
    },
    customNextButton: {
        text: '>',
        click: editSchedMoveNext
    },
    customTodayButton: {
        text: 'Today',
        click: editSchedMoveToday
    },
    runSchedulerButton: {
        text: 'Schedule',
        click: showRunModal
    },
    addEventButton: {
        text: 'Add Duty',
        click: showAddDutyModal
    }
}
var calToolbar = {
    left: 'customPrevButton,customNextButton customTodayButton',
    center: 'title',
    right: 'addEventButton runSchedulerButton'
}

/*   Override Calendar Navigation Functions   */
function editSchedMoveCalendar(direction) {
    // Call the appropriate base function to actually change the calendar.
    switch (direction) {
        case -1:
            movePrev();
            break;
        case  0:
            moveToday();
            break;
        case  1:
            moveNext();
            break;
    }

    // Adjust the datepicker in the run scheduler modal to look at the next month.
    resetDatePicker(
        new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth(), 1),
        new Date(appConfig.calDate.getFullYear(), appConfig.calDate.getMonth()+1, 0),
        []
    );
}

function editSchedMovePrev()  { editSchedMoveCalendar(-1) }
function editSchedMoveToday() { editSchedMoveCalendar( 0) }
function editSchedMoveNext()  { editSchedMoveCalendar( 1) }

function resetDatePicker(start, end, disabledDates) {

console.log(start);
console.log(end);
let opts = {
        dateFormat: "d",
        maxDate: start,
        minDate: end,
        mode: "multiple",
        conjunction: ", "
    }
    console.log(opts)

    $("#runNoDutyDates").flatpickr().destroy()

    $("#runNoDutyDates").flatpickr(opts);

    $("#runNoDutyDates").flatpickr(opts).redraw()

}

function initEditSchedCal() {
    initCal({
        height: "75%",
        initialView: 'dayGridMonth',
        dayMaxEventRows: true,
        moreLinkClick: "popover",
        customButtons: schedButtons,
        dateClick: showAddDutyModal,
        headerToolbar: calToolbar,
        eventSources: [
            {
                url: '/schedule/api/getSchedule',
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
                eventDataTransform: displayFlaggedDuties
            },
            {
                url: '/breaks/api/getBreakDuties',
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
        eventClick: eventClicked,
        eventOrder: "flagged, title"
    });
}

function makeBackgroundEvent(event) {
    // Add the display: background attributed to each event

    let tmp = {};

    tmp.id = event.id;
    tmp.title = "Break Duty";
    tmp.display = "background";
    tmp.start = event.start;
    tmp.classNames = ["bkg-breakDuty"];
    tmp.extendedProps = event.extendedProps;

    return tmp;
}

function displayFlaggedDuties(event) {
    // Add the

    // Create a temporary event object
    let tmp = {};

    // Translate all of the event information
    //  over to the new event object
    tmp.id = event.id;
    tmp.title = event.title;
    tmp.start = event.start;
    tmp.color = event.color;
    tmp.extendedProps = event.extendedProps;

    // Check to see if this event has been flagged
    if (tmp.extendedProps.flagged) {
       tmp.display = "list-item";
    }

    // Return the transformed event object
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

    // If the event that was clicked is a break duty
    if (info.event.extendedProps.dutyType === "brk") {
        // Do nothing
        return;
    }

    let modalTitle = document.getElementById("editModalLongTitle");
    modalTitle.innerHTML = info.event.start.toLocaleDateString();

    let prevRA = document.getElementById("editModalPrevRA");
    prevRA.value = info.event.title;

    let selector = document.getElementById("editModalNextRA");
    selector.value = info.event.title;

    switch (info.event.extendedProps.dutyType) {
        case "std":
            // If the duty clicked is a normal duty, then activate the del and save buttons
            document.getElementById("editDelButt").disabled = false;
            document.getElementById("editSavButt").disabled = false;

            // Also hide the break duty message
            document.getElementById("breakDutyWarning").style.display = "none";

            // Load whether or not the duty has already been flagged
            document.getElementById("editFlag").checked = info.event.extendedProps.flagged;

            // Load the duty's point value
            document.getElementById("editDatePts").value = info.event.extendedProps.pts;

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

            // Hide the break duty message
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

    let dutyFlag = document.getElementById("editFlag").checked;
    let pts = parseInt(document.getElementById("editDatePts").value);

    // Check to make sure that we have selected an RA.
    if (typeof selRAOption !== "undefined") {
        // Save the changes
        console.log(dateStr+": Switching RA '"+oldName+"' for '"+newName+"'");

        let changeParams = {
            dateStr: dateStr,
            newId: newId,
            oldName: oldName,
            flag: dutyFlag,
            pts: pts
        }

        appConfig.base.callAPI("alterDuty", changeParams,
            function(msg) {
                passModalSave('#editModal',msg);
            }, "POST",
            function(msg) {passModalSave("#editModal", {status:-1,msg:msg})});

    } else {
        // No change -- do nothing
        console.log(dateStr+": No change detected - Nothing to save");

    }
}

async function passModalSave(modalId, msg, extraWork=() => {}) {

    //console.log(msg);

    let modal = document.getElementById(modalId.slice(1));

    // Wait for the msg to arrive (if needed)
    await msg;

    // If the status is '1', then the save was successful
    switch (msg.status) {
        case 1:
            // If the status is '1', then the save was successful

            // Refetch the current month's calendar
            calendar.currentData.calendarApi.refetchEvents();
            // Get the updated points
            getPoints();
            // Get the updated scheduler requests
            getSchedRequests();
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

            // Complete any additional work
            extraWork();

            // Update the errorDiv with the message
            errDiv.getElementsByClassName("msg")[0].innerHTML = msg.msg;

            // Hide the user info div
            hideModalUserInfoDiv(modalId.slice(1));

            // Display the errorDiv
            errDiv.style.display = "block";

            break;

        default:
            console.error("REACHED DEFAULT STATE: ",msg);
            break;
    }
}

function showRunModal() {
    // Show the runModal to the user.

    // Grab the modal from the DOM.
    let title = document.getElementById("runModalLongTitle");

    // Grab the date from the calendar view.
    title.textContent = appConfig.calDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    // Hide any errors from previous scheduler runs
    hideModalErrorDiv("runModal");

    // Hide any user info messages from previous scheduler runs
    hideModalUserInfoDiv("runModal");

    // Show the modal to the user.
    $('#runModal').modal('show');
}

function hideModalErrorDiv(modalName) {
    // Hide the error div in the provided modal.

    // Grab the modal
    let modal = document.getElementById(modalName);
    //Get the errorDiv within the modal
    let errDiv = modal.getElementsByClassName("modalError")[0];
    // Hide it from sight
    errDiv.style.display = "none";
}

function hideModalUserInfoDiv(modalName) {
    // Hide the user info div in the provided modal.

    // Grab the modal
    let modal = document.getElementById(modalName);
    //Get the errorDiv within the modal
    let infoDiv = modal.getElementsByClassName("modalUserInfo")[0];

    // If this modal has a modalUserInfo div
    if (infoDiv !== undefined) {
        // Hide it from sight
        infoDiv.style.display = "none";
    }
}

function runScheduler() {
    let noDutyDays = document.getElementById("runNoDutyDates").value;

    // Hide any error message within the DIV
    hideModalErrorDiv("runModal");

    // Get the list of selected eligibleRAs
    let eligibleRAs = $('#runRAList').val()

    let monthNum = appConfig.calDate.getMonth();
    let year = appConfig.calDate.getFullYear();

    // Get the value of the autoExcAdj checkbox -- currently unused
    //let autoExcAdjVal = document.getElementById("autoExcAdj").checked;


    console.log("Running Scheduler for month: "+(monthNum+1));
    console.log("  with no duties on: "+noDutyDays);
    console.log("  and RAs: "+eligibleRAs);

    // Indicate to user that scheduler is running
    document.getElementById("runButton").disabled = true;
    document.getElementById("runModalProgressBar").style.display = "inherit";
    //$("body").css("cursor", "wait");

    let data = {
        monthNum: monthNum + 1,
        year: year,
        noDuty: noDutyDays,
        eligibleRAs: eligibleRAs,
        //autoExcAdj: autoExcAdjVal - Currently unused
    }

    //document.getElementById("loading").style.display = "block";
    appConfig.base.callAPI(
        "runScheduler",
        data,
        function(msg) {checkPendingSchedule(msg)},
        "POST",
        function(msg) {passModalSave("#runModal", {status:-1,msg:msg})}
    );
}

function schedulerMaxRetriesReached() {
    // The scheduler was not able to create a schedule in the allotted
    //  amount of time.

    return {
        status: 0,
        msg: "Due to a high amount traffic, we are unable to create your duty schedule at this time. " +
             "We have your request on record, and will get to it as soon as we are able. Please check again later."
    };
}

function schedulerEvalStatus(res) {
    // Evaluate whether or not the scheduler has completed. If it has
    //  (either successfully or unsuccessfully) finished, return true,
    //  otherwise return false.

    // The provided res is expected to have the following three attributes:
    //  status, msg, and sqid
    return res.status !== 0;
}

function schedulerUpdateDisplayStatus(res, retriesLeft, backoff) {
    // Determine whether or not to update the status message displayed
    //  to the user while they wait for the scheduler.

    // Determine what retry number we are currently on.
    let retryNumber = 7 - retriesLeft;

    // If we have retried a number of times already, then let's entertain the user while they wait.
    let msg = "";
    switch (retryNumber) {
        case 1:
            msg = "Queueing schedule request...";
            break;

        case 3:
            msg = "Creating duty schedule...";
            break;

        case 5:
            msg = "We are still working on your request-- thank you for your patience!";
            break;

    }

    // Only update the message the user sees if it has changed.
    if (msg !== "") {
        // Grab the modal
        let modal = document.getElementById("runModal");
        // Grab the user info div
        let infoDiv = modal.getElementsByClassName("modalUserInfo")[0];
        // Update the user info div with the message
        infoDiv.innerHTML = msg;
        // Display the errorDiv
        infoDiv.style.display = "block";
    }
}


function checkPendingSchedule(retMsg) {
    // Retrieve the status of the pending scheduler task with the provided SQID.
    // retMsg should have three attributes: status, msg, and sqid

    // Begin a fetch-retry loop that will reach out to checkSchedulerStatus API
    //  with an exponential backoff and a max of 10 retries.
    appConfig.base.fetchRetry(
        appConfig.base.assembleAPIURLString("checkSchedulerStatus") + "?" + new URLSearchParams({sqid: retMsg.sqid}),
        schedulerEvalStatus,
        schedulerMaxRetriesReached,
        schedulerUpdateDisplayStatus,
        {method:'GET'},
        7,      // Max number of retries
        1000    // Starting backoff in milliseconds
    ).then((res) => {
        // Pass in a an object indicating that the scheduling was successful regardless of
        //  what actually occurred. This is because the runScheduler modal does not handle
        //  messages from the scheduler queue.
        passModalSave("#runModal", {msg:"",status:1}, () => {
            document.getElementById("runButton").disabled = false;
            document.getElementById("runModalProgressBar").style.display = "none";

        });
    });

    // Add the resulting scheduler queue request information to the queue list
    addSchedReqItem(retMsg);
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
    let setFlag = document.getElementById("addFlag").checked;

    // id = "selector_xxxxxx"
    // There are 9 characters before the id
    let newId = parseInt(selRAOption.id.slice(9));

    let newParams = {
        id: newId,
        dateStr: dateVal,
        pts: ptVal,
        flag: setFlag
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

    appConfig.base.callAPI("getStats", params, updatePoints, "GET", null, "/staff");

}

function updatePoints(pointDict) {
    // PointDict is expected to be as follows:
    // { raId: {name: x, pts: { dutyPts: x, modPts: x}, ... }
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
            newPtsDiv.innerHTML = pointDict[idKey].pts.dutyPts;

            newLi.appendChild(newNameDiv);
            newLi.appendChild(newPtsDiv);
            raListDiv.getElementsByTagName("ul")[0].appendChild(newLi);

        } else {
            // Else update the point value
            ptDiv.innerHTML = pointDict[idKey].pts.dutyPts;
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

/*   Export to Google Calendar   */
function exportSchedule() {

    // Verify that the user would like to export.
    if (confirm("Export this schedule's current state to Google Calendar?")) {

        console.log("Exporting to Google Calendar");

        // Indicate to user that the export is running
        document.getElementById("exportBut").disabled = true;
        $("body").css("cursor", "wait");

        let params = {
            monthNum: appConfig.calDate.getMonth() + 1,
            year: appConfig.calDate.getFullYear()
        };

        appConfig.base.callAPI("exportToGCal",
            params,
            function(msg) {
                passModalSave("#exportModal", msg, () => {
                    document.getElementById("exportBut").disabled = false;
                    $("body").css("cursor", "auto");
                });
            }, "GET", function(msg) {passModalSave("#exportModal", msg)},
            "/int");
    }
}

function showExportModal() {
    // Make the exportModal visible to the user

    let title = document.getElementById("exportModalLongTitle");
    let sub = document.getElementById("exportModalMonth")

    title.textContent = appConfig.calDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    sub.textContent = appConfig.calDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    // Hide any errors from previous Export runs
    let modal = document.getElementById("exportModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    $('#exportModal').modal('show');
}

function getSchedulerQueueEntry(QueueID) {
    // Get additional information from the server for the given Queue ID

    // Call the appropriate API
    appConfig.base.callAPI("getSchedulerQueueItemInfo",
        {sqid:QueueID},
        function(data) {showSchedQueueModal(data)},
        "GET",
        console.err
    );
}

function showSchedQueueModal(info) {
    // set the schedQueueModal inputs to display the given values.

    // Manipulate the datetime for datetime-local inputs
    let tmp = new Date(info.requestDatetime);
    console.log(tmp);
    console.log(tmp.getMinutes())
    console.log(tmp.getTimezoneOffset());
    console.log(tmp.getMinutes() - tmp.getTimezoneOffset());

    tmp.setMinutes(tmp.getMinutes() - tmp.getTimezoneOffset());

    console.log(info.requestDatetime);
    console.log(tmp);

    // Set the Requested Date
    document.getElementById("schedQueueDate").value = tmp.toISOString().slice(0,16);

    // Set the Status
    let badgeStatusColor = "badge-";
    let badgeStatusText = "";

    switch (info.status) {
        case 0:
            // Status is still in progress
            badgeStatusColor += "secondary";
            badgeStatusText = "In Progress";
            break;

        case 1:
            // Status is successful
            badgeStatusColor += "success";
            badgeStatusText = "Success";
            break;

        case -3:
        case -2:
        case -1:
            // Status is failed
            badgeStatusColor += "danger";
            badgeStatusText = "Failed";
            break;

        case -99:
            // Status indicates record not found
            badgeStatusColor += "dark";
            badgeStatusText = "Not Found"
            break;

        default:
            // Default to a warning badge
            badgeStatusColor += "warning";
            badgeStatusText = "Unknown";
            break;
    }
    document.getElementById("schedQueueStatus").innerHTML = badgeStatusText;
    document.getElementById("schedQueueStatus").className = "badge " + badgeStatusColor;

    // Set the Requesting User
    document.getElementById("schedQueueRequestingUser").value = info.requestingRA;

    // Set the Additional Information/Reason
    document.getElementById("schedQueueReason").value = info.reason;

    // Set the modal title to include the SQID
    document.getElementById("schedReqID").innerHTML = info.sqid;

    $('#schedQueueModal').modal('show');
}

function addSchedReqItem(schedReqDict) {
    // Add the provided scheduler queue request to the list

    // Get the appropriate UL element
    let listUL = document.getElementById("queueListUL");

    // Create a new row
    let newLI = document.createElement("li");
    newLI.onclick = () => {getSchedulerQueueEntry(schedReqDict.sqid)};
    newLI.classList.add("clickable", "hoverItem");

    // Create a new Request div
    let newReqDiv = document.createElement("div");
    newReqDiv.id = "list_request_" + schedReqDict.sqid.toString();
    newReqDiv.classList.add("tName");
    newReqDiv.innerHTML = schedReqDict.created_date;

    // Create a new Status div
    let newStatusDiv = document.createElement("div");
    newStatusDiv.id = "list_status_" + schedReqDict.sqid.toString();
    newStatusDiv.classList.add("tPoints");
    let newStatusSpan = document.createElement("span");
    newStatusSpan.classList.add("badge", "badge-secondary");
    let statusText;
    switch (schedReqDict.status) {
        case -3:
        case -2:
            statusText = "Failed";
            break;
        case 0:
            statusText = "In Progress";
            break;
        case -1:
        case 1:
            statusText = "Success";
            break;
        default:
            statusText = "Unknown";
    }
    newStatusSpan.innerHTML = statusText;
    newStatusSpan.id = "list_status_span_" + schedReqDict.sqid.toString();
    newStatusDiv.appendChild(newStatusSpan);

    // Zip everything together
    newLI.appendChild(newReqDiv);
    newLI.appendChild(newStatusDiv);
    listUL.insertBefore(newLI, listUL.childNodes[2])

    // If there are more than 11 elements in the list,
    //  then remove the last node
    if (listUL.childNodes.length > 11) {
        listUL.removeChild(listUL.lastElementChild);
    }
}

function getSchedRequests() {
    appConfig.base.callAPI("getRecentSchedulerRequests", {}, updateSchedReqList, "GET");

}

function updateSchedReqList(schedReqDict) {
    // PointDict is expected to be as follows:
    // { sqid: {status: x, created_date: x}, ... }
    console.log(schedReqDict);

    let reqListDiv = document.getElementById("queueList");

    for (let idKey in schedReqDict) {
        // Get the Div containing the points for the respective RA
        let statusDiv = document.getElementById("list_status_" + idKey);

        let statusText;
        let statusClass;
        switch (schedReqDict[idKey].status) {
            case -3:
            case -2:
            case -1:
                statusText = "Failed";
                statusClass = "badge-danger";
                break;
            case 0:
                statusText = "In Progress";
                statusClass = "badge-secondary";
                break;
            case 1:
                statusText = "Success";
                statusClass = "badge-success";
                break;
            default:
            statusText = "Unknown";
            statusClass = "badge-warning";
        }

        let newStatusSpan = document.createElement("span");
        newStatusSpan.classList.add("badge", statusClass);
        newStatusSpan.innerHTML = statusText;

        if (statusDiv == null) {
            // If the RA is not currently in the raList
            //  then create a new entry for them.

            let newLi = document.createElement("li");
            newLi.id = "schedReqList_" + idKey;

            let newDateDiv = document.createElement("div");
            newDateDiv.id = "list_request_" + idKey;
            newDateDiv.classList.add("tName");
            newDateDiv.innerHTML = schedReqDict[idKey].created_date;

            let newStatusDiv = document.createElement("div");
            newStatusDiv.id = "list_status_" + idKey;
            newStatusDiv.classList.add("tPoints");
            newStatusDiv.appendChild(newStatusSpan);

            newLi.appendChild(newNameDiv);
            newLi.appendChild(newStatusDiv);
            let ulElement = reqListDiv.getElementsByTagName("ul")[0];
            ulElement.insertBefore(newLi, ulElement.ChildNodes[2]);

        } else {
            // Else update the point value
            statusDiv.replaceChild(newStatusSpan, statusDiv.lastElementChild);
        }
    }
}