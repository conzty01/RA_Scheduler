"use strict"

function editStaff(id) {
    let row = document.getElementById(id);

    for (let node of row.children) {
        if (node.className != "raID" && node.className != "edit" &&
                node.className != "del" && node.className != "resHall") {

            let input = document.createElement("input");
            input.type = "text";

            let tmp = node.innerHTML;
            input.value = tmp;
            node.innerHTML = "";

            node.appendChild(input);
        }
    }

    let checkmark = document.createElement("span");
    checkmark.className = "glyphicon glyphicon-ok";
    checkmark.setAttribute("onclick","submitChanges("+id.toString()+")");

    let editTD = row.getElementsByClassName("edit")[0];
    editTD.removeChild(editTD.childNodes[0]);
    editTD.appendChild(checkmark);
}

function submitChanges(id) {
    let row = document.getElementById(id);
    let data = {};

    for (let col of row.children) {
        //console.log(col);
        // columns with inputs
        if (col.className != "edit" && col.className != "del") {
            data[col.className] = col.childNodes[0].value;
        }
    }

    data["raID"] = row.children[0].innerHTML;

    appConfig.base.callAPI("changeStaffInfo",data,resetRow,"POST");
}

function resetRow(id) {
    let row = document.getElementById(id);

    for (let col of row.children) {
        if (col.className == "edit") {
            let pencil = document.createElement("span");
            pencil.className = "glyphicon glyphicon-pencil";
            pencil.setAttribute("onclick","editStaff("+id.toString()+")");

            let editTD = row.getElementsByClassName("edit")[0];
            editTD.removeChild(editTD.childNodes[0]);
            editTD.appendChild(pencil);

        } else if (col.children.length != 0 && col.className != "del") {
            let tmp = col.children[0].value;

            col.removeChild(col.children[0]);
            col.innerHTML = tmp;
        }
    }
}

function delStaff(id) {
    appConfig.base.callAPI("removeStaffer",id,function(i) {
        let row = document.getElementById(i);
        row.parentNode.removeChild(row);
    },"POST");
}

function addStaff() {

}
