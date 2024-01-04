odoo.define('SismatixCore.FilterMenu', function (require) {
    "use strict";
    var FiltersMenu = require('web.FiltersMenu');
    var time = require('web.time');
    FiltersMenu.include({
        _renderMenuItems: function () {
            var dateFormat = time.getLangDateFormat();
            // Inherited for : Add Tooltip On Tomorrow
            this._super.apply(this, arguments);
            var option = this.$('.o_filters_menu .o_item_option[data-option_id="tomorrow"]');
            $(option).tooltip("dispose").tooltip({
                delay: {show: 500, hide: 0},
                title: function () {
                    return moment().add(1, 'days').format(dateFormat);
                }
            });
        },
    })
});
