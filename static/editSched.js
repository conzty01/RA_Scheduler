"use strict"

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
            newNameDiv.id = "list_points_" + idKey;
            newNameDiv.classList.add("tPoints");
            newNameDiv.innerHTML = pointDict[idKey].pts;

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
