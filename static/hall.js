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

    } else {
        // Otherwise generate a "standard" input valDiv
        valDiv = generateInputRow(setVal, "text");

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
    if (!(alreadyConnected)) {
        // Disable the Disconnect button
        disconnButton.setAttribute("disabled", true)
    }

    // Set the Disconnect Attributes
    disconnButton.innerHTML = "Disconnect Account";
    disconnButton.setAttribute("type", "button");
    disconnButton.setAttribute("class", "btn btn-danger");
    disconnButton.setAttribute("onclick", "location.href='../int/disconnectGCal'");

    // Set the Connect/Reconnect Attributes
    connectButton.setAttribute("type", "button");
    connectButton.setAttribute("class", "btn btn-primary");
    connectButton.setAttribute("onclick", "location.href='../int/GCalRedirect'");
    connectButton.innerHTML = alreadyConnected ? "Reconnect Account" : "Connect Account";

    // Assemble the valDiv
    valDiv.appendChild(disconnButton);
    valDiv.appendChild(connectButton);

    // Return the newly generated valDiv
    return valDiv
}

function submitChanges() {
    console.log("SUBMIT CHANGES");
}