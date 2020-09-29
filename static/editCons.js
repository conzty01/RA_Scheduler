"use strict"

///////////////////////////////////////////
/* Functions for the editCons.html page */
///////////////////////////////////////////

function initEditConsCal() {
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
        dateClick: '',
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: ''
        },
        events: {
            url: '/api/getRAConflicts',
            failure: function () {
                alert('there was an error while fetching events!');
            },
            extraParams: function () {
                return {
                    monthNum: appConfig.calDate.getMonth() + 1,
                    year: appConfig.calDate.getFullYear(),
                    raID: getSelectedRAID(),
                    allColors: true
                };
            }
        },
        lazyFetching: true,
        showNonCurrentDates: false,
        fixedWeekCount: false,
        eventClick: '',
        dayMaxEventRows: 2
    });
}

function getSelectedRAID() {

    let i;

    // Check if an RA has been selected
    if (selectedRAli === undefined) {
        i = -1

    } else {
        i = selectedRAli.id.slice(5)
    }

    return parseInt(i)
}

function filterConflicts(id) {
    let tmp = document.getElementById("list_"+id);

    // If the user selected a new RA
    if (selectedRAli !== tmp) {
        selectedRAli = document.getElementById("list_"+id);

    } else {
        // Otherwise undefine the selectedRAli
        selectedRAli = undefined;
    }

    // refetch events
    calendar.currentData.calendarApi.refetchEvents();
}

var selectedRAli;
