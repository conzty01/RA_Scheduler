"use strict"

function showEditModal(id) {
    // Set the values of the form.

    // Get the information from the row
    let tr = document.getElementById(id);
    let setName = tr.getElementsByClassName("settingName")[0].innerHTML;
    let setDesc = tr.getElementsByClassName("settingDescription")[0].innerHTML;
    let setVal = tr.getElementsByClassName("settingValue")[0].innerHTML;
    let setData = tr.getElementsByClassName("settingData")[0].innerHTML;

    // Get the valRow and remove its previous elements.
    let valRow = document.getElementById("valRow");

    // Delete the previous child node from valRow
    valRow.innerHTML = "";

    // Check to see if there any special settings that we should handle
    let divCollection = [];
    let initSelect = false;
    switch(setName) {
        case "Google Calendar Integration":
            // Create the necessary buttons for the Google Calendar Integration

            let googDiv = generateGoogleRow( setVal === "Connected" );

            // Hide the Save button as it is not necessary
            document.getElementById("savBut").style.display = "none";

            // Add the div to the divCollection
            divCollection.push(googDiv);
            break;

        case "Duty Configuration":
            // Create the necessary input rows for the Duty Configuration settings

            // Parse the json from the data
            let d = JSON.parse(setData.replaceAll("'", '"'));

            // Create the form-row for the <select> element

            // Create the Days of the week for the select
            let dsow = [];
            let i = 0;
            for (let dow of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]) {
                dsow.push({
                    value: i,
                    text: dow,
                    selected: d.multi_duty_days.includes(i)
                });
                i++;
            }

            // Create the <select> for the multi-duty day setting
            let sel = generateSelectRow("Weekly Multi-Duty Days", dsow, "mddSelect", true);

            // Add the <select> div to the divCollection
            divCollection.push(sel);

            // Create the duty config fields for regular duties, multi-duties, and break duties
            let numOnDuty;
            let numPts;

            // Create an array of objects containing their respective information.
            //  This will simplify the coming for of loop.
            let iterArray = [
                {
                    name: "Regular Duty Days",
                    pts: d.reg_duty_pts,
                    num: d.reg_duty_num_assigned
                },
                {
                    name: "Multi-Duty Days",
                    pts: d.multi_duty_pts,
                    num: d.multi_duty_num_assigned
                },
                {
                    name: "Break Duty Days",
                    pts: d.brk_duty_pts,
                    num: d.brk_duty_num_assigned
                }
            ]

            // Iterate over our iterArray
            i = 0;
            for (let c of iterArray) {
                // Create the Number On Duty Field with the label for the row
                numOnDuty = generateInputRow(
                    c.num,
                    "number",
                    c.name,
                    "col-sm-6",
                    "Number of RAs on Duty",
                    "dutyConfigNum".concat("-", i)
                )

                // Add the No. on Duty div to the divCollection
                divCollection.push(numOnDuty);

                // Create the Number Points Awarded field for the regular duties
                numPts = generateInputRow(
                    c.pts,
                    "number",
                    "&nbsp;",
                    "col-sm-6",
                    "Number of Points Awarded",
                    "dutyConfigPts".concat("-", i)
                )

                // Add the Pts Awarded div to the divCollection
                divCollection.push(numPts);

                // Increment our counter
                i++;
            }

            // Make sure the Save Button is displayed
            document.getElementById("savBut").style.display = "block";

            // Set the onclick function of the save button
            document.getElementById("savBut").onclick = saveDutyConfig;

            // Set the flag so that we initialize the selectpicker
            initSelect = true;

            break;

        case "Defined School Year":
            // Create the necessary input rows for the School Year settings

            // Parse the json from the data
            let da = JSON.parse(setData.replaceAll("'", '"'));

            // Create the Months for the start select
            let monthNames = ["January", "February", "March", "April", "May", "June", "July",
                              "August", "September", "October", "November", "December"];
            let startMonths = [];
            let index = 1;
            for (let m of monthNames) {
                startMonths.push({
                    value: index,
                    text: m,
                    selected: da.start == index
                });
                index++;
            }

            // Create the Months for the end select
            let endMonths = [];
            index = 1;
            for (let m of monthNames) {
                endMonths.push({
                    value: index,
                    text: m,
                    selected: da.end == index
                });
                index++;
            }

            // Create the <select> for the multi-duty day setting
            let sele = generateSelectRow("Start Month", startMonths, "start", false, "col-sm-6");

            // Add the <select> div to the divCollection
            divCollection.push(sele);

            // Create the <select> for the multi-duty day setting
            sele = generateSelectRow("End Month", endMonths, "end", false, "col-sm-6");

            // Add the <select> div to the divCollection
            divCollection.push(sele);

            // Set the initSelect flag to true
            initSelect = true;

            // Make sure the Save Button is displayed
            document.getElementById("savBut").style.display = "block";

            // Set the onclick function of the save button
            document.getElementById("savBut").onclick = () => {
                // Grab the setting name and value from the modal
                let setName = document.getElementById("modalTitle").innerHTML;
                let startVal = parseInt($('#modalSettingSelect-start').val());
                let endVal = parseInt($('#modalSettingSelect-end').val());

                // Pass this data to submitChanges()
                submitChanges({
                    "name": setName,
                    "value": { start: startVal, end: endVal}
                });
            };

            break;

        case "Multi-Duty Day Flag":
            // Create the necessary input rows for the Multi-Duty Flag Settings

            // Reformat the Python booleans into javascript booleans
            setData = setData.replaceAll("True", "true");
            setData = setData.replaceAll("False", "false");

            // Parse the json from the data
            let dat = JSON.parse(setData.replaceAll("'", '"'));

            // Create an onchange function for when the switch is turned on
            let mddOnChange = () => {
                document.getElementById("mddLabel").disabled = true;
            };

            // Create the toggle switch for the boolean value
            let mddFlag = generateBooleanRow(
                dat.flag,
                "Enable Use of Duty Flags",
                "mddFlag",
                () => {
                    document.getElementById("mddLabel").disabled = !document.getElementById("mddFlag").checked;
                },
                "col-sm-12"
            );

            // Add the boolean row to the divCollection
            divCollection.push(mddFlag[0]);
            divCollection.push(mddFlag[1]);

            // Create the input row for the label
            let mddLabel = generateInputRow(
                dat.label,
                "text",
                "Duty Flag Label",
                "col",
                "",
                "mddLabel",
                !(dat.flag)
            );

            // Add the input row to the divCollection
            divCollection.push(mddLabel);

            // Make sure the Save Button is displayed
            document.getElementById("savBut").style.display = "block";

            // Set the onclick function of the save button
            document.getElementById("savBut").onclick = () => {
                // Grab the setting name and value from the modal
                let setName = document.getElementById("modalTitle").innerHTML;
                let flag = document.getElementById("mddFlag").checked;
                let label = document.getElementById("mddLabel").value;

                // Pass this data to submitChanges()
                submitChanges({
                    "name": setName,
                    "value": { flag: flag, label: label}
                });
            };

            break;

        case "Automatic RA Point Adjustment":
            // Create the necessary input rows for the Automatic RA Point Adjustment Setting

            // Reformat the Python booleans into javascript booleans
            setData = setData.replaceAll("True", "true");
            setData = setData.replaceAll("False", "false");

            // Evaluate the boolean
            let autoRAPtAdj = setData === "true";

            // Create the toggle switch for the boolean value
            let autoRAPtAdjBool = generateBooleanRow(
                autoRAPtAdj,
                "Enable Automatic RA Point Adjustment",
                "autoRAPtAdjFlag",
                () => {},
                "col-sm-12"
            );

            // Add the boolean row to the divCollection
            divCollection.push(autoRAPtAdjBool[0]);
            divCollection.push(autoRAPtAdjBool[1]);

            // Make sure the Save Button is displayed
            document.getElementById("savBut").style.display = "block";

            // Set the onclick function of the save button
            document.getElementById("savBut").onclick = () => {
                // Grab the setting name and value from the modal
                let setName = document.getElementById("modalTitle").innerHTML;
                let flag = document.getElementById("autoRAPtAdjFlag").checked;

                // Pass this data to submitChanges()
                submitChanges({
                    "name": setName,
                    "value": flag
                });
            };

            break;

        default:
            // Otherwise generate a "standard" text input valDiv
            let valDiv = generateInputRow(setVal, "text", "Value");

            // Make sure the Save Button is displayed
            document.getElementById("savBut").style.display = "block";

            // Add the div to the divCollection
            divCollection.push(valDiv);

            // Set the save
            document.getElementById("savBut").onclick = () => {saveChanges("modalSettingValue")};
    }

    // Set the values in the form.
    document.getElementById("modalTitle").innerHTML = setName;
    document.getElementById("modalSettingDescription").innerHTML = setDesc;

    // Add all items in the divCollection to the valRow
    for (let i of divCollection) {
        valRow.appendChild(i);
    }

    // If we need to initialize the selectpicker
    if (initSelect) {
        // Then initialize the selectpicker
        $('.selectpicker').selectpicker();
    }

    // Display the modal
    $('#editSettingModal').modal('toggle');
}

