function create_calendar(e) {
    "use strict";
    var t = function() {
        this.$body = e("body"), this.$modal = e("#event-modal"), this.$event = "#external-events div.external-event", this.$calendar = e("#calendar"), this.$calendarObj = null
    };
    t.prototype.onEventClick = function(t, n, a) {
        var o = this,
            i = e("<form></form>");
        i.append("<label>Change event name</label>"), i.append("<div class='input-group'><input class='form-control' type=text value='" + t.title + "' /><span class='input-group-btn'><button type='submit' class='btn btn-success waves-effect waves-light'><i class='fa fa-check'></i> Save</button></span></div>"), o.$modal.modal({
            backdrop: "static"
        }), o.$modal.find(".delete-event").show().end().find(".save-event").hide().end().find(".modal-body").empty().prepend(i).end().find(".delete-event").unbind("click").on("click", function() {
            o.$calendarObj.fullCalendar("removeEvents", function(e) {
                return e._id == t._id
            }), o.$modal.modal("hide")
        }), o.$modal.find("form").on("submit", function() {
            return t.title = i.find("input[type=text]").val(), o.$calendarObj.fullCalendar("updateEvent", t), o.$modal.modal("hide"), !1
        })
    }, 
    t.prototype.onSelect = function(t, n, a) {
        var o = this;
        o.$modal.modal({
            backdrop: "static"
        });
        var i = e("<form></form>");
        i.append("<div class='row'></div>"), i.find(".row").append("<div class='col-md-6'><div class='form-group'><label class='control-label'>Event Name</label><input class='form-control' placeholder='Insert Event Name' type='text' name='title'/></div></div>").append("<div class='col-md-6'><div class='form-group'><label class='control-label'>Category</label><select class='form-control' name='category'></select></div></div>").find("select[name='category']").append("<option value='bg-danger'>Danger</option>").append("<option value='bg-success'>Success</option>").append("<option value='bg-dark'>Dark</option>").append("<option value='bg-primary'>Primary</option>").append("<option value='bg-pink'>Pink</option>").append("<option value='bg-info'>Info</option>").append("<option value='bg-warning'>Warning</option></div></div>"), o.$modal.find(".delete-event").hide().end().find(".save-event").show().end().find(".modal-body").empty().prepend(i).end().find(".save-event").unbind("click").on("click", function() {
            i.submit()
        }), o.$modal.find("form").on("submit", function() {
            var e = i.find("input[name='title']").val(),
                a = (i.find("input[name='beginning']").val(), i.find("input[name='ending']").val(), i.find("select[name='category'] option:checked").val());
            return null !== e && 0 != e.length ? (o.$calendarObj.fullCalendar("renderEvent", {
                title: e,
                start: t,
                end: n,
                allDay: !1,
                className: a
            }, !0), o.$modal.modal("hide")) : alert("You have to give a title to your event"), !1
        }), o.$calendarObj.fullCalendar("unselect")
    }, 
    t.prototype.init = function() {
        var t = new Date,
            n = (t.getDate(), t.getMonth(), t.getFullYear(), new Date(e.now())),
            a = [
                // event list !!!
            ],
            o = this;
        o.$calendarObj = o.$calendar.fullCalendar({
            slotDuration: "01:00:00",
            minTime: "00:00:00",
            maxTime: "23:59:00",
            defaultView: "agendaWeek",
            handleWindowResize: !0,
            height: 'parent',
            header: {
                left: "prev,next",
                center: "title",
            },
            // events: a,
            editable: !0,
            // eventLimit: !0,
            selectable: !0,
            select: function(e, t, n) {
                o.onSelect(e, t, n)
            },
            eventClick: function(e, t, n) {
                o.onEventClick(e, t, n)
            }
        })
    }, e.CalendarApp = new t, e.CalendarApp.Constructor = t
};
function init(e) {
    "use strict";
    e.CalendarApp.init()
};
function init_calendar(e) {
    create_calendar(e)
    init(e)
};