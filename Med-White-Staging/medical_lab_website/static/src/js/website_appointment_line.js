odoo.define('medical_lab_website.website_appointment_line', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var core = require('web.core');
    var session = require('web.session');
    var utils = require('web.utils');
    var rpc = require('web.rpc')
    var publicWidget = require('web.public.widget');
    var _t = core._t;
    var QWeb = core.qweb;

    var wysiwygLoader = require('web_editor.loader');


    sAnimations.registry.appointment = sAnimations.Class.extend({
        selector: '#appointment',
        xmlDependencies: ['/medical_lab_website/static/src/xml/website_appointment_line.xml'],
        read_events: {
            'click .add_new_line': '_onClickAddNewLine',
            'click .remove_line': '_onRemoveLine',
            'click .save': '_onClickSave',
            'click .filter-button': '_filter_button',
            'click .gallery_product':'_onClickProductLine',
            // 'click .gallery_product':'_onClickProductLine',
            'keyup .product_search': '_product_search',
            'click .card-header': function(ev){
                ev.stopPropagation();
                $(ev.currentTarget).next().slideToggle();
            },
        },

        _product_search: function(ev){
            ev.stopPropagation();
            var value = $(ev.currentTarget).val().toLowerCase();
            $('.filter').filter(function() {
              $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
            });
        },

        _filter_button: function(ev){
            ev.stopPropagation();
            var value = $(ev.currentTarget).data('filter');
            if(value == 1)
            {
                $('.filter').show('1000');
            }
            else
            {
                $(".filter").not('.'+value).hide('3000');
                $('.filter').filter('.'+value).show('3000');
            }
        },

        init: function() {
            var def = this._super.apply(this, arguments);

            this.products = [];
            this.product_by_id = {};
            this.orders_data = {
                'name': 0,
                'phone': false,
                'civil_id': false,
                'requested_by': false,
                'mobile': false,
                'orderlines': {}
            };

            return def;
        },

        willStart: function() {
            var prodDef = this._loadProduct();
            return $.when(this._super.apply(this, arguments), prodDef);
        },

        start: function() {
            var self = this;
            var def = this._super.apply(this, arguments);
            return def;
        },

        start: function () {
        var defs = [this._super.apply(this, arguments)];
        var self = this;
        var job_id = parseInt(this.$el.find('.order_id').val());

        var toolbar = [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['history', ['undo', 'redo']],
        ];

        _.each(this.$el.find('textarea.o_wysiwyg_loader'), function (textarea) {
            var $textarea = $(textarea),
            options = {
                    height: 200,
                    minHeight: 80,
                    toolbar: toolbar,
            };
            var loadProm = wysiwygLoader.load(self, $textarea[0], options).then(wysiwyg => {
                self._wysiwyg = wysiwyg;
            });
            defs.push(loadProm);

        });

        return Promise.all(defs);
    },





         _onClickProductLine: function(ev) {
            ev.stopPropagation();

            var self = this;
            var product = $(ev.currentTarget).data('product'),
                product_name = $(ev.target).find('product').text();
            var line_data = {
                'product_id': parseInt(product),
                'name': '',
            };
            console.log('_ $(ev.target) : ', $(ev.target));
            // $(ev.currentTarget).hide('3000');
            var $cur_row = $('.add_new_line_tr');
            var $newLine = this._renderLine(line_data)
            // 
            $newLine.insertBefore($cur_row);
            $newLine.find('select').select2();
            // this.do_notify(_t('Service Added...'));
            this.displayNotification({
                type: 'success',
                title: _t('Added'),
                message: product_name,
                sticky: false,
                className: false,
            });
        },

        _onClickAddNewLine: function(ev) {
            ev.stopPropagation();
            var self = this;
            var line_data = {
                'product_id': 0,
                'name': '',
            };
            var $cur_row = $(ev.currentTarget).closest('tr');

            if ($cur_row.prev()){
                if ($cur_row.prev().find('select option:selected').val() == 0) {
                    alert('Somelines are missing products. Please use that first.');
                    return;
                }
            }
            var $newLine = this._renderLine(line_data)
            // 
            $newLine.insertBefore($cur_row);
            $newLine.find('select').select2();

        },


        _onRemoveLine: function(ev) {
            ev.stopPropagation();

            var $cur_row = $(ev.currentTarget).closest('tr');
            var line_id = parseInt($cur_row.attr('line_id'));

            var product = $cur_row.find('td').find('option:selected').val()
            delete this.orders_data.orderlines[line_id];

            this._saveToStorage();
            $cur_row.remove();
        },

        _onClickSave: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();

            var self = this;
            this._loadFromStorage();

            var vals = {};
            _.each(this.$('.p-patient-info input'), function(input){
                if (input.name) {
                    vals[input.name] = input.value;
                }
            });

             _.each(this.$('textarea'), function(textarea){
                if (textarea.name) {
                    vals[textarea.name] = textarea.value;
                }
            });


            _.each(this.$('.p-patient-info select'), function(select){
                if (select.name) {
                    vals[select.name] = $(select).find('option:selected').val();
                }
            });

            console.log('_ vals : ', vals);

            var $btn = $(ev.currentTarget);

            var orderlines = [];
            _.each(this.$('tr.p-orderline'), function(tr){
                var $tr = $(tr),
                    prod_id = parseInt($tr.find('select option:selected').val());
                    // name =  $tr.find('input')[1].value;
                if (prod_id) {
                    orderlines.push(prod_id);
                }
            });
            vals['orderlines'] = orderlines;
            if (vals['partner_name'] && vals['phone'] &&vals['gender'] &&  vals['civil_id'] &&  vals['app_notes']) {
                // $btn.attr('disabled', 'disabled');
                this._rpc({
                    'route': '/medical/lab/create',
                    'params': {
                        'order_vals': vals
                    }
                }).then( function (result) {
                    if (result) {
                        window.location.href = '/appointment/details/'+ result.appointment ;
                        // window.location.href = '/thank-you-note';
                    }
                    $btn.removeAttr('disabled');
                });
            } else {
                alert('All Inputs are required.');
            }
        },

        _onClickReset: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            var confirm_status = confirm("It will remove unsaved data. Make sure data is saved. Press 'Ok' to reset.");
            if (confirm_status == true) {
                this.orders_data = {
                    'partner_id': 0,
                    'orderlines': {}
                };
                this._saveToStorage();
                this._renderData();
            }
        },

        _loadProduct: function(pricelist_id) {
            var self = this;
            var Def = $.Deferred();
            rpc.query({
                'model': 'product.product',
                'method': 'search_read',
                'domain': [
                    ['sale_ok', '=', true],
                    ['categ_id.publish', '=', true],
                ],
                'fields': ['id', 'name', 'display_name', 'list_price'],
                'context': pricelist_id ? {
                    'pricelist': pricelist_id
                } : {}
            }).then(function(products) {
                self.products = products;
                _.each(self.products, function(prod) {
                    self.product_by_id[prod['id']] = prod;
                });
                Def.resolve();
            });
            return Def;
        },

        _renderData: function() {
            var self = this;

            this._loadFromStorage();
            this.$el.find('.tbody_lines tr').not(':last').remove();
            this.$el.find('#partner_id').val(this.orders_data.partner_id).change();
            this.$el.find('#phone').val(this.orders_data.phone).change();
            this.$el.find('#civil_id').val(this.orders_data.civil_id).change();
            this.$el.find('#mobile').val(this.orders_data.mobile).change();

            if (this.orders_data) {
                var $last_line = this.$el.find('.tbody_lines tr:last');
                _.each(this.orders_data.orderlines, function(line) {
                    var $line = self._renderLine(line);
                    $line.find('select').select2();
                    $line.insertBefore($last_line);
                });
            }
        },

        _renderLine: function(line) {
            var tobe_line = QWeb.render('medical_lab_website.SalesmanOrderLine', _.extend({}, line, {
                'products': this.products,
            }));
            return $(tobe_line);
        },

        _saveToStorage: function() {
            if (!_.has(sessionStorage, 'orders_data')) {
                sessionStorage.setItem('orders_data', '{}');
            }
            sessionStorage.setItem('orders_data', JSON.stringify(this.orders_data));
        },

        _loadFromStorage: function() {
            if (!_.has(sessionStorage, 'orders_data')) {
                sessionStorage.setItem('orders_data', JSON.stringify(this.orders_data));
            }
            this.orders_data = JSON.parse(sessionStorage.getItem('orders_data'));
        },
    });

    publicWidget.registry.MyAppointment_table = publicWidget.Widget.extend({
        selector: '.MyAppointment_table',
        events: {
            'click .p-lab-print': '_onTestEachPrint',
            'click .p-app-print': '_onTestResultPrint',
        },
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            this._super.apply(this, arguments);
        },
        _onTestEachPrint: function(ev){
            var test_ids = $(ev.currentTarget).data('lab_test_ids');
            if (test_ids) {
                this.print_report('medical_lab.report_medical_patient_labtest/' + test_ids.toString() , 'qweb-pdf');
                this.displayLoading();
            }
        },
        _onTestResultPrint: function(ev){
            var app_id = $(ev.currentTarget).data('appointment');
            var lab_test_ids = $(ev.currentTarget).data('lab_test_ids');
            console.log('____ lab_test_ids : ', lab_test_ids);
            if (app_id) {
                this.print_report('medical_lab.report_medical_app_test_result/' + app_id.toString() , 'qweb-pdf');
                this.displayLoading();
            }
        },
        print_report: function (url, type) {
            var self = this;
            var response = ["/report/pdf/" + url, type];
            return session.get_file({
                url: '/report/download',
                data: {data: JSON.stringify(response)},
                complete: $.unblockUI,
                error: function () {
                    alert('Print failed possibly server issue.');
                },
            })
        },
        displayLoading: function () {
            var msg = _t("Downloading ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });
        },
    });

});
