let user_dict = {}
let cur_user = ""
let agent_list = []

let check_tree_interval = {}
let tree_status = "building"
let check_pool_interval = {}
let pool_status = "building"

window.onload = function(){
    loadContent("/dashboard");
}

function loadContent(content) {
    if (content.startsWith("user")){
        username = content.split("-")[1]
        $("#mainContent").load("/user", success=function(){
            load_user_page(username)
            cur_user = username
            draw()
        }); 
    }
    else{
        $("#mainContent").load(content, success=function(){
            addListener()
        }); 
    }
    update_user_list();
}

function loadAgent(id) {
    $("#mainContent").load("/" + cur_user + "/" + id.toString(), success=function(){
        console.log(cur_user + id.toString())
        draw_agent()
        init_calendar(window.jQuery)
        // TODO！！！
    }); 
};

function addListener() {

    document.getElementById('create_user_form').addEventListener('submit', (event) => {
            console.log("success find create_user_form")
            event.preventDefault();
            create_user()
        });
    document.getElementById('description_form').addEventListener('submit', (event) => {
            console.log("success find description_form")
            event.preventDefault();
            random_create_user()
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
        if (["username","birthday","city"].includes(key)){
            if (value=='None' || value=='') {
                alert("Missing " + key);
                return 0;
            }
        }
        if (["start_date","birthday"].includes(key)){
            splited = value.split("-");
            formData.set(key, splited[1]+"-"+splited[2]+"-"+splited[0]);
        }
    }
    
    $.ajax({
        url: "/user/create",
        type: 'POST',
        async: false,
        data: formData,
        processData: false,
        contentType: false,
        dataType: 'json',
        success: function(res) {
            activate_user(formData.get("username"));
            alert("Success");
            // check_tree_interval[formData.get("username")] = setInterval(check_info_tree, 1000, formData.get("username"));
        },
        error: function(res){
            console.log(res)
            alert("Error\n" + res)
        }
    });
    loadContent("/dashboard");
}

function check_info_tree(username){
    $.ajax({
        url: "/agents/" + username + "/infotree/status",
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            update_status_area(res, "InfoTree status")
            console.log("Tree status: " + res["message"])
            if (res["message"].includes("ready")){
                tree_status = "ready";
                document.getElementById("generate_pool_btn").innerText = "Regenerate InfoTree";
                clearInterval(check_tree_interval[username]);
                delete check_tree_interval[username];
            }
            else if (res["message"].includes("error")) {
                tree_status = "error";
                clearInterval(check_tree_interval[username]);
                delete check_tree_interval[username];
            }
            else{
                tree_status = res["message"];
            }
        }
      });
}

function random_create_user(){
    var formData = new FormData(document.getElementById('description_form'))
    for (var [key, value] of formData.entries()) {
        if (["short_description"].includes(key)){
            if (value=='None' || value=='') {
                alert("Missing " + key)
                return 0
            }
        }
    }

    document.getElementById('waiting').classList.remove("d-none");

    $.ajax({
        url: "/user/random",
        type: 'POST',
        async: true,
        data: formData,
        processData: false,
        contentType: false,
        dataType: 'json',
        success: function(res) {
            infos = res["infos"]
            for (var key in infos){
                var value = infos[key];
                _list = document.getElementsByName(key);
                if (_list.length > 0){
                    if(key==="gender"){
                        if (value.toLowerCase()==="male"){
                            _list[0].value = "Male"
                        }
                        else{
                            _list[0].value = "Female"
                        }
                    }
                    else if (key==="retirement") {
                        if (value.toLowerCase()==="yes"){
                            _list[0].value = "Yes"
                        }
                        else{
                            _list[0].value = "No"
                        }
                    }
                    else if (key==="birthday"){
                        splited = value.split("-")
                        _list[0].value = splited[2]+"-"+splited[0]+"-"+splited[1];
                    }
                    else{
                        _list[0].value = value;
                    }
                }
            }
            document.getElementById('waiting').classList.add("d-none");
            document.getElementById('information').classList.remove("d-none");
        },
        error: function(res){
            console.log(res)
            alert("Error\n" + res)
        }
      });

}

