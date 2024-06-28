
const catelog = [
    "Personal care activities",
    "Eating and drinking",
    "Household activities",
    "Purchasing goods and services",
    "Consumer goods purchases",
    "Professional and personal care services",
    "Caring for and helping others",
    "Working and work-related activities",
    "Educational activities",
    "Organizational, civic, and religious activities",
    "Leisure and sports",
    "Telephone calls, mail, and e-mail",
    "Other activities, not elsewhere classified",
]

const colors_rgb = [
    'rgb(23,75,205)', 
    'rgb(195,230,222)', 
    'rgb(62,95,23)', 
    'rgb(148,50,207)', 
    'rgb(88,116,44)', 
    'rgb(191,28,181)', 
    'rgb(206,222,159)', 
    'rgb(128,112,41)', 
    'rgb(51,56,161)', 
    'rgb(135,138,236)', 
    'rgb(49,9,24)', 
    'rgb(170,103,182)', 
    'rgb(209,171,151)', 
    'rgb(234,77,198)', 
    'rgb(154,24,174)'
]

const colors_rgba = [
    'rgba(100,224,188,0.78)', 
    'rgba(27,160,141,0.21)', 
    'rgba(221,230,134,0.33)', 
    'rgba(71,212,99,0.08)', 
    'rgba(170,58,96,0.44)', 
    'rgba(40,119,63,0.48)', 
    'rgba(182,177,169,0.45)', 
    'rgba(50,197,218,0.11)', 
    'rgba(163,101,126,0.20)', 
    'rgba(192,240,119,0.81)', 
    'rgba(167,5,28,0.08)', 
    'rgba(39,222,98,0.05)', 
    'rgba(255,139,71,0.48)', 
    'rgba(114,54,176,0.19)', 
    'rgba(116,34,92,0.17)'
]

let act_dist_line = null;
let act_dist = null;
let heartrate_line = null;
let heart_rate_activity = null;

function avg(array) {
    var total = 0;
    var count = 0;

    array.forEach(function(item, index) {
        total += item;
        count++;
    });

    return total / count;
}

function draw_stat() {
    draw_act_dist_line()
    draw_act_dist("12:00")

    draw_heart_rate_line()
    draw_heart_rate_activity("12:00")
}

function draw_act_dist_line() {
    if (act_dist_line) {act_dist_line.destroy();}
    const _act_dist_line = document.getElementById("daily_activity").getContext('2d');
    let count_max = 0;
    
    let time_labels = [];
    let catelog_datasets = {};
    let datasets = [];

    for (var i=0;i<catelog.length;i++){
        // console.log(catelog[i])
        catelog_datasets[catelog[i]] = {
            label: catelog[i],
            data: [],
            borderColor: colors_rgb[i],
            borderWidth: "2",
            backgroundColor: 'transparent', 
            pointBackgroundColor: colors_rgb[i]
        }
    }

    for (const time in act_stat) {
        if (count_max==0){
            count_max = act_stat[time].length
        }

        time_labels.push(time)

        let _temp_act = {}
        for (const key of catelog) {_temp_act[key] = 0;}

        for (const agent_id in act_stat[time]){_temp_act[act_stat[time][agent_id]] += 1;}
        
        for (const key of catelog){catelog_datasets[key].data.push(_temp_act[key])}
    }
    for (const key of catelog){datasets.push(catelog_datasets[key])}
        
    _act_dist_line.height = 100;
    act_dist_line = new Chart(_act_dist_line, {
        type: 'line',
        data: {
            defaultFontFamily: 'Poppins',
            labels: time_labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            onClick: function(Event){
                const points = this.getElementAtEvent(Event);
                if (points.length) {
                    const firstPoint = points[0];
                    draw_act_dist(this.data.labels[firstPoint._index])
                    draw_heart_rate_activity(this.data.labels[firstPoint._index])
                }
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true, 
                        max: count_max,
                        min: 0, 
                        stepSize: Math.floor(count_max/5), 
                        padding: 10
                    }
                }],
                xAxes: [{ 
                    ticks: {
                        padding: 5
                    }
                }]
            }
        }
    });
}

