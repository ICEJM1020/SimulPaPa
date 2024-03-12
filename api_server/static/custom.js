let user_dict = {}

window.onload = function(){
    loadContent("/dashboard");
    update_user_list()
}

function loadContent(content) {
    if (content.startsWith("user")){
        username = content.split("-")[1]
        $("#mainContent").load("/user", success=function(){
            load_user_page(username)
        }); 
    }
    else{
        $("#mainContent").load(content, success=function(){
            addListener()
        }); 
    }
}

function addListener() {

    document.getElementById('create_user_form').addEventListener('submit', (event) => {
            console.log("success find create_user_form")
            event.preventDefault();
            create_user()
        });
    document.getElementById('create_user_form').addEventListener('random', (event) => {
            console.log("success find create_user_form")
            event.preventDefault();
            random_create()
        });
}

function update_user_list(){
    user_dict = fetch_users();

    _html = ""
    for(var key in user_dict) {
        _html += "<li><a href=\"javascript:void(0)\" onclick=\"loadContent('user-"
        _html += key
        _html += "')\">"
        _html += key
        _html += "</a></li>"
    }
    document.getElementById("user_list").innerHTML = _html
}


function fetch_users(){
    let return_val = null
    $.ajax({
        url: "/user/all",
        type: 'POST',
        async: false,
        contentType: "application/json",
        dataType: 'json',
        success: function( res ) {
            console.log(res['msg'])
            return_val = res['users'];
        },
        error: function(){
            return_val =  "error"
        }
      });
    return return_val
}

function create_user(){
    var formData = new FormData(document.getElementById('create_user_form'))

    for (var [key, value] of formData.entries()) {
        // if (key=="username"){
        //     if (key.includes(" ")){
        //         alert("No  " + key)
        //         return 0
        //     }
        // }
        if (["name" ,"gender","birthday","city"].includes(key)){
            if (value=='None' || value=='') {
                alert("Missing " + key)
                return 0
            }
        }
    }
    
    $.ajax({
        url: "/user/create",
        type: 'POST',
        async: false,
        data: formData,
        processData: false,
        contentType: false,
        // contentType: "application/form-data",
        dataType: 'json',
        success: function(res) {
            alert("Success");
        },
        error: function(res){
            console.log(res)
            alert("Error\n" + res)
        }
      });
    location.replace("/")

}

function random_create(){

}


function load_user_page(username){
    let if_activated = activate_user(username)
    if (if_activated){
        console.log("here")
        document.getElementById("user_description").innerText = fetch_user_info(username)
    }
    else {
        alert("Activate user failed")
    }
}

function activate_user(username){
    let status = false
    $.ajax({
        url: "/user/activate/" + username,
        type: 'GET',
        async: false,
        success: function(res) {
            status = true
        },
        error: function(res){
            alert(res["message"])
            console.log(res["message"])
        }
      });
      return status
}

function fetch_user_info(username){
    let return_val = "Waiting for Server..."
    $.ajax({
        url: "/user/description/" + username,
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            return_val = res["description"]
        },
        error: function(res){
            console.log(res)
        }
      });
    return return_val
}
