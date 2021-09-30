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
        eventOrder: "flagged, title",
        eventClick: eventClicked
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

    let formattedDateStr = tmp.start.replaceAll("-", "/");

    // If the event date is before the current date
    if (new Date(formattedDateStr) >= appConfig.curDate) {
        // Add a css class to the event
        tmp.classNames = ["clickable"];
    }

    // Check to see if this event has been flagged
    if (tmp.extendedProps.flagged) {
       tmp.display = "list-item";
    }

    // Return the transformed event object
    return tmp;
}

function eventClicked(info) {
    // Function to be called when an event on the calendar is clicked.

    console.log(info);
    console.log(info.event.extendedProps.isUser);

    // If the event that was clicked is a duty that has already happened
    if (info.event.start < appConfig.curDate) {
        // These duties cannot be traded.
        return;
    }

    // If the event that was clicked is assigned to the user...
    if (info.event.extendedProps.isUser == 1) {
        // then call an API to get a list of staff members to trade with
        appConfig.base.callAPI(
            "getStats",
            {start:"", end:""},
            showYourTradeDutyModal,
            "GET",
            console.err,
            "/staff"
        )

    } else {
        // Otherwise, call an API to get a list of the user's duties to trade with.
        appConfig.base.callAPI(
            "getStafferDuties",
            {start:"", end:""},
            showOtherTradeDutyModal,
            "GET",
            console.err,
            "/staff"
        )
    }

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
        showDutyExchangeModal,
        "GET",
        console.err,
        "/schedule"
    );
}

function showDutyExchangeModal(tradeInfo) {
    // Show the selected Duty Exchange Request to the user.

    console.log(tradeInfo);
    console.log(selectedTrade_traderName);
    console.log(selectedTrade_date);
    console.log(selectedTrade_ID);
    console.log(selectedTrade_specUser);

    let textForTrade;

    // Update the modal's Trade Duty Fields as appropriate
    document.getElementById("tradeDutyTraderName").innerHTML = selectedTrade_traderName;
    document.getElementById("tradeDutyDate").value = selectedTrade_date.toLocaleDateString("en-us", tradeDutyFormatOptions);
    document.getElementById("tradeDutyDateFlag").checked = tradeInfo.trDuty.flagged;
    document.getElementById("trFlaggedDutyLabel").innerHTML = tradeInfo.trDuty.label;
    document.getElementById("tradeDutyReason").value = tradeInfo.tradeReason;
    document.getElementById("exFlaggedDutyLabel").innerHTML = tradeInfo.trDuty.label;

    // If the trade request is for a specific user...
    if (selectedTrade_specUser) {
        // Then format the textForTrade appropriately
        textForTrade = `
            <i>By accepting this trade, you will no longer be assigned for duty on
            <b><span id="textExchangeDutyDate">${new Date(tradeInfo.exDuty.date).toLocaleDateString()}</span></b> and will instead be
            assigned for duty on <b><span id="textTradeDutyDate">${selectedTrade_date.toLocaleDateString()}</span></b>.</i>
        `
        // Show the reject button
        document.getElementById("rejectDutyButt").hidden = false;
        // White-out the the exchangeDutyDate
        document.getElementById("exchangeDutyDate").removeAttribute("disabled");
        document.getElementById("exchangeDutyDate").setAttribute("readonly", true);

        // Update the Exchange Duty Information
        document.getElementById("exchangeDutyDate").value = new Date(tradeInfo.exDuty.date).toLocaleDateString("en-us", tradeDutyFormatOptions);
        document.getElementById("exchangeDutyDateFlag").checked = tradeInfo.exDuty.flagged;

    } else {
        // Otherwise format the textForTrade appropriately
        textForTrade = `
            <i>By accepting this trade, you will be assigned for duty on
            <b><span id="textTradeDutyDate">${selectedTrade_date.toLocaleDateString()}</span></b>.</i>
        `
        // Hide the reject button
        document.getElementById("rejectDutyButt").hidden = false;
        // Grey-out the the exchangeDutyDate
        document.getElementById("exchangeDutyDate").setAttribute("disabled", true);
        document.getElementById("exchangeDutyDate").removeAttribute("readonly");

        // Remove the Exchange Duty Information
        document.getElementById("exchangeDutyDate").value = '';
        document.getElementById("exchangeDutyDateFlag").checked = false;
    }


    //document.getElementById("textExchangeDutyDate").innerHTML = new Date(tradeInfo.exDuty.date).toLocaleDateString();
    //document.getElementById("textTradeDutyDate").innerHTML = selectedTrade_date.toLocaleDateString();

    document.getElementById("textForTrade").innerHTML = textForTrade;

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
        (msg) => {modal_handleAPIResponse("#exchangeDutyModal", msg, getDutyTradeRequests)},
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
        (msg) => {modal_handleAPIResponse("#exchangeDutyModal", msg, getDutyTradeRequests)},
        "POST",
        console.err,
        "/schedule"
    );
}