function generateInputRow(value, type, labelName, colClass="col", smallText, inputID="modalSettingValue",
                          disable=false) {
    // Generate a valDiv that contains an input field with the appropriate value.

    // Create the necessary elements
    let valDiv = document.createElement("div");
    let label = document.createElement("label");
    let input = document.createElement("input");

    // Set the attributes of the valDiv element
    valDiv.setAttribute("id", "valDiv");
    valDiv.setAttribute("class", colClass);

    // Set the attributes of the label element
    label.setAttribute("for", "modalSettingValue");
    label.innerHTML = labelName;

    // Set the attributes of the input element
    input.setAttribute("class", "form-control");
    input.setAttribute("type", type);
    input.setAttribute("id", inputID);
    input.setAttribute("value", value);
    input.disabled = disable;

    // Connect all of the elements together
    valDiv.appendChild(label);
    valDiv.appendChild(input);

    // If smallText is defined
    if (smallText) {
        // Then create a small element
        let sm = document.createElement("small");
        sm.setAttribute("class", "form-text text-muted");
        sm.innerHTML = smallText;

        valDiv.appendChild(sm);
    }

    // Return the newly created valDiv
    return valDiv
}

function generateSelectRow(label, options, id, multiple, col="col-sm-12") {
    // Generate a valDic that contains a select field with the provided
    //  options. The provided options are a collection of objects containing
    //  the following properties:
    //     value      - The value of the <option>
    //     text       - The text to be displayed for the <option>
    //     selected   - A boolean denoting whether the <option> should be
    //                   selected once created.

    // Create the necessary elements
    let valDiv = document.createElement("div");
    let labelEl = document.createElement("label");
    let sel = document.createElement("select");

    // Set the attributes of the valDiv element
    valDiv.setAttribute("id", id);
    valDiv.setAttribute("class", col);

    // Set the attributes of the label element
    labelEl.setAttribute("for", "modalSettingSelect".concat("-",id));
    labelEl.innerHTML = label;

    // Set the attributes of the select element
    sel.setAttribute("id", "modalSettingSelect".concat("-",id));
    sel.setAttribute("name", "modalSettingSelect".concat("-",id));
    sel.setAttribute("class", "form-control selectpicker");
    if (multiple) {
        sel.setAttribute("multiple", "true");
    }

    // Connect all of the elements together
    valDiv.appendChild(labelEl);
    valDiv.appendChild(sel)

    // Iterate through the options collection and generate the necessary elements.
    let optEl;
    for (let item of options) {
        // Create an option element
        optEl = document.createElement("option");

        // Set the appropriate attributes for the <option>
        optEl.setAttribute("value", item.value);
        optEl.innerHTML = item.text;
        optEl.selected = item.selected;

        // Add the option to the select element
        sel.appendChild(optEl);
    }

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
    connectButton.setAttribute("onclick", "location.href='../integration/int/GCalRedirect'");
    connectButton.innerHTML = alreadyConnected ? "Reconnect Account" : "Connect Account";

    // Assemble the valDiv
    valDiv.appendChild(connectButton);

    // Return the newly generated valDiv
    return valDiv
}

