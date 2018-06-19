"use strict"

function AppBase () {

}

AppBase.prototype.init = function () {

}

AppBase.prototype.logEvent = function (eventInfo) {
    eventInfo.course = eBookConfig.course;
    if (eBookConfig.useRunestoneServices && eBookConfig.logLevel > 0) {
        $.get(eBookConfig.ajaxURL + 'hsblog', eventInfo); // Log the run event
    }
    console.log("logging event " + JSON.stringify(eventInfo));
};

AppBase.prototype.callAPI = function (apiStr, params, fun) {
    // apiStr = remainder of the api address
    // params = data that is to be sent to the server
    //    fun = the function that will handle the returning data

    let dfd = new $.Deferred();
    console.log("Calling API: " + apiStr);
    console.log(params);

	$.ajax({
		url: appConfig.apiURL + apiStr,
		method: "GET",
        data: params
    }).done(function(data) {
        fun(data)
        dfd.resolve();
    });

    return dfd;

    // $.get(appConfig.apiURL + apiStr, params, fun);

}

function testResponse (data) {
    console.log(data);
}

/* Checking/loading from storage */

AppBase.prototype.checkServer = function (eventInfo) {
    // Check if the server has stored answer
    if (this.useRunestoneServices || this.graderactive) {
        let data = {};
        data.div_id = this.divid;
        data.course = eBookConfig.course;
        data.event = eventInfo;
        if (this.sid) {
            data.sid = this.sid
        }
        if (!eBookConfig.practice_mode){
            jQuery.getJSON(eBookConfig.ajaxURL + "getAssessResults", data, this.repopulateFromStorage.bind(this)).error(this.checkLocalStorage.bind(this));
        }
        else{
            this.loadData({});
        }
    } else {
        this.checkLocalStorage();   // just go right to local storage
    }
};

AppBase.prototype.repopulateFromStorage = function (data, status, whatever) {
    // decide whether to use the server's answer (if there is one) or to load from storage
    if (data !== null && this.shouldUseServer(data)) {
        this.restoreAnswers(data);
        this.setLocalStorage(data);
    } else {
        this.checkLocalStorage();
    }
};

AppBase.prototype.shouldUseServer = function (data) {
    // returns true if server data is more recent than local storage or if server storage is correct
    if (data.correct === "T" || localStorage.length === 0 || this.graderactive === true) {
        return true;
    }
    let ex = localStorage.getItem(eBookConfig.email + ":" + this.divid + "-given");
    if (ex === null) {
        return true;
    }
    let storedData;
    try {
        storedData = JSON.parse(ex);
    } catch (err){
        // error while parsing; likely due to bad value stored in storage
        console.log(err.message);
        localStorage.removeItem(eBookConfig.email + ":" + this.divid + "-given");
        // definitely don't want to use local storage here
        return true;
    }
    if (data.answer == storedData.answer)
        return true;
    let storageDate = new Date(storedData.timestamp);
    let serverDate = new Date(data.timestamp);

    return serverDate >= storageDate;

};
