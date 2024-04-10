let user_dict = {}
let cur_user = ""
let agent_list = []

let check_tree_interval = {}
let tree_status = ""
let check_pool_interval = {}
let pool_status = ""
let new_user_start_simulation = {}
let simul_status = ""
let check_simul_interval = {}

let update_stat_interval = null
let all_donedates = []
let cur_date = ""
let act_stat = {}
let hr_stat = {}

let page_status = 'user'

let check_interval = 100

window.onload = function(){
    loadContent("/dashboard");
}

function loadContent(content) {
    if (content.startsWith("user")){

        username = ""
        segs = content.split("-")
        for (var seg in segs){
            if (seg==0){
                continue;
            }
            else{
                username += segs[seg];
                username += "-";
            }
        }
        username = username.slice(0, -1);
        console.log(username)
        $("#mainContent").load("/user", success=function(){
            load_user_page(username)
            cur_user = username
            document.getElementsByClassName('nav-control')[0].click();
        }); 
    }
    else if (content.startsWith("back")){
        $("#mainContent").load("/user", success=function(){
            load_user_page(cur_user)
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
    // $("#mainContent").load("/" + cur_user + "/" + id.toString(), success=function(){
    //     cur_agent_id = id.toString()
    //     console.log(cur_user + "," + id.toString())
    //     load_agent_page()
    // }); 
    $("#display-area").load("/" + cur_user + "/" + id.toString(), success=function(){
        cur_agent_id = id.toString()
        console.log(cur_user + "," + id.toString())
        load_agent_page()
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
            return_val = res['users'];
        },
        error: function(){
            return_val =  []
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
            new_user_start_simulation[formData.get("username")] = setInterval(GenerateAgentsPool, check_interval, formData.get("username"));
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

function load_agent_pool(username){
    $.ajax({
        url: "/agents/" + username + "/loadlocal",
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function( res ) {
            console.log("Load agents pool");
            // update_status_area({"message":"ready-Loaded from local machine"}, "Agents Pool");
            if (!(username in check_pool_interval)) check_pool_interval[username] = setInterval(check_agents_pool, check_interval, username);
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
            console.log(res['message'])
            agent_list = res['data'];

            if (res['message']=="done"){
                update_status_area({"message":"ready in last agents creation."}, "Agents Pool")
            }
            else{
                update_status_area({"message":"error in last agents pool creation. Regenerate or use exitsed agents."}, "Agents Pool")
            }
        }
      });
}

function update_agents_list(username){

    if (username=="ready_update"){
        fetch_agents_list(cur_user);
    } 
    else{
        fetch_agents_list(username);
        load_agent_pool(username);
    }

    len_agent = Object.keys(agent_list).length

    _html = ""

    // <li class="list-group-item">
    //     <div class="row">
    //         <div class="custom-control custom-checkbox col-md-4"><input type="checkbox"></div>
    //         <div class="col-md-8"><a onclick="loadAgent(1)">Agent 1</a></div>
    //     </div>
    // </li>
    // <a class="list-group-item list-group-item-action" onclick="loadAgent(1)">Agent 1</a>
    for(var idx in agent_list) {
        _html += "<a href=\"javascript:void()\" class=\"list-group-item agent-list-group-item-action\" onclick=\"loadAgent("
        _html += agent_list[idx].split("-")[1]
        _html += ")\">"
        _html += agent_list[idx]
        _html += "</a>"
    }
    if (len_agent>10){
        document.getElementById("agent_list").classList.add("agent-list")
    }
    document.getElementById("agent_list").innerHTML = _html

    _html = ""
    // <button class="btn btn-primary" type="button">Button</button>
    for(var idx in agent_list) {
        _html += "<button class=\"btn btn-outline-primary\" type=\"button\">" + agent_list[idx] + "</button>"
    }
    if (len_agent>3){
        document.getElementById("agent-btn-group").classList.add("agent-btn-list")
    }
    document.getElementById("agent-btn-group").innerHTML = _html
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
                    document.getElementById("generate_agent_btn").innerText = "Regenerate Agents"
                    clearInterval(check_pool_interval[username]);
                    delete check_pool_interval[username]

                    update_agents_list("ready_update");
                }
                else if (res["message"].includes("error")){
                    pool_status = "error"
                    clearInterval(check_pool_interval[username]);
                    delete check_pool_interval[username]
                }
                else if (res["message"].includes("init")){
                    pool_status = "init"
                    clearInterval(check_pool_interval[username]);
                    delete check_pool_interval[username];

                    update_agents_list(username);
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
    if (res["message"].includes("ing")){
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-cogs")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-warning", "solid", "alert-right-icon", "col-md-12", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]
    }
    else if (res["message"].includes("ready")){
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-check")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-success", "solid", "alert-right-icon", "col-md-12", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]
    }
    else {
        document.getElementById("status_icon").classList = ""
        document.getElementById("status_icon").classList.add("mdi", "mdi-alert")
        document.getElementById("status_area").classList = ""
        document.getElementById("status_area").classList.add("alert", "alert-danger", "solid", "alert-right-icon", "col-md-12", "mb-0")
        document.getElementById("status_text").innerText = type + "-" + res["message"]

    }
}

function check_simulation(username){
    if (tree_status=="ready" && pool_status=="ready"){
        $.ajax({
            url: "/simulation/status/" + username ,
            type: 'GET',
            async: false,
            dataType: 'json',
            success: function(res) {
                console.log("Simulation status: " + res["message"])
                update_status_area(res, "Simulation status")
                if (res["message"].includes("ing")){
                    simul_status = "working";
                    if (cur_user in check_simul_interval){
                        clearInterval(check_simul_interval[cur_user]);
                        delete check_simul_interval[cur_user];
                    }
                    check_simul_interval[cur_user] = setInterval(check_simulation, check_interval*100, cur_user);
                }
                else if (res["message"].includes("ready") || res["message"].includes("failed")){
                    clearInterval(check_simul_interval[username]);
                    delete check_simul_interval[username];
                }
                else {
                    
                }
            }
        });
    }
}

function start_simulation(username){
    // if (simul_status == "working") return;

    if (username){
        console.log("Start simulate for " + username)
        $.ajax({
            url: "/simulation/start/" + username,
            type: 'GET',
            async: true,
            success: function(res) {
                if (cur_user in check_simul_interval){
                    clearInterval(check_simul_interval[cur_user]);
                    delete check_simul_interval[cur_user];
                }
                check_simul_interval[cur_user] = setInterval(check_simulation, check_interval*100, cur_user);
            }
          });
    }
    else{
        $.ajax({
            url: "/simulation/start/" + cur_user,
            type: 'GET',
            async: true,
            success: function(res) {
                if (cur_user in check_simul_interval){
                    clearInterval(check_simul_interval[cur_user]);
                    delete check_simul_interval[cur_user];
                }
                check_simul_interval[cur_user] = setInterval(check_simulation, check_interval*100, cur_user);
            }
          });
    }
}

function continue_simulation(){
    if (simul_status == "working") return;

    var formData = new FormData()
    formData.set("days", document.getElementsByName("new_days")[0].value)

    $.ajax({
        url: "/simulation/continue/" + cur_user,
        type: 'POST',
        async: true,
        data: formData,
        processData: false,
        contentType: false,
        dataType: 'json',
        success: function(res) {
            if (cur_user in check_simul_interval){
                clearInterval(check_simul_interval[cur_user]);
                delete check_simul_interval[cur_user];
            }
            check_simul_interval[cur_user] = setInterval(check_simulation, check_interval*100, cur_user);
        }
        });
}

function GenerateInfoTree(){
    if (tree_status==="ready"){
        $.ajax({
            url: "/agents/" + cur_user + "/infotree/generate",
            type: 'GET',
            async: true,
            dataType: 'json',
            success: function(res) {
                check_tree_interval[cur_user] = setInterval(check_info_tree, check_interval*50, cur_user);
            }
          });
    }
}

function new_user_simulation(username){
    if (tree_status==="ready" && pool_status==="ready"){
        clearInterval(new_user_start_simulation[username]);
        delete new_user_start_simulation[username];
        load_agent_pool(username);
        start_simulation(username);
    }
}

function GenerateAgentsPool(username){
    if (username){
        console.log("New user attempt to create")
        $.ajax({
            url: "/agents/" + username + "/create",
            type: 'GET',
            async: true,
            dataType: 'json',
            success: function(res) {
                if (res["message"].includes("error") || res["message"].includes("ing")){
                    clearInterval(new_user_start_simulation[username]);
                    delete new_user_start_simulation[username];
                    if (res["message"].includes("error")){
                        alert("Error creation for " + username)
                    }
                    else{
                        new_user_start_simulation[username] = setInterval(new_user_simulation, check_interval*50, username)
                    }

                }
            }
            });
    }
    else{
        if (!pool_status.includes("ing")){
            document.getElementById("agent_list").innerHTML = ""
            $.ajax({
                url: "/agents/" + cur_user + "/create",
                type: 'GET',
                async: true,
                dataType: 'json',
                success: function(res) {
                    if (!(cur_user in check_pool_interval)){
                        check_pool_interval[cur_user] = setInterval(check_agents_pool, check_interval, cur_user);
                    }
                }
                });
        }

    }
}

function fetch_all_donedates(){
    $.ajax({
        url: "/agents/" + cur_user + "/all-donedates",
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            all_donedates = res["data"]
        }
        });
}

function fetch_activity_statistic(date){
    $.ajax({
        url: "/agents/" + cur_user + "/statistic/" + date,
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            act_stat = res["data"]["activity"]
            hr_stat = res["data"]["heartrate"]
        },
        error: function(res) {
            console.log(res)
        }
        });
}

function show_donedates_cal(){
    $('.year-calendar').pignoseCalendar({
        format: 'MM-DD-YYYY',
        date: cur_date,
        minDate: all_donedates[0],
        maxDate: all_donedates[all_donedates.length-1],
        theme: 'blue', // light, dark, blue

        select: function(date, context) {

            
            cur_date = date[0].format('MM-DD-YYYY');
            if (page_status=='user'){
                fetch_activity_statistic(cur_date);
                draw_stat(act_stat, hr_stat);
            }
            else{
                draw_agent_heartrate(cur_date);
                draw_chat(cur_date);
                draw_map(cur_date);
            }
        }
    });
}

function show_stat(){
    if (pool_status=="ready"){
        clearInterval(update_stat_interval);

        fetch_all_donedates();
        cur_date = all_donedates[0]
        fetch_activity_statistic(cur_date);

        show_donedates_cal();
        draw_stat(act_stat, hr_stat);
    }
}

function load_user_page(username){
    if_activated = activate_user(username)
    if (if_activated) {
        cur_date = ""
        page_status = 'user'

        tree_status = ""
        pool_status = ""
        simul_status = ""

        if (!(username in check_tree_interval)) check_tree_interval[username] = setInterval(check_info_tree, check_interval, username);
        if (!(username in check_pool_interval)) check_pool_interval[username] = setInterval(check_agents_pool, check_interval, username);
        if (!(username in check_simul_interval)) check_simul_interval[username] = setInterval(check_simulation, check_interval, username);

        document.getElementById("top-user-name").innerText = username
        
        all_donedates = []
        act_stat = {}
        hr_stat = {}
        update_stat_interval = setInterval(show_stat, check_interval)
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



// single agent
let cur_agent_id = ""
let agent_info = {}
let donedates =  []
let chat_his = {}
let loc_hist = {}
let schedules = {}

function load_agent_page(){
    page_status = 'agent'

    // document.getElementById("back_btn").onclick = function() { loadContent("user-"+cur_user)}
    // document.getElementById("user-name").innerText = cur_user
    // document.getElementById("agent-name").innerText = "Agent "+cur_agent_id
    // document.getElementById("agent-name-link").innerText = "Agent "+cur_agent_id
    document.getElementById("portrait").src = "/agent/"+cur_user+"/"+cur_agent_id+"/portrait"


    agent_info = {}
    donedates =  []
    chat_his = {}
    loc_hist = {}
    schedules = {}

    load_info();
    fetch_done_date();

    var missing_date = []
    for (var _date of donedates){
        if (!(all_donedates.includes(_date))){
            missing_date.push(_date)
        }
    }
    if (missing_date.length!==0){
        $('.year-calendar').pignoseCalendar('settings', {
            disabledDates: missing_date
        })
        cur_date = donedates[0];
        $('.year-calendar').pignoseCalendar('set', cur_date);
    }

    draw_agent_heartrate(cur_date);
    draw_chat(cur_date);
    show_location_hist(cur_date);
    init_schedule();
}

function load_info(){
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/info",
        type: 'GET',
        async: true,
        dataType: 'json',
        success: function(res) {
            agent_info = res["info"]
            document.getElementById("description").innerText = agent_info["description"]
            document.getElementById("name-show").innerHTML = "<strong>Name:"+ agent_info["name"] +"</strong>"
            document.getElementById("birthday-show").innerHTML = "<strong>Birthday:"+ agent_info["birthday"] +"</strong>"
            document.getElementById("disease-show").innerHTML = "<strong>Disease(s):"+ agent_info["disease"] +"</strong>"
        }
        });
}

function fetch_done_date() {
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/donedate",
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            donedates = res["data"]
        }
        });
}

