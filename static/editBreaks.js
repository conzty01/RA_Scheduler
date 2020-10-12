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
            url: '/api/getBreakDuties',
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
    selector.value = info.event.backgroundColor;

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