function fetch_agents_list(username){
    $.ajax({
        url: "/agents/" + username + "/fetchall",
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function( res ) {
            agent_list = res['data'];
            if (res['message']==="done"){
                check_agents_pool(username)
            }
        }
      });
}

function update_agents_list(username){
    fetch_agents_list(username);

    _html = ""

    // <li class="list-group-item">
    //     <div class="row">
    //         <div class="custom-control custom-checkbox col-md-4"><input type="checkbox"></div>
    //         <div class="col-md-8"><a onclick="loadAgent(1)">Agent 1</a></div>
    //     </div>
    // </li>

    for(var agent in agent_list) {
        _html += "<li class=\"list-group-item\"><div class=\"row\"><div class=\"custom-control custom-checkbox col-md-4\"><input type=\"checkbox\"></div>"
        _html += "<div class=\"col-md-8\"><a onclick=\"loadAgent("
        _html += agent.split("-")[1]
        _html += ")\">"
        _html += agent
        _html += "</a></div></div></li>"
    }
    document.getElementById("agent_list").innerHTML = _html
}

function check_agents_pool(username){
    if (tree_status==="ready"){
        $.ajax({
            url: "/agents/" + username + "/status",
            type: 'GET',
            async: false,
            dataType: 'json',
            success: function(res) {
                update_status_area(res, "Agent pool status")
                console.log("Agent pool status: " + res["message"])
                if (res["message"].includes("ready")){
                    pool_status = "ready"
                    document.getElementById("generate_agent_btn").innerText("Regenerate Agents")
                    clearInterval(check_pool_interval[username]);
                    delete check_pool_interval[username]
                    update_agents_list(username)
                }
                else if (res["message"].includes("error")){
                    pool_status = "error"
                    clearInterval(check_pool_interval[username]);
                    delete check_pool_interval[username]
                }
                else {
                    pool_status = res["message"]
                }
            }
          });

    }
}

function activate_user(username){
    let status=false
    $.ajax({
        url: "/user/activate/" + username,
        type: 'GET',
        async: false,
        success: function(res) {
            console.log(res)
            fetch_user_status(username)
            status = true
        },
        error: function(res){
            console.log(res["message"])
            status = false
        }
      });
      return status
};

function fetch_user_status(username){
    $.ajax({
        url: "/user/status/" + username,
        type: 'GET',
        async: false,
        success: function(res) {
            update_status_area(res, "User status")
        }
      });
}

function update_status_area(res, type){
    if (res["message"].includes("building")){
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-cogs")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-warning", "solid", "alert-right-icon", "col-md-8", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]
    }
    else if (res["message"].includes("ready")){
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-check")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-success", "solid", "alert-right-icon", "col-md-8", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]
    }
    else {
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-alert")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-danger", "solid", "alert-right-icon", "col-md-8", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]

    }
}

function GenerateInfoTree(){
    if (tree_status==="ready"){
        $.ajax({
            url: "/agents/" + cur_user + "/infotree/generate",
            type: 'GET',
            async: true,
            dataType: 'json',
            success: function(res) {
                check_tree_interval[cur_user] = setInterval(check_info_tree, 1000, cur_user);
            }
          });
    }
}

function GenerateAgentsPool(){
    if (pool_status === "init" || pool_status === "ready"){
        document.getElementById("agent_list").innerHTML = ""
        $.ajax({
            url: "/agents/" + cur_user + "/create",
            type: 'GET',
            async: true,
            dataType: 'json',
            success: function(res) {
                check_pool_interval[cur_user] = setInterval(check_agents_pool, 1000, cur_user);
            }
          });
    }
}

function load_user_page(username){
    if_activated = activate_user(username)
    if (if_activated) {
        check_tree_interval[username] = setInterval(check_info_tree, 1000, username);
        check_pool_interval[username] = setInterval(check_agents_pool, 1000, username);
        // 1. load agents
        // 2. load statistic
    }
    else{
        alert("Activate user failed")
    }
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



