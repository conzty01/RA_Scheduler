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
                click: movePrevCons
            },
            customNextButton: {
                text: '>',
                click: moveNextCons
            },
            customTodayButton: {
                text: 'Today',
                click: moveTodayCons
            }
        },
        dateClick: '',
        headerToolbar: {
            left: 'customPrevButton,customNextButton customTodayButton',
            center: 'title',
            right: ''
        },
        events: {
            url: '/conflicts/api/getRAConflicts',
            failure: function () {
                alert('there was an error while fetching events!');
            },
            extraParams: function () {
                return {
                    raID: getSelectedRAID(),
                    allColors: true
                };
            }
        },
        lazyFetching: true,
        showNonCurrentDates: false,
        fixedWeekCount: false,
        //eventClick: clickedConflict,
        dayMaxEventRows: 2
    });
}

function moveNextCons() {
    console.log("Change Month: Next");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() + 1);
    console.log(appConfig.calDate);

    // Get the number of conflicts
    getNumberConflicts();
    // Get the conflicts
    calendar.currentData.calendarApi.next();
}

function movePrevCons() {
    console.log("Change Month: Prev");

    appConfig.calDate.setMonth(appConfig.calDate.getMonth() - 1);
    console.log(appConfig.calDate);

    // Get the number of conflicts
    getNumberConflicts();
    // Get the conflicts
    calendar.currentData.calendarApi.prev();
}

function moveTodayCons() {
    console.log("Change Month: Today");

    appConfig.calDate.setMonth(appConfig.curDate.getMonth());
    appConfig.calDate.setFullYear(appConfig.curDate.getFullYear());

    // Get the number of conflicts
    getNumberConflicts();
    // Get the conflicts
    calendar.currentData.calendarApi.today();
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

// function clickedConflict(obj) {
//     console.log(obj);
// }

function filterConflicts(id) {
    let tmp = document.getElementById("list_"+id);

    // If the user selected a new RA
    if (selectedRAli !== tmp) {
        selectedRAli = document.getElementById("list_"+id);

        // Iterate through all the <li> elements and remove
        //  any highlighting
        for (let li of document.getElementById("raList").children[0].children) {
            li.classList.remove("filterRA");
        }

        // Lastly, highlight just the we want.
        tmp.classList.add("filterRA");


    } else {
        // Otherwise undefine the selectedRAli
        selectedRAli = undefined;

        // Remove highlighting to the <li> element.
        tmp.classList.remove("filterRA");
    }

    // refetch events
    calendar.currentData.calendarApi.refetchEvents();


}

function getNumberConflicts() {

    // Fetch the conflict count for each RA for the currently viewed month.
    let params = {
        monthNum: appConfig.calDate.getMonth() + 1,
        year: appConfig.calDate.getFullYear(),
    }
    appConfig.base.callAPI("getConflictNums", params, setConflictNumbers, "GET");

}

function setConflictNumbers(results) {
    console.log("Redrawing Conflict Numbers");
    //console.log(results);

    let curRow;
    for (let key of Object.keys(results)) {
        //console.log("list_points_"+key);
        curRow = document.getElementById("list_points_"+key);
        curRow.innerHTML = results[key];
    }

}

var selectedRAli;