function generateBooleanRow(value, labelName, id, onChange, col="col-sm-12") {
    // Generate a valDiv that contains an input field with the appropriate value.

    // Create the necessary elements
    let valDiv1 = document.createElement("div");
    let label = document.createElement("label");
    let input = document.createElement("input");
    let span = document.createElement("span");
    let valDiv2 = document.createElement("div");

    // Set the attributes for the valDiv1 element
    valDiv1.setAttribute("id", "valDiv");
    valDiv1.setAttribute("class", "col-sm-1");

    // Set the attributes of the label element
    label.setAttribute("class", "switch");
    label.setAttribute("for", id);

    // Set the attributes for the input element
    input.setAttribute("class", "form-control");
    input.setAttribute("type", "checkbox");
    input.setAttribute("id", id);
    input.checked = value;
    input.onchange = onChange;

    // Set the attributes for the span element
    span.setAttribute("class", "slider round");

    // Set the attributes for the valDiv2 element
    valDiv2.setAttribute("class", "col-sm-11");
    valDiv2.setAttribute("style", "margin-bottom:16px;")
    valDiv2.innerHTML = labelName;

    // Zip everything together
    valDiv1.appendChild(label);
    label.appendChild(input);
    label.appendChild(span);

    return [valDiv1, valDiv2];
}

