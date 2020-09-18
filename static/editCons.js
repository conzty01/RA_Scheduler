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
            url: '/api/getStaffConflicts',
            failure: function () {
                alert('there was an error while fetching events!');
            },
            extraParams: function () {
                return {
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
