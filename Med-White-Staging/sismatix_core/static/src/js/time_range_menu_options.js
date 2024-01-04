odoo.define('SismatixCore.TimeRangeMenuOptions', function (require) {
    "use strict";
    var core = require('web.core');
    var _lt = core._lt;
    var TimeRangeMenuOptions = require('web.TimeRangeMenuOptions');
    var today_index = _.findIndex(TimeRangeMenuOptions.PeriodOptions, {"optionId": "today"});
    TimeRangeMenuOptions.PeriodOptions.splice(today_index + 1, 0, {description: _lt('Tomorrow'), optionId: 'tomorrow', groupId: 2});
    _.extend({}, {
        PeriodOptions: TimeRangeMenuOptions.PeriodOptions,
        ComparisonOptions: TimeRangeMenuOptions.ComparisonOptions,
    });
    return {
        PeriodOptions: TimeRangeMenuOptions.PeriodOptions,
        ComparisonOptions: TimeRangeMenuOptions.ComparisonOptions,
    };
});
