"use strict"

function AppBase () {

}

AppBase.prototype.init = function () {

}

AppBase.prototype.assembleAPIURLString = function (apiStr, bpPrefix="") {
    // Assemble and return a URL for the provided API.

    // If the bpPrefix is not provided
    if (bpPrefix === "") {
        // Then use the one associated with the current BP
        bpPrefix = bpAPIPrefix;
    }

    // Build the API URL
    return appConfig.host + bpPrefix + "/api/" + apiStr;
}

AppBase.prototype.fetchRetry = function (url, evalFun, failFun, extraWork=() => {}, options={}, retries=3, backoff=300) {
    // Fetch the provided URL until either the evalFun returns True or the number
    //  of retries reach 0.

    // Fetch the requested url and return the promise
    return fetch(url, options)
        // Add a .then clause to the promise to evaluate the result
        .then((resp) => resp.json())
        .then(async (resJSON) => {
            console.log(resJSON);

            // If the status is ok and the evaluation function returns True,
            //  then return the json from the result.
            console.log(evalFun(resJSON));
            if (evalFun(resJSON)) return resJSON;

            // Otherwise, if we still have retries left...
            if (retries > 0) {
                // Execute the extra work function passing it the res, retries and backoff
                extraWork(resJSON, retries, backoff);

                // Wait for the backoff amount of time
                await new Promise(r => setTimeout(r, backoff));
                // Try again with a delay
                //setTimeout(() => {
                return AppBase.prototype.fetchRetry(url, evalFun, failFun, extraWork, options, retries - 1, backoff * 2);
                //}, backoff)

            } else {
                // If we do not have any retries left, then call the Failure function and
                //  return the result to the caller.
                return failFun()
            }
        // If any funny business happens, log the error
        }).catch(console.error);
}

AppBase.prototype.callAPI = function (apiStr, params, fun, m="GET", errorFun=null, bpPrefix="") {
    // apiStr = remainder of the api address
    // params = data that is to be sent to the server
    //    fun = the function that will handle the returning data

    if (errorFun === null) {
        errorFun = function(data){console.log("Ajax Error: ",data);}
    }

    let urlStr = this.assembleAPIURLString(apiStr, bpPrefix);

    let dfd = new $.Deferred();
    console.log("Calling API: " + apiStr);
    //console.log(params);

    if (m === "GET") {
        $.ajax({
    		url: urlStr,
    		method: "GET",
            data: params
        }).done(function(data) {
            fun(data)
            dfd.resolve();
        });
    } else if (m === "POST") {
        $.ajax({
    		url: urlStr,
    		method: "POST",
            contentType: "application/json;charset=UTF-8",
            data: JSON.stringify(params)
        }).done(function(data) {
            fun(data)
            dfd.resolve();
        });
    }
    return dfd;

    // $.get(appConfig.apiURL + apiStr, params, fun);

}

function testResponse (data) {
    console.log(data);
}
