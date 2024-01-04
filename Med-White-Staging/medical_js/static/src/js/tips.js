odoo.define("medical_js.tips",function(require){"use strict";var t=require("medical_js.appointment"),
    e=require("medical_js.BaseWidget");require("medical_js.models");var n=require("web.core"),
    o=require("web.rpc"),
    p=e.PopupWidget,a=n._t,s=t.ActionButtonWidget.extend({template:"BtnAppointmentTips",button_click:function(){var i=this.medical.get_order(),t=i.get_tip();this.gui.show_popup("popup-tips",{title:a("Tips"),employee_id:t.employee_id,amount:t.amount,current_branch_id:i.get_clinic(),confirm:function(t,e){i.set_tip(t,e)}})}});t.define_action_button({name:"appointment_tips",widget:s,condition:function(){return console.log("___ config.allow_tips : ",this.medical.config.allow_tips),this.medical.config.allow_tips}});var c=p.extend({template:"AppointmentTipsPopupWidget",show:function(){this._super.apply(this,arguments),this.$el.find("select").select2(),this.options.employee_id&&this.$el.find("select").select2("val",this.options.employee_id),this.options.amount&&this.$("input").val(this.options.amount)},click_confirm:function(){var i=Number(this.$("select").val()),t=Number(this.$("input").val());this.gui.close_popup(),this.options.confirm&&this.options.confirm.call(this,i,t)}});e.gui.define_popup({name:"popup-tips",widget:c});var d=t.ActionButtonWidget.extend({template:"BtnPackageHistory",default_display:a("Package History"),button_click:function(){var i=this,t=this.medical.get_order().get_client();if(t)o.query({route:"/partner/packages",params:{partner_id:t.id}}).then(function(e){t.running_packages=e,i.gui.show_popup("popup-package-history",{title:i.default_display,running_packages:e,partner_id:t.id})});else{i.gui.show_popup("error",a("Please select the customer !"));return}}});t.define_action_button({name:"btn_package_history",widget:d,condition:function(){return console.log("___ config.allow_package : ",this.medical.config.allow_package),this.medical.config.allow_package}});var r=p.extend({template:"PopupPackageHistory",events:_.extend({},p.prototype.events,{"click .v-add-package":"click_confirm"}),show:function(){this._super.apply(this,arguments),this.running_packages=this.options&&this.options.running_packages,this.partner_id=this.options.partner_id},add_new_pkg_line:function(i,t){var e=this.medical.db.product_by_id[t.product_id];if(e){i.add_product(e,{quantity:parseFloat(1),price:0,discount:0});var n=i.get_last_orderline();n.related_pkg_id=t.id,n.duration=t.duration,i.add_orderline(n)}},click_confirm:function(i){var t=$(i.currentTarget).data("pkgid"),e=_.findWhere(this.running_packages,{id:t}),n=this.medical.get_order(),o=n&&n.not_added_packages(this.running_packages)||[];o.length&&_.findWhere(o,{id:e.id})&&this.add_new_pkg_line(n,e),this._super.apply(this,arguments)}});e.gui.define_popup({name:"popup-package-history",widget:r})});