let chat_display = true
// true for chat bubble
// false for word cloud
function change_chat_display()
{
    // if (chat_display){
    //     document.getElementById("chat_history").classList.remove("d-none");
    //     document.getElementById("chatbot_wordcloud").classList.add("d-none");
    //     chat_display = false;
    // }else{
    //     document.getElementById("chatbot_wordcloud").classList.remove("d-none");
    //     document.getElementById("chat_history").classList.add("d-none");
    //     chat_display = true;
    // }

    if (chat_display){
        document.getElementById("chatbot_wordcloud").classList.remove("d-none");
        document.getElementById("chat_history").classList.add("d-none");
        document.getElementById("change_chat_display").innerText = "Dialogue"
        chat_display = false;
    }else{
        document.getElementById("chat_history").classList.remove("d-none");
        document.getElementById("chatbot_wordcloud").classList.add("d-none");
        document.getElementById("change_chat_display").innerText = "Word Cloud"
        chat_display = true;
    }
}

//
// draw wordcloud
// 
function wordFreq(words) {
    // var words = string.replace(/[.]/g, '').split(/\s/);
    // words
    var freqMap = {};
    words.forEach(function(w) {
        if (!freqMap[w]) {
            freqMap[w] = 0;
        }
        freqMap[w] += 1;
    });

    return freqMap;
}

