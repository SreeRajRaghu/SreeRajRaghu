odoo.define("medical_js.lab", function(require) {
    "use strict";
    var i = require("medical_js.BaseWidget"),
        t = require("web.core"),
        c = require("web.utils"),
        o = i.PopupWidget;
    i.screens,i.Chrome;var s=i.gui;t.qweb;var r=t._t;c.round_precision;var l=o.extend({template:"RefDoctorPopupWidget",events:_.extend({},o.prototype.events,{"click .v-create-new":"_onClickNew"}),_onClickNew:function(){var e=this;this.chrome.gui.show_popup("textinput2",{title:r("Create New Resource"),label1:r("Doctor"),label2:r("Clinic"),confirm:function(n,a){console.log("_ name : ",n,a),n&&(this.chrome.blockUI(),this._rpc({model:"medical.resource",method:"add_new_resource",args:[{name:n,clinic_name:a,resource_type:"free"}]}).then(function(n){e.chrome.unblockUI(),n&&(e.chrome.success_toast(r("Resource added Successfully.")),e.medical.db.all_resources.push(n),e.medical.get_order().set_resource_id(n.id),e.medical.resource_by_id[n.id]=n,e.medical.db.cal_resources.push(e.medical.toCalendarResource([n])),$("#span_order_resource").text(n.name))}))}})},show:function(){this._super.apply(this,arguments),this.$el.find("select").select2(),this.options.value&&this.$el.find("select").select2("val",this.options.value)},click_confirm:function(){var e=Number(this.$("select").val());this.gui.close_popup(),this.options.confirm&&this.options.confirm.call(this,e)}});s.define_popup({name:"popup-ref-doctor",widget:l});});