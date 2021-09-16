"use strict"

///////////////////////////////////////////
/*   Functions for the index.html page   */
///////////////////////////////////////////

function initIndexCal() {
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
            }
        },
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: ''
        },
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
                        allColors: 0
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
                        allColors: 0
                    };
                },
            }
        ],
        lazyFetching: true,
        fixedWeekCount: false,
        eventOrder: "flagged, title"
    });
}

function displayFlaggedDuties(event) {
    // Alter any duties that are flagged so that
    //  they appear visually different from the
    //  non-flagged duties.

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

var selectedTrade_traderName;
var selectedTrade_date;
var selectedTrade_ID;
var selectedTrade_specUser;
var tradeDutyFormatOptions = {weekday:'short', year:'numeric', month:'short', day:'numeric'};

function getDutyTradeInfo(tradeID, traderName, date, tradeSpecUser) {
    // Grab the necessary information from the server

    // Set global information for the selected duty trade request
    selectedTrade_traderName = traderName;
    selectedTrade_date = date;
    selectedTrade_ID = tradeID;
    selectedTrade_specUser = tradeSpecUser;

    // Call the appropriate API
    appConfig.base.callAPI(
        "getAddTradeInfo",
        {tradeReqID: tradeID},
        showAppropriateModal,
        "GET",
        console.err,
        "/schedule"
    );
}

function showAppropriateModal(tradeInfo) {
    // Show the appropriate trade duty modal to the user depending
    //  on whether or not the trade is with a specific user.

    if (selectedTrade_specUser) {
        showDutyExchangeModal(tradeInfo);
    } else {
        showAcceptDutyModal(tradeInfo);
    }
}

function showDutyExchangeModal(tradeInfo) {
    // Show the selected Duty Exchange Request to the user.

    console.log(tradeInfo);
    console.log(selectedTrade_traderName);
    console.log(selectedTrade_date);
    console.log(selectedTrade_ID);
    console.log(selectedTrade_specUser);

    // Update the modal's fields to appropriate values based on the
    //  provided tradeInfo.
    document.getElementById("tradeDutyTraderName").innerHTML = selectedTrade_traderName;
    document.getElementById("tradeDutyDate").value = selectedTrade_date.toLocaleDateString("en-us", tradeDutyFormatOptions);
    document.getElementById("tradeDutyDateFlag").checked = tradeInfo.trDuty.flagged;
    document.getElementById("trFlaggedDutyLabel").innerHTML = tradeInfo.trDuty.label;
    document.getElementById("tradeDutyReason").value = tradeInfo.tradeReason;

    document.getElementById("exchangeDutyDate").value = new Date(tradeInfo.exDuty.date).toLocaleDateString("en-us", tradeDutyFormatOptions);
    document.getElementById("exchangeDutyDateFlag"). checked = tradeInfo.exDuty.flagged;
    document.getElementById("exFlaggedDutyLabel").innerHTML = tradeInfo.trDuty.label;

    document.getElementById("textExchangeDutyDate").innerHTML = new Date(tradeInfo.exDuty.date).toLocaleDateString();
    document.getElementById("textTradeDutyDate").innerHTML = selectedTrade_date.toLocaleDateString();

    document.getElementById("tradeDutyButt").onclick = () => {acceptTrade(selectedTrade_ID)};

    // Hide any errors from previous event clicks
    let modal = document.getElementById("exchangeDutyModal");
    let errDiv = modal.getElementsByClassName("modalError")[0];
    errDiv.style.display = "none";

    // Show the modal to the user
    $('#exchangeDutyModal').modal('show');
}

function acceptTrade(tradeID) {
    // Make a call to the appropriate API endpoint to accept the
    //  selected trade request.

    // Call the appropriate API
    appConfig.base.callAPI(
        "acceptTradeRequest",
        {tradeReqID: tradeID},
        (msg) => {modal_handleAPIResponse("#exchangeDutyModal", msg)},
        "POST",
        console.err,
        "/schedule"
    );

}

function rejectTrade(tradeID) {
    // Prompt the user to enter a rejection reason and call
    //  the appropriate API endpoint to reject the trade request.
    let rejectReason = prompt("Please enter a reason for rejecting the request.");

    // Call the appropriate API
    appConfig.base.callAPI(
        "rejectTradeRequest",
        {tradeReqID: tradeID, reason: rejectReason},
        (msg) => {modal_handleAPIResponse("#exchangeDutyModal", msg)},
        "POST",
        console.err,
        "/schedule"
    );
}

function modal_handleAPIResponse(modalId, msg, extraWork=() => {}) {

    //console.log(msg);

    let modal = document.getElementById(modalId.slice(1));

    // If the status is '1', then the save was successful
    switch (msg.status) {
        case 1:
            // If the status is '1', then the save was successful

            // Refetch the current month's calendar
            calendar.currentData.calendarApi.refetchEvents();
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