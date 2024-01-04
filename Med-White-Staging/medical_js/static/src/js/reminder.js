odoo.define("medical_js.reminder",function(require){"use strict";var t=require("medical_js.BaseWidget"),
    i=require("web.core"),
    r=require("web.utils"),
    n=t.PopupWidget,d=t.screens,a=t.Chrome,s=t.gui,c=i.qweb,o=i._t;r.round_precision;var p=n.extend({template:"ReminderAddPopup",renderElement:function(){this._super();var e=this,t=this.options&&this.options.line;this.callback=this.options&&this.options.callback,_.isObject(t)&&_.each(_.keys(t),function(i){var r=t[i];"medical_order_id"==i&&(r=t[i]&&t[i][0]),e.$("[name='"+i+"']").val(r)})},click_confirm:function(){var e,t=this,i={},r=!1;if(_.each(this.$("input, textarea"),function(e){var t=$(e),n=t.parents("tr").children("th"),d=t.attr("name");n.children("span").remove(),i[d]=t.val(),t.val()||_.contains(["id","medical_order_id"],d)||(n.append("<span class='text-danger'> * </span>"),r=!0)}),r){this.chrome.error_toast("* Field values missing...!",o("Missing"));return}return i.medical_order_id=parseInt(i.medical_order_id),i.id?e=this._rpc({model:"app.reminder",method:"write",args:[[i.id],i]}):(delete i.id,e=this._rpc({model:"app.reminder",method:"create",args:[i]})),e.then(function(e){return t.chrome.success_toast("Reminder Updated Successfully."),t.callback&&t.callback(),t.gui.close_popup(),t.gui.current_screen.show(!0),e})}});s.define_popup({name:"reminder-add",widget:p});var m=d.ScreenWidget.extend({template:"ReminderListScreen",auto_back:!0,events:_.extend({},d.ScreenWidget.prototype.events,{"click .v-add-new":"edit_reminder","click .v-btn-edit":"edit_reminder","click .v-btn-done":"done_reminder","click .v-btn-cancel":"cancel_reminder"}),show:function(){this._super.apply(this,arguments),this.renderTable()},renderTable:function(){console.log("___ renderTable : ",this.medical.app_reminders);var e=this;this._rpc({model:"app.reminder",method:"search_read",domain:[["state","=","draft"]],fields:["id","name","todo_date","description","medical_order_id"]}).then(function(t){e.medical.app_reminders=t;var i=$(c.render("ReminderListTBody",{widget:e}));e.$("#ReminderListBody").html(""),i.appendTo(e.$("#ReminderListBody"))})},edit_reminder:function(e){e.stopPropagation();var t=$(e.currentTarget).parents("tr"),i=_.where(this.medical.app_reminders,{id:t.data().id});i=i&&i[0],this.medical.gui.show_popup("reminder-add",{title:"Add Reminder",line:i,callback:this.renderTable})},done_reminder:function(e){e.stopPropagation();var t=this,i=$(e.currentTarget).parents("tr"),r=_.where(this.medical.app_reminders,{id:i.data().id});r=r&&r[0],t.change_state(r.id,"done").then(function(){t.gui.current_screen.show(!0)})},cancel_reminder:function(e){e.stopPropagation();var t=this,i=$(e.currentTarget).parents("tr"),r=_.where(this.medical.app_reminders,{id:i.data().id});r=r&&r[0],t.change_state(r.id,"cancel").then(function(){t.gui.current_screen.show(!0)})},change_state:function(e,t){return this._rpc({model:"app.reminder",method:"write",args:[[e],{state:t}]})},update_state:function(e){return this._rpc({model:"app.reminder",method:"update_state",args:[[record.id],e],context:context})}});s.define_screen({name:"reminder-list",widget:m});var h=t.StatusWidget.extend({template:"ReminderIcon",start:function(){var e=this;this.$el.off("click"),this.$el.click(function(t){e.medical.gui.show_screen("reminder-list")})}});a.include({build_widgets:function(){this.widgets.push({name:"reminder_app",widget:h,append:".v-top-right"}),this.medical.app_reminders=[],this._super.apply(this,arguments)},update_reminder_count:function(e){$(".v-reminder-count").html(e)},fetch_reminder_count:function(){var e=[["todo_date","=",moment().format(this.date_server_format)],["state","!=","done"]],t=this;this._rpc({model:"app.reminder",method:"search_count",args:[e]},{timeout:6e3,shadow:!0}).then(function(e){t.update_reminder_count(e)})},execute_auto_refresh_pool:function(){this._super(),this.fetch_reminder_count()}})});