function d3_draw_cloud(myWords){
    document.getElementById("chatbot_wordcloud").innerHTML = ""

    let words = []
    let large = -1
    for (var key in myWords) {
        large = Math.max(large, myWords[key])
    }
    for (var key in myWords) {
        words.push(
            {text: key, size: 10 + (myWords[key]/large) * 90, test: "haha"}
        )
    }
    // set the dimensions and margins of the graph
    loc = document.getElementById("chatbot_wordcloud").getBoundingClientRect()
    var margin = {top: 10, right: 10, bottom: 10, left: 10},
        width = loc.width - margin.left - margin.right,
        // height = ((loc.width * 9) / 16) - margin.top - margin.bottom;
        height = 600 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#chatbot_wordcloud").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
    .append("g")
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    // Constructs a new cloud layout instance. It run an algorithm to find the position of words that suits your requirements
    var layout = d3.layout.cloud()
    .size([width, height])
    // .words(myWords.map(function(d) {
    //   return {text: d, size: 10 + Math.random() * 90, test: "haha"};
    // }))
    .words(words)
    .padding(5)
    .rotate(function() { return ~~(Math.random() * 2) * 90; })
    .font("Impact")
    .fontSize(function(d) { return d.size; })
    .on("end", draw);
    layout.start();

    // This function takes the output of 'layout' above and draw the words
    // Better not to touch it. To change parameters, play with the 'layout' variable above
    function draw(words) {
        svg.append("g")
        .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")")
        .selectAll("text")
            .data(words)
        .enter().append("text")
            .style("font-size", function(d) { return d.size + "px"; })
            .attr("text-anchor", "middle")
            .attr("transform", function(d) {
            return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
            })
            .text(function(d) { return d.text; });
    }
}

