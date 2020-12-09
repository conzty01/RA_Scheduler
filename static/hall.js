"use strict"

function showEditModal(id) {
    // Set the values of the form.

    // Get the information from the row
    let tr = document.getElementById(id);
    let setName = tr.getElementsByClassName("settingName")[0].innerHTML;
    let setDesc = tr.getElementsByClassName("settingDescription")[0].innerHTML;
    let setVal = tr.getElementsByClassName("settingValue")[0].innerHTML;

    // Get the valRow and remove its previous elements.
    let valRow = document.getElementById("valRow");

    // Delete the previous child node from valRow
    valRow.innerHTML = "";

    // Check to see if there any special settings that we should handle
    let valDiv;
    if (setName === "Google Calendar Integration") {
        valDiv = generateGoogleRow( setVal === "Connected" );
        // Hide the Save button as it is not necessary
        document.getElementById("savBut").style.display = "none";

    } else {
        // Otherwise generate a "standard" input valDiv
        valDiv = generateInputRow(setVal, "text");

        // Make sure the Save Button is displayed
        document.getElementById("savBut").style.display = "block";

    }

    // Set the values in the form.
    document.getElementById("modalTitle").innerHTML = setName;
    document.getElementById("modalSettingDescription").innerHTML = setDesc;

    // Add the new valDiv to the valRow
    valRow.appendChild(valDiv);

    // Display the modal
    $('#editSettingModal').modal('toggle');
}

function generateInputRow(value, type) {
    // Generate a valDiv that contains an input field with the appropriate value.

    // Create the necessary elements
    let valDiv = document.createElement("div");
    let label = document.createElement("label");
    let input = document.createElement("input");

    // Set the attributes of the valDiv element
    valDiv.setAttribute("id", "valDiv");
    valDiv.setAttribute("class", "col");

    // Set the attributes of the label element
    label.setAttribute("for", "modalSettingValue");
    label.innerHTML = "Value:";

    // Set the attributes of the input element
    input.setAttribute("class", "form-control");
    input.setAttribute("type", type);
    input.setAttribute("id", "modalSettingValue");
    input.setAttribute("value", value);

    // Connect all of the elements together
    valDiv.appendChild(label);
    valDiv.appendChild(input);

    // Return the newly created valDiv
    return valDiv
}

function generateGoogleRow(alreadyConnected) {
    // Generate the Google Integration valDiv

    // Create the necessary elements
    let valDiv = document.createElement("div");
    let connectButton = document.createElement("button");
    let disconnButton = document.createElement("button");

    // If an account/partial account has not already been connected
    if (alreadyConnected) {
        // Set the Disconnect Attributes
        disconnButton.innerHTML = "Disconnect Account";
        disconnButton.setAttribute("type", "button");
        disconnButton.setAttribute("class", "btn btn-danger");
        disconnButton.setAttribute("onclick", "location.href='../int/disconnectGCal'");

        // Add the disconnect button to the div
        valDiv.appendChild(disconnButton);
    }

    // Set the Connect/Reconnect Attributes
    connectButton.setAttribute("type", "button");
    connectButton.setAttribute("class", "btn btn-primary");
    connectButton.setAttribute("onclick", "location.href='../int/GCalRedirect'");
    connectButton.innerHTML = alreadyConnected ? "Reconnect Account" : "Connect Account";

    // Assemble the valDiv
    valDiv.appendChild(connectButton);

    // Return the newly generated valDiv
    return valDiv
}

function submitChanges() {
    // Submit the Hall Setting changes to be saved.

    let setName = document.getElementById("modalTitle").innerHTML;
    let setVal = document.getElementById("modalSettingValue").value;

    // Indicate to user that the setting is being saved
    document.getElementById("savBut").disabled = true;
    $("body").css("cursor", "wait");

    // Set the parameters for the API
    let params = {
        "name": setName,
        "value": setVal
    }

    console.log(params);

    // Call the API
    appConfig.base.callAPI("saveHallSettings",
            params,
            function(msg) {
                passModalSave("#editSettingModal", msg, () => {
                    // Re-enable the save button
                    document.getElementById("savBut").disabled = false;
                    $("body").css("cursor", "auto");
                    // Get the latest setting information
                    getSettingInfo();

                });
            }, "POST", function(msg) {passModalSave("#editSettingModal", msg)});
}

function passModalSave(modalId, msg, extraWork=() => {}) {

    //console.log(msg);

    let modal = document.getElementById(modalId.slice(1));

    // If the status is '1', then the save was successful
    switch (msg.status) {
        case 1:
            // If the status is '1', then the save was successful

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

            // Complete any additional work
            extraWork();

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

function getSettingInfo() {
    console.log("Refreshing Setting List");

    appConfig.base.callAPI("getHallSettings",{},
                             (data) => {
                                reDrawTable(data);
                             },"GET");
}

function reDrawTable(settingList) {
    // data = [ {settingName: "", settingDesc: "", settingVal: ""}, {...}, ...],

    console.log("Redrawing Setting Table");

    let table = document.getElementById("settingTable");
    let oldTBody = table.getElementsByTagName("tbody")[0];

    let newTBody = document.createElement("tbody");

    let i = 0;
    for (let setting of settingList) {

        // Add the row to the table
        addRow(setting, i, newTBody);

        // Increment the counter
        i++;
    }

    table.replaceChild(newTBody, oldTBody);
}

function addRow(data, rowId, table) {
    let newRow = table.insertRow(-1);
    newRow.id = rowId;
    newRow.setAttribute("scope","row");

    let col;

    // Add SettingName
    col = newRow.insertCell(0);
    col.className = "settingName";
    col.innerHTML = data["settingName"];

    // Add SettingDescription
    col = newRow.insertCell(1);
    col.className = "settingDescription";
    col.innerHTML = data["settingDesc"];

    // Add SettingValue
    col = newRow.insertCell(2);
    col.className = "settingValue";
    col.innerHTML = data["settingVal"];

    // Add Edit column
    let edit = newRow.insertCell(3);
    let editSpan = document.createElement("span");

    editSpan.className = "fa fa-pencil";
    editSpan.setAttribute("onclick","showEditModal("+rowId.toString()+")");
    edit.appendChild(editSpan);

}