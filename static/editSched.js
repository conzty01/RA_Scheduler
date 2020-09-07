"use strict"

var editCal = {};

function updatePoints(pointDict) {
    console.log(pointDict);

    for (let idKey in pointDict) {
        let ptDiv = document.getElementById("list_points_"+idKey);
        ptDiv.innerHTML = pointDict[idKey];
    }
}

function tallyPoints() {
    let sels = document.getElementsByTagName("select");
    let resDict = {};
    for (let i of sels) {
        let raName = i.value;
        if (raName in resDict) {
            resDict[raName] += parseInt(i.parentNode.parentNode.dataset.points);
        } else {
            resDict[raName] = parseInt(i.parentNode.parentNode.dataset.points);
        }
    }
    for (let raKey in resDict) {
        let i = editCal[raKey];
        let ptsDiv = document.getElementById("list_points_"+i);
        ptsDiv.innerHTML = resDict[raKey];
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
