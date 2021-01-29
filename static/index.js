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
        fixedWeekCount: false
    });
}

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