function getDutyTradeRequests() {
    // Call the appropriate API to get the duty trade requests for the user.

    // Call the appropriate API
    appConfig.base.callAPI(
        "getTradeRequestsForUser",
        {},
        redrawTradeRequests,
        "GET",
        console.err,
        "/schedule"
    );
}

function redrawTradeRequests(data) {
    // Redraw the section of the UI with Duty Trade Requests

    console.log("Redrawing Duty Trade Requests Section");

    // Grab the Duty Trade Request Container
    let dtrCont = document.getElementById("dutySwitchContainer");
    let oldPDTCont = document.getElementById("pendingDutyTrades");

    // Create a new pendingDutyTrades container
    let newPDTCont = document.createElement("div");
    newPDTCont.setAttribute("id", "pendingDutyTrades");
    newPDTCont.classList.add("tradeList");
    dtrCont.replaceChild(newPDTCont, oldPDTCont);

    // If there are any pending duty requests..
    if (data.length > 0) {
        console.log(data.length + " Pending Trades Found");

        // Parse through them
        let newCardDiv;
        let newCardDiv_onClick;
        let newCardDiv_header;
        let newCardDiv_body;
        let newCardDiv_bodyText;
        let newCardDiv_date;

        // Iterate over the data and create cards for each Duty Trade Request
        for (let tradeReq of data) {
            // Expected data format:
            // {
            //    "id": xx,
            //    "traderName": xx xx,
            //    "tradeWithSpecificUser": true/false,
            //    "date": xx
            // }

            // Create a date object for the current trade request
            newCardDiv_date = new Date(tradeReq.date);

            // Create the new card's onclick function
            newCardDiv_onClick = "getDutyTradeInfo(" + tradeReq.id + ",'"+ tradeReq.traderName + "'," +
                                 "new Date('" + tradeReq.date + "')," + tradeReq.tradeWithSpecificUser + ")";

            // Create the new card
            newCardDiv = document.createElement("div");
            newCardDiv.classList.add("card");
            newCardDiv.setAttribute("onclick", newCardDiv_onClick);
            //setAttribute("onClick", newCardDiv_onClick);

            // Create the card's header
            newCardDiv_header = document.createElement("p");
            newCardDiv_header.classList.add("card-header");
            newCardDiv_header.innerHTML = newCardDiv_date.toLocaleDateString();
            newCardDiv.appendChild(newCardDiv_header);

            // Create the card's body
            newCardDiv_body = document.createElement("div");
            newCardDiv_body.classList.add("card-body");
            newCardDiv.appendChild(newCardDiv_body);

            // Create the card's body text
            newCardDiv_bodyText = document.createElement("p");
            newCardDiv_bodyText.classList.add("card-text");
            newCardDiv_bodyText.innerHTML = "<b>" + tradeReq.traderName + "</b> is seeking to trade duties with <b>" +
                                            (tradeReq.tradeWithSpecificUser ? 'you' : 'anyone') + "</b>."
            newCardDiv_body.appendChild(newCardDiv_bodyText);

            // Add the new card to the new pendingDutyTrades container
            newPDTCont.appendChild(newCardDiv);
        }
    } else {
        console.log("No Pending Trades Found");

        // Otherwise just add an empty message
        let noRequests = document.createElement("p");
        noRequests.classList.add("noPendingTrades");
        noRequests.innerHTML = "*No Pending Trade Requests*";
        newPDTCont.appendChild(noRequests);
    }


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