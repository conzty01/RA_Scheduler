"use strict"

function AppBase () {

}

AppBase.prototype.init = function () {

}

AppBase.prototype.callAPI = function (apiStr, params, fun, m="GET") {
    // apiStr = remainder of the api address
    // params = data that is to be sent to the server
    //    fun = the function that will handle the returning data

    let dfd = new $.Deferred();
    console.log("Calling API: " + apiStr);
    //console.log(params);

    if (m === "GET") {
        $.ajax({
    		url: appConfig.apiURL + apiStr,
    		method: "GET",
            data: params
        }).done(function(data) {
            fun(data)
            dfd.resolve();
        }).error(function(data){
            console.log("Ajax Error: ",data);
        });
    } else if (m === "POST") {
        $.ajax({
    		url: appConfig.apiURL + apiStr,
    		method: "POST",
            contentType: "application/json;charset=UTF-8",
            data: JSON.stringify(params)
        }).done(function(data) {
            fun(data)
            dfd.resolve();
        }).error(function(data){
            console.log("Ajax Error: ",data);
        });
    }
    return dfd;

    // $.get(appConfig.apiURL + apiStr, params, fun);

}

function testResponse (data) {
    console.log(data);
}
