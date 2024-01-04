odoo.define('medical_pcr.pcr_request', function (require) {
"use strict";

var appointment = require('medical_js.appointment');
var baseWidget = require('medical_js.BaseWidget');
var models = require('medical_js.models');
var ClientListScreenWidget = require('medical_js.patient');
var core = require('web.core');
var rpc = require('web.rpc');
var gui = baseWidget.gui;
var time = require('web.time');
var PopupWidget = baseWidget.PopupWidget;
var CalendarScreenWidget = require('medical_js.calendar');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

baseWidget.load_models([{
        model:  'airline.selection',
        fields: ['id', 'name'],
        condition: function(self) {return self.config.allow_pcr_test},
        loaded: function(self, records){
            self.airlines = records;
        },
    },{
        model:  'quarantine.station',
        fields: ['id', 'name'],
        condition: function(self) {return self.config.allow_pcr_test},
        loaded: function(self, records){
            self.quarantine_stations = records;
        },
    },{
        model:  'swab.location',
        fields: ['id', 'name'],
        condition: function(self) {return self.config.allow_pcr_test},
        loaded: function(self, records){
            self.swab_locations = records;
        },
    }
]);
baseWidget.load_fields('res.company', ['test_before_travel_days', 'pcr_test_duration']);
baseWidget.load_fields('product.product', ['medical_type']);

CalendarScreenWidget.include({
    searchedEvent: function(record){
        var self = this;
        var result = this._super.apply(this, arguments);

        var search_on = self.search_on,
            search_text = self.search_text,
            search_state = (self.search_state == 'all') ? '' : self.search_state;

        if (!result) {
            if (search_on == 'apmt_name') {
                if (record.pcr_qr_code && record.pcr_qr_code.toLowerCase().includes(search_text)) {
                    result = true;
                }
            }
        }
        return result;
    },
    appointment_eventClick: function(cal, eventClickInfo, options){
        var self = this;
        if (eventClickInfo && eventClickInfo.jsEvent && eventClickInfo.jsEvent.target){
            var $target = $(eventClickInfo.jsEvent.target);
            if ($target.hasClass('has-action')){
                if ($target.data('event') && !$target.hasClass('disabled')){
                    var event_name = $target.data('event');
                    self[event_name](eventClickInfo.event, $target);
                }
                return;
            }
        }
        return this._super.apply(this, arguments);
    },
    show_popup_batch_no: function(event, $target){
        var self = this;
        var record = event.extendedProps.record;
        var props = {};
        props = _.extend({}, {
            'value': record.vaccine_batch_no || '',
            'title': 'Vaccine Batch No.',
            'confirm': function(value){
                if (!value) {
                    self.medical.chrome.warning_toast('Batch No. is required !', 'Invalid Input')
                    self.gui.show_popup('textinput', props);
                    return;
                }
                self._rpc({
                model: 'medical.order',
                    method: 'write',
                    args: [[record.id], {
                        'vaccine_batch_no': value,
                    }],
                }).then(function(res){
                    self.medical.chrome.success_toast('Batch No. saved !');
                    $target.addClass('disabled');
                    $target.find('.jab-str').html("Jab Taken");
                    $target.parents('td').find('.v-qr-print').removeClass('disabled');
                    var $tr = $target.parents('tr');
                    $tr.find('.v-qr-code').html('<span class="fa fa-barcode mr-1" />' + value);
                    $tr.find('.v-vaccine-batch').removeClass('d-none');
                });
            },
        });
        this.gui.show_popup('textinput', props);
    },
    app_open_invoice: function(event){
        this.chrome.blockUI();
        var self = this;
        return session.rpc("/event", {order_id: event.id}).then(function (order) {
            if (!_.isEmpty(order)) {
                if (order.invoice_state) {
                    self._rpc({'route': "/event/invoice", 'params': {order_id: order.id}}).then(function (invoice) {
                        if (invoice && !invoice.partner && invoice.partner_id && invoice.partner_id.length > 1) {
                            invoice.partner = self.medical.db.get_partner_by_id(invoice.partner_id[0]);
                        }
                        self.gui.show_screen('page_invoice', {
                            'prev-screen': 'calendar',
                            'invoice': invoice,
                            'order': order,
                        }, true);
                        self.chrome.unblockUI();
                    });
                }
                else {
                    // console.log('____ order : ', order);
                    self.chrome.unblockUI();
                    var new_order = self.medical.toPosOrder(order);
                    // self.open_invoice_screen();
                    self.medical.set_order(new_order);
                    self.gui.show_screen('appointment');
                }
            } else {
                self.chrome.unblockUI();
            }
        });
    },
    app_create_invoice: function(event){
        var self = this;
        return session.rpc("/event", {order_id: event.id}).then(function (order) {
            console.log('___ Creating Invoice : ', order);

            var ctx = {'default_med_employee_id': self.medical.get_cashier().id};
            self.chrome.success_toast(_t("Appointment Validating..."));
            self.blockUI();
            self._rpc({
                model: 'medical.order',
                method: 'action_create_invoice_wrapper',
                args: [[order.id]],
                context: ctx,
            }).then(function(invoice){
                self.chrome.unblockUI();
                self.chrome.success_toast(_t("Appointment Validated Successfully."));

                if (invoice && !invoice.partner && invoice.partner_id && invoice.partner_id.length > 1) {
                    invoice.partner = self.medical.db.get_partner_by_id(invoice.partner_id[0]);
                    order.partner_id = invoice.partner_id[0];
                }
                self.gui.show_screen('page_invoice', {
                    'previous-screen': 'calendar',
                    'invoice': invoice,
                    'order': order,
                }, true);
            }).guardedCatch(function (error) {
                self.chrome.unblockUI();
            });
        });
    },
    send_result_SMS: function(event, $target){
        var self = this;
        var record = event.extendedProps.record;
        this._rpc({
            model: 'medical.order',
            method: 'send_result_by_sms',
            args: [[parseInt(record.id)]],
        }).then(function(result) {
            if(result && result.success){
                self.chrome.info_toast(_t("SMS has been sent successfully"));
            }
            else{
                self.chrome.error_toast(result.error || _t('Something went wrong.'));
            }
        });
    },
    send_invoice_SMS: function(event, $target){
        var self = this;
        var record = event.extendedProps.record;
        this._rpc({
            model: 'medical.order',
            method: 'send_invoice_by_sms',
            args: [[parseInt(record.id)]],
        }).then(function(result) {
            if(result && result.success){
                self.chrome.info_toast(_t("Invoice has been sent successfully"));
            }
            else{
                self.chrome.error_toast(result.error || _t('Something went wrong.'));
            }
        });
    },
    log_sample_date: function(event, $target){
        var self = this;
        var record = event.extendedProps.record;
        if (record.handover_file_on || $target.hasClass('disabled')) {
            self.chrome.warning_toast(_t('Sample is already taken.'));
        } else {
            self.generate_order_qr(record.id).then(function(qr_code){
                self.chrome.success_toast(_t('Logged time for sample.'));
                $target.addClass('disabled');
                $target.parents('td').find('.v-qr-print').removeClass('disabled');
                $target.html('<span class="fa fa-hand-lizard-o has-action text-primary" data-event="log_sample_date"></span> Sample Taken');
                $target.attr('title', 'Sample Taken');
                if (qr_code) {
                    $target.parents('tr').find('.v-qr-code').html('<span class="fa fa-file-o mr-1" />' + qr_code);
                }
            });
        }
    },
    generate_order_qr: function(order_id){
        var self = this;
        var current_employee_id = parseInt(self.medical.get_cashier().id);
        return this._rpc({
            model: 'medical.order',
            method: 'generate_order_qr',
            args: [[order_id], current_employee_id]
        });
    },
    getListViewHeader: function(){
        var partner_lbl = this.label_list['partner_id'],
            resource_lbl = this.label_list['resource_id'];
        return '<thead><th /><th /><th>'+partner_lbl+'</th><th>Contact</th><th>'+resource_lbl+'</th><th>State</th><th>Ref Code</th><th>Operation</th></thead>';
    },
    getCalendarOptions: function(){
        var result = this._super.apply(this, arguments);
        var self = this,
            config = this.gui.medical.config;
        self.search_on = 'apmt_name';
        self.search_text = '';
        self.search_state = 'all';

        return _.extend({}, result, {
            eventDidMount: function ( info ) {
                var event = info.event;
                if (event.display == 'background' || event.display == 'inverse-background') {
                    return;
                }
                var $event_el = $(info.el);
                var view_type = info.view.type;
                var record = event.extendedProps.record;

                var add_title = '<strong class="badge badge-info">' + record.name + '</strong>';
                if (config.company_code == 'pcr') {
                    if (record.is_app_pcr){
                        add_title += '<strong class="badge badge-warning">PCR</strong>';
                    }
                    if (record.is_app_vaccine){
                        add_title += '<span class="badge badge-warning">Vaccination</span>';
                    }
                }
                if(record && record.visit_opt_id && record.visit_opt_id[1]){
                    add_title += '<strong class="badge badge-primary">' + record.visit_opt_id[1] + '</strong>';
                }
                add_title += '<br />';
                if (self.show_file_no_first && record.file_no) {
                    add_title += '<span class="font-italic font-weight-bold mr-1">' + record.file_no + '</span>';
                }
                if (record && record.visit_type && record.visit_type == 'pre_app') {
                    add_title += '<span class="fa fa-link mr-1" style="color: cyan" />';
                }
                var add_suffix = '';
                var contact = ''
                if (record.partner) {
                    if (record.partner.civil_code){
                        add_suffix += '<br /><span>Civil ID: ' + record.partner.civil_code + '</span>';
                    }
                    if (record.partner.passport_no) {
                        add_suffix += '<br /><span>Passport: ' + record.partner.passport_no + '</span>';
                    }
                    if (record.partner.phone || record.partner.mobile) {
                        contact = '<span>' + (record.partner.phone || '') + ' ' + (record.partner.mobile || '') +  '</span>';
                    }
                    if(record && record.sample_taken_emp_id && record.sample_taken_emp_id[1]){
                     add_suffix += '<br />';
                     add_suffix += '<span> Sample Taken By <b>' + record.sample_taken_emp_id[1] + '</b></span>';
                    }
                }


                if (add_title) {
                    if ($event_el.find('.fc-event-title').length){
                        $event_el.find('.fc-event-title').prepend(add_title);
                    }
                    else if ($event_el.find('.fc-list-event-title').length){
                        $event_el.find('.fc-list-event-title').prepend(add_title);
                    }
                }

                if (add_suffix && config.company_code == 'pcr') {
                    if ($event_el.find('.fc-event-title').length){
                        $event_el.find('.fc-event-title').prepend(add_suffix);
                    }
                    else if ($event_el.find('.fc-list-event-title').length){
                        $event_el.find('.fc-list-event-title').append(add_suffix);
                    }
                }

                var services = '<ul class="p-0 pl-3 services">';
                _.each(record.order_lines, function (l) {
                    services += "<li>" + l['product_id'][1] + "</li>";
                });
                services += '</ul>';
                $event_el.find('.fc-event-title').after($(services));

                if (record.employee_id && record.employee_id.length) {
                    var emp = '<strong><span class="fa fa-id-badge ml-1" /> ' + record.employee_id[1] + '</strong>';
                    $event_el.find('.services').after($(emp));
                }
                if (view_type == 'listDay' || view_type == 'listMonth') {
                    var el_btn = QWeb.render('PCRListButtons', {
                        'widget': self,
                        'order': record,
                        'invoice_state': record.invoice_state,
                    });
                    var doc_name = record.resource_id && record.resource_id[1] || '';
                    var td_list = '<td>' + (contact || '') + '</td>' +
                        '<td>' + doc_name + '</td>' + 
                        '<td>' + record.state_display + '</td>' +
                        '<td class="v-qr-code">';
                    if (record.pcr_qr_code){
                        td_list += '<span class="fa fa-file-o mr-1" />' + (record.pcr_qr_code || '');
                    }
                    else if(record.vaccine_batch_no) {
                        td_list += '<span class="fa fa-barcode mr-1" />' + (record.vaccine_batch_no || '');
                    }
                    td_list += '</td>';
                    $event_el.find('.fc-list-event-title').after(td_list + el_btn);
                }

                // Tooltip Of Event
                function getTooltip () {
                    return QWeb.render('EventTooltip',{
                        record: record,
                        widget: self,
                    });
                }

                new Tooltip(info.el, {
                    title: getTooltip,
                    placement: 'right',
                    trigger: 'hover',
                    container: 'body'
                });
            },
        });
    },
});

// appointment.PopupOrderDetails.include({
//     events: _.extend({}, appointment.PopupOrderDetails.prototype.events, {
//         'click .p-pcr-report': 'pcr_report',
//     }),
//     pcr_report: function(){
//         var order = this.options.order;
//         if (order) {
//             // this.chrome.print_report('medical_pcr.pcr_qr_custom_report/' + order.id, 'qweb-pdf');
//         }
//     },
// });

// var PCRScreen = baseWidget.screens.ScreenWidget.extend({
var PCRScreen = PopupWidget.extend({
    // template: 'PCRScreenWidget',
    template: 'PCRPopupWidget',
    events: _.extend({}, PopupWidget.prototype.events, {
        'change .pcr_appointments_type': '_onChangeAppType',
        // 'change .is_vaccinated': '_onChangeIsVaccinated',
        '.back': 'home',
        'change .v-check': '_onChangeVisibility',
        'change .patient_work_place': '_onChangePlaceOfWork',
        'click .card-header': '_togglePanel',
        'click .v-contact-delete': 'removeContactTR',
        'click .v-contact-add': 'addContactTR',
    }),
    addContactTR: function(ev){
        var el_str  = QWeb.render('PCR.ContactListTR');
        self.$('.v-contact-list').append(el_str);
    },
    removeContactTR: function(ev){
        var $elem = $(ev.currentTarget),
            idx = $elem.data('line');
        $elem.parents('tr').remove();
        if (idx) {
            var self = this;
            this._rpc({
                model: 'medical.contact.list',
                method: 'unlink',
                args: [[parseInt(idx)]]
            }).then(function (res) {
                self.chrome.success_toast("Removed contact line.");
            });
        }
    },
    home: function(){
        this.back();
    },
    _togglePanel: function(ev){
        $(ev.currentTarget).next().toggle('slide');
    },
    _onChangePlaceOfWork: function(ev){
        var $elem = this.$('.v-department');
        if ($(ev.target).find(":selected").val() == 'public'){
            $elem.show()
        }
        else {
            $elem.hide()
        }
    },
    _onChangeVisibility: function(ev){
        var is_selected = $(ev.currentTarget).prop('checked');
        var $elem = $(ev.currentTarget).parents('.v-panel').find('.v-visible');
        if (is_selected) {
            $elem.show()
        }
        else {
            $elem.hide()
        }
    },
    _onChangeAppType: function(ev){
        ev.preventDefault();
        var cmp_country_id = this.medical.company.country.id;
        if ($(ev.target).find(":selected").val() == 'departure'){
            $(this.$(".v-not-departure")).hide();
            if (cmp_country_id){
                this.$('.origin_country_id option[value="' + cmp_country_id + '"]').attr({
                    'disabled': false,
                    'selected': 'selected',
                }).trigger('change');
                // this.$('.origin_country_id option[value="' + cmp_country_id + '"]').prop('selected', 'selected');
            }
        }
        else{
            if(cmp_country_id){
                this.$('.origin_country_id option[value="' + cmp_country_id + '"]').attr({
                    'disabled': 'disabled',
                    'selected': false,
                }).trigger('change');
            }
            $(this.$(".v-not-departure")).show();
        }
    },
    // _onChangeIsVaccinated: function(ev){
    //     var is_selected = $(ev.currentTarget).prop('checked');
    //     if (is_selected) {
    //         this.$('.show_on_vaccinated').children().show()
    //     }
    //     else {
    //         this.$('.show_on_vaccinated').children().hide()
    //     }
    // },
    init: function (parent, args) {
        this._super(parent, args);
        this.symptomatic_list = [
            {'name': 'cough', 'label': 'Dry Cough', 'value': false},
            {'name': 'fever', 'label': 'Fever', 'value': false},
            {'name': 'breath', 'label': 'Shortness of Breath', 'value': false},
            {'name': 'aches', 'label': 'Fatigue/Muscle Aches', 'value': false},
            {'name': 'throat', 'label': 'Sore Throat', 'value': false},
            {'name': 'diarrhea', 'label': 'Diarrhea', 'value': false},
            {'name': 'headache', 'label': 'Headache', 'value': false},
            {'name': 'nose', 'label': 'Runny Nose', 'value': false},
            {'name': 'taste', 'label': 'Loss of smell/taste', 'value': false},
        ];
    },
    show: function(){
        this._super.apply(this, arguments);
        this.order = this.options && this.options.order;
        this.partner = this.medical.get_order().get_client();
        this.pcr_data = this.options && this.options.pcr_data || {};
        // this.order = this.gui.get_current_screen_param('order') || {};
        // this.pcr_data = this.gui.get_current_screen_param('pcr_data') || {};
        this.renderElement();

        var self = this;

        if (!_.isEmpty(this.pcr_data)){
            _.each(this.$('.v-checkbox'), function(elem){
                if (elem && elem.name && _.indexOf(_.keys(self.pcr_data), elem.name) > -1){
                    $(elem).prop('checked', self.pcr_data[elem.name]);
                    $(elem).trigger('change');
                }
            });
            _.each(this.$('.v-select'), function(elem){
                if (elem && elem.name && _.indexOf(_.keys(self.pcr_data), elem.name) > -1 && self.pcr_data[elem.name]){
                    $(elem).find('option[value="'+self.pcr_data[elem.name]+'"]').prop('selected', 'selected');
                    $(elem).trigger('change');
                }
            });

            if (this.pcr_data && this.pcr_data.in_contact_list){
                _.each(this.pcr_data.in_contact_list, function(line){
                    var el_str  = QWeb.render('PCR.ContactListTR', {
                        widget: self,
                        line: line,
                    });
                    self.$('.v-contact-list').append(el_str);
                });
            }
        }
        function get_items(records) {
            var alist = [];
            _.each(records, function(r){
                alist.push({'id': r.id, 'text': r.name});
            });
            return alist;
        }
        
        _.each(this.$('.m2o-field'), function(elem) {
            var $elem = $(elem);
            if ($elem.hasClass('v-allow-create')){
                var _field = $elem.data('field'),
                    current_model = $elem.data('model');
                var records = get_items(self.medical[_field]);
                $elem.select2({
                    data: records,
                    allowClear: true,
                    createSearchChoice: function (term, data) {
                        var added_tags = $(this.opts.element).select2('data');
                        if (_.filter(_.union(added_tags, data), function (tag) {
                            return tag.text && tag.text.toLowerCase().localeCompare(term.toLowerCase()) === 0;
                        }).length === 0) {
                            return {
                                id: _.uniqueId('tag_'),
                                create: true,
                                tag: term,
                                text: _.str.sprintf(_t("Create '%s'"), term),
                            };
                        }
                    }
                }).on('change', function (e) {
                    var ele = this;
                    if (e.added && e.added.create) {
                        self._rpc({
                            model: current_model,
                            method: 'create',
                            args: [{'name': e.added.tag}]
                        }).then(function (m_id) {
                            records.push({
                                'id': m_id,
                                'text': e.added.tag
                            });
                            var datas = $(ele).select2('data') || [];
                            var tagIndex = _.findIndex(datas, function (d) { return d['id'] == e.added.id});
                            datas[tagIndex] = {'id': m_id, 'text': e.added.tag};
                            $(ele).select2('data', datas);
                            self.medical[_field].push({
                                'id': m_id,
                                'name': e.added.tag
                            });
                        });
                    }
                });

                // });
            }
            else {
                $elem.select2();
            }
        });

        console.log("Value : ", this.$('center_id').val());
    },
    click_confirm: function(){
        var data = {};
        var self = this;
        var order  = this.medical.get_order();
        if (order) {
            _.each(this.$('.v-checkbox'), function(elem){
                 if (elem.name){
                    data[elem.name] = $(elem).prop('checked');
                 }
            });
            _.each(this.$('select'), function(elem){
                if (elem.name) {
                    if (elem.value && $(elem).hasClass('m2o-field')) {
                        data[elem.name] = parseInt(elem.value);
                    }
                    else{
                        data[elem.name] = elem.value;
                    }
                }
            });
            _.each(this.$('input.m2o-field'), function(elem){
                if (elem.name) {
                    data[elem.name] = parseInt($(elem).select2('val'));
                }
            });
            _.each(this.$('textarea, .v-input'), function(elem){
                if (elem.name) {
                    data[elem.name] = elem.value;
                }
            });
            var in_contact_list = [];
            _.each(this.$('.v-contact-list tr'), function(tr){
                var $tr = $(tr),
                    tr_vals = {};
                _.each($tr.find('input'), function(input){
                    tr_vals[input.name] = input.value;
                });
                in_contact_list.push(tr_vals);
            });
            data.in_contact_ids = in_contact_list;

            // if (!data.pcr_type) {
            //     self.chrome.warning_toast("Immune Type is required.");
            //     return;
            // }
            if (!data.swab_type) {
                self.chrome.warning_toast("Swab Type is required.");
                return;
            }
            if (!data.swab_location_id) {
                self.chrome.warning_toast("Collection Center is required.");
                return;
            }

            if (data.pcr_appointments_type){
                if (!data.travel_date) {
                    self.chrome.warning_toast("Travel Date is required.");
                    return;
                }
                var travel_type = data.pcr_appointments_type;
                var today = moment().startOf('day'),
                    travel_date = moment(data.travel_date).startOf('day');

                // if (travel_type == 'arrival' && travel_date.isAfter(today)) {
                //     self.chrome.warning_toast("Arrival cannot be after today !");
                //     return;
                // }
                // else
                if (travel_type == 'departure') {
                    if(travel_date.isBefore(today)){
                        self.chrome.warning_toast("Departure cannot be before today !");
                        return;
                    }
                    var test_days = self.medical.company.test_before_travel_days || 0;
                    if (test_days) {
                        today.add(test_days, 'days');
                    }
                    if(travel_date.isBefore(today)){
                        self.chrome.warning_toast("PCR is allowed only if departure is after " + test_days + " days!");
                        return;
                    }
                }
            }

            if (data.is_traveller_swab && !data.passport_no) {
                self.chrome.warning_toast("Passport No. is required in case of Traveller Swab.");
                return;
            }
            console.log('____ Set PCR Data : ', data);
            order.set_pcr_details(data);
        }
        this.medical.gui.close_popup();
        if(this.options.confirm){
            this.options.confirm.call(this,value);
        }
        // }
    },
});
// gui.define_screen({name: 'popup-pcr-request', widget: PCRScreen});
gui.define_popup({name: 'popup-pcr-request', widget: PCRScreen});

var PcrRequestButton = appointment.ActionButtonWidget.extend({
    template: 'PcrRequestButton',
    button_click: function(){
        var self = this;
        var order = this.medical.get_order(),
            partner_id = (order.get_client() || {}).id;
        if (!partner_id) {
            self.chrome.warning_toast("Please select the patient first.");
            return;
        }
        if (order.server_id || order.uid){
            return rpc.query({
                'route': '/pcr/order/details',
                'params': {'order_id': order.server_id, 'config_id': self.medical.config.id, 'ui_ref': order.uid, 'partner_id': partner_id}
            }).then(function (result) {
                var dur_day = self.medical.company.pcr_test_duration || 0;
                console.log('____ Opening PCR1 : ', order.server_id, order.uid, dur_day, result, partner_id, order);
                if (result.is_allowed){
                    var swab_location_id = order.swab_location_id || self.medical.config.default_collection_center_id && self.medical.config.default_collection_center_id[0] || null;
                    var temp_pcr_data = {'swab_type': order.swab_type,'pcr_type':order.pcr_type,'swab_location_id':[swab_location_id,'']}
                    var pcr_data = result.pcr_data || temp_pcr_data;
                    order = _.extend({}, order, pcr_data);
                    self.medical.gui.show_popup('popup-pcr-request', {
                        'order': order,
                        'pcr_data': pcr_data, 'previous-screen': 'appointment'
                    });
                }
                else {
                    self.chrome.warning_toast("You cannot book second PCR Appointment before "+dur_day.toString()+" days from last Appointment.");
                    return;
                }
            });
        } else{
            if (order && order.get_client().passport_no){
                order.passport_no = order.get_client().passport_no;
            }
            self.medical.gui.show_popup('popup-pcr-request', {order: order, 'previous-screen': 'appointment'});
        }
    },
});

appointment.define_action_button({
    'name': 'btn_pcr_request',
    'widget': PcrRequestButton,
    'condition': function(){
        return this.medical.config.allow_pcr_test;
    },
});


var _super_order = models.Order;
models.Order = models.Order.extend({
    set_pcr_details: function(data) {
        console.log('____ data : ', _.keys(data), data);
        if (!_.isEmpty(data)) {
            _.extend(this, data);
        }
        this.pcr_data = data || {};
    },
    get_pcr_data: function() {
        return this.pcr_data || {};
    },
    set_send_sms: function(){
        this.send_sms = true;
    },
    export_as_JSON: function(){
        var json = _super_order.prototype.export_as_JSON.apply(this,arguments);
        if (!_.isEmpty(this.get_pcr_data())) {
            _.extend(json, this.pcr_data);
        }
        json.send_sms = this.send_sms;
        json.swab_type = this.swab_type;
        json.pcr_type = this.pcr_type;
        json.swab_location_id = this.swab_location_id;
        return json;
    },
    update_order_medical_type: function(){
        var is_app_pcr = false,
            is_app_vaccine = false;

        var lines = this.get_orderlines();
        for (var i = 0; i < lines.length; i++) {
            var medical_type = lines[i].get_product().medical_type;
            if (medical_type === 'pcr') {
                is_app_pcr = true;
            }
            if (medical_type === 'vaccine') {
                is_app_vaccine = true;
            }
        }
        this.is_app_pcr = is_app_pcr;
        this.is_app_vaccine = is_app_vaccine;
    },
    validate_order: function(){
        var order = this.export_as_JSON();
        this.update_order_medical_type();
        if (this.is_app_pcr){
            // if (!order.pcr_type) {
            //     this.medical.gui.show_popup("error", "PCR Request : Immune Type is required.");
            //     return false;
            // }
            if (!order.swab_type) {
                this.medical.gui.show_popup("error", "PCR Request : Swab Type is required.");
                return false;
            }
            if (!order.swab_location_id) {
                this.medical.gui.show_popup("error", "PCR Request : Collection Center is required.");
                return false;
            }
        }
        return _super_order.prototype.validate_order.apply(this, arguments);
    },
    update_db_data: function(order, action) {
        _super_order.prototype.update_db_data.apply(this,arguments);
        this.swab_type = order.swab_type;
        this.pcr_type = order.pcr_type;
        this.sms_sent = order.sms_sent;
        this.send_sms = order.send_sms;
        this.swab_location_id = order.swab_location_id && order.swab_location_id[0] || false;
    },
});

appointment.AppointmentScreenWidget.include({
    sync_appointment: function(order) {
        if (!order) {
            order = this.medical.get_order();
        }
        var self = this,
            _super = this._super;
        var $def = $.Deferred();

        if (!order.validate_order()){
            self.unblockUI();
            return $def.fail();
        }

        console.log('____ order : ', order.sms_sent, order.send_sms, order);

        if (this.medical.config.company_code == 'pcr' && order && !order.sms_sent && !order.send_sms) {
            self.unblockUI();
            this.gui.show_popup('confirm-yes-no',{
                'title': _t('Do you want to send SMS ?'),
                confirm: function(){
                    order.set_send_sms();
                    $def.resolve();
                },
                cancel: function(){
                    $def.resolve();
                },
            });
            return $def.then(function(){
                return _super.apply(self, arguments)
            })
        }
        else {
            return this._super.apply(self, arguments);
        }
    },
});

});
