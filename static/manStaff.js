"use strict"

function editStaff(id) {
    let row = document.getElementById(id);

    for (let node of row.children) {
        if (node.className != "raID" && node.className != "edit" &&
                node.className != "del" && node.className != "resHall") {

            let input = document.createElement("input");

            switch (node.className) {
                case "color":
                    input.type = "color";

                    let tm = node.value;
                    input.value = tm;
                    node.innerHTML = "";
                    break;

                case "email":
                    input.type = "email";

                    let tmp = node.innerHTML;
                    input.value = tmp;
                    node.innerHTML = "";
                    break;

                case "authLevel":
                    input = document.createElement("select");

                    for (let opt of document.getElementById("authLevelOpts").options) {
                        let o = document.createElement("option");

                        o.value = opt.value;
                        o.innerHTML = opt.innerHTML;

                        if (o.innerHTML == node.innerHTML) {
                            o.selected = true;
                        }

                        input.add(o);
                    }
                    node.innerHTML = "";
                    break;

                default:
                    input.type = "text";

                    let t = node.innerHTML;
                    input.value = t;
                    node.innerHTML = "";
            }

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

function addRow(data) {
    console.log(data);
    let tab = document.getElementsByTagName("table")[0];
    let newRow = tab.insertRow(1);
    newRow.id = data[0];
    newRow.setAttribute("scope","row");

    let col;
    let i = 0;
    for (let d of ["raID","fName","lName","email","startDate","resHall","points","color","authLevel"]) {
        col = newRow.insertCell(i);
        col.className = d;

        if (d == "startDate") {
            let tmp = new Date(data[i]);
            col.innerHTML = tmp.getFullYear().toString()+"-"+(tmp.getMonth()+1).toString()+"-"+tmp.getDate().toString();
        } else {
            col.innerHTML = data[i];
        }
        i++;
    }

    let edit = newRow.insertCell(i);
    let editSpan = document.createElement("span");

    editSpan.className = "glyphicon glyphicon-pencil";
    editSpan.setAttribute("onclick","editStaff("+data[0].toString()+")");
    edit.appendChild(editSpan);

    let del = newRow.insertCell(i+1);
    let delSpan = document.createElement("span");

    delSpan.className = "glyphicon glyphicon-remove";
    delSpan.setAttribute("onclick","delStaff("+data[0].toString()+")");
    del.appendChild(delSpan);

}

function delStaff(id) {
    appConfig.base.callAPI("removeStaffer",id,function(i) {
        let row = document.getElementById(i);
        row.parentNode.removeChild(row);
    },"POST");
}

function addStaff() {
    let row = document.getElementById("addRow");
    let data = {
        "fName": row.children[0].children[0].value,
        "lName": row.children[1].children[0].value,
        "email": row.children[2].children[0].value,
        "color": row.children[3].children[0].value,
        "authLevel": row.children[4].children[0].value
    }

    appConfig.base.callAPI("addStaffer",data,addRow,"POST");
}