function fetch_chat_his(date){
    let chathis = {0:{"time":"null", "chatbot":"null null null"}}
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/chathis/" + date,
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            if (Object.keys(res["data"]).length !== 0){chathis = res["data"]}
        }
        });
    return chathis;
}

function count_words_freq(){
    _str = ""
    for (var idx in chat_his){
        _str = _str + chat_his[idx]["chatbot"]
    }
    _str = _str.split(' ')
    _str = sw.removeStopwords(_str)
    return wordFreq(_str)
}

function get_utter(chat){
    if (chat.includes(":")){
        return chat.split(":")[1];
    }
    else{
        return chat;
    }
}

function show_chat_hist(){
    let _html = "";
    for (var idx in chat_his){
        // console.log(chat_his[idx]["chatbot"])
        // console.log(chat_his[idx]["time"])
        // <div class="balon1 p-2 m-0 position-relative" data-is="You - 3:20 pm"><a class="float-right"> Hey there! What's up? </a></div>
        if (chat_his[idx]["chatbot"].includes(";")){
            _temp = chat_his[idx]["chatbot"].split(";")
            for (var idx_2 in _temp){
                // console.log(_temp[idx])
                // console.log(_temp[idx].toLowerCase().includes("chatbot:"))
                if ( (_temp[idx_2].toLowerCase().includes("chatbot:")) || (_temp[idx_2].toLowerCase().includes("coco:")) || (_temp[idx_2].toLowerCase().includes("alexa:"))) {
                    _html += "<div class=\"row balonbot p-2 m-0 position-relative\" data-is=\"" 
                    _html += chat_his[idx]["time"] 
                    _html += "\"><img class=\"balon-img mx-1 mt-3\" src=\"static/chatbot.png\"><a class=\"float-left mt-auto\">" 
                    _html += get_utter(_temp[idx_2])
                    _html += "</a></div>"
                } else {
                    _html += "<div class=\"row balonuser p-2 m-0 position-relative\" data-is=\"" 
                    _html += chat_his[idx]["time"] 
                    _html += "\"><a class=\"float-right ml-auto mt-auto\">" 
                    _html += get_utter(_temp[idx_2]) 
                    _html += "</a><img class=\"float-right balon-img mt-3 mx-1\" src=\""
                    _html += "/agent/"+cur_user+"/"+cur_agent_id+"/portrait"
                    _html += "\"></div>"
                }
            }
        }
        else{
            if ( (chat_his[idx]["chatbot"].toLowerCase().includes("chatbot:")) || (chat_his[idx]["chatbot"].toLowerCase().includes("coco:")) || (chat_his[idx]["chatbot"].toLowerCase().includes("alexa:"))) {
                _html += "<div class=\"row balonbot p-2 m-0 position-relative\" data-is=\"" 
                _html += chat_his[idx]["time"] 
                _html += "\"><img class=\"balon-img  mx-1 mt-3\" src=\"static/chatbot.png\"><a class=\"float-left mt-auto\">" 
                _html += get_utter(chat_his[idx]["chatbot"]) 
                _html += "</a></div>"
            } else {
                _html += "<div class=\"row balonuser p-2 m-0 position-relative\" data-is=\"" 
                _html += chat_his[idx]["time"] + "\"><a class=\"float-right ml-auto mt-auto\">" 
                _html += get_utter(chat_his[idx]["chatbot"]) 
                _html += "</a><img class=\"float-right balon-img mt-3 mx-1\" src=\""
                _html += "/agent/"+cur_user+"/"+cur_agent_id+"/portrait"
                _html += "\"></div>"
            }        
        }
    }
    document.getElementById("chat_history").innerHTML = _html
}

