odoo.define('SismatixCore.Domain', function (require) {
"use strict";

var domain = require('web.Domain');

domain.include({
    constructDomain: function (fieldName, period, type, forTooltip, comparisonPeriod) {
        var res_domain = this._super.apply(this, arguments);
        if (period === "tomorrow") {
            res_domain = "['&'," +
                "('" + fieldName + "', '>', " +
                "(datetime.datetime.combine(context_today() + relativedelta(days=1), datetime.time(0,0,0)).to_utc()).strftime('%Y-%m-%d'))," +
                "('" + fieldName + "', '<=', " +
                "(datetime.datetime.combine(context_today() + relativedelta(days=2), datetime.time(0,0,0)).to_utc()).strftime('%Y-%m-%d'))" +
                "]";
        }
        return res_domain;
    },
});

});