function draw_act_dist(time) {
    if (act_dist) {act_dist.destroy();}
    const _act_dist = document.getElementById("activity_bar").getContext('2d');
    _act_dist.height = 100;

    let _temp_act = {}
    let data = []
    let labels = []
    for (const key of catelog) {_temp_act[key] = [];}
    for (const agent_id in act_stat[time]){_temp_act[act_stat[time][agent_id]].push(agent_id);}
    for (const key of catelog) {data.push(_temp_act[key].length)}
    for (var key of catelog){
        let _agents = "\n"
        for (const agent of _temp_act[key]){
            _agents += agent;
            _agents += "\n";
        }
        labels.push(_agents)
    }

    act_dist = new Chart(_act_dist, {
        type: 'bar',
        data: {
            defaultFontFamily: 'Poppins',
            labels: catelog,
            datasets: [
                {
                    labels: labels,
                    data: data,
                    borderColor: 'rgba(26, 51, 213, 0.8)',
                    borderWidth: "0",
                    backgroundColor: 'rgba(26, 51, 213, 0.8)'
                }
            ]
        },
        options: {
            title: {
                display: true,
                text: time
            },
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        var label = 'Count : ';
                        label += Math.round(tooltipItem.yLabel * 100) / 100;
                        return label;
                    },
                    footer: function(tooltipItems, data) {
                        var label = "Agents:"
                        label += data.datasets[tooltipItems[0].datasetIndex].labels[tooltipItems[0].index] || '';
                        return label;
                    },
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }],
                xAxes: [{
                    barPercentage: 0.8
                }]
            }
        }
    });
}

function draw_heart_rate_line() {

    if (heartrate_line) {heartrate_line.destroy();}
    const _heartrate_line = document.getElementById("heartrate").getContext('2d');
    
    let time_labels = [];
    let datasets = [
        {
            label: "Mean",
            type: "line",
            backgroundColor: "rgb(75, 192, 192, 0.5)",
            borderColor: "rgb(75, 192, 192)",
            hoverBorderColor: "rgb(175, 192, 192)",
            fill: false,
            tension: 0,
            data: [],
        },
        {
            label: "Max",
            type: "line",
            backgroundColor: "rgb(75, 192, 255, 0.5)",
            borderColor: "transparent",
            pointRadius: 0,
            fill: 0,
            tension: 0,
            data: [],
        },
        {
            label: "Min",
            type: "line",
            backgroundColor: "rgb(75, 192, 255, 0.5)",
            borderColor: "transparent",
            pointRadius: 0,
            fill: 0,
            tension: 0,
            data: [],
        }
    ]

    for (const time in hr_stat) {

        time_labels.push(time)

        let _temp_hr = []

        for (const agent_id in hr_stat[time]){_temp_hr.push(parseInt([hr_stat[time][agent_id]]));}
        datasets[0].data.push(avg(_temp_hr))
        datasets[1].data.push(Math.max(..._temp_hr))
        datasets[2].data.push(Math.min(..._temp_hr))
    }
    
    _heartrate_line.height = 100;

    heartrate_line = new Chart(_heartrate_line, {
        type: 'line',
        data: {
            defaultFontFamily: 'Poppins',
            labels: time_labels,
            datasets: datasets
        },
        options: {
            onClick: function(Event){
                const points = this.getElementAtEvent(Event);
                if (points.length) {
                    const firstPoint = points[0];
                    draw_act_dist(this.data.labels[firstPoint._index])
                    draw_heart_rate_activity(this.data.labels[firstPoint._index])
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true, 
                        max: 120, 
                        min: 30, 
                        stepSize: 20, 
                        padding: 10
                    }
                }],
                xAxes: [{ 
                    ticks: {
                        padding: 5
                    }
                }]
            }
        }
    });
}