function draw_chat(date){
    // document.getElementById("chatbot_wordcloud_backup").classList.add("d-none")
    // fetch_chat_his(date);
    // words_freq = count_words_freq();
    // d3_draw_cloud(words_freq)
    try{
        document.getElementById("chatbot_wordcloud_backup").classList.add("d-none")
        chat_his = fetch_chat_his(date);
        words_freq = count_words_freq();
        d3_draw_cloud(words_freq);
        if (chat_display){
            document.getElementById("chatbot_wordcloud").classList.add("d-none");
        }
        show_chat_hist();
    }
    catch{
        document.getElementById("chatbot_wordcloud").classList.add("d-none")
        document.getElementById("chatbot_wordcloud_backup").classList.remove("d-none")
    }
}


//
// draw heartrate
// 
function draw_agent_heartrate(date){
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/heartrate/" + date,
        type: 'GET',
        async: true,
        dataType: 'json',
        success: function(res) {
            draw_agent_heartrate_charjs(res["data"])
        }
        });
}


//
// draw maps
// 

let map = null;
let data_layer=null;
const styles = {
    'icon' : new ol.style.Style({
        image: new ol.style.Icon({
            anchor: [0.5, 1],
            src: "/static/marker.png"
        })
    }),
    'route' : new ol.style.Style({
        renderer: (_coords, state) => {
            const ctx = state.context;
            const coords = _coords;
            ctx.lineWidth = 5;
            
            for (let i = 1; i < coords.length; i++) {
                const start = coords[i - 1];
                const end = coords[i];
                const grd = ctx.createLinearGradient(start[0], start[1], end[0], end[1]);
                grd.addColorStop(0, '#00ff00ff');
                grd.addColorStop(1, '#ff0000ff');
                ctx.strokeStyle = grd;
                ctx.beginPath();
                ctx.moveTo(start[0], start[1]);
                ctx.lineTo(end[0], end[1]);
                ctx.stroke();
            }
        }
    }),
}

