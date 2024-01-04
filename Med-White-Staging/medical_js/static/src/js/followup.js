odoo.define("medical_js.folloup",function(require){
    "use strict";
    require("medical_js.appointment");
    var a=require("medical_js.BaseWidget");
    require("medical_js.models");
    var e=require("web.core"),
    i=a.screens,n=a.gui;e.qweb;var o=e._t,s=a.PopupWidget.extend({template:"MessagePost",click_confirm:function(){var t=this.$("input").val(),a=this.$("textarea").val();if(_.isEmpty(t)||_.isEmpty(a)){this.chrome.error_toast(_("Both fields are required."));return}this.gui.close_popup(),this.options.confirm&&this.options.confirm.call(this,t,a)}});n.define_popup({name:"post-message",widget:s});var l=i.ScreenWidget.extend({template:"FollowupListScreenWidget",events:_.extend({},a.PopupWidget.prototype.events,{"click .back":"click_back","click .btn-refresh":"refresh_data","change .search-states":"_onChangeState","change .search-action":"_onChangeAction"}),click_back:function(){this.gui.show_screen("calendar")},refresh_data:function(){return this.reload_appointments()},init:function(t,a){this._super(t,a),this.weekdays=moment.weekdays},show:function(){this._super.apply(this,arguments);var t=this;this.refresh_data().then(function(){t.bind_events()})},bind_events:function(){var t=this,a=this.$("table.appointment-table tbody"),e=function(a,e,i){var n={state:e};i&&_.extend(n,i),t._rpc({model:"medical.order",method:"write",args:[a,n]}).then(function(){t.chrome.success_toast(o("Appointment Status Updated !")),t.refresh_data()})},i=function(a,i){t.gui.show_popup("ask-action-note",{title:o(i),mode:i,note:a[10],last_action_id:a[11],confirm:function(){var n=this.$el.find(".action").val(),o=this.$el.find(".note").val();e(a[0],i,{last_action_id:n,note:o,last_action_emp_id:t.medical.get_cashier().id})}})};a.on("click",".action-confirm",function(a){a.stopPropagation();var i=t.table_followup_list.row($(this).parents("tr")).data();e(i[0],"confirmed")}),a.on("click",".action-cancel",function(a){a.stopPropagation();var i=t.table_followup_list.row($(this).parents("tr")).data();e(i[0],"cancel")}),a.on("click",".action-noshow",function(a){a.stopPropagation();var e=t.table_followup_list.row($(this).parents("tr")).data();i(e,"no_show")}),a.on("click",".action-noanswer",function(a){a.stopPropagation();var e=t.table_followup_list.row($(this).parents("tr")).data();i(e,"no_answer")}),a.on("click",".action-email",function(a){a.stopPropagation();var e=t.table_followup_list.row($(this).parents("tr")).data(),i=t.events_data_by_key[e[0]].email||"";if(!i){t.chrome.error_toast(o("Please update email address in "+t.label_list.partner_id));return}t.gui.show_popup("post-message",{title:o("Email To"),msg_to:i,confirm:function(a,i){t._rpc({model:"medical.order",method:"message_post",args:[e[0]],kwargs:{body:i,email_to:a,subtype:"mail.mt_comment"}}).then(function(){t.chrome.success_toast(o("Email Sent !"))})}})}),a.on("click",".action-sms",function(a){a.stopPropagation(),t.table_followup_list.row($(this).parents("tr")).data(),t.chrome.info_toast(o("Please configure SMS Provider !"))}),a.on("click",".action-note",function(a){a.stopPropagation();var e=t.table_followup_list.row($(this).parents("tr")).data(),i=t.events_data_by_key[e[0]];t.gui.show_popup("textarea",{title:o("Appointment Note !"),value:i.note||"",confirm:function(a){t._rpc({model:"medical.order",method:"write",args:[[e[0]],{note:a}]}).then(function(){t.chrome.success_toast(o("Appointment Note Updated !")),t.refresh_data()})}})})},hide:function(){this.destroy_table(),this._super.apply(this,arguments)},destroy_table:function(){this.$("table.appointment-table").dataTable({bDestroy:!0}).fnDestroy(),this.$("table.appointment-table").html("")},reload_appointments:function(){var t=this,a=[["start_time",">",moment.utc().subtract(2,"day").format(this.date_server_format)+" 00:00:00"],],e=t.medical.current_clinic;return _.isEmpty(e)||a.push(["clinic_id","=",e.id]),this._rpc({model:"medical.order",method:"search_read",domain:a,fields:["name","start_time","end_time","state","resource_id","partner_id","mobile","phone","email","note","file_no","file_no2","total_duration","clinic_id","last_action_id","last_action_emp_id","last_action_dt"]}).then(function(a){t.renderTable(a)})},renderTable:function(t){var a=this;this.dataSet=[],this.events_data_by_key={};var e=moment().startOf("day"),i=0,n=0,o=0,s=0,l=a.medical.chrome.state_display;_.each(t,function(t){a.events_data_by_key[t.id]=t;var r=moment(a.toUserTZ(t.start_time)),c=moment(a.toUserTZ(t.last_action_dt)),d=r.clone().startOf("day").diff(e,"days"),p="!TODAY";d>1?(p="!FUTURE",o+=1):1==d?(p="!TOMORROW",s+=1):d<0?(p="!OLD",n+=1):i+=1;var f=_.filter([t.mobile||"",t.phone||""],function(t){return!_.isEmpty(t)});t=[t.id,p,t.name,t.clinic_id&&(t.clinic_id[1]||""),a.medical.get_file_no(t),t.partner_id&&(t.partner_id[1]||"")+'\n<span class="fa fa-phone" /> '+f.join(", "),r.format(a.datetime_format),l[t.state],t.resource_id&&t.resource_id[1]||"",t.total_duration&&'<span class="fa fa-clock-o" /> '+a.floatToHour(t.total_duration)||"",t.note||"",t.last_action_id&&t.last_action_id[1]||"",(t.last_action_emp_id&&t.last_action_emp_id[1]||"")+"\n"+c.format(a.datetime_format),"","","",],a.dataSet.push(t)}),this.total_today=i,this.total_old=n,this.total_future=o,this.total_tomorrow=s,this.table_followup_list=this.$("table.appointment-table").DataTable({data:this.dataSet,responsive:!0,destroy:!0,columns:[{title:"ID"},{title:"Filter"},{title:"Ref"},{title:"Branch"},{title:"File Number"},{title:a.label_list.partner_id},{title:"Date"},{title:"State"},{title:"Resource"},{title:"Duration"},{title:"Note",orderable:!1},{title:"Last Action",orderable:!1},{title:"Last Action Employee",orderable:!1,searchable:!1},{title:"Action",orderable:!1,searchable:!1},{title:"FollowUp",orderable:!1,searchable:!1},{title:"Call Note",orderable:!1,searchable:!1},],columnDefs:[{visible:!1,targets:0,searchable:!1},{visible:!1,targets:1},{targets:-3,data:null,defaultContent:`
                        <div class='btn btn-sm btn-success action-confirm'><span class='fa fa-thumbs-up'/> Confirm</div>
                        <div class='btn btn-sm btn-danger action-cancel'><span class='fa fa-thumbs-down'/> Cancel</div> <br/>
                        <div class='btn btn-sm btn-info action-noshow'><span class='fa fa-eye-slash'/> No Show</div>
                        <div class='btn btn-sm btn-info action-noanswer'><span class='fa fa-phone'/> No Answer</div>`},{targets:-2,data:null,defaultContent:`
                        <div class='btn btn-sm btn-info action-email'><span class='fa fa-envelope'/> Email</div>
                        <div class='btn btn-sm btn-warning action-sms'><span class='fa fa-sms'/> SMS</div>`},{targets:-1,data:null,defaultContent:`
                    <div class='btn btn-sm btn-success action-note'><span class='fa fa-sticky-note-o'/> Note</div>`}],dom:"Bfrtip",buttons:[{text:'<i class="fa text-dark"> Old <span class="badge badge-pill badge-secondary"> '+this.total_old+"</span></i>",action:function(t,a,e,i){a.data().search("!OLD").draw()}},{text:'<i class="fa text-dark"> Today <span class="badge badge-pill badge-secondary"> '+this.total_today+"</span></i>",action:function(t,a,e,i){a.data().search("!TODAY").draw()}},{text:'<i class="fa text-dark"> Tomorrow <span class="badge badge-pill badge-secondary"> '+this.total_tomorrow+"</span></i>",action:function(t,a,e,i){a.data().search("!TOMORROW").draw()}},{text:'<i class="fa text-dark"> Future <span class="badge badge-pill badge-secondary"> '+this.total_future+"</span></i>",action:function(t,a,e,i){a.data().search("!FUTURE").draw()}},{text:'<i class="fa"> ALL <span class="badge badge-pill badge-secondary"> '+(this.total_future+this.total_today+this.total_old)+"</span></i>",action:function(t,a,e,i){a.data().search("").draw()}}]})},_onChangeState:function(t){if(this.table_followup_list){var a=parseInt(t.currentTarget.value),e=this.medical.db.states_by_id[a].name;this.table_followup_list.data().search(e).draw()}},_onChangeAction:function(t){if(this.table_followup_list){var a=t.currentTarget.value,e=this.medical.db.last_action_by_id[a].name;this.table_followup_list.data().search(e).draw()}}});n.define_screen({name:"followup_list",widget:l});var r=a.MenuButtonWidget.extend({template:"BtnFollowUpScreen",button_click:function(){this.gui.show_screen("followup_list")}});a.define_menu_button({name:"btn_show_followup",widget:r,condition:function(){return this.medical.config.enable_followup}},{after:"btn_show_patient"})});