function draw_heart_rate_activity(time) {
    if (heart_rate_activity) {heart_rate_activity.destroy();}

    const _heart_rate_activity = document.getElementById("h-a-sankey").getContext('2d');

    const _cur_time_hr = hr_stat[time];
    const _cur_time_act = act_stat[time];
    
    let catelog_datasets = {};
    let datasets = [];

    for (var i=0;i<catelog.length;i++){
        // console.log(catelog[i])
        catelog_datasets[catelog[i]] = {
            label: catelog[i],
            data: [0,0,0,0],
            backgroundColor: colors_rgb[i],
            agents : ["","","",""]
        }
    }

    for (const agent_id in _cur_time_hr) {
        if (_cur_time_hr[agent_id] < 60){
            catelog_datasets[_cur_time_act[agent_id]].data[0] += 1;
            catelog_datasets[_cur_time_act[agent_id]].agents[0] += agent_id +"\n"
        }
        else if (_cur_time_hr[agent_id] < 80 && _cur_time_hr[agent_id] >= 60){
            catelog_datasets[_cur_time_act[agent_id]].data[1] += 1;
            catelog_datasets[_cur_time_act[agent_id]].agents[1] += agent_id +"\n"
        }
        else if (_cur_time_hr[agent_id] < 100 && _cur_time_hr[agent_id] >= 80){
            catelog_datasets[_cur_time_act[agent_id]].data[2] += 1;
            catelog_datasets[_cur_time_act[agent_id]].agents[2] += agent_id +"\n"
        }
        else{
            catelog_datasets[_cur_time_act[agent_id]].data[3] += 1;
            catelog_datasets[_cur_time_act[agent_id]].agents[3] += agent_id +"\n"
        }
    }
    for (const key of catelog){datasets.push(catelog_datasets[key])}

    _heart_rate_activity.height = 100;

    heart_rate_activity = new Chart(_heart_rate_activity, {
        type: 'bar',
        data: {
            defaultFontFamily: 'Poppins',
            labels: ["<60","60-80", "80-100", ">=100"],
            datasets: datasets
        },
        options: {
            title: {
                display: true,
                text: time
            },
            tooltips: {
                callbacks: {
                    footer: function(tooltipItems, data) {
                        var label = 'Agents:\n';
                        label += data.datasets[tooltipItems[0].datasetIndex].agents[tooltipItems[0].index]
                        return label;
                    },
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            scales: {
                yAxes: [{
                    stacked: true,
                    ticks: {
                        beginAtZero: true
                    }
                }],
                xAxes: [{
                    stacked: true,
                    barPercentage: 1.0
                }]
            }
        }
    });

}

let agent_heartrate = null;
function draw_agent_heartrate_charjs(data) {
    if (agent_heartrate) {agent_heartrate.destroy();}
    const _agent_heartrate = document.getElementById("agent-heartrate").getContext('2d');
    
    _agent_heartrate.height = 100;

    labels = []
    heartrate = []
    for (var idx in data){
        labels.push(data[idx]["time"].split(" ")[1])
        heartrate.push(data[idx]["heartrate"])
    }

    agent_heartrate = new Chart(_agent_heartrate, {
        type: 'line',
        data: {
            defaultFontFamily: 'Poppins',
            labels: labels,
            datasets: [
                {
                    label: "Heartrate",
                    type: "line",
                    backgroundColor: "rgb(75, 192, 192, 0.5)",
                    borderColor: "rgb(75, 192, 192)",
                    hoverBorderColor: "rgb(175, 192, 192)",
                    fill: false,
                    tension: 0,
                    data: heartrate,
                  },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            tooltips: {
                enabled : false,
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true, 
                        max: 140, 
                        min: 30, 
                        stepSize: 20, 
                        padding: 10
                    }
                }],
                xAxes: [{ 
                    ticks: {
                        padding: 5
                    }
                }]
            }
        }
    });
}

let agent_steps = null;
function draw_agent_steps_charjs(data) {
    if (agent_steps) {agent_steps.destroy();}
    const _agent_steps = document.getElementById("agent-steps").getContext('2d');

    labels = [];
    steps = [];
    var _cur_h = 0;
    var _cur_steps = 0;
    for (var idx in data){
        if (parseInt(data[idx]["time"].split(" ")[1])==_cur_h){
            _cur_steps = _cur_steps + parseInt(data[idx]["steps"]);
        }
        else{
            labels.push(_cur_h.toString() + ":00");
            steps.push(_cur_steps);
            _cur_h = _cur_h + 1;
            _cur_steps = 0;
        }
    }

    agent_steps = new Chart(_agent_steps, {
        type: 'bar',
        data: {
            defaultFontFamily: 'Poppins',
            labels: labels,
            datasets: [
                {
                    labels: labels,
                    data: steps,
                    borderColor: 'rgba(26, 51, 213, 0.8)',
                    borderWidth: "0",
                    backgroundColor: 'rgba(26, 51, 213, 0.8)'
                }
            ]
        },
        options: {
            tooltips: {
                callbacks: {
                    title :function(tooltipItems, data) {
                        var label = labels[tooltipItems[0].index];
                        label += "-"
                        try{
                            label += labels[tooltipItems[0].index+1] || '';
                        } catch{
                            label += "0:00";
                        }
                        return label;
                    },
                    label: function(tooltipItem, data) {
                        var label = 'Step Count : ';
                        label += data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index] || '';
                        return label;
                    },
                    footer: function(tooltipItems, data) {
                        return "";
                    },
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            legend: false, 
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }],
                xAxes: [{
                    barPercentage: 1.0,
                    type: 'time',
                    time: {
                      parser: 'HH',
                      unit: 'hour',
                      displayFormats: {
                        hour: 'Ha'
                      },
                      tooltipFormat: 'Ha'
                    },
                    gridLines: {
                      offsetGridLines: true
                    },
                    ticks: {
                      min: moment(labels[0], 'HH').subtract(1, 'hours'),
                    }
                  }]
            }
        }
    });
}
