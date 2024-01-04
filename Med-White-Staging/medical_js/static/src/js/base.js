odoo.define("medical_js.BaseWidget", function(require) {
    "use strict";
    var i = require("web.field_utils"),
        n = require("web.utils"),
        r = require("web.Widget"),
        o = require("web.time"),
        s = require("web.core"),
        a = require("web.framework"),
        c = require("web.rpc"),
        d = require("medical_js.models"),
        u = n.round_decimals,
        l = n.round_precision,
        p = {},
        h = s.qweb,
        f = [],
//        flatted = require("medical_js.flatted"),
        m = ["name", "ar_name", "type", "phone", "mobile", "email", "street", "street2", "city", "state_id", "country_id", "birthday", "file_no", "file_no2", "passport_no", "marital", "person_status", "comment", "diagnosis_summary", "gender", "child_ids", "property_product_pricelist", "civil_code", "parent_id", "is_insurance_company", "ins_running_card_ids", "history", "utm_source_id", "utm_medium_id", "person_status", "medical_attachment_ids", "blocked_doctor_ids", "app_no_show_count", "app_cancelled_count", "credit", "total_due", "area", "block", "avenue", "house", "floor", "apartment_no", "blood_group", "work_phone", "civil_id_issued", "civil_id_expiry", "civil_sponser", "civil_paci_no", "area_kw_moh_code", "governorate", "street2", "residence", "area_id", "nationality_id", "passport_name"],
        g = r.extend({
            init: function(t, i) {
                this._super(t), i = i || {}, this.medical = i.medical || (t ? t.medical : void 0), this.chrome = i.chrome || (t ? t.chrome : void 0), this.gui = i.gui || (t ? t.gui : void 0), this.setElement(this._makeDescriptive()), this.datetime_format = o.getLangDatetimeFormat(), this.date_format = o.getLangDateFormat(), this.time_format = o.getLangTimeFormat(), this.datetime_server_format = "YYYY-MM-DD HH:mm:ss", this.date_server_format = "YYYY-MM-DD", this.locale = "en", this.date_dp_format = "d/m/Y", this.tm_dp_format = "g:i A", this.datetm_dp_format = "d/m/Y H:i:s", this.show_file_no_first = !0, this.show_blocked_by_resource = !0, this.dt_picker_options = {
                    format: this.date_dp_format,
                    timepicker: !1,
                    validateOnBlur: !1,
                    autoclose: !0,
                    closeOnDateSelect: !0
                }, this.dttm_picker_options = {
                    format: this.datetm_dp_format,
                    validateOnBlur: !1,
                    autoclose: !0,
                    closeOnDateSelect: !0
                }, this.time_picker_options = {
                    timeFormat: "H:i",
                    step: 5
                }, this.marital = {
                    single: "Single",
                    married: "Married",
                    cohabitant: "Legal Cohabitant",
                    widower: "Widower",
                    divorced: "Divorced"
                }, this.state_display = {
                    draft: "New",
                    cancel: "Cancelled",
                    confirmed: "Confirmed",
                    arrived: "Arrived",
                    late: "Late",
                    paid: "Paid",
                    done: "Posted",
                    invoiced: "Invoiced",
                    no_answer: "No Answer",
                    no_show: "No Show",
                    in: "In",
                    out: "Out"
                }, this.person_status = {
                    normal: "Normal",
                    vip: "Very Important Person (VIP)"
                }, this.label_list = {
                    resource_id: "Doctor",
                    clinic_id: "Branch",
                    partner_id: "Patient"
                }, this.label_file = {
                    file_no: "File",
                    file_no2: "Derma File"
                }, this.report_tags = {
                    payment: "account.report_payment_receipt"
                }, this.invoice_report = "medical_report.report_patient_invoice", this.report_list = [{
                    name: "Cash Invoice",
                    report_tag: this.invoice_report,
                    model: "account.move",
                    rep_id: "2",
                    field: "patient_invoice_id",
                    type: "qweb-pdf"
                }, {
                    name: "Insurance Patient Invoice",
                    report_tag: "medical_report.report_patient_ins_invoice",
                    model: "account.move",
                    rep_id: "3",
                    field: "insurance_invoice_id",
                    type: "qweb-pdf"
                }, {
                    name: "Insurance Company Invoice",
                    report_tag: "medical_report.report_ins_company_invoice_comp",
                    model: "account.move",
                    rep_id: "4",
                    field: "insurance_invoice_id",
                    type: "qweb-pdf"
                }, {
                    name: "Appointment",
                    report_tag: "medical_report.medical_appointment_report_template",
                    model: "medical.order",
                    field: "id",
                    rep_id: "1",
                    type: "qweb-pdf"
                }, {
                    name: "Payment Receipts",
                    report_tag: "account.report_payment_receipt",
                    model: "account.payment",
                    field: "payment_ids",
                    rep_id: "5",
                    type: "qweb-pdf"
                }]
            },
            get_file_label: function() {
                return this.label_file[this.get_config_file_key()]
            },
            get_config_file_key: function() {
                return this.medical.config.depends_on
            },
            get_file_no: function(t) {
                return t[this.get_config_file_key()]
            },
            open_invoice_screen: function(t, i) {
                this.chrome.blockUI();
                var n = this;
                t || i ? this._rpc({
                    route: "/event/invoice",
                    params: {
                        invoice_id: t,
                        order_id: i
                    }
                }).then(function(t) {
                    t && !t.partner && t.partner_id && t.partner_id.length > 1 && (t.partner = n.medical.db.get_partner_by_id(t.partner_id[0])), n.gui.show_screen("page_invoice", {
                        "prev-screen": "calendar",
                        invoice: t
                    }, !0), n.chrome.unblockUI()
                }) : n.chrome.unblockUI()
            },
            _select2Wrapper: function(t, i, n, r, o) {
                r = r || "name", o = o || [r];
                var s = {
                    width: "100%",
                    minimumInputLength: 2,
                    minimumResultsForSearch: 10,
                    placeholder: t,
                    allowClear: !0,
                    formatNoMatches: !1,
                    fetch_rpc_fnc: n,
                    cache: !0,
                    formatSelection: function(t) {
                        return t.tag && (t.text = t.tag), t.text
                    },
                    fill_data: function(t, i) {
                        var n = this,
                            s = {
                                results: []
                            };
                        _.each(i, function(i) {
                            var a = "";
                            _.each(o, function(t) {
                                i[t] && (a = a + "|" + (i[t] || ""))
                            }), n.matcher(t.term, a) && (i.text = i[r], s.results.push(i))
                        }), t.callback(s)
                    },
                    query: function(t) {
                        var i = this;
                        this.fetch_rpc_fnc(t).then(function(n) {
                            i.can_create = !1, i.fill_data(t, n)
                        })
                    }
                };
                return i && (s.multiple = !0), s
            },
            print_selected_report: function(t, i) {
                var n = _.findWhere(this.report_list, {
                        rep_id: t
                    }),
                    r = n.report_tag,
                    o = i[n.field];
                if (o instanceof Array && o.length > 0 && (o = o[0]), console.info("___ Print Report : ", r, o, n, i), "medical.order" == n.model) {
                    if (!o) {
                        this.chrome.error_toast("Order ID doesn't found.");
                        return
                    }
                    r = r + "/" + o
                } else if ("account.move" == n.model) {
                    if (!o) {
                        this.chrome.error_toast("Invoice doesn't found.");
                        return
                    }
                    r = r + "/" + o
                } else {
                    if (!o) {
                        this.chrome.error_toast("Record doesn't exist.");
                        return
                    }
                    r = r + "/" + o
                }
                return this.chrome.print_report(r, n.type)
            },
            get_display_state: function(t) {
                return this.state_display[t]
            },
            format_date: function(t) {
                return !t || _.isUndefined(t) ? "" : moment(t).format(this.date_format)
            },
            format_time: function(t, i) {
                return !t || _.isUndefined(t) ? "" : (i && (t = this.toUserTZ(t)), moment(t).format(this.time_format))
            },
            format_datetime: function(t, i) {
                return (i = !!i, !t || _.isUndefined(t)) ? "" : (i && (t = this.toUserTZ(t)), moment(t).format(this.datetime_format))
            },
            format_server_date: function(t) {
                return !t || _.isUndefined(t) ? "" : moment(t).format(this.date_server_format)
            },
            format_server_datetime: function(t) {
                return !t || _.isUndefined(t) || "Invalid date" == t ? "" : moment(t).format(this.datetime_server_format)
            },
            format_currency: function(t, i) {
                var n = this.medical && this.medical.currency ? this.medical.currency : {
                    symbol: "$",
                    position: "after",
                    rounding: .01,
                    decimals: 2
                };
                return (t = this.format_currency_no_symbol(t, i), "after" === n.position) ? t + " " + (n.symbol || "") : (n.symbol || "") + " " + t
            },
            format_currency_no_symbol: function(t, n) {
                var r = (this.medical && this.medical.currency ? this.medical.currency : {
                    symbol: "$",
                    position: "after",
                    rounding: .01,
                    decimals: 2
                }).decimals;
                return n && void 0 !== this.medical.dp[n] && (r = this.medical.dp[n]), "number" == typeof t && (t = u(t, r).toFixed(r), t = i.format.float(u(t, r), {
                    digits: [69, r]
                })), t
            },
            show: function() {
                this.$el.removeClass("oe_hidden")
            },
            hide: function() {
                this.$el.addClass("oe_hidden")
            },
            format_pr: function(t, i) {
                return t.toFixed(i > 0 ? Math.max(0, Math.ceil(Math.log(1 / i) / Math.log(10))) : 0)
            },
            format_fixed: function(t, i, n) {
                var r = (t = t.toFixed(n || 0)).indexOf(".");
                r < 0 && (r = t.length);
                for (var o = i - r; o > 0;) t = "0" + t, o--;
                return t
            },
            floatToHour: function(t) {
                if (!t) return "";
                var i = t >= 0 ? 1 : -1,
                    n = 1 / 60,
                    r = Math.floor(t *= i),
                    o = t - r,
                    s = Math.floor(60 * (o = n * Math.round(o / n)));
                return i = 1 == i ? "" : "-", this.padLeft(i + r, "00") + ":" + this.padLeft(s, "00")
            },
            blockUI: function() {
                a.blockUI()
            },
            unblockUI: function() {
                a.unblockUI()
            },
            floatToHourMin: function(t) {
                var i, n = t >= 0 ? 1 : -1,
                    r = 1 / 60,
                    o = Math.floor(t *= n),
                    s = t - o;
                return {
                    hours: (n = 1 == n ? "" : "-") + o,
                    minutes: Math.floor(60 * (s = r * Math.round(s / r)))
                }
            },
            floatToMinutes: function(t) {
                var i = this.floatToHourMin(t);
                return 60 * Number(i.hours) + Number(i.minutes)
            },
            padLeft: function(t, i) {
                return i || (i = "0000"), i.substring(0, i.length - t.length) + t
            },
            getUTC: function(t) {
                return t ? new Date(t.getTime() + 6e4 * t.getTimezoneOffset()) : ""
            },
            toUserTZ: function(t, i) {
                return t ? ((i || "string" == typeof t) && (t = new Date(t)), new Date(t.getTime() - 6e4 * t.getTimezoneOffset())) : ""
            },
            parseServerDatetime: function(t) {
                return i.parse.datetime(t, {
                    type: "datetime"
                })
            },
            parseM2o: function(t) {
                return i.parse.many2one(t) || {}
            },
            get_str_datetime: function(t) {
                if (t) return (t = this.to_moment(t)).local().format(this.datetime_format)
            },
            get_str_date: function(t) {
                if (t) return (t = this.to_moment(t)).format(this.date_format)
            },
            get_str_time: function(t) {
                if (t) return (t = this.to_moment(t)).format(this.time_format)
            },
            get_server_date: function(t) {
                if (t) return (t = this.to_moment(t)).clone().utc().locale(this.locale).format(this.date_server_format)
            },
            get_server_datetime: function(t) {
                if (t) return (t = this.to_moment(t)).clone().utc().locale(this.locale).format(this.datetime_server_format)
            },
            to_moment: function(t, i, n) {
                if (n = n || this.datetime_format, i = !!i, t && !t._isAMomentObject) {
                    var r = moment(t, n);
                    return r.isValid() || (r = moment(t, this.datetime_server_format)), r
                }
                return t._isAMomentObject ? t : i
            }
        }),
        s = require("web.core"),
        i = require("web.field_utils"),
        y = require("web.session"),
        v = s._t,
        b = s.Class.extend({
            screen_classes: [],
            popup_classes: [],
            init: function(t) {
                var i = this;
                this.medical = t.medical,
                this.chrome = t.chrome,
                this.screen_instances = {},
                this.popup_instances = {},
                this.default_screen = null,
                this.startup_screen = null,
                this.current_popup = null,
                this.current_screen = null,
                this.show_sync_errors = !0,
                this.chrome.ready.then(function() {
                    i.close_other_tabs(), i._show_first_screen(), i.medical.bind("change:selectedOrder", function() {
                        i.show_saved_screen(i.medical.get_order(), {
                            default_screen: "calendar"
                        })
                    })
                })
            },
            _show_first_screen: function() {
                var t = this.medical.get_order();
                t ? this.show_saved_screen(t, {
                    default_screen: this.default_screen
                }) : this.show_screen(this.startup_screen)
            },
            add_screen: function(t, i) {
                i.hide(), this.screen_instances[t] = i
            },
            set_default_screen: function(t) {
                this.default_screen = t
            },
            set_startup_screen: function(t) {
                this.startup_screen = t
            },
            show_saved_screen: function(t, i) {
                i = i || {}, this.close_popup(), t ? this.show_screen(t.get_screen_data("screen") || i.default_screen || this.default_screen, null, "refresh") : this.show_screen(this.startup_screen)
            },
            show_screen: function(t, i, n, r) {
                var o = this.screen_instances[t];
                if (n = void 0 == n, !o) {
                    var s = "ERROR: show_screen(" + t + ") : screen not found";
                    console.log("___ screen_name, params, refresh : ", t, i, n, this), this.chrome.show_error({
                        message: s,
                        data: {}
                    }), console.error(s);
                    return
                }
                r || this.close_popup();
                var a = this.medical.get_order();
                if (a) {
                    var c = a.get_screen_data("screen") || "calendar";
                    a.set_screen_data("screen", t), i && a.set_screen_data("params", i), t !== c && a.set_screen_data("previous-screen", c)
                }(n || o !== this.current_screen) && (this.current_screen && (this.current_screen.close(), this.current_screen.hide()), this.current_screen = o, this.current_screen.show(n))
            },
            get_current_screen: function() {
                return this.medical.get_order() ? this.medical.get_order().get_screen_data("screen") || this.default_screen : this.startup_screen
            },
            back: function() {
                var t = this.medical.get_order().get_screen_data("previous-screen");
                t && this.show_screen(t)
            },
            get_current_screen_param: function(t) {
                if (this.medical.get_order()) {
                    var i = this.medical.get_order().get_screen_data("params");
                    return i ? i[t] : void 0
                }
            },
            add_popup: function(t, i) {
                i.hide(), this.popup_instances[t] = i
            },
            show_popup: function(t, i) {
                return this.current_popup && this.close_popup(),
                this.current_popup = this.popup_instances[t],
                this.current_popup || console.log("___ name, options, this.current_popup : ", this.current_popup, t, i, this.popup_instances),
                this.current_popup.show(i)
            },
            show_sync_error_popup: function() {
                this.show_sync_errors && this.show_popup("error-sync", {
                    title: v("Changes could not be saved"),
                    body: v("You must be connected to the internet to save your changes.\n\nOrders that where not synced before will be synced next time you close an order while connected to the internet or when you close the session.")
                })
            },
            close_popup: function() {
                this.current_popup && (this.current_popup.close(), this.current_popup.hide(), this.current_popup = null), this.chrome.unblockUI()
            },
            has_popup: function() {
                return !!this.current_popup
            },
            close_other_tabs: function() {
                var t = this,
                    i = Date.now();
                localStorage.message = "", localStorage.message = JSON.stringify({
                    message: "close_tabs",
                    config: this.medical.config.id,
                    window_uid: i
                }), window.addEventListener("storage", function(n) {
                    var r = n.data;
                    if ("message" === n.key && n.newValue) {
                        var r = JSON.parse(n.newValue);
                        "close_tabs" === r.message && r.config == t.medical.config.id && r.window_uid != i && (console.info("POS / Session opened in another window. EXITING POS"), t._close())
                    }
                }, !1)
            },
            sudo: function(t) {
                return "manager" === (t = t || this.medical.get_cashier()).role ? Promise.resolve(t) : this.select_employee({
                    security: !0,
                    only_managers: !0,
                    title: v("Login as a Manager")
                })
            },
            close: function() {
                var t = this;
                if (this.medical.db.get_orders().length) {
                    var i = function() {
                        if (t.medical.db.get_orders().length) {
                            var i = t.medical.get("failed") ? v("Some orders could not be submitted to the server due to configuration errors. You can exit the Point of Sale, but do not close the session before the issue has been resolved.") : v("Some orders could not be submitted to the server due to internet connection issues. You can exit the Point of Sale, but do not close the session before the issue has been resolved.");
                            t.show_popup("confirm", {
                                title: v("Offline Orders"),
                                body: i,
                                confirm: function() {
                                    t._close()
                                }
                            })
                        } else t._close()
                    };
                    this.medical.push_order().then(i, i)
                } else this._close()
            },
            _close: function() {
                this.chrome.loading_show(), this.chrome.loading_message(v("Closing ...")), this.medical.push_order().then(function() {
                    window.location = "/web#action=medical_js.action_client_medical_menu"
                })
            },
            play_sound: function(t) {
                var i = "";
                if ("error" === t) i = "/medical_js/static/src/sounds/error.wav";
                else if ("bell" === t) i = "/medical_js/static/src/sounds/bell.wav";
                else {
                    console.error("Unknown sound: ", t);
                    return
                }
                $("body").append('<audio src="' + i + '" autoplay="true"></audio>')
            },
            download_file: function(t, i) {
                href_params = this.prepare_file_blob(t, i);
                var n = document.createEvent("HTMLEvents");
                n.initEvent("click"), $("<a>", href_params).get(0).dispatchEvent(n)
            },
            prepare_download_link: function(t, i, n, r) {
                var o = this.prepare_file_blob(t, i);
                $(r).parent().attr(o), $(n).addClass("oe_hidden"), $(r).removeClass("oe_hidden"), $(r).click(function() {
                    $(n).removeClass("oe_hidden"), $(this).addClass("oe_hidden")
                })
            },
            prepare_file_blob: function(t, i) {
                var n = window.URL || window.webkitURL;
                "string" != typeof t && (t = JSON.stringify(t, null, 2));
                var r = new Blob([t]);
                return {
                    download: i || "document.txt",
                    href: n.createObjectURL(r)
                }
            },
            send_email: function(t, i, n) {
                window.open("mailto:" + t + "?subject=" + (i ? window.encodeURIComponent(i) : "") + "&body=" + (n ? window.encodeURIComponent(n) : ""))
            },
            numpad_input: function(t, n, r) {
                var o = t.slice(0);
                r = r || {};
                var s = "-" === o ? o : i.parse.float(o),
                    a = v.database.parameters.decimal_point;
                return (n === a ? r.firstinput ? o = "0." : o.length && "-" !== o ? 0 > o.indexOf(a) && (o += a) : o += "0." : "CLEAR" === n ? o = "" : "BACKSPACE" === n ? o = o.substring(0, o.length - 1) : "+" === n ? "-" === o[0] && (o = o.substring(1, o.length)) : "-" === n ? o = r.firstinput ? "-0" : "-" === o[0] ? o.substring(1, o.length) : "-" + o : "+" !== n[0] || isNaN(parseFloat(n)) ? isNaN(parseInt(n)) || (r.firstinput ? o = "" + n : o += n) : o = this.chrome.format_currency_no_symbol(s + parseFloat(n)), "-" === o && (o = ""), o.length > t.length && o.length > 12) ? (this.play_sound("bell"), t.slice(0)) : o
            }
        }),
        w = function(t) {
            b.prototype.screen_classes.push(t)
        },
        k = function(t) {
            b.prototype.popup_classes.push(t)
        },
        x = {
            Gui: b,
            define_screen: w,
            define_popup: k
        },
        P = s.Class.extend({
            name: "medical_js_db",
            limit: 100,
            init: function(t) {
                t = t || {}, this.name = t.name || this.name, this.limit = t.limit || this.limit, t.uuid && (this.name = this.name + "_" + t.uuid), this.cache = {}, this.product_by_id = {}, this.product_by_barcode = {}, this.product_by_category_id = {}, this.partner_sorted = [], this.partner_by_id = {}, this.partner_by_barcode = {}, this.partner_search_string = "", this.partner_write_date = null, this.category_by_id = {}, this.root_category_id = 0, this.category_products = {}, this.category_ancestors = {}, this.category_childs = {}, this.category_parent = {}, this.category_search_string = {}, this.last_action_by_id = []
            },
            set_uuid: function(t) {
                this.name = this.name + "_" + t
            },
            get_category_by_id: function(t) {
                if (!(t instanceof Array)) return this.category_by_id[t];
                for (var i = [], n = 0, r = t.length; n < r; n++) {
                    var o = this.category_by_id[t[n]];
                    o ? i.push(o) : console.error("get_category_by_id: no category has id:", t[n])
                }
                return i
            },
            get_category_childs_ids: function(t) {
                return this.category_childs[t] || []
            },
            get_category_ancestors_ids: function(t) {
                return this.category_ancestors[t] || []
            },
            get_category_parent_id: function(t) {
                return this.category_parent[t] || this.root_category_id
            },
            add_categories: function(t) {
                var i = this;
                this.category_by_id[this.root_category_id] || (this.category_by_id[this.root_category_id] = {
                    id: this.root_category_id,
                    name: "Root"
                }), t.forEach(function(t) {
                    i.category_by_id[t.id] = t
                }), t.forEach(function(t) {
                    var n = t.parent_id[0];
                    n && i.category_by_id[n] || (n = i.root_category_id), i.category_parent[t.id] = n, i.category_childs[n] || (i.category_childs[n] = []), i.category_childs[n].push(t.id)
                }), ! function t(n, r) {
                    i.category_ancestors[n] = r, (r = r.slice(0)).push(n);
                    for (var o = i.category_childs[n] || [], s = 0, a = o.length; s < a; s++) t(o[s], r)
                }(this.root_category_id, [])
            },
            category_contains: function(t, i) {
                var n = this.product_by_id[i];
                if (n) {
                    for (var r = n.categ_id[0]; r && r !== t;) r = this.category_parent[r];
                    return !!r
                }
                return !1
            },
            load: function(t, i) {
                if (void 0 !== this.cache[t]) return this.cache[t];
                var n = localStorage[this.name + "_" + t];
                return void 0 !== n && "" !== n ? (n = JSON.parse(n), this.cache[t] = n, n) : i
            },
            save: function(t, i) {
                localStorage[this.name + "_" + t] = JSON.stringify(i), this.cache[t] = i
//                localStorage[this.name + "_" + t] = Flatted.parse(Flatted.stringify(i)), this.cache[t] = i
            },
            _product_search_string: function(t) {
                var i = t.display_name;
                return t.barcode && (i += "|" + t.barcode), t.default_code && (i += "|" + t.default_code), t.description && (i += "|" + t.description), t.description_sale && (i += "|" + t.description_sale), i = t.id + ":" + i.replace(/:/g, "") + "\n"
            },
            add_products: function(t) {
                var i = this.product_by_category_id;
                !t instanceof Array && (t = [t]);
                for (var n = 0, r = t.length; n < r; n++) {
                    var o = t[n],
                        s = this._product_search_string(o),
                        a = o.medical_categ_id ? o.medical_categ_id[0] : this.root_category_id;
                    o.product_tmpl_id = o.product_tmpl_id[0], i[a] || (i[a] = []), i[a].push(o.id), void 0 === this.category_search_string[a] && (this.category_search_string[a] = ""), this.category_search_string[a] += s;
                    for (var c = this.get_category_ancestors_ids(a) || [], d = 0, u = c.length; d < u; d++) {
                        var l = c[d];
                        i[l] || (i[l] = []), i[l].push(o.id), void 0 === this.category_search_string[l] && (this.category_search_string[l] = ""), this.category_search_string[l] += s
                    }
                    this.product_by_id[o.id] = o, o.barcode && (this.product_by_barcode[o.barcode] = o)
                }
            },
            _partner_search_string: function(t) {
                var i = t.name || "";
                return t.barcode && (i += "|" + t.barcode), t.address && (i += "|" + t.address), t.phone && (i += "|" + t.phone.split(" ").join("")), t.civil_code && (i += "|" + t.civil_code.split(" ").join("")), t.passport_no && (i += "|" + t.passport_no.split(" ").join("")), t.mobile && (i += "|" + t.mobile.split(" ").join("")), t.email && (i += "|" + t.email), t.vat && (i += "|" + t.vat), i = "" + t.id + ":" + i.replace(":", "") + "\n"
            },
            add_partners: function(t) {
                for (var i, n = 0, r = "", o = 0, s = t.length; o < s; o++) {
                    (i = t[o]).insurance_cards = [];
                    var a = (this.partner_write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z"),
                        c = (i.write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                    !(this.partner_write_date && this.partner_by_id[i.id] && new Date(a).getTime() + 1e3 >= new Date(c).getTime()) && (r < i.write_date && (r = i.write_date), this.partner_by_id[i.id] || this.partner_sorted.push(i.id), this.partner_by_id[i.id] = i, n += 1)
                }
                if (n)
                    for (var d in this.partner_search_string = "", this.partner_by_barcode = {}, this.partner_by_id)(i = this.partner_by_id[d]).barcode && (this.partner_by_barcode[i.barcode] = i), i.address = (i.street ? i.street + ", " : "") + (i.zip ? i.zip + ", " : "") + (i.city ? i.city + ", " : "") + (i.state_id ? i.state_id[1] + ", " : "") + (i.country_id ? i.country_id[1] : ""), this.partner_search_string += this._partner_search_string(i);
                return n
            },
            get_partner_write_date: function() {
                return this.partner_write_date || moment().utc().format("YYYY-MM-DD 00:00:00")
            },
            get_partner_by_id: function(t) {
                return this.partner_by_id[t]
            },
            get_partner_by_barcode: function(t) {
                return this.partner_by_barcode[t]
            },
            get_partners_sorted: function(t) {
                t = t ? Math.min(this.partner_sorted.length, t) : this.partner_sorted.length;
                for (var i = [], n = 0; n < t; n++) i.push(this.partner_by_id[this.partner_sorted[n]]);
                return i
            },
            get_patients_only: function(t) {
                var i = this.get_partners_sorted(t);
                return _.filter(i, function(t) {
                    return !1 == t.is_insurance_company
                })
            },
            search_partner: function(t) {
                try {
                    t = (t = t.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, ".")).replace(/ /g, ".+");
                    var i = RegExp("([0-9]+):.*?" + n.unaccent(t), "gi")
                } catch (r) {
                    return []
                }
                for (var o = [], s = 0; s < this.limit; s++) {
                    var a = i.exec(n.unaccent(this.partner_search_string));
                    if (a) {
                        var c = Number(a[1]);
                        o.push(this.get_partner_by_id(c))
                    } else break
                }
                return o
            },
            clear: function() {
                for (var t = 0, i = arguments.length; t < i; t++) localStorage.removeItem(this.name + "_" + arguments[t])
            },
            _count_props: function(t) {
                var i = 0;
                for (var n in t) t.hasOwnProperty(n) && i++;
                return i
            },
            get_product_by_id: function(t) {
                return this.product_by_id[t]
            },
            get_product_by_barcode: function(t) {
                return this.product_by_barcode[t] ? this.product_by_barcode[t] : void 0
            },
            get_product_by_category: function(t) {
                var i = this.product_by_category_id[t],
                    n = [];
                if (i)
                    for (var r = 0, o = Math.min(i.length, this.limit); r < o; r++) n.push(this.product_by_id[i[r]]);
                return n
            },
            search_product_in_category: function(t, i) {
                try {
                    i = (i = i.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, ".")).replace(/ /g, ".+");
                    var r = RegExp("([0-9]+):.*?" + n.unaccent(i), "gi")
                } catch (o) {
                    return []
                }
                for (var s = [], a = 0; a < this.limit; a++) {
                    var c = this.category_search_string[t];
                    if (!c) break;
                    var d = r.exec(n.unaccent(c));
                    if (d) {
                        var u = Number(d[1]);
                        s.push(this.get_product_by_id(u))
                    } else break
                }
                return s
            },
            is_product_in_category: function(t, i) {
                t instanceof Array || (t = [t]);
                for (var n = this.get_product_by_id(i).categ_id[0]; n;) {
                    for (var r = 0; r < t.length; r++)
                        if (n == t[r]) return !0;
                    n = this.get_category_parent_id(n)
                }
                return !1
            },
            add_order: function(t) {
                for (var i = t.uid, n = this.load("orders", []), r = 0, o = n.length; r < o; r++)
                    if (n[r].id === i) return n[r].data = t, this.save("orders", n), i;
                return this.remove_unpaid_order(t), n.push({
                    id: i,
                    data: t
                }), this.save("orders", n), i
            },
            remove_order: function(t) {
                var i = this.load("orders", []);
                i = _.filter(i, function(i) {
                    return i.id !== t
                }), this.save("orders", i)
            },
            remove_all_orders: function() {
                this.save("orders", [])
            },
            get_orders: function() {
                return this.load("orders", [])
            },
            get_order: function(t) {
                for (var i = this.get_orders(), n = 0, r = i.length; n < r; n++)
                    if (i[n].id === t) return i[n]
            },
            save_unpaid_order: function(t) {
                for (var i = t.uid, n = this.load("unpaid_orders", []), r = t.export_as_JSON(), o = 0; o < n.length; o++)
                    if (n[o].id === i) return n[o].data = r, this.save("unpaid_orders", n), i;
                return n.push({
                    id: i,
                    data: r
                }), this.save("unpaid_orders", n), i
            },
            remove_unpaid_order: function(t) {
                var i = this.load("unpaid_orders", []);
                i = _.filter(i, function(i) {
                    return i.id !== t.uid
                }), this.save("unpaid_orders", i)
            },
            remove_all_unpaid_orders: function() {
                this.save("unpaid_orders", [])
            },
            get_unpaid_orders: function() {
                for (var t = this.load("unpaid_orders", []), i = [], n = 0; n < t.length; n++) i.push(t[n].data);
                return i
            },
            get_unpaid_orders_to_sync: function(t) {
                var i = this.load("unpaid_orders", []),
                    n = [];
                return i.forEach(function(i) {
                    t.includes(i.id) && (i.data.server_id || i.data.lines.length) && n.push(i)
                }), n
            },
            set_order_to_remove_from_server: function(t) {
                if (void 0 !== t.server_id) {
                    var i = this.load("unpaid_orders_to_remove", []);
                    i.push(t.server_id), this.save("unpaid_orders_to_remove", i)
                }
            },
            get_ids_to_remove_from_server: function() {
                return this.load("unpaid_orders_to_remove", [])
            },
            set_ids_removed_from_server: function(t) {
                var i = this.load("unpaid_orders_to_remove", []);
                i = _.filter(i, function(i) {
                    return !t.includes(i)
                }), this.save("unpaid_orders_to_remove", i)
            },
            set_cashier: function(t) {
                this.save("cashier", t || null)
            },
            get_cashier: function() {
                return this.load("cashier")
            }
        }),
        C = require("web.concurrency").Mutex,
        W = require("web.config"),
        I = Backbone.Model.extend({
            initialize: function(t, i) {
                _.extend(this, i)
            },
            get_price: function(t, i) {
                var n = this,
                    r = moment().startOf("day");
                if (void 0 === t) return alert(v("An error occurred when loading product prices. Make sure all pricelists are available in the POS.")), n.lst_price;
                for (var o = [], s = this.categ; s;) o.push(s.id), s = s.parent;
                var a = _.filter(t.items, function(t) {
                        return (!t.product_tmpl_id || t.product_tmpl_id[0] === n.product_tmpl_id) && (!t.product_id || t.product_id[0] === n.id) && (!t.categ_id || _.contains(o, t.categ_id[0])) && (!t.date_start || moment(t.date_start).isSameOrBefore(r)) && (!t.date_end || moment(t.date_end).isSameOrAfter(r))
                    }),
                    c = n.lst_price;
                return _.find(a, function(t) {
                    if (t.min_quantity && i < t.min_quantity) return !1;
                    if ("pricelist" === t.base ? c = n.get_price(t.base_pricelist, i) : "standard_price" === t.base && (c = n.standard_price), "fixed" === t.compute_price) return c = t.fixed_price, !0;
                    if ("percentage" === t.compute_price) return c -= c * (t.percent_price / 100), !0;
                    var r = c;
                    return c -= c * (t.price_discount / 100), t.price_round && (c = l(c, t.price_round)), t.price_surcharge && (c += t.price_surcharge), t.price_min_margin && (c = Math.max(c, r + t.price_min_margin)), t.price_max_margin && (c = Math.min(c, r + t.price_max_margin)), !0
                }), c
            }
        }),
        T = g.extend({
            template: "HeaderButtonWidget",
            init: function(t, i) {
                i = i || {}, this._super(t, i), this.action = i.action, this.label = i.label, this.button_class = i.button_class
            },
            renderElement: function() {
                var t = this;
                this._super(), this.action && this.$el.click(function() {
                    t.action()
                })
            },
            show: function() {
                this.$el.removeClass("oe_hidden")
            },
            hide: function() {
                this.$el.addClass("oe_hidden")
            }
        }),
        E = Backbone.Model.extend({
            initialize: function(t, i) {
                Backbone.Model.prototype.initialize.call(this, i);
                var n = this;
                this.flush_mutex = new C, this.chrome = i.chrome, this.gui = i.gui, this.db = new P, this.debug = W.isDebug(), this.company_logo = null, this.company_logo_base64 = "", this.currency = null, this.company = null, this.user = {}, this.users = [], this.employee = {
                    name: null,
                    id: null,
                    barcode: null,
                    user_id: null,
                    pin: null
                }, this.employees = [], this.partners = [], this.taxes = [], this.medical_session = {}, this.config = null, this.units = [], this.units_by_id = {}, this.default_pricelist = null, this.order_sequence = 1, window.MedicalModel = this;
                var r = RegExp("[?&]config_id=([^&#]*)").exec(window.location.href);

                function o() {
                    var t = n.get_order();
                    this.set("selectedClient", t ? t.get_client() : null)
                }
                this.config_id = r && r[1] && parseInt(r[1]) || !1, this.set({
                    synch: {
                        state: "connected",
                        pending: 0
                    },
                    orders: new d.OrderCollection,
                    selectedOrder: null,
                    selectedClient: null,
                    cashier: null
                }), this.get("orders").bind("add remove change", o, this), this.bind("change:selectedOrder", o, this), this.ready = this.load_server_data().then(function() {
                    return n.after_load_server_data()
                })
            },
            set_order: function(t) {
                this.set({
                    selectedOrder: t
                })
            },
            short_toPosOrder_line_upd: (t, i, n) => n,
            short_toPosOrder: function(t) {
                var i = this,
                    n = this.get_order().screen_data || {},
                    r = i.add_new_order({
                        screen_data: n
                    });
                if (!_.isEmpty(t)) {
                    var o = t.partner && t.partner.id,
                        s = {};
                    o && (s = i.db.get_partner_by_id(o), r.set_client(s)), _.each(t.order_lines || [], function(n) {
                        var o = i.db.product_by_id[n.product_id[0]];
                        if (!_.isUndefined(o)) {
                            r.add_product(o, {
                                quantity: parseFloat(n.qty),
                                price: n.price_unit,
                                discount: n.discount,
                                discount_fixed: n.discount_fixed,
                                analytic_account_id: n.analytic_account_id && n.analytic_account_id[0],
                                analytic_tag_ids: n.analytic_tag_ids,
                                consumable_ids: n.consumable_ids
                            });
                            var s = r.get_last_orderline();
                            s = i.short_toPosOrder_line_upd(t, n, s), r.add_orderline(s)
                        }
                    })
                }
                return r
            },
            toPosOrder: function(t, i) {
                var n = this,
                    r = n.add_new_order();
                if (!_.isEmpty(t)) {
                    var o = t.partner_id && t.partner_id[0],
                        s = {};
                    o && (s = n.db.get_partner_by_id(o), r.set_client(s));
                    var a = n.config.depends_on;
                    if (!_.isEmpty(s) && a in s && s[a] && (s[a] = t[a]), r.set_resource_id(t.resource_id && t.resource_id[0]), r.set_start_time(new Date(t.start_time)), n.config.enable_insurance && t.insurance_card_id && t.insurance_card_id.length > 1) {
                        var c = this.insurance_card_by_id[t.insurance_card_id[0]];
                        c && r.set_insurance_card(c)
                    }
                    if (t.pricelist_id && t.pricelist_id.length) {
                        var d = _.findWhere(this.pricelists, {
                            id: t.pricelist_id[0]
                        });
                        d && r.set_pricelist(d)
                    }
                    r.clinic_id = t.clinic_id, r.end_time = t.end_time, r.invoice_note = t.invoice_note, r.is_followup = t.is_followup, r.is_first = t.is_first, r.amount_paid = t.amount_paid || 0, r.net_amount = t.net_amount, r.amount_due = t.amount_due, r.paymentlines = t.paymentlines, r.is_readonly = t.is_readonly, r.sequence_no = t.sequence_no, r.analytic_tag_ids = t.analytic_tag_ids, r.analytic_account_id = t.analytic_account_id && t.analytic_account_id[0] || !1, r.ins_approval_no = t.ins_approval_no, r.ins_ticket_no = t.ins_ticket_no, r.ins_ref = t.ins_ref, r.ins_member = t.ins_member;
                    var u = t.ui_reference,
                        l = u ? u.split(" ") : [],
                        p = l.length > 1 ? l[1] : u;
                    i && "duplicate" == i || (r.orig_order_id = t.id, r.server_id = t.id, r.state = t.state, r.name = t.name, r.ui_reference = u, r.uid = p || r.uid), _.each(t.order_lines, function(o) {
                        var s = n.db.product_by_id[o.product_id[0]];
                        if (s) {
                            r.add_product(s, {
                                quantity: parseFloat(o.qty),
                                price: o.price_unit,
                                analytic_account_id: o.analytic_account_id && o.analytic_account_id[0],
                                analytic_tag_ids: o.analytic_tag_ids,
                                consumable_ids: o.consumable_ids
                            });
                            var a = r.get_last_orderline();
                            o.discount ? a.set_discount(o.discount) : o.discount_fixed && a.set_fix_discount(o.discount_fixed), a.update_db_line_data(t, o, i), a.line_id = o.line_id, a.set_insurance_cover(o), a.price_unit_orig = o.price_unit_orig, a.approved_price_unit = o.approved_price_unit, a.related_pkg_id = o.related_pkg_id, a.pkg_index = o.pkg_index, a.duration = o.duration, a.pricelist_item_id = o.pricelist_item_id && o.pricelist_item_id[0] || !1, a.employee_id = o.employee_id && o.employee_id[0] || !1, r.add_orderline(a)
                        }
                    })
                }
                return r.update_db_data(t, i), r
            },
            get_order_list: function() {
                return this.get("orders").models
            },
            after_load_server_data: function() {
                return this.load_orders(), this.set_start_order(), Promise.resolve()
            },
            load_orders: function() {
                for (var t = this.db.get_unpaid_orders(), i = [], n = 0; n < t.length; n++) {
                    var r = t[n];
                    r.medical_session_id === this.medical_session.id && i.push(new d.Order({}, {
                        medical: this,
                        json: r
                    }))
                }
                for (var n = 0; n < t.length; n++) {
                    var r = t[n];
                    r.medical_session_id !== this.medical_session.id && r.lines.length > 0 ? i.push(new d.Order({}, {
                        medical: this,
                        json: r
                    })) : r.medical_session_id !== this.medical_session.id && this.db.remove_unpaid_order(t[n])
                }(i = i.sort(function(t, i) {
                    return t.sequence_number - i.sequence_number
                })).length && this.get("orders").add(i)
            },
            set_start_order: function() {
                var t = this.get("orders").models;
                t.length && !this.get("selectedOrder") ? this.set("selectedOrder", t[0]) : this.add_new_order()
            },
            destroy: function() {
                this.flush()
            },
            toCalendarResource: function(t) {
                var i = [];
                return _.each(t, function(t) {
                    i.push({
                        id: t.id,
                        title: t.name || t.title,
                        sequence: t.sequence || 8
                    })
                }), i
            },
            generate_by_id: function(t, i) {
                return i = i || "id", _.indexBy(t, i)
            },
            models: [{
                label: "version",
                loaded: function(t) {
                    return y.rpc("/web/webclient/version_info", {}).then(function(i) {
                        t.version = i
                    })
                }
            }, {
                model: "res.company",
                fields: ["currency_id", "email", "website", "company_code", "vat", "name", "phone", "partner_id", "country_id", "state_id", "tax_calculation_rounding_method", "max_apmt_no_show", "max_apmt_cancel", "auto_patient_sequence", "auto_derma_sequence", "depends_on"],
                ids: function(t) {
                    return [y.user_context.allowed_company_ids[0]]
                },
                loaded: function(t, i) {
                    t.company = i[0], t.chrome.company = i[0]
                }
            }, {
                model: "decimal.precision",
                fields: ["name", "digits"],
                loaded: function(t, i) {
                    t.dp = {};
                    for (var n = 0; n < i.length; n++) t.dp[i[n].name] = i[n].digits
                }
            }, {
                model: "uom.uom",
                fields: [],
                domain: null,
                context: function(t) {
                    return {
                        active_test: !1
                    }
                },
                loaded: function(t, i) {
                    t.units = i, _.each(i, function(i) {
                        t.units_by_id[i.id] = i
                    })
                }
            }, {
                model: "medical.attachment.type",
                fields: ["name"],
                loaded: function(t, i) {
                    t.attachment_types = i
                }
            }, {
                model: "medical.session",
                fields: ["id", "name", "user_id", "config_id", "start_at", "stop_at", "statement_ids", "login_number", "sequence_number"],
                domain: function(t) {
                    var i = [
                        ["state", "=", "opened"],
                    ];
                    return t.config_id && i.push(["config_id", "=", t.config_id]), i
                },
                loaded: function(t, i, n) {
                    t.medical_session = i[0], t.config_id = t.config_id || t.medical_session && t.medical_session.config_id[0]
                }
            }, {
                model: "medical.config",
                fields: [],
                domain: function(t) {
                    return [
                        ["id", "=", t.config_id]
                    ]
                },
                loaded: function(t, i) {
                    if (i && i.length) {
                        var n = i[0];
                        t.config = n, t.config.sync_wait_time = 5, t.db.save("current_session_id", n.current_session_id[0]);
                        var r = t.db.get_orders();
                        console.log("___ Config : ", n, t.get("orders"), t);
                        for (var o = 0; o < r.length; o++) t.medical_session.sequence_number = Math.max(t.medical_session.sequence_number, r[o].data.sequence_number + 1)
                    }
                    t.db.set_uuid(W.uuid), t.set_cashier(t.get_cashier())
                }
            }, {
                model: "res.partner",
                label: "load_partners",
                fields: m,
                context: {
                    quick_load_limit: 100
                },
                domain: [
                    ["is_insurance_company", "=", !1],
                    ["user_ids", "=", !1]
                ],
                loaded: function(t, i) {
                    t.db.partner_write_date = moment().utc().format("YYYY-MM-DD 00:00:00"), t.partners = i, t.db.add_partners(i)
                }
            }, {
                model: "res.partner",
                condition: function(t) {
                    return t.config.enable_insurance
                },
                label: "Insurance_Company",
                fields: m,
                domain: [
                    ["is_insurance_company", "=", !0]
                ],
                loaded: function(t, i) {
                    for (var n, r = [], o = [], s = 0, a = i.length; s < a; s++)(n = i[s]).parent_id ? r.push(n) : o.push(n);
                    t.ins_sub_companies = r, t.ins_main_companies = o
                }
            }, {
                model: "res.country.state",
                fields: ["name", "country_id"],
                loaded: function(t, i) {
                    t.states = i
                }
            }, {
                model: "res.area",
                fields: ["name", "code"],
                loaded: function(t, i) {
                    t.all_areas = i
                }
            }, {
                model: "res.country",
                fields: ["name", "vat_label", "code"],
                loaded: function(t, i) {
                    t.countries = i, t.company.country = null;
                    for (var n = 0; n < i.length; n++) i[n].id === t.company.country_id[0] && (t.company.country = i[n])
                }
            }, {
                model: "account.analytic.tag",
                fields: ["name"],
                loaded: function(t, i) {
                    t.analytic_tags = i, t.analytic_tag_by_id = t.generate_by_id(i)
                }
            }, {
                model: "account.analytic.account",
                fields: ["name"],
                loaded: function(t, i) {
                    t.analytic_accounts = i, t.analytic_account_by_id = t.generate_by_id(i)
                }
            }, {
                model: "account.tax",
                fields: ["name", "amount", "price_include", "include_base_amount", "amount_type", "children_tax_ids"],
                domain: function(t) {
                    return [
                        ["company_id", "=", t.company && t.company.id || !1]
                    ]
                },
                loaded: function(t, i) {
                    return t.taxes = i, t.taxes_by_id = {}, _.each(i, function(i) {
                        t.taxes_by_id[i.id] = i
                    }), _.each(t.taxes_by_id, function(i) {
                        i.children_tax_ids = _.map(i.children_tax_ids, function(i) {
                            return t.taxes_by_id[i]
                        })
                    }), new Promise(function(i, n) {
                        var r = _.pluck(t.taxes, "id");
                        c.query({
                            model: "account.tax",
                            method: "get_real_tax_amount",
                            args: [r]
                        }).then(function(n) {
                            _.each(n, function(i) {
                                t.taxes_by_id[i.id].amount = i.amount
                            }), i()
                        })
                    })
                }
            }, {
                model: "res.users",
                fields: ["name", "company_id", "id", "groups_id"],
                domain: function(t) {
                    return [
                        ["company_ids", "in", [t.config.company_id[0]]], "|", "|", "|", "|", ["groups_id", "=", t.config.group_medical_admin_id[0]],
                        ["groups_id", "=", t.config.group_medical_cashier_id[0]],
                        ["groups_id", "=", t.config.group_medical_user_id[0]],
                        ["groups_id", "=", t.config.group_medical_invoice_reset[0]],
                        ["groups_id", "=", t.config.group_medical_invoice_paid_edit[0]],
                    ]
                },
                loaded: function(t, i) {
                    console.log("User is loaded"), i.forEach(function(i) {
                        if (i.role = "user", i.groups_id.some(function(n) {
                                return n === t.config.group_medical_admin_id[0] ? (i.role = "manager", !0) : n === t.config.group_medical_cashier_id[0] ? (i.role = "cashier", !0) : void 0
                            }), i.id === y.uid) {
                            t.user = i;
                            var n = t.config.group_medical_invoice_reset,
                                r = t.config.group_medical_invoice_paid_edit; - 1 != t.user.groups_id.indexOf(n[0]) ? t.user.is_reset_invoice = "true" : t.user.is_reset_invoice = "false", -1 != t.user.groups_id.indexOf(r[0]) ? t.user.is_edit_paid_invoice = "true" : t.user.is_edit_paid_invoice = "false", console.log("Selected User is : ", t.user), console.log("Reset Invoice Group : ", n), console.log("Edit Paid Invoice Group : ", r), console.log("Session is : ", y)
                        }
                    }), t.users = i
                }
            }, {
                model: "hr.employee",
                fields: ["name", "department_id", "clinic_id", "mobile_phone", "user_id", "pin", "max_discount", "is_medical_user"],
                domain: function(t) {
                    var i = t.config.resource_emp_ids.length && ["id", "in", t.config.resource_emp_ids] || [],
                        n = t.config.allowed_dept_ids.length && ["department_id", "child_of", t.config.allowed_dept_ids] || [],
                        r = [];
                    return i.length && n.length && r.push("|"), i.length && r.push(i), n.length && r.push(n), r
                },
                loaded: function(t, i) {
                    var n = _.where(i, {
                        is_medical_user: !0
                    });
                    t.employees = n;
                    var r = t.config.default_employee_id && t.config.default_employee_id[0],
                        o = _.findWhere(n, {
                            id: r
                        });
                    t.set_cashier(o);
                    var s = [],
                        a = {};
                    _.each(n, function(i) {
                        _.indexOf(t.config.employee_ids, i.id) >= 0 && s.push(i)
                    }), _.each(i, function(t) {
                        if (t.clinic_id && 2 == t.clinic_id.length) {
                            var i = t.clinic_id[0];
                            a.hasOwnProperty(i) ? a[i].push(t) : a[i] = [t]
                        }
                    }), t.allowed_employees = s, t.all_employees = i, t.employees_by_branch = a
                }
            }, {
                model: "account.journal",
                fields: ["name", "need_ref"],
                domain: function(t) {
                    return [
                        ["id", "in", t.config.journal_ids]
                    ]
                },
                loaded: function(t, i) {
                    t.cashregisters = i, t.cashregister_by_id = t.generate_by_id(i), console.log("CashRegister : ", t.cashregisters)
                }
            }, {
                model: "medical.resource",
                fields: ["name", "display_name", "note", "clinic_name", "working_hour_id", "hr_staff_id", "sequence", "analytic_account_id", "group_id", "pricelist_id", "emp_ids"],
                loaded: function(t, i) {
                    _.each(i, function(t) {
                        t.name = t.display_name
                    }), t.db.all_resources = i;
                    var n = {},
                        r = {},
                        o = [];
                    _.each(i, function(t) {
                        n[t.id] = t;
                        var i = t.group_id;
                        if (i) {
                            var s = _.findWhere(o, {
                                id: i[0]
                            });
                            s ? s.resources.push(t) : (s = {
                                id: i[0],
                                name: i[1],
                                resources: [t]
                            }, o.push(s), r[i[0]] = s)
                        }
                    }), t.resource_by_id = n, t.resource_group_by_id = r, t.db.all_resource_groups = o, t.db.cal_resources = t.toCalendarResource(i)
                }
            }, {
                model: "medical.clinic",
                fields: ["name", "resource_ids"],
                loaded: function(t, i) {
                    var n = t.db.cal_resources,
                        r = t.config.clinic_id && t.config.clinic_id[0];
                    _.each(i, function(i) {
                        var o = _.filter(n, function(t) {
                            return _.indexOf(i.resource_ids, t.id) > -1
                        });
                        i.resources = o, i.id == r && (t.current_clinic = i, t.clinic = i)
                    }), t.db.all_clinics = i, t.db.clinic_by_id = t.generate_by_id(i)
                }
            }, {
                model: "product.pricelist",
                fields: ["name", "display_name", "ins_based_on", "discount_policy", "scheme_code", "share_limit_type", "insurance_company_id", "insurance_parent_id", "need_approval"],
                domain: function(t) {
                    return t.company.id ? (console.log("____ self.config.company_id[0] : ", t.config.company_id[0]), [
                        ["company_id", "in", [t.company.id, !1]]
                    ]) : []
                },
                loaded: function(t, i) {
                    _.map(i, function(t) {
                        t.items = []
                    }), t.default_pricelist = _.findWhere(i, {
                        id: t.config.pricelist_id[0]
                    }), t.pricelists = _.filter(i, function(i) {
                        return _.indexOf(t.config.allowed_pricelist_ids, i.id) >= 0
                    }), t.insurance_schemes = _.filter(i, function(t) {
                        return !1 != t.insurance_company_id
                    })
                }
            }, {
                model: "product.pricelist.item",
                domain: function(t) {
                    return [
                        ["pricelist_id", "in", _.pluck(t.pricelists, "id")],
                        ["pricelist_id.insurance_company_id", "=", !1]
                    ]
                },
                loaded: function(t, i) {
                    var n = {};
                    _.each(t.pricelists, function(t) {
                        n[t.id] = t
                    }), _.each(i, function(t) {
                        n[t.pricelist_id[0]].items.push(t), t.base_pricelist = n[t.base_pricelist_id[0]]
                    })
                }
            }, {
                model: "product.category",
                fields: ["name", "parent_id"],
                loaded: function(t, i) {
                    var n = {};
                    _.each(i, function(t) {
                        n[t.id] = t
                    }), _.each(i, function(t) {
                        t.parent = n[t.parent_id[0]]
                    }), t.product_categories = i
                }
            }, {
                model: "res.currency",
                fields: ["name", "symbol", "position", "rounding", "rate"],
                ids: function(t) {
                    return [t.config.currency_id[0], t.company.currency_id[0]]
                },
                loaded: function(t, i) {
                    t.currency = i[0], t.currency.rounding > 0 && t.currency.rounding < 1 ? t.currency.decimals = Math.ceil(Math.log(1 / t.currency.rounding) / Math.log(10)) : t.currency.decimals = 0, t.company_currency = i[1]
                }
            }, {
                model: "medical.category",
                fields: ["id", "name", "parent_id", "child_ids"],
                domain: function(t) {
                    return t.config.limit_categ_ids && t.config.limit_categ_ids.length ? [
                        ["id", "in", t.config.limit_categ_ids]
                    ] : []
                },
                loaded: function(t, i) {
                    t.db.medical_categories = i, t.db.add_categories(i)
                }
            }, {
                model: "product.product",
                fields: ["display_name", "lst_price", "standard_price", "categ_id", "taxes_id", "barcode", "default_code", "uom_id", "description_sale", "description", "product_tmpl_id", "tracking", "type", "medical_categ_id", "available_in_medical", "is_medical_service", "is_medical_consumable", "duration", "session_count", "analytic_account_id", "consumable_ids", "analytic_tag_ids"],
                order: _.map(["sequence", "default_code", "name"], function(t) {
                    return {
                        name: t
                    }
                }),
                domain: function(t) {
                    var i = [
                        ["sale_ok", "=", !0],
                        ["company_id", "in", [t.config.company_id[0], !1]]
                    ];
                    return t.config.limit_categories && t.config.iface_available_categ_ids.length && (i.unshift("&"), i.push(["medical_categ_id", "in", t.config.iface_available_categ_ids])), t.config.iface_tipproduct && (i.unshift(["id", "=", t.config.tip_product_id[0]]), i.unshift("|")), i
                },
                context: function(t) {
                    return {
                        display_default_code: !1
                    }
                },
                loaded: function(t, i) {
                    var n = t.config.currency_id[0] === t.company.currency_id[0],
                        r = t.currency.rate / t.company_currency.rate,
                        o = _.where(i, {
                            is_medical_consumable: !0
                        });
                    console.log("__ consumable_products : ", o, _.pluck(i, "is_medical_consumable"));
                    var s = _.map(i, function(i) {
                        n || (i.lst_price = l(i.lst_price * r, t.currency.rounding)), i.categ = _.findWhere(t.product_categories, {
                            id: i.categ_id[0]
                        });
                        var o = {};
                        return i.medical_categ_id && i.medical_categ_id.length > 0 && (o = t.db.category_by_id[i.medical_categ_id[0]]), i.medical_categ = o, new I({}, i)
                    });
                    t.db.all_products = s, t.db.product_consumables = o, t.db.add_products(s)
                }
            }, {
                model: "account.fiscal.position",
                fields: [],
                domain: function(t) {
                    return [
                        ["id", "in", t.config.fiscal_position_ids]
                    ]
                },
                loaded: function(t, i) {
                    t.fiscal_positions = i
                }
            }, {
                model: "account.fiscal.position.tax",
                fields: [],
                domain: function(t) {
                    var i = [];
                    return t.fiscal_positions.forEach(function(t) {
                        t.tax_ids.forEach(function(t) {
                            i.push(t)
                        })
                    }), [
                        ["id", "in", i]
                    ]
                },
                loaded: function(t, i) {
                    t.fiscal_position_taxes = i, t.fiscal_positions.forEach(function(t) {
                        t.fiscal_position_taxes_by_id = {}, t.tax_ids.forEach(function(n) {
                            var r = _.find(i, function(t) {
                                return t.id === n
                            });
                            t.fiscal_position_taxes_by_id[r.id] = r
                        })
                    })
                }
            }, {
                model: "medical.state",
                fields: ["id", "name", "sequence", "s_color"],
                loaded: function(t, i) {
                    var n = {};
                    _.each(i, function(t) {
                        n[t.id] = t
                    }), t.db.states_by_id = n
                }
            }, {
                model: "resource.calendar",
                fields: ["name", "attendance_ids", "hours_per_day", "tz"],
                loaded: function(t, i) {
                    var n = {};
                    _.each(i, function(t) {
                        t.attendances = [], n[t.id] = t
                    }), t.calendars = i, t.calendar_by_id = n
                }
            }, {
                model: "resource.calendar.attendance",
                fields: ["calendar_id", "date_from", "date_to", "dayofweek", "hour_from", "hour_to", "name", "branch_id"],
                loaded: function(t, i) {
                    _.each(i, function(i) {
                        if (i && i.calendar_id && i.calendar_id.length > 1) {
                            var n = t.calendar_by_id[i.calendar_id[0]];
                            n && n.attendances.push(i)
                        }
                    })
                }
            }, {
                model: "insurance.card",
                condition: function(t) {
                    return t.config.enable_insurance
                },
                fields: ["name", "partner_id", "ins_based_on", "main_company_id", "insurance_company_id", "pricelist_id", "issue_date", "expiry_date", "state", "ins_based_on"],
                domain: [
                    ["state", "=", "running"]
                ],
                loaded: function(t, i) {
                    t.insurance_card_by_id = t.generate_by_id(i), _.each(i, function(i) {
                        var n = t.db.get_partner_by_id(i.partner_id[0]);
                        n && n.insurance_cards.push(i)
                    })
                }
            }, {
                model: "utm.source",
                fields: ["name"],
                loaded: function(t, i) {
                    t.utm_sources = i
                }
            }, {
                model: "utm.medium",
                fields: ["name"],
                loaded: function(t, i) {
                    t.utm_mediums = i
                }
            }, {
                model: "last.action",
                condition: function(t) {
                    return t.config.enable_followup
                },
                fields: ["name", "use_in_state"],
                loaded: function(t, i) {
                    var n = {};
                    _.each(i, function(t) {
                        n[t.id] = t
                    }), t.db.last_action_by_id = n
                }
            }, {
                model: "complain.type",
                condition: function(t) {
                    return t.config.enable_app_complain
                },
                fields: ["name"],
                loaded: function(t, i) {
                    t.complain_types = i
                }
            }, {
                model: "discount.reason",
                condition: function(t) {
                    return t.config.allow_global_disc
                },
                fields: ["name"],
                loaded: function(t, i) {
                    t.discount_reasons = i
                }
            }, {
                model: "visit.option",
                condition: function(t) {
                    return t.config.enable_visit_option
                },
                fields: ["name"],
                loaded: function(t, i) {
                    t.visit_options = i
                }
            }],
            load_server_data: function() {
                var t = this,
                    i = 0,
                    n = 1 / t.models.length,
                    r = {};
                return this.chrome.loading_show(), new Promise(function(o, s) {
                    try {
                        return function a(d) {
                            if (d >= t.models.length) o();
                            else {
                                var u = t.models[d];
                                if (t.chrome.loading_message(v("Loading") + " " + (u.label || u.model || ""), i), !("function" != typeof u.condition || u.condition(t, r))) {
                                    a(d + 1);
                                    return
                                }
                                var l = "function" == typeof u.fields ? u.fields(t, r) : u.fields,
                                    p = "function" == typeof u.domain ? u.domain(t, r) : u.domain,
                                    h = "function" == typeof u.context ? u.context(t, r) : u.context || {},
                                    f = "function" == typeof u.ids ? u.ids(t, r) : u.ids,
                                    m = "function" == typeof u.order ? u.order(t, r) : u.order;
                                if (i += n, u.model) {
                                    var g = {
                                        model: u.model,
                                        context: _.extend(h, y.user_context || {})
                                    };
                                    u.ids ? (g.method = "read", g.args = [f, l]) : (g.method = "search_read", g.domain = p, g.fields = l, g.orderBy = m), c.query(g).then(function(i) {
                                        try {
                                            Promise.resolve(u.loaded(t, i, r)).then(function() {
                                                a(d + 1)
                                            }, function(t) {
                                                s(t)
                                            })
                                        } catch (n) {
                                            console.error(n.message, n.stack), s(n)
                                        }
                                    }, function(t) {
                                        s(t)
                                    })
                                } else if (u.loaded) try {
                                    Promise.resolve(u.loaded(t, r)).then(function() {
                                        a(d + 1)
                                    }, function(t) {
                                        s(t)
                                    })
                                } catch (b) {
                                    s(b)
                                } else a(d + 1)
                            }
                        }(0)
                    } catch (a) {
                        return Promise.reject(a)
                    }
                })
            },
            prepare_new_partners_domain: function() {
                return [
                    ["write_date", ">", this.db.get_partner_write_date()],
                    ["is_insurance_company", "=", !1]
                ]
            },
            load_new_partners: function() {
                var t = this;
                return new Promise(function(i, n) {
                    var r = _.find(t.models, function(t) {
                            return "load_partners" === t.label
                        }).fields,
                        o = t.prepare_new_partners_domain();
                    c.query({
                        model: "res.partner",
                        method: "search_read",
                        args: [o, r]
                    }, {
                        timeout: 6e3,
                        shadow: !0
                    }).then(function(r) {
                        t.db.add_partners(r) ? i() : n()
                    }, function(t, i) {
                        n()
                    })
                })
            },
            on_removed_order: function(t, i, n) {
                var r = this.get_order_list();
                ("abandon" === n || t.temporary) && r.length > 0 ? this.set_order(r[i] || r[r.length - 1]) : this.add_new_order()
            },
            get_order: function() {
                return this.get("selectedOrder")
            },
            get_clinic: function() {
                var t = parseInt($(".js_clinic option:selected").val());
                return this.db.clinic_by_id[t]
            },
            get_cashier: function() {
                return this.db.get_cashier() || this.get("cashier") || this.employee
            },
            set_cashier: function(t) {
                this.set("cashier", t), this.db.set_cashier(this.get("cashier"))
            },
            add_new_order: function(t) {
                t = t || {};
                var i = new d.Order({}, _.extend({}, {
                    medical: this
                }, t));
                return this.get("orders").add(i), this.set("selectedOrder", i), i
            },
            reloadEvents: function(t, i, n, r) {
                var o = _.findWhere(this.models, {
                    model: "res.partner"
                }).fields;
                return y.rpc("/medical/appointments", {
                    from_dtime: t,
                    to_dtime: i,
                    tz: n,
                    partner_fields: o,
                    branch_id: r,
                    config_id: this.config.id
                })
            },
            reloadResources: function() {
                return this._rpc({
                    model: "medical.resource",
                    method: "search_read",
                    args: [
                        [],
                        ["display_name", "id", "resource_id", "sequence"]
                    ]
                })
            },
            open_aging_popup: function(t) {
                var i = this;
                c.query({
                    route: "/partner/aging-report",
                    params: {
                        partner_id: t
                    }
                }).then(function(t) {
                    t && i.gui.show_popup("partner-aging", {
                        aging_data: t
                    })
                })
            },
            push_order: function(t, i) {
                i = i || {
                    show_error: !1
                };
                var n = this;
                return console.log("___ push_order order : ", t && t.export_as_JSON() || {}), t && this.db.add_order(t.export_as_JSON()), new Promise(function(t, r) {
                    n.flush_mutex.exec(function() {
                        var o = n._flush_orders(n.db.get_orders(), i);
                        return o.then(t, r), o
                    })
                })
            },
            _flush_orders: function(t, i) {
                var n = this;
                return this.set_synch("connecting", t.length), this._save_to_server(t, i).then(function(t) {
                    return n.set_synch("connected"), t
                }).catch(function(t) {
                    return Promise.reject(t)
                })
            },
            set_synch: function(t, i) {
                -1 === ["connected", "connecting", "error", "disconnected"].indexOf(t) && console.error(t, " is not a known connection state."), i = i || this.db.get_orders().length + this.db.get_ids_to_remove_from_server().length, this.set("synch", {
                    state: t,
                    pending: i
                })
            },
            _save_to_server: function(t, i) {
                if (!t || !t.length) return Promise.resolve([]);
                var n = this,
                    r = "number" == typeof(i = i || {}).timeout ? i.timeout : 3e4 * t.length,
                    o = _.pluck(t, "id"),
                    s = [_.map(t, function(t) {
                        return t.to_invoice = i.to_invoice || !1, t
                    })];
                return c.query({
                    model: "medical.order",
                    method: "create_from_ui",
                    args: s,
                    kwargs: {
                        context: y.user_context
                    }
                }, {
                    timeout: r,
                    shadow: !i.to_invoice
                }).then(function(t) {
                    return _.each(o, function(t) {
                        n.db.remove_order(t)
                    }), n.set("failed", !1), t
                }).catch(function(i) {
                    throw _.each(o, function(t) {
                        n.db.remove_order(t)
                    }), n.set("failed", !1), console.warn("Failed to send orders:", t), ""
                })
            },
            _rpc_check_insurance_wrapper: function(t, i) {
                var n = this;
                return console.log("___ _ins_wrapper : card, lines : ", t, i), this.chrome._rpc({
                    model: "insurance.card",
                    method: "check_insurance_wrapper",
                    args: [t, i]
                }).then(function(t) {
                    console.log("___ Result Insurance Check : ", t);
                    var r = [];
                    _.each(_.keys(t), function(o) {
                        var s = n.db.get_product_by_id(o),
                            a = t[o],
                            c = i[o].is_insurance_applicable,
                            d = i[o].qty,
                            u = a.price_unit_orig;
                        a.pricelist_item_id && (u = a.price_unit + (u - a.approved_price_unit)), a.payable_price_unit = u, a.product = s, a.is_insurance_applicable = c, r.push({
                            product: s,
                            result: a,
                            is_checked: c,
                            qty: d
                        })
                    });
                    var o = {
                        lines: r,
                        result_by_product: t
                    };
                    return console.log("___ _rpc_check_insurance_wrapper : result : ", o), o
                })
            }
        }),
        O = function(t, i) {
            i instanceof Array || (i = [i]);
            for (var n = E.prototype.models, r = 0; r < n.length; r++) {
                var o = n[r];
                o.model === t && o.fields instanceof Array && o.fields.length > 0 && (o.fields = o.fields.concat(i || []))
            }
        },
        S = function(t, i) {
            i = i || {}, t instanceof Array || (t = [t]);
            var n = E.prototype.models,
                r = n.length;
            if (i.before) {
                for (var o = 0; o < n.length; o++)
                    if (n[o].model === i.before || n[o].label === i.before) {
                        r = o;
                        break
                    }
            } else if (i.after)
                for (var o = 0; o < n.length; o++)(n[o].model === i.after || n[o].label === i.after) && (r = o + 1);
            n.splice.apply(n, [r, 0].concat(t))
        },
        q = g.extend({
            status: ["connected", "connecting", "disconnected", "warning", "error"],
            set_status: function(t, i) {
                for (var n = 0; n < this.status.length; n++) this.$(".js_" + this.status[n]).addClass("oe_hidden");
                this.$(".js_" + t).removeClass("oe_hidden"), i ? this.$(".js_msg").removeClass("oe_hidden").html(i) : this.$(".js_msg").addClass("oe_hidden").html("")
            }
        }),
        U = q.extend({
            template: "SynchNotificationWidget",
            start: function() {
                var t = this;
                t.allowSync = !0, this.medical.bind("change:synch", function(i, n) {
                    t.set_status(n.state, n.pending)
                }), this.$el.click(function() {
                    t.allowSync && (t.allowSync = !1, t.medical.push_order(null, {
                        show_error: !1
                    }), setTimeout(function() {
                        t.allowSync = !0
                    }, 6e4 * t.medical.config.sync_wait_time))
                }), this.$el.off("click"), this.$el.click(function() {})
            }
        }),
        M = q.extend({
            template: "WidgetFullScreen",
            start: function() {
                this.$el.off("click"), this.$el.click(function(t) {
                    t.stopPropagation(), $(document).toggleFullScreen()
                })
            }
        }),
        D = require("web.AbstractAction"),
        Y = require("web.CrashManager").CrashManager,
        R = g.extend(D.prototype, {
            template: "Chrome",
            init: function() {
                var t = this;
                this._super(arguments[0], {}), this.started = new $.Deferred, this.ready = new $.Deferred;
                var i = this.getSession();
                this.current_session = i, this.medical = new E(i, {
                    chrome: this
                }), this.gui = new b({
                    medical: this.medical,
                    chrome: this
                }), this.chrome = this, this.medical.gui = this.gui, this.company_id = i.company_id, this.company = i.user_companies.current_company[1], this.logo_click_time = 0, this.logo_click_count = 0, this.previous_touch_y_coordinate = -1, this.widget = {}, this.medical.ready.then(function() {
                    t.build_chrome(), t.build_widgets(), t.disable_rubberbanding(), t.disable_backpace_back(), t.ready.resolve(), t.loading_hide(), t.replace_crashmanager(), t.build_auto_refresh()
                }).guardedCatch(function(i) {
                    t.loading_error(i)
                })
            },
            build_auto_refresh: function() {
                var t = this,
                    i = 1e4;
                this.medical.config.auto_refresh_interval && (i = 6e4 * this.medical.config.auto_refresh_interval), this.auto_refresh_timeout = setInterval(function() {
                    t.execute_auto_refresh_pool()
                }, i), t.execute_auto_refresh_pool()
            },
            execute_auto_refresh_pool: function() {
                console.info("___ Executing Auto Pull Count : ", this.medical.config.auto_refresh_interval, new Date)
            },
            cleanup_dom: function() {
                $(document).off(), $(window).off(), $("html").off(), $("body").off()
            },
            build_chrome: function() {
                this.renderElement(), this.menu_buttons = {};
                for (var t = f, i = 0; i < t.length; i++) {
                    var n = t[i];
                    if (!n.condition || n.condition.call(this)) {
                        var r = new n.widget(this, {});
                        r.appendTo(this.$(".control-buttons")), this.menu_buttons[n.name] = r
                    }
                }
                _.size(this.menu_buttons) && this.$(".control-buttons").removeClass("oe_hidden")
            },
            show_error: function(t) {
                this.gui.show_popup("error-traceback", {
                    title: t.message,
                    body: t.message + "\n" + t.data.debug + "\n"
                })
            },
            replace_crashmanager: function() {
                var t = this;
                Y.include({
                    show_error: function(i) {
                        t.gui ? t.show_error(i) : this._super(i)
                    }
                })
            },
            click_logo: function() {
                if (this.medical.debug) this.widget.debug.show();
                else {
                    var t = this,
                        i = new Date().getTime();
                    this.logo_click_time + 500 < i ? (this.logo_click_time = i, this.logo_click_count = 1) : (this.logo_click_time = i, this.logo_click_count += 1, this.logo_click_count >= 6 && (this.logo_click_count = 0, this.gui.sudo().then(function() {
                        t.widget.debug.show()
                    })))
                }
            },
            _scrollable: function(t, i) {
                var n = $(t),
                    r = !0;
                return !i && 0 >= n.scrollTop() ? r = !1 : i && n.scrollTop() + n.height() >= t.scrollHeight && (r = !1), r
            },
            disable_rubberbanding: function() {
                var t = this;
                document.body.addEventListener("touchstart", function(i) {
                    t.previous_touch_y_coordinate = i.touches[0].clientY
                }), document.body.addEventListener("touchmove", function(i) {
                    var n, r = i.target;
                    for (n = i.touches[0].clientY < t.previous_touch_y_coordinate; r;) {
                        if (r.classList && r.classList.contains("touch-scrollable") && t._scrollable(r, n)) return;
                        r = r.parentNode
                    }
                    i.preventDefault()
                })
            },
            disable_backpace_back: function() {
                $(document).on("keydown", function(t) {
                    8 !== t.which || $(t.target).is("input, textarea") || t.preventDefault()
                })
            },
            loading_error: function(t) {
                console.error("Loading Error (loading_error)", t, this);
                var i = this,
                    n = t.message,
                    r = t.stack;
                "XmlHttpRequestError " === t.message ? (n = "Network Failure (XmlHttpRequestError)", r = "The Point of Sale could not be loaded due to a network problem.\n Please check your internet connection.") : 200 === t.code && (n = t.data.message, r = t.data.debug), "string" != typeof r && (r = "Traceback not available.");
                var o = $(h.render("ErrorTracebackPopupWidget", {
                    widget: {
                        options: {
                            title: n,
                            body: r
                        }
                    }
                }));
                o.find(".button").click(function() {
                    i.gui.close()
                }), o.css({
                    zindex: 9001
                }), o.appendTo(this.$el)
            },
            loading_progress: function(t) {
                this.$(".loader .loader-feedback").removeClass("oe_hidden"), this.$(".loader .progress").removeClass("oe_hidden").css({
                    width: "" + Math.floor(100 * t) + "%"
                })
            },
            loading_message: function(t, i) {
                this.$(".loader .loader-feedback").removeClass("oe_hidden"), this.$(".loader .message").text(t), void 0 !== i ? this.loading_progress(i) : this.$(".loader .progress").addClass("oe_hidden")
            },
            loading_skip: function(t) {
                t ? (this.$(".loader .loader-feedback").removeClass("oe_hidden"), this.$(".loader .button.skip").removeClass("oe_hidden"), this.$(".loader .button.skip").off("click"), this.$(".loader .button.skip").click(t)) : this.$(".loader .button.skip").addClass("oe_hidden")
            },
            loading_hide: function() {
                var t = this;
                this.$(".loader").animate({
                    opacity: 0
                }, 1500, "swing", function() {
                    t.$(".loader").addClass("oe_hidden")
                }), this.$(".medical-base").removeClass("oe_hidden").animate({
                    opacity: 1
                }, 150, "swing")
            },
            loading_show: function() {
                this.$(".medical-base").addClass("oe_hidden"), this.$(".loader").removeClass("oe_hidden").animate({
                    opacity: 1
                }, 150, "swing"), this.$(".medical-base").animate({
                    opacity: 0
                }, 1500, "swing")
            },
            widgets: [{
                name: "full_screen",
                widget: M,
                append: ".v-top-control"
            }, {
                name: "notification",
                widget: U,
                append: ".v-top-control"
            }, {
                name: "close_button",
                widget: T,
                append: ".v-top-control",
                args: {
                    label: v("Close"),
                    action: function() {
                        this.$el.addClass("close_button");
                        var t = this;
                        this.confirmed ? (clearTimeout(this.confirmed), this.gui.close()) : (this.$el.addClass("confirm"), this.$el.find(".v-close-span").text(v("Confirm")), this.confirmed = setTimeout(function() {
                            t.$el.removeClass("confirm"), t.$el.find(".v-close-span").text(""), t.confirmed = !1
                        }, 2e3))
                    }
                }
            }, ],
            load_widgets: function(t) {
                for (var i = 0; i < t.length; i++) {
                    var n = t[i];
                    if (!n.condition || n.condition.call(this)) {
                        var r = "function" == typeof n.args ? n.args(this) : n.args,
                            o = new n.widget(this, r || {});
                        n.replace ? o.replace(this.$(n.replace)) : n.append ? o.appendTo(this.$(n.append)) : n.prepend ? o.prependTo(this.$(n.prepend)) : n.after ? o.insertAfter(this.$(n.after)) : n.before ? o.insertBefore(this.$(n.before)) : o.appendTo(this.$el), this.widget[n.name] = o
                    }
                }
            },
            build_widgets: function() {
                var t, i = this;
                this.load_widgets(this.widgets), this.screens = {};
                for (var n = 0; n < this.gui.screen_classes.length; n++)
                    if (!(t = this.gui.screen_classes[n]).condition || t.condition.call(this)) {
                        var r = new t.widget(this, {});
                        r.appendTo(this.$(".screens")), this.screens[t.name] = r, this.gui.add_screen(t.name, r)
                    } this.popups = {}, _.forEach(this.gui.popup_classes, function(t) {
                    if (!t.condition || t.condition.call(i)) {
                        var n = new t.widget(i, {});
                        n.appendTo(i.$(".popups")).then(function() {
                            i.popups[t.name] = n, i.gui.add_popup(t.name, n)
                        })
                    }
                }), this.gui.set_startup_screen("calendar"), this.gui.set_default_screen("calendar")
            },
            destroy: function() {
                this.medical.destroy(), this._super()
            },
            updateRecord: function(t) {
                var i = _.omit(this.calendarEventToRecord(t), "name");
                for (var n in i) i[n] && i[n]._isAMomentObject && (i[n] = dateToServer(i[n]));
                var r = _.extend({
                    from_ui: !0
                }, y.user_context);
                return this._rpc({
                    model: "medical.order",
                    method: "write",
                    args: [
                        [t.id], i
                    ],
                    context: r
                })
            },
            error_toast: function(t, i, n) {
                return this.displayNotification({
                    type: "danger",
                    title: i,
                    message: t,
                    sticky: !0,
                    className: ""
                })
            },
            info_toast: function(t, i, n) {
                return this.displayNotification({
                    type: "info",
                    title: i,
                    message: t,
                    sticky: n || !1,
                    className: ""
                })
            },
            warning_toast: function(t, i, n) {
                return this.displayNotification({
                    type: "warning",
                    title: i,
                    message: t,
                    sticky: n || !1,
                    className: ""
                })
            },
            success_toast: function(t, i, n) {
                return this.displayNotification({
                    type: "success",
                    title: i,
                    message: t,
                    sticky: n || !1,
                    className: ""
                })
            },
            print_report: function(t, i) {
                var n = this,
                    r = ["/report/pdf/" + t, i];
                if (console.log("_ response : ", t, i, r), "pcr" != this.medical.config.company_code) return this.blockUI(), y.get_file({
                    url: "/report/download",
                    data: {
                        data: JSON.stringify(r)
                    },
                    complete: n.unblockUI,
                    error: function() {
                        n.gui.show_popup("error", {
                            title: v("Failed To Print"),
                            body: v("Print failed possibly server issue.")
                        }), n.unblockUI()
                    }
                });
                var o = window.location.origin;
                window.open(o + "/report/pdf/" + t, "_blank")
            },
            print_custom_reports: function(t, i, n) {
                var r = this;
                return this.blockUI(), y.get_file({
                    url: t,
                    data: {
                        report_tag: JSON.stringify(i),
                        report_data: JSON.stringify(n)
                    },
                    complete: r.unblockUI,
                    error: function() {
                        r.gui.show_popup("error", {
                            title: v("Failed To Print"),
                            body: v("Print failed possibly server issue.")
                        }), r.unblockUI()
                    }
                })
            },
            blockUI: a.blockUI,
            unblockUI: a.unblockUI
        });
    s.action_registry.add("medical.ui", R);
    var N = g.extend({
            init: function(t, i) {
                this._super(t, i), this.hidden = !1
            },
            barcode_product_screen: "products",
            barcode_product_action: function(t) {
                this.medical.scan_product(t) ? this.barcode_product_screen && this.gui.show_screen(this.barcode_product_screen, null, null, !0) : this.barcode_error_action(t)
            },
            barcode_client_action: function(t) {
                var i = this.medical.db.get_partner_by_barcode(t.code);
                return i ? (this.medical.get_order().get_client() !== i && (this.medical.get_order().set_client(i), this.medical.get_order().set_pricelist(_.findWhere(this.medical.pricelists, {
                    id: i.property_product_pricelist[0]
                }) || this.medical.default_pricelist)), !0) : (this.barcode_error_action(t), !1)
            },
            barcode_discount_action: function(t) {
                var i = this.medical.get_order().get_last_orderline();
                i && i.set_discount(t.value)
            },
            barcode_error_action: function(t) {
                var i;
                i = t.code.length > 32 ? t.code.substring(0, 29) + "..." : t.code, this.gui.show_popup("error-barcode", i)
            },
            show: function() {
                this.hidden = !1, this.$el && this.$el.removeClass("oe_hidden")
            },
            close: function() {
                this.payment_interface && this.payment_interface.close()
            },
            hide: function() {
                this.hidden = !0, this.$el && this.$el.addClass("oe_hidden")
            },
            renderElement: function() {
                this._super(), this.hidden && this.$el && this.$el.addClass("oe_hidden")
            },
            _handleFailedPushForInvoice: function(t, i, n) {
                var r = this;
                t = t || this.medical.get_order(), this.invoicing = !1, t.finalized = !1, "Missing Customer" === n.message ? this.gui.show_popup("confirm", {
                    title: v("Please select the Customer"),
                    body: v("You need to select the customer before you can invoice an order."),
                    confirm: function() {
                        r.gui.show_screen("clientlist", null, i)
                    }
                }) : "Backend Invoice" === n.message ? this.gui.show_popup("confirm", {
                    title: v("Please print the invoice from the backend"),
                    body: v("The order has been synchronized earlier. Please make the invoice from the backend for the order: ") + n.data.order.name,
                    confirm: function() {
                        this.gui.show_screen("receipt", null, i)
                    },
                    cancel: function() {
                        this.gui.show_screen("receipt", null, i)
                    }
                }) : n.code < 0 ? this.gui.show_popup("error", {
                    title: v("The order could not be sent"),
                    body: v("Check your internet connection and try again."),
                    cancel: function() {
                        this.gui.show_screen("receipt", {
                            button_print_invoice: !0
                        }, i)
                    }
                }) : 200 === n.code ? this.gui.show_popup("error-traceback", {
                    title: n.data.message || v("Server Error"),
                    body: n.data.debug || v("The server encountered an error while receiving your order.")
                }) : this.gui.show_popup("error", {
                    title: v("Unknown Error"),
                    body: v("The order could not be sent to the server due to an unknown error")
                })
            }
        }),
        j = g.extend({
            template: "PopupWidget",
            init: function(t, i) {
                this._super(t, i), this.options = {}
            },
            events: {
                "click .button.cancel": "click_cancel",
                "click .popup-close": "click_cancel",
                "click .button.confirm": "click_confirm",
                "click .selection-item": "click_item",
                "click .input-button": "click_numpad",
                "click .mode-button": "click_numpad"
            },
            show: function(t) {
                var i = this;
                this.$el && this.$el.removeClass("oe_hidden"), "string" == typeof t ? this.options = {
                    title: t
                } : this.options = t || {}, this.renderElement(), $(document).on("keydown", function(t) {
                    27 === e.keyCode && i.gui.close_popup()
                })
            },
            close: function() {},
            hide: function() {
                this.$el && this.$el.addClass("oe_hidden")
            },
            click_cancel: function() {
                this.gui.close_popup(), this.options.cancel && this.options.cancel.call(this)
            },
            click_confirm: function() {
                this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this)
            },
            click_item: function() {},
            click_numad: function() {}
        });
    x.define_popup({
        name: "alert",
        widget: j
    }), p.ErrorPopupWidget = j.extend({
        template: "ErrorPopupWidget",
        show: function(t) {
            this._super(t)
        }
    }), x.define_popup({
        name: "error",
        widget: p.ErrorPopupWidget
    }), p.SyncErrorPopupWidget = p.ErrorPopupWidget.extend({
        template: "SyncErrorPopupWidget",
        show: function(t) {
            var i = this;
            this._super(t), this.$(".stop_showing_sync_errors").off("click").click(function() {
                i.gui.show_sync_errors = !1, i.click_confirm()
            })
        }
    }), x.define_popup({
        name: "error-sync",
        widget: p.SyncErrorPopupWidget
    }), p.ErrorTracebackPopupWidget = p.ErrorPopupWidget.extend({
        template: "ErrorTracebackPopupWidget",
        show: function(t) {
            var i = this;
            this._super(t), this.$(".download").off("click").click(function() {
                i.gui.prepare_download_link(i.options.body, v("error") + " " + moment().format("YYYY-MM-DD-HH-mm-ss") + ".txt", ".download", ".download_error_file")
            }), this.$(".email").off("click").click(function() {
                i.gui.send_email(i.medical.company.email, v("IMPORTANT: Bug Report From Odoo Point Of Sale"), i.options.body)
            })
        }
    }), x.define_popup({
        name: "error-traceback",
        widget: p.ErrorTracebackPopupWidget
    }), p.ErrorBarcodePopupWidget = p.ErrorPopupWidget.extend({
        template: "ErrorBarcodePopupWidget",
        show: function(t) {
            this._super({
                barcode: t
            })
        }
    }), x.define_popup({
        name: "error-barcode",
        widget: p.ErrorBarcodePopupWidget
    }), p.ConfirmPopupWidget = j.extend({
        template: "ConfirmPopupWidget"
    }), x.define_popup({
        name: "confirm",
        widget: p.ConfirmPopupWidget
    }), p.YesNoPopupWidget = j.extend({
        template: "YesNoPopupWidget"
    }), x.define_popup({
        name: "confirm-yes-no",
        widget: p.YesNoPopupWidget
    }), p.SelectionPopupWidget = j.extend({
        template: "SelectionPopupWidget",
        show: function(t) {
            t = t || {}, this._super(t), this.list = t.list || [], this.is_selected = t.is_selected || function(t) {
                return !1
            }, this.renderElement()
        },
        click_item: function(t) {
            if (this.gui.close_popup(), this.options.confirm) {
                var i = this.list[parseInt($(t.target).data("item-index"))];
                i = i ? i.item : i, this.options.confirm.call(self, i)
            }
        }
    }), x.define_popup({
        name: "selection",
        widget: p.SelectionPopupWidget
    }), p.TextInputPopupWidget = j.extend({
        template: "TextInputPopupWidget",
        show: function(t) {
            t = t || {}, this._super(t), this.renderElement(), this.$("input,textarea").focus()
        },
        click_confirm: function() {
            var t = this.$("input,textarea").val();
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, t)
        }
    }), x.define_popup({
        name: "textinput",
        widget: p.TextInputPopupWidget
    }), p.TextInput2PopupWidget = j.extend({
        template: "TextInput2PopupWidget",
        show: function(t) {
            t = t || {}, this._super(t), this.renderElement(), this.$(".input1").focus()
        },
        click_confirm: function() {
            var t = this.$(".input1").val(),
                i = this.$(".input2").val();
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, t, i)
        }
    }), x.define_popup({
        name: "textinput2",
        widget: p.TextInput2PopupWidget
    }), p.TextAreaPopupWidget = p.TextInputPopupWidget.extend({
        template: "TextAreaPopupWidget"
    }), x.define_popup({
        name: "textarea",
        widget: p.TextAreaPopupWidget
    }), p.TextAndRadioInputPopupWidget = j.extend({
        template: "TextAndRadioInputPopupWidget",
        show: function(t) {
            t = t || {}, this._super(t), this.renderElement(), this.$("input,textarea").focus()
        },
        click_confirm: function() {
            var t = this.$("textarea").val(),
                i = this.$('input[type="checkbox"]').prop("checked");
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, t, i)
        }
    }), x.define_popup({
        name: "textarea_radio",
        widget: p.TextInputPopupWidget
    }), p.NumberPopupWidget = j.extend({
        template: "NumberPopupWidget",
        show: function(t) {
            t = t || {}, this._super(t), this.inputbuffer = "" + (t.value || ""), this.decimal_separator = v.database.parameters.decimal_point, this.renderElement(), this.firstinput = !0
        },
        click_numpad: function(t) {
            var i = this.gui.numpad_input(this.inputbuffer, $(t.target).data("action"), {
                firstinput: this.firstinput
            });
            this.firstinput = 0 === i.length, i !== this.inputbuffer && (this.inputbuffer = i, this.$(".value").text(this.inputbuffer))
        },
        click_confirm: function() {
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, this.inputbuffer)
        }
    }), x.define_popup({
        name: "number",
        widget: p.NumberPopupWidget
    }), p.PasswordPopupWidget = p.NumberPopupWidget.extend({
        keypress_number: function(t) {
            if (13 == t.keyCode) this.click_confirm();
            else if (8 == t.keyCode || t.keyCode >= 48 && t.keyCode <= 57 || t.keyCode >= 96 && t.keyCode <= 105) {
                var i = 8 == t.keyCode ? "BACKSPACE" : parseInt(t.key),
                    n = this.gui.numpad_input(this.inputbuffer, i, {
                        firstinput: this.firstinput
                    });
                this.firstinput = 0 === n.length, n !== this.inputbuffer && (this.inputbuffer = n, this.$(".value").text(this.inputbuffer.replace(/./g, "•")))
            }
        },
        renderElement: function() {
            this._super(), this.$(".popup").addClass("popup-password")
        },
        show: function() {
            this._super.apply(this, arguments);
            var t = this;
            $(document).on("keydown", function(i) {
                t.keypress_number(i)
            })
        },
        click_cancel: function() {
            $(document).unbind("keydown"), this._super.apply(this, arguments)
        },
        click_confirm: function() {
            $(document).unbind("keydown"), this._super.apply(this, arguments)
        },
        click_numpad: function(t) {
            this._super.apply(this, arguments);
            var i = this.$(".value");
            i.text(i.text().replace(/./g, "•"))
        }
    }), x.define_popup({
        name: "password",
        widget: p.PasswordPopupWidget
    }), j.include({
        show: function(t) {
            this._super.apply(this, arguments), this.$(".v-input-datetime").datetimepicker(this.dttm_picker_options), this.$(".v-input-date").datetimepicker(this.dt_picker_options), this.$(".ol-input-time").timepicker(this.time_picker_options), this.options && this.options.value && this.$(".v-input-datetime, .v-input-date, .ol-input-time").val(this.options.value)
        }
    }), p.InputPopupWidget = j.extend({
        click_confirm: function() {
            var t = this.$("input,textarea").val();
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, t)
        }
    }), p.DateInputPopupWidget = p.InputPopupWidget.extend({
        template: "DateInputPopupWidget"
    }), x.define_popup({
        name: "date-input",
        widget: p.DateInputPopupWidget
    }), p.DateTimeInputPopupWidget = p.InputPopupWidget.extend({
        template: "DateTimeInputPopupWidget",
        click_confirm: function() {
            var t = this.$("input").val();
            if (t)(t = moment(t, this.chrome.datetime_format)).isValid() && (t = t._d);
            else {
                self.medical.chrome.error_toast(v("Please fill the date and time."));
                return
            }
            this.gui.close_popup(), this.options.confirm && this.options.confirm.call(this, t)
        }
    }), x.define_popup({
        name: "datetime-input",
        widget: p.DateTimeInputPopupWidget
    }), p.TimeInputPopupWidget = p.InputPopupWidget.extend({
        template: "TimeInputPopupWidget"
    }), x.define_popup({
        name: "time-input",
        widget: p.TimeInputPopupWidget
    }), p.UniversalPopupWidget = j.extend({
        template: "UniversalPopupWidget",
        show: function(t) {
            this._super(t), this.options = t
        },
        click_confirm: function() {
            this.options.callback(), this.gui.close_popup()
        }
    }), x.define_popup({
        name: "universal_popup",
        widget: p.UniversalPopupWidget
    });
    var A = function(t, i) {
            i = i || {};
            var n, r = f,
                o = r.length;
            if (i.after)
                for (n = 0; n < r.length; n++) r[n].name === i.after && (o = n + 1);
            else if (i.before) {
                for (n = 0; n < r.length; n++)
                    if (r[n].name === i.after) {
                        o = n;
                        break
                    }
            }
            r.splice(n, 0, t)
        },
        L = g.extend({
            template: "MenuButtonWidget",
            label: v("Button"),
            renderElement: function() {
                var t = this;
                this._super(), this.$el.click(function() {
                    t.button_click()
                })
            },
            button_click: function() {
                this.$el.addClass("active").siblings().removeClass("active")
            },
            highlight: function(t) {
                this.$el.toggleClass("highlight", !!t)
            },
            altlight: function(t) {
                this.$el.toggleClass("altlight", !!t)
            }
        });
    return {
        MedicalBaseWidget: g,
        MedicalModel: E,
        gui: x,
        MedicalDB: P,
        Chrome: R,
        screens: {
            ScreenWidget: N
        },
        load_models: S,
        load_fields: O,
        define_menu_button: A,
        MenuButtonWidget: L,
        PopupWidget: j,
        popups: p,
        Product: I,
        StatusWidget: q,
        PARTNER_FIELDS: m
    }
});