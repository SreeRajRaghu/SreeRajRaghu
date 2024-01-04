odoo.define("medical_js.uninvoiced_orders",function(require){"use strict";var t=require("medical_js.appointment"),
    i=require("medical_js.BaseWidget");require("medical_js.models"),
    require("web.core")._t;var n=i.PopupWidget.extend({template:"UnInvoicedOrderPopupWidget",events:_.extend({},i.PopupWidget.prototype.events,{"click .cancel":"click_cancel"})});i.gui.define_popup({name:"appointment-history-popup",widget:n});var o=t.ActionButtonWidget.extend({template:"BtnUnInvoicedAppointments",button_click:function(){var e=this,t=this.medical.get_order(),i=t.get_client(),n=[];t.id&&n.push(t.id),this._rpc({model:"medical.order",method:"get_uninvoiced_orders",args:[i.id,n]}).then(function(t){e.gui.show_popup("appointment-history-popup",{order_history:t})})}});t.define_action_button({name:"btn_uninvoiced_order",widget:o,condition:function(){return this.medical.config.allow_multi_appointments}})});