function submitChanges(params) {
    // Submit the Hall Setting changes to be saved.

    console.log("Submitting changes to server")

    // Indicate to user that the setting is being saved
    document.getElementById("savBut").disabled = true;
    $("body").css("cursor", "wait");

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

    //console.log(data.settingData);
    //console.log(data.settingData.toString());

    let col;

    // Add SettingName
    col = newRow.insertCell(0);
    col.className = "settingName";
    col.innerHTML = data["settingName"];

    // Add SettingValue
    col = newRow.insertCell(1);
    col.className = "settingValue";
    col.innerHTML = data["settingVal"];

    // Add SettingDescription
    col = newRow.insertCell(2);
    col.className = "settingDescription";
    col.innerHTML = data["settingDesc"];

    // Add SettingData
    col = newRow.insertCell(3);
    col.className = "settingData";
    col.innerHTML = JSON.stringify(data["settingData"]);

    // Add Edit column
    let edit = newRow.insertCell(4);
    let editSpan = document.createElement("span");

    editSpan.className = "fa fa-pencil";
    editSpan.setAttribute("onclick","showEditModal("+rowId.toString()+")");
    edit.appendChild(editSpan);

}

function saveChanges(settingID) {
    // Assemble the setting values from the modal and pass them to submitChanges
    //  to be sent to the server

    // Grab the setting name and value from the modal
    let setName = document.getElementById("modalTitle").innerHTML;
    let setVal = document.getElementById(settingID).value;

    // Set the parameters for the API
    let params = {
        "name": setName,
        "value": setVal
    }

    // Pass the assembled data to submitChanges()
    submitChanges(params);
}

function saveDutyConfig() {
    // Gather and assemble all of the values relating to the duty configuration
    //  settings and pass them to the submitChanges() function.

    // Grab the selected options from the multi-duty day field and convert them to Integers
    let rawDays = $('#modalSettingSelect-mddSelect').val();
    let days = [];
    for (let dStr of rawDays) {
        days.push(parseInt(dStr));
    }

    // Grab the setting name and assemble the setting value into the expected
    //  JSON format.
    let setName = document.getElementById("modalTitle").innerHTML;
    let setVal = {
        reg_duty_num_assigned: parseInt(document.getElementById("dutyConfigNum-0").value),
        reg_duty_pts: parseInt(document.getElementById("dutyConfigPts-0").value),

        multi_duty_num_assigned: parseInt(document.getElementById("dutyConfigNum-1").value),
        multi_duty_pts: parseInt(document.getElementById("dutyConfigPts-1").value),

        brk_duty_num_assigned: parseInt(document.getElementById("dutyConfigNum-2").value),
        brk_duty_pts: parseInt(document.getElementById("dutyConfigPts-2").value),

        multi_duty_days: days
    };

    // Set the parameters for the API
    let params = {
        "name": setName,
        "value": setVal
    }

    // Pass the assembled data to submitChanges()
    submitChanges(params);
}