function draw_map(date){
    loc_hist = fetch_location_hist(date)

    let icons = [];
    for (var idx in loc_hist) {
        let _temp = new ol.Feature({
                type : 'icon',
                geometry: new ol.geom.Point(ol.proj.fromLonLat([loc_hist[idx]['longitude'], loc_hist[idx]['latitude']])),
                name: loc_hist[idx]['location'],
                start_time: loc_hist[idx]['start_time'],
                end_time: loc_hist[idx]['end_time'], 
            });
        icons.push(_temp)
    }

    var polyline = new ol.geom.LineString(loc_hist.map(function(entry){
        return [entry['longitude'], entry['latitude']]
    }));
    let routeFeature = new ol.Feature({
        type: 'route',
        geometry: polyline.transform('EPSG:4326', 'EPSG:3857')
    });

    try{
        data_layer.getSource().clear()
        data_layer.getSource().addFeatures([...icons, routeFeature])
        data_layer.setStyle(function (feature) {
            return styles[feature.get('type')];
        })
        console.log("Map Features Update Successfully!")
    }
    catch{
        data_layer = new ol.layer.Vector({
            source: new ol.source.Vector({
                features: [...icons, routeFeature],
            }),
            style: function (feature) {
                return styles[feature.get('type')];
            },
        })
        map.addLayer(data_layer);
    }
    map.getView().setCenter(ol.proj.fromLonLat([loc_hist[Math.floor(idx / 2)]['longitude'], loc_hist[Math.floor(idx / 2)]['latitude']]));
    map.getView().setZoom(12);
}

function fetch_location_hist(date){
    let loc = {}
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/lochis/" + date,
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            if (Object.keys(res["data"]).length !== 0){
                loc = res["data"]
            }
        }
        });
    return loc;
}

function init_map(){
    const container = document.getElementById('ol-popup');
    const content = document.getElementById('ol-popup-content');
    const closer = document.getElementById('ol-popup-closer');

    closer.onclick = function () {
        overlay.setPosition(undefined);
        closer.blur();
        return false;
    };

    const overlay = new ol.Overlay({
        element: container,
        autoPan: {
            animation: {
                duration: 250,
            },
        },
    })

    map = new ol.Map({
        target: 'map',
        overlays: [overlay],
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM(),
            }),
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([0.0, 0.0]),
            zoom: 1,
        }),
    });

    map.on(['singleclick'], function (evt) {
        // console.log(evt.pixel)
        let feature = null;
        feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
            return feature;
        }, options={"hitTolerance":15});
        if (feature) {
            if (feature.get('type')=="icon"){
                const coordinates = feature.getGeometry().getCoordinates();
                content.innerHTML =
                    '<p>Location:</p><code>' + feature.get('name') + '</code><br>' +
                    '<p>Start:</p><code>' + feature.get('start_time') + '</code><br>' +
                    '<p>End:</p><code>' + feature.get('end_time') + '</code>'
                overlay.setPosition(coordinates);
            }
        }
    });

}

function show_location_hist(date){

    // document.getElementById("location_backup").classList.add("d-none");
    // init_map();
    // draw_map(date);
    try{
        document.getElementById("location_backup").classList.add("d-none");
        init_map();
        draw_map(date);
    }
    catch{
        document.getElementById("map").classList.add("d-none")
        document.getElementById("location_backup").classList.remove("d-none")
    }
}


//
// draw schedule
// 

function fetch_schedule(date){
    let schedule = {}
    $.ajax({
        url: "/agent/" + cur_user + "/" + cur_agent_id + "/schedule/" + date,
        type: 'GET',
        async: false,
        dataType: 'json',
        success: function(res) {
            if (Object.keys(res["data"]).length !== 0){
                schedule = res["data"]
            }
        },
        error: function(res){
            console.log(res)
        }
        });

    return schedule;
}

function fetch_all_schedule(){
    for (let idx in donedates){
        schedules[donedates[idx]] = fetch_schedule(donedates[idx])
    }
}

function init_schedule(){
    fetch_all_schedule();
    init_calendar(window.jQuery, schedules);
}
