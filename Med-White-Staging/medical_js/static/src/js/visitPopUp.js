odoo.define("medical_js.visitpopup", function(require) {
    "use strict";
    var i = require("medical_js.BaseWidget"),
        t = require("web.core"),
        c = require("web.utils"),
        o = i.PopupWidget;
    i.screens, i.Chrome;
    var s = i.gui;
    t.qweb;
    var r = t._t;
    c.round_precision;
    var l=o.extend({template:"RefVisitPopupWidget",events:_.extend({},o.prototype.events,{}),show:function(){this._super.apply(this,arguments),this.$el.find("select").select2(),this.options.value&&this.$el.find("select").select2("val",this.options.value)},click_confirm:function(){var e=Number(this.$("select").val());this.gui.close_popup(),this.options.confirm&&this.options.confirm.call(this,e)}});s.define_popup({name:"popup-ref-visit",widget:l});
});