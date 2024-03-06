

window.onload = function(){
    loadContent("dashboard")
}

function loadContent(content) {
    if (content === "dashboard"){
        console.log("Here")
        $("#mainContent").load("/dashboard"); 
    }
}

function requstHTMLContent(req) {
    let return_val = null
    $.ajax({
        url: "/api/getRange",
        type: 'POST',
        async: false,
        data: JSON.stringify({
            "gender": gender,
            "edu": edu,
            "age": age
        }),
        contentType: "application/json",
        dataType: 'json',
        success: function( res ) {
            return_val = res;
        },
        error: function(){
            return_val =  "error"
        }
      });
    return return_val
}

