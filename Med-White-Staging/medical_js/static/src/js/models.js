odoo.define("medical_js.models",function(require){"use strict";var i=require("web.core"),
    e=require("web.utils");require("web.session");var n=require("web.field_utils"),
    r=require("web.config"),
    s=require("web.concurrency"),
    a=i.qweb,c=i._t,o=e.round_precision,d=e.round_decimals;s.Mutex;var u=0,l="Medical Price",h={};h.Orderline=Backbone.Model.extend({initialize:function(t,i){if(this.medical=i.medical,this.order=i.order,i.json){try{this.init_from_JSON(i.json)}catch(e){console.error("ERROR: attempting to recover product ID",i.json.product_id,"not available in the point of sale. Correct the product or clean the browser cache.")}return}this.product=i.product,this.set_quantity(1),this.discount=0,this.discount_fixed=0,this.discountStr="0",this.selected=!1,this.id=u++,this.price_manually_set=!1,this.is_tip=!1,this.related_pkg_id=!1,i.price?this.set_unit_price(i.price):this.set_unit_price(this.product.get_price(this.order.pricelist,this.get_quantity()))},init_from_JSON:function(t){this.product=this.medical.db.get_product_by_id(t.product_id),this.price=t.price_unit,this.discount_fixed=t.discount_fixed,this.set_discount(t.discount),this.set_quantity(t.qty,"do not recompute unit price"),this.id=t.id?t.id:u++,u=Math.max(this.id+1,u)},clone:function(){var t=new h.Orderline({},{medical:this.medical,order:this.order,product:this.product,price:this.price});return t.order=null,t.quantity=this.quantity,t.quantityStr=this.quantityStr,t.discount=this.discount,t.discount_fixed=this.discount_fixed,t.price=this.price,t.selected=!1,t.price_manually_set=this.price_manually_set,t},set_discount:function(t){var i=Math.min(Math.max(parseFloat(t)||0,0),100);this.discount=i,this.discountStr=""+i+"%",this.trigger("change",this)},set_fix_discount:function(t){t=t&&t.toFixed(3),this.discount_fixed=t,this.discountStr=""+t,this.trigger("change",this)},get_discount:function(){return this.discount},get_actual_discount:function(){var t=this.medical.currency.rounding;return this.discount_fixed>0?o(this.discount_fixed,t):this.discount>0?o(this.get_discount()/100,t):0},get_discount_str:function(){return this.discountStr},set_quantity:function(t,i){if(this.order.assert_editable(),"remove"===t){this.order.remove_orderline(this);return}var e=parseFloat(t)||0,r=this.get_unit();if(r){if(r.rounding){this.quantity=o(e,r.rounding);var s=this.medical.dp["Product Unit of Measure"];this.quantity=d(this.quantity,s),this.quantityStr=n.format.float(this.quantity,{digits:[69,s]})}else this.quantity=o(e,1),this.quantityStr=this.quantity.toFixed(0)}else this.quantity=e,this.quantityStr=""+this.quantity;i||this.price_manually_set||(this.set_unit_price(this.product.get_price(this.order.pricelist,this.get_quantity())),this.order.fix_tax_included_price(this)),this.trigger("change",this)},get_quantity:function(){return this.quantity},get_quantity_str:function(){return this.quantityStr},get_quantity_str_with_unit:function(){var t=this.get_unit();return t&&!t.is_pos_groupable?this.quantityStr+" "+t.name:this.quantityStr},get_required_number_of_lots:function(){var t=1;return"serial"==this.product.tracking&&(t=Math.abs(this.quantity)),t},compute_lot_lines:function(){var t=this.pack_lot_lines,i=t.length,e=this.get_required_number_of_lots();if(e>i)for(var n=0;n<e-i;n++)t.add(new h.Packlotline({},{order_line:this}));if(e<i){var r=t.sortBy("lot_name").slice(0,i-e);t.remove(r)}return this.pack_lot_lines},has_valid_product_lot:function(){if(!this.has_product_lot)return!0;var t=this.pack_lot_lines.get_valid_lots();return this.get_required_number_of_lots()===t.length},get_unit:function(){var t=this.product.uom_id;if(t){if(t=t[0],this.medical)return this.medical.units_by_id[t]}},get_product:function(){return this.product},set_selected:function(t){this.selected=t,this.trigger("change",this)},is_selected:function(){return this.selected},can_be_merged_with:function(t){var i=parseFloat(d(this.price||0,this.medical.dp[l]).toFixed(this.medical.dp[l]));if(this.get_product().id!==t.get_product().id||!this.get_unit()||!this.get_unit().is_pos_groupable)return!1;if(this.get_actual_discount()>0)return!1;if(!e.float_is_zero(i-t.get_product().get_price(t.order.pricelist,this.get_quantity()),this.medical.currency.decimals))return!1;if("lot"==this.product.tracking)return!1;else return!0},merge:function(t){this.order.assert_editable(),this.set_quantity(this.get_quantity()+t.get_quantity())},export_as_JSON:function(){var t=[];return this.has_product_lot&&this.pack_lot_lines.each(_.bind(function(i){return t.push([0,0,i.export_as_JSON()])},this)),{qty:this.get_quantity(),price_unit:this.get_unit_price(),price_subtotal:this.get_price_without_tax(),price_subtotal_incl:this.get_price_with_tax(),discount:this.get_discount(),discount_fixed:this.discount_fixed,product_id:this.get_product().id,tax_ids:[[6,!1,_.map(this.get_applicable_taxes(),function(t){return t.id})]],id:this.id,pack_lot_ids:t}},export_for_printing:function(){return{quantity:this.get_quantity(),unit_name:this.get_unit().name,price:this.get_unit_display_price(),discount:this.get_discount(),discount_fixed:this.discount_fixed,product_name:this.get_product().display_name,product_name_wrapped:this.generate_wrapped_product_name(),price_lst:this.get_lst_price(),display_discount_policy:this.display_discount_policy(),price_display_one:this.get_display_price_one(),price_display:this.get_display_price(),price_with_tax:this.get_price_with_tax(),price_without_tax:this.get_price_without_tax(),price_with_tax_before_discount:this.get_price_with_tax_before_discount(),tax:this.get_tax(),product_description:this.get_product().description,product_description_sale:this.get_product().description_sale}},generate_wrapped_product_name:function(){for(var t=[],i=this.get_product().display_name,e="";i.length>0;){var n=i.indexOf(" ");-1===n&&(n=i.length),e.length+n>24&&(e.length&&t.push(e),e=""),e+=i.slice(0,n+1),i=i.slice(n+1)}return e.length&&t.push(e),t},set_unit_price:function(t){this.order.assert_editable(),this.price=d(parseFloat(t)||0,this.medical.dp[l]),this.pricelist_item_id||(this.price_unit_orig=t,this.approved_price_unit=t),this.compute_payable_unit_price(),this.trigger("change",this)},get_unit_price:function(){var t=this.medical.dp[l];return parseFloat(d(this.price||0,t).toFixed(t))},compute_payable_unit_price:function(){var t=this.price_unit_orig;return this.pricelist_item_id&&(t=this.price+(t-this.approved_price_unit)),this.payable_price_unit=t,t},get_payable_unit_price:function(){var t=this.medical.dp[l];return parseFloat(d(this.compute_payable_unit_price()||0,t).toFixed(t))},get_payable_subtotal:function(){var t=this.medical.currency.rounding;return this.discount_fixed?o(this.get_payable_price_unit()*this.get_quantity()-this.get_actual_discount(),t):o(this.get_payable_price_unit()*this.get_quantity()*(1-this.get_actual_discount()),t)},get_price_unit_orig:function(){var t=this.medical.dp[l];return parseFloat(d(this.price_unit_orig||this.price,t).toFixed(t))},get_approved_price_unit:function(){var t=this.medical.dp[l];return parseFloat(d(this.approved_price_unit||this.price,t).toFixed(t))},get_payable_price_unit:function(){var t=this.medical.dp[l];return parseFloat(d(this.payable_price_unit,t).toFixed(t))},get_ins_price_unit:function(){var t=this.medical.dp[l];return parseFloat(d(this.ins_price_unit||0,t).toFixed(t))},get_unit_display_price:function(){if("total"!==this.medical.config.iface_tax_included)return this.get_unit_price();var t=this.quantity;this.quantity=1;var i=this.get_all_prices().priceWithTax;return this.quantity=t,i},get_base_price:function(){var t=this.medical.currency.rounding;return this.discount_fixed?o(this.get_unit_price()-this.get_actual_discount(),t):o(this.get_unit_price()*this.get_quantity()*(1-this.get_actual_discount()),t)},get_display_price_one:function(){var t=this.medical.currency.rounding,i=this.get_unit_price();if("total"!==this.medical.config.iface_tax_included)return this.discount_fixed?o(i-this.get_actual_discount(),t):o(i*(1-this.get_actual_discount()),t);var e=this.get_product().taxes_id,n=this.medical.taxes,r=[];_(e).each(function(t){r.push(_.detect(n,function(i){return i.id===t}))});var s=this.compute_all(r,i,1,this.medical.currency.rounding);return this.discount_fixed?o(s.total_included-this.get_actual_discount(),t):o(s.total_included*(1-this.get_actual_discount()),t)},get_display_price:function(){return"total"===this.medical.config.iface_tax_included?this.get_price_with_tax():this.get_payable_subtotal()},get_price_without_tax:function(){return this.get_all_prices().priceWithoutTax},get_price_with_tax:function(){return this.get_all_prices().priceWithTax},get_price_with_tax_before_discount:function(){return this.get_all_prices().priceWithTaxBeforeDiscount},get_tax:function(){return this.get_all_prices().tax},get_applicable_taxes:function(){var t,i=this.get_product().taxes_id,e={};for(t=0;t<i.length;t++)e[i[t]]=!0;var n=[];for(t=0;t<this.medical.taxes.length;t++)e[this.medical.taxes[t].id]&&n.push(this.medical.taxes[t]);return n},get_tax_details:function(){return this.get_all_prices().taxDetails},get_taxes:function(){for(var t=this.get_product().taxes_id,i=[],e=0;e<t.length;e++)i.push(this.medical.taxes_by_id[t[e]]);return i},_map_tax_fiscal_position:function(t){var i=this,e=this.medical.get_order(),n=e&&e.fiscal_position,r=[];if(n){var s=_.filter(n.fiscal_position_taxes_by_id,function(i){return i.tax_src_id[0]===t.id});s&&s.length?_.each(s,function(t){t.tax_dest_id&&r.push(i.medical.taxes_by_id[t.tax_dest_id[0]])}):r.push(t)}else r.push(t);return r},_compute_all:function(t,i,e,n){if(void 0===n)var r=t.price_include;else var r=!n;return"fixed"===t.amount_type?t.amount*(Math.sign(i)||1)*Math.abs(e):"percent"!==t.amount_type||r?"percent"===t.amount_type&&r?i-i/(1+t.amount/100):"division"!==t.amount_type||r?"division"===t.amount_type&&!!r&&i-i*(t.amount/100):i/(1-t.amount/100)-i:i*t.amount/100},compute_all:function(t,i,e,n){var r,s=this,a=function(t,i){return t.sort(function(t,i){return t.sequence-i.sequence}),_(t).each(function(t){"group"===t.amount_type?i=a(t.children_tax_ids,i):i.push(t)}),i};t=a(r=t,[]);var c=!1,d=!1;_(t).each(function(t){if(t.price_include?d=!0:t.include_base_amount&&(c=!0),c&&d)throw Error("Unable to mix any taxes being price included with taxes affecting the base amount but not included in price.")}),"round_globally"!=this.medical.company.tax_calculation_rounding_method||(n*=1e-5);var u=function(t,i,e,n){return(t-i)/(1+e/100)*(100-n)/100},l=o(i*e,n);this.discount_fixed&&(l-=this.discount_fixed);var h=1;l<0&&(l=-l,h=-1);var p={},m=t.length-1,g=!0,f=0,y=0,v=0,x={};_(t.reverse()).each(function(t){if(t.include_base_amount&&(l=u(l,f,y,v),f=0,y=0,v=0,g=!0),t.price_include){if("percent"===t.amount_type)y+=t.amount;else if("division"===t.amount_type)v+=t.amount;else if("fixed"===t.amount_type)f+=e*t.amount;else{var i=s._compute_all(t,l,e);f+=i,x[m]=i}g&&(p[m]=l,g=!1)}m-=1});var $=u(l,f,y,v),b=$;l=$;var q=[];m=0;var w=0;return _(t.reverse()).each(function(t){if(t.price_include&&void 0!==p[m]){var i=p[m]-(l+w);w=0}else var i=s._compute_all(t,l,e,!0);i=o(i,n),t.price_include&&void 0===p[m]&&(w+=i),q.push({id:t.id,name:t.name,amount:h*i,base:h*o(l,n)}),t.include_base_amount&&(l+=i),b+=i,m+=1}),this.compute_payable_unit_price(),{taxes:q,total_excluded:h*o($,this.medical.currency.rounding),total_included:h*o(b,this.medical.currency.rounding)}},get_all_prices:function(){var t=this,i=this.get_payable_unit_price(),e=i;this.discount&&(e=i*(1-this.get_actual_discount()));var n=0,r=this.get_product().taxes_id,s=this.medical.taxes,a={},c=[];_(r).each(function(i){var e=_.detect(s,function(t){return t.id===i});c.push.apply(c,t._map_tax_fiscal_position(e))});var o=this.compute_all(c,e,this.get_quantity(),this.medical.currency.rounding),d=this.compute_all(c,i,this.get_quantity(),this.medical.currency.rounding);return _(o.taxes).each(function(t){n+=t.amount,a[t.id]=t.amount}),{priceWithTax:o.total_included,priceWithoutTax:o.total_excluded,priceSumTaxVoid:o.total_void,priceWithTaxBeforeDiscount:d.total_included,tax:n,taxDetails:a}},display_discount_policy:function(){return this.order.pricelist.discount_policy},compute_fixed_price:function(t){var i=this.order;if(i.fiscal_position){var e=this.get_taxes(),n=[],r=this;if(_(e).each(function(t){var i=r._map_tax_fiscal_position(t);t.price_include&&!_.contains(i,t)&&n.push(t)}),n.length>0)return this.compute_all(n,t,1,i.medical.currency.rounding,!0).total_excluded}return t},get_fixed_lst_price:function(){return this.compute_fixed_price(this.get_lst_price())},get_lst_price:function(){return this.product.lst_price},set_lst_price:function(t){this.order.assert_editable(),this.product.lst_price=d(parseFloat(t)||0,this.medical.dp[l]),this.trigger("change",this)}}),h.OrderlineCollection=Backbone.Collection.extend({model:h.Orderline});var p=1;h.Order=Backbone.Model.extend({initialize:function(t,i){Backbone.Model.prototype.initialize.apply(this,arguments);var e=this;return i=i||{},this.init_locked=!0,this.medical=i.medical,i.resource_id&&this.set_resource_id(i.resource_id),i.start_time&&this.set_start_time(i.start_time),this.selected_orderline=void 0,this.selected_paymentline=void 0,this.screen_data=i&&i.screen_data||{},this.temporary=i.temporary||!1,this.creation_date=new Date,this.to_invoice=!1,this.to_email=!1,this.orderlines=new h.OrderlineCollection,this.medical_session_id=this.medical.medical_session.id||this.medical.medical_session_id,this.employee=this.medical.employee||this.get_client(),this.finalized=!1,this.set_pricelist(this.medical.default_pricelist),this.amount_paid=0,this.set({client:null}),i.json?this.init_from_JSON(i.json):(this.sequence_number=this.medical.medical_session.sequence_number++,this.sequence_number=p++,this.uid=this.generate_unique_id(),this.name=_.str.sprintf(c("REF %s"),this.uid),this.validation_date=void 0,this.fiscal_position=_.find(this.medical.fiscal_positions,function(t){return t.id===e.medical.config.default_fiscal_position_id[0]})),this.on("change",function(){this.save_to_db("order:change")},this),this.orderlines.on("change",function(){this.save_to_db("orderline:change")},this),this.orderlines.on("add",function(){this.save_to_db("orderline:add")},this),this.orderlines.on("remove",function(){this.save_to_db("orderline:remove")},this),this.init_locked=!1,this.save_to_db(),this},save_to_db:function(){this.temporary||this.init_locked||this.medical.db.save_unpaid_order(this)},update_db_data:function(t,i){},init_from_JSON:function(t){t.medical_session_id!==this.medical.medical_session.id?this.sequence_number=this.medical.medical_session.sequence_number++:(this.sequence_number=t.sequence_number,this.medical.medical_session.sequence_number=Math.max(this.sequence_number+1,this.medical.medical_session.sequence_number))},export_as_JSON:function(){t=[],this.orderlines.each(_.bind(function(i){return t.push([0,0,i.export_as_JSON()])},this));var t,i=this.get_pricelist(),e=i&&i.need_approval||!1,n={name:this.get_name(),amount_total:this.get_total_with_tax(),amount_tax:this.get_total_tax(),lines:t,medical_session_id:this.medical_session_id,pricelist_id:i&&i.id||!1,need_pricelist_approval:e,partner_id:!!this.get_client()&&this.get_client().id,user_id:this.medical.user.id,employee_id:this.medical.get_cashier().id,uid:this.uid,sequence_number:this.sequence_number,creation_date:this.validation_date||this.creation_date,fiscal_position_id:!!this.fiscal_position&&this.fiscal_position.id,server_id:!!this.server_id&&this.server_id,to_invoice:!!this.to_invoice&&this.to_invoice};return!this.is_paid&&this.user_id&&(n.user_id=this.user_id),n},export_for_printing:function(){var t=[],i=this;this.orderlines.each(function(i){t.push(i.export_for_printing())});var e=this.get("client"),n=this.medical.get_cashier(),s=this.medical.company,c=new Date;function o(t){return!!t&&t.split("\n")[0].indexOf("<!DOCTYPE QWEB")>=0}function d(t){if(!o(t))return t;t=t.split("\n").slice(1).join("\n");var e=new QWeb2.Engine;return e.debug=r.isDebug(),e.default_dict=_.clone(a.default_dict),e.add_template('<templates><t t-name="subreceipt">'+t+"</t></templates>"),e.render("subreceipt",{pos:i.medical,widget:i.medical.chrome,order:i,receipt:u})}var u={orderlines:t,subtotal:this.get_subtotal(),total_with_tax:this.get_total_with_tax(),total_without_tax:this.get_total_without_tax(),total_tax:this.get_total_tax(),total_discount:this.get_total_discount(),tax_details:this.get_tax_details(),name:this.get_name(),client:e?e.name:null,invoice_id:null,cashier:n?n.name:null,precision:{price:2,money:2,quantity:3},date:{year:c.getFullYear(),month:c.getMonth(),date:c.getDate(),day:c.getDay(),hour:c.getHours(),minute:c.getMinutes(),isostring:c.toISOString(),localestring:c.toLocaleString()},company:{email:s.email,website:s.website,company_registry:s.company_registry,contact_address:s.partner_id[1],vat:s.vat,vat_label:s.country&&s.country.vat_label||"",name:s.name,phone:s.phone,logo:this.medical.company_logo_base64},currency:this.medical.currency};return o(this.medical.config.receipt_header)?(u.header="",u.header_html=d(this.medical.config.receipt_header)):u.header=this.medical.config.receipt_header||"",o(this.medical.config.receipt_footer)?(u.footer="",u.footer_html=d(this.medical.config.receipt_footer)):u.footer=this.medical.config.receipt_footer||"",u},is_empty:function(){return 0===this.orderlines.models.length},generate_unique_id:function(){function t(t,i){for(var e=""+t;e.length<i;)e="0"+e;return e}return t(this.medical.config.id,5)+"-"+t(this.medical.medical_session.id,4)+"-"+t(this.medical.medical_session.login_number,3)+"-"+t(this.sequence_number,4)},get_name:function(){return this.name},assert_editable:function(){if(this.finalized)throw Error("Finalized Order cannot be modified")},add_orderline:function(t){this.assert_editable(),t.order&&t.order.remove_orderline(t),t.order=this,this.orderlines.add(t),this.select_orderline(this.get_last_orderline())},get_orderline:function(t){for(var i=this.orderlines.models,e=0;e<i.length;e++)if(i[e].id===t)return i[e];return null},get_orderlines:function(){return this.orderlines.models},get_last_orderline:function(){return this.orderlines.at(this.orderlines.length-1)},get_tip:function(){var t=this.medical.db.get_product_by_id(this.medical.config.tip_prod_id[0]),i=this.get_orderlines(),e={employee_id:!1,amount:0};if(!t)return e;for(var n=0;n<i.length;n++)if(i[n].get_product()===t)return{employee_id:i[n].employee_id,amount:i[n].get_unit_price()};return e},get_total_without_discount:function(){return o(this.orderlines.reduce(function(t,i){return t+i.get_payable_unit_price()*i.get_quantity()},0),this.medical.currency.rounding)},initialize_validation_date:function(){this.validation_date=new Date,this.formatted_validation_date=n.format.datetime(moment(this.validation_date),{},{timezone:!1})},set_tip:function(t,i){var e=this.medical.db.get_product_by_id(this.medical.config.tip_prod_id[0]),n=this.get_orderlines();if(e){for(var r=0;r<n.length;r++)if(n[r].get_product()===e&&n[r].employee_id==t){n[r].set_unit_price(i),n[r].set_lst_price(i),n[r].price_manually_set=!0;return}this.add_product(e,{quantity:1,price:i,lst_price:i,is_tip:!0,extras:{price_manually_set:!0}});var s=this.get_last_orderline();s.is_tip=!0,s.set_line_employee_id(t)}},set_pricelist:function(t){var i=this;this.pricelist=t,this.pricelist_id=t.id;var e=_.filter(this.get_orderlines(),function(t){return!t.price_manually_set});_.each(e,function(t){t.set_unit_price(t.product.get_price(i.pricelist,t.get_quantity())),i.fix_tax_included_price(t)}),this.trigger("change")},get_pricelist:function(){return this.pricelist||this.medical.default_pricelist},remove_orderline:function(t){this.assert_editable(),this.orderlines.remove(t),this.select_orderline(this.get_last_orderline())},fix_tax_included_price:function(t){t.set_unit_price(t.compute_fixed_price(t.price))},set_order:function(t){this.set({selectedOrder:t})},add_product:function(t,i){if(this._printed)return this.destroy(),this.medical.get_order().add_product(t,i);this.assert_editable(),console.log("____ product : ",t,i),i=i||{};var e,n=JSON.parse(JSON.stringify(t));n.medical=this.medical,n.order=this;var r={medical:this.medical,order:this,product:t};void 0!==i.price&&(r.price=i.price);var s=new h.Orderline({},r);if(this.fix_tax_included_price(s),void 0!==i.quantity&&s.set_quantity(i.quantity),i.is_tip&&(s.is_tip=!0),void 0!==i.price&&(s.set_unit_price(i.price),this.fix_tax_included_price(s)),void 0!==i.lst_price&&s.set_lst_price(i.lst_price),void 0!==i.discount&&s.set_discount(i.discount),void 0!==i.discount_fixed&&s.set_fix_discount(i.discount_fixed),void 0!==i.extras)for(var a in i.extras)s[a]=i.extras[a];for(var c=0;c<this.orderlines.length;c++)this.orderlines.at(c).can_be_merged_with(s)&&!1!==i.merge&&(e=this.orderlines.at(c));e?(e.merge(s),this.select_orderline(e)):(this.orderlines.add(s),this.select_orderline(this.get_last_orderline())),s.has_product_lot&&this.display_lot_popup(),this.medical.config.iface_customer_facing_display&&this.medical.send_current_order_to_customer_facing_display()},get_selected_orderline:function(){return this.selected_orderline},select_orderline:function(t){t?t!==this.selected_orderline&&(this.selected_orderline&&this.selected_orderline.set_selected(!1),this.selected_orderline=t,this.selected_orderline.set_selected(!0)):this.selected_orderline=void 0},deselect_orderline:function(){this.selected_orderline&&(this.selected_orderline.set_selected(!1),this.selected_orderline=void 0)},display_lot_popup:function(){var t=this.get_selected_orderline();if(t){var i=t.compute_lot_lines();this.medical.gui.show_popup("packlotline",{title:c("Lot/Serial Number(s) Required"),pack_lot_lines:i,order_line:t,order:this})}},get_subtotal:function(){return o(this.orderlines.reduce(function(t,i){return t+i.get_display_price()},0),this.medical.currency.rounding)},get_total_with_tax:function(){return this.get_total_without_tax()+this.get_total_tax()},get_total_without_tax:function(){return o(this.orderlines.reduce(function(t,i){return t+i.get_price_without_tax()},0),this.medical.currency.rounding)},get_total_discount:function(){return o(this.orderlines.reduce(function(t,i){return i.discount_fixed?t=i.get_actual_discount():t+=i.get_unit_price()*i.get_actual_discount()*i.get_quantity(),"without_discount"===i.display_discount_policy()&&(t+=(i.get_lst_price()-i.get_unit_price())*i.get_quantity()),t},0),this.medical.currency.rounding)},get_total_tax:function(){if("round_globally"!==this.medical.company.tax_calculation_rounding_method)return o(this.orderlines.reduce(function(t,i){return t+i.get_tax()},0),this.medical.currency.rounding);var t={};this.orderlines.each(function(i){for(var e=i.get_tax_details(),n=Object.keys(e),r=0;r<n.length;r++){var s=n[r];s in t||(t[s]=0),t[s]+=e[s]}});for(var i=0,e=Object.keys(t),n=0;n<e.length;n++)i+=o(t[e[n]],this.medical.currency.rounding);return i},get_total_paid:function(){return this.amount_paid||0},get_tax_details:function(){var t={},i=[];for(var e in this.orderlines.each(function(i){var e=i.get_tax_details();for(var n in e)e.hasOwnProperty(n)&&(t[n]=(t[n]||0)+e[n])}),t)t.hasOwnProperty(e)&&i.push({amount:t[e],tax:this.medical.taxes_by_id[e],name:this.medical.taxes_by_id[e].name});return i},get_total_for_category_with_tax:function(t){var i=0,e=this;if(t instanceof Array){for(var n=0;n<t.length;n++)i+=this.get_total_for_category_with_tax(t[n]);return i}return this.orderlines.each(function(n){e.medical.db.category_contains(t,n.product.id)&&(i+=n.get_price_with_tax())}),i},get_total_for_taxes:function(t){var i=0;t instanceof Array||(t=[t]);for(var e={},n=0;n<t.length;n++)e[t[n]]=!0;return this.orderlines.each(function(t){for(var n=t.get_product().taxes_id,r=0;r<n.length;r++)if(e[n[r]]){i+=t.get_price_with_tax();return}}),i},get_due:function(t){return o(this.get_total_with_tax(),this.medical.currency.rounding)},is_paid:function(){return 0>=this.get_due()},finalize:function(){this.destroy()},destroy:function(){Backbone.Model.prototype.destroy.apply(this,arguments),this.medical.db.remove_unpaid_order(this)},set_to_invoice:function(t){this.assert_editable(),this.to_invoice=t},is_to_invoice:function(){return this.to_invoice},set_to_email:function(t){this.to_email=t},is_to_email:function(){return this.to_email},set_client:function(t){this.assert_editable(),this.set("client",t)},get_client:function(){return this.get("client")},get_client_name:function(){var t=this.get("client");return t?t.name:""},set_screen_data:function(t,i){if(2===arguments.length)this.screen_data[t]=i;else if(1===arguments.length)for(var t in arguments[0])this.screen_data[t]=arguments[0][t]},get_screen_data:function(t){return this.screen_data[t]},wait_for_push_order:function(){return this.is_to_email()},set_insurance_card:function(t){this.insurance_card_id=t.id,this.insurance_card=t,this.pricelist_id=t.pricelist_id&&t.pricelist_id[0]},get_insurance_card:function(){var t=this.insurance_card;return!t&&this.insurance_card_id&&(t=this.medical.insurance_card_by_id[Number(this.insurance_card_id)]),t||{}},get_insurance_card_display:function(){return this.get_insurance_card().name||""},set_start_time:function(t){this.start_time=t,this.user_start_time=this.medical.chrome.toUserTZ(t),this.set({selectedStarttime:this.user_start_time})},get_start_time:function(t,i){if(t){var e=this.m_start_time;return!i&&e&&(e=e.clone()),e}return this.start_time},get_start_time_display:function(){return this.medical.chrome.format_datetime(this.user_start_time)||""},get_end_time:function(t){var i=this.get_start_time(!0);if(!i)return!1;var e=this.medical.floatToMinutes(this.get_total_duration()),n="";return i&&e&&(n=i.add(e,"minutes"),t||(n=this.medical.chrome.get_str_datetime(n))),n},set_resource_id:function(t){this.resource_id=parseInt(t),this.resource=_.findWhere(this.medical.db.cal_resources,{id:this.resource_id});var i=_.findWhere(this.medical.db.all_resources,{id:t}),e=this.get_orderlines();i&&i.analytic_account_id&&_.each(e,function(t){_.isEmpty(i.analytic_account_id)||t.analytic_account_id||t.set_analytic(i.analytic_account_id[0])})},get_resource_id:function(){return this.resource_id},get_resource_display:function(){var t=this.resource;return!t&&this.resource_id&&(t=_.findWhere(this.medical.db.cal_resources,{id:this.get_resource_id()})),t&&t.title||""},get_state_display:function(){return this.medical.chrome.state_display[this.state]},get_total_duration:function(){var t=this.get_orderlines(),i=0;return _.each(t,function(t){(t.is_medical_service||t.product.is_medical_service)&&(i+=t.duration||0)}),i},get_total_duration_display:function(){var t=this.get_total_duration();return this.medical.chrome.floatToHour(t)},validate_order:function(){var t=this.export_as_JSON(),i=moment(t.start_time,this.medical.chrome.datetime_server_format);if(!t)return this.medical.gui.show_popup("error",c("Invalid Order")),!1;if(!t.partner_id)return this.medical.gui.show_popup("error",c("Please Select the Customer.")),!1;if((!t.lines||0==t.lines.length)&&this.medical.config.req_one_service)return this.medical.gui.show_popup("error",c("Please Enter Atleast one Orderline.")),!1;if(!t.resource_id)return this.medical.gui.show_popup("error",c("Resource is Required.")),!1;if(!t.start_time)return this.medical.gui.show_popup("error",c("Appointment start time not defined.")),!1;else if("Invalid date"==t.start_time||!i._isValid)return this.medical.gui.show_popup("error",c("Invalid appointment start time.")),!1;return this.initialize_validation_date(),!0},get_patient_name:function(){return this.get_client_name()},get_start_time:function(){return this.medical.chrome.format_datetime(this.start_time)},get_resource_name:function(){return this.get_resource_display()}}),h.OrderCollection=Backbone.Collection.extend({model:h.Order});var m=h.Order.prototype;h.Order=h.Order.extend({init_from_JSON:function(t){this.resource_id=t.resource_id,this.start_time=t.start_time,this.end_time=t.end_time,this.orig_order_id=t.orig_order_id,this.invoice_note=t.invoice_note,this.is_followup=t.is_followup,this.insurance_card_id=t.insurance_card_id,this.clinic_id=!1,this.state=t.state,this.amount_paid=t.amount_paid,m.init_from_JSON.call(this,t)},add_product:function(t,i){m.add_product.apply(this,arguments),i=i||{analytic_tag_ids:[],analytic_account_id:!1};var e=this.get_selected_orderline(),n=!1;if(_.isEmpty(i.analytic_tag_ids)?_.isEmpty(t.analytic_tag_ids)?(i.analytic_account_id||t.analytic_account_id)&&(e.set_analytic(i.analytic_account_id||t.analytic_account_id&&t.analytic_account_id[0],[]),n=!0):(e.set_analytic(!1,t.analytic_tag_ids),n=!0):(e.set_analytic(!1,i.analytic_tag_ids),n=!0),e.order.resource_id){var r=this.medical.resource_by_id[e.order.resource_id];!n&&r.analytic_account_id&&r.analytic_account_id.length&&e.set_analytic(r.analytic_account_id[0],[]),!e.employee_id&&r.hr_staff_id&&e.set_line_employee_id(r.hr_staff_id[0])}},set_clinic:function(t){this.clinic_id=t},get_clinic:function(){var t=this.clinic_id;return Array.isArray(t)&&t.length>1&&(t=t[0]),!t&&(t=(this.medical.get_clinic()||{}).id),t||this.medical.config.clinic_id&&this.medical.config.clinic_id[0]},not_added_packages:function(t){var i=this.get_client(),t=t||i.running_packages,e=this.get_orderlines()||[],n=[];if(i){var r=_.pluck(e,"related_pkg_id");_.each(t,function(t){-1==_.indexOf(r,t.id)&&t.session_remaining&&n.push(t)})}return n},has_not_added_packages:function(){return this.not_added_packages().length||0},set_waiting_list:function(t){this.waiting_list_id=t},export_as_JSON:function(){var t=m.export_as_JSON.apply(this,arguments),i=this.get_client(),e=!!i&&"vip"==i.person_status,n=this.pricelist_id||this.insurance_card&&this.insurance_card.pricelist_id&&this.insurance_card.pricelist_id[0],r=this.get_clinic();return _.extend(t,{resource_id:this.resource_id,start_time:this.medical.chrome.format_server_datetime(this.start_time),orig_order_id:this.orig_order_id,has_priority:e,invoice_note:this.invoice_note,is_followup:this.is_followup,insurance_card_id:this.insurance_card_id,pricelist_id:n,ins_approval_no:this.ins_approval_no,ins_ticket_no:this.ins_ticket_no,ins_ref:this.ins_ref,ins_member:this.ins_member,clinic_id:r||this.MedicalModel.config.clinic_id[0],waiting_list_id:this.waiting_list_id||!1})},export_for_printing:function(){var t=m.export_for_printing.call(this);return _.extend(t,{resource_id:this.resource_id,start_time:this.start_time,start_time_display:this.get_start_time_display(),end_time:this.get_end_time(),insurance_card_id:this.insurance_card_id})},set_insurance_cover:function(t,i){if(t){var e=this.get_orderlines();_.each(e,function(i){var e=t[i.product.id];e&&i.set_insurance_cover(e)}),i&&(this.ins_approval_no=i.ins_approval_no||"",this.ins_ticket_no=i.ins_ticket_no||"",this.ins_ref=i.ins_ref||"",this.ins_member=i.ins_member||"")}},set_clinic:function(t){this.clinic_id=t},_checkOrderInsurance:function(){var t=this,i=this,e=this.get_orderlines();if(!i||!i.insurance_card_id){console.info("___ Insurance Card ID Not Found : ",i.insurance_card_id,i.insurance_card,i),this.medical.chrome.error_toast(c("Please select the Insurance Card first."));return}var n={};return _.each(e,function(t){var i=t.product.id,e=t.get_approved_price_unit(),r=t.get_price_unit_orig();e==r&&(e=0),n[i]?n[i].qty=n[i].qty+t.quantity:n[i]={qty:t.quantity,approved_amt:e,actual_amt:r,is_insurance_applicable:!0}}),console.log("___ models _checkOrderInsurance : ",i.insurance_card_id,n,e),this.medical._rpc_check_insurance_wrapper(i.insurance_card_id,n).then(function(n){console.log("___ models _checkOrderInsurance : Result : ",n),t.medical.gui.show_popup("popup-insurance-cover",{orderlines:e,result_lines:n.lines,insurance_card:i.get_insurance_card(),result_by_product:n.result_by_product,confirm:!1})})}});var g=h.Orderline.prototype;return h.Orderline=h.Orderline.extend({initialize:function(t,i){if(g.initialize.apply(this,arguments),this.product){var e;this.duration=this.product.duration,this.session_count=this.product.session_count,this.analytic_tag_ids=[],this.analytic_account_id=!1,this.is_medical_service=this.product.is_medical_service,this.is_insurance_applicable=!0,this.employee_id=!1,this.consumable_ids=[],this.start_time=!1,this.end_time=!1,e=void 0!==i.price?i.price:this.product.get_price(this.order.pricelist,this.get_quantity()),this.price_unit_orig=e,this.approved_price_unit=e,this.ins_price_unit=0,this.pricelist_item_id=!1}},update_db_line_data:function(t,i,e){console.log("___ child update_db_data : ",i.employee_id,t,i,e),i&&i.employee_id&&i.employee_id.length>1&&this.set_line_employee_id(i.employee_id[0]),i&&i.consumable_ids&&i.consumable_ids.length>1&&this.set_consumables(i.consumable_ids),i&&(this.orig_line_id=i.id)},set_insurance_cover:function(t){t.price_unit_orig&&(this.price_unit_orig=t.price_unit_orig),t.approved_price_unit&&(this.approved_price_unit=t.approved_price_unit),t.pricelist_item_id&&this.set_unit_price(t.price_unit),this.ins_fixed=t.ins_fixed,this.share_limit_type=t.share_limit_type,this.ins_price_unit=t.ins_price_unit,this.pricelist_item_id=t.pricelist_item_id,this.is_insurance_applicable=t.is_insurance_applicable,this.apply_ins_disc=t.apply_ins_disc,this.insurance_disc=t.insurance_disc,this.patient_share=t.patient_share,this.patient_share_limit=t.patient_share_limit,this.trigger("change",this)},set_session_count:function(t){this.session_count=t,this.trigger("change",this)},get_session_count:function(){return this.session_count},set_orderline_duration:function(t){this.duration=t,this.trigger("change",this)},set_analytic:function(t,i){t?(this.analytic_account_id=t,this.analytic_tag_ids=[]):i&&(this.analytic_account_id=!1,this.analytic_tag_ids=i),console.log("___ set_analytic : ",t,i,this.analytic_account_id,this.analytic_tag_ids),this.trigger("change",this)},get_analytic_acc_id:function(){return this.analytic_account_id},get_analytic_acc_display:function(){var t="",i=this.get_analytic_acc_id();if(i){var e=this.medical.analytic_account_by_id[i];e&&(t=e.name)}return t},get_analytic_tag_display:function(){var t=this,i=[];return this.analytic_tag_ids&&_.each(this.analytic_tag_ids,function(e){i.push(t.medical.analytic_tag_by_id[e].name)}),i},set_line_employee_id:function(t){this.employee_id=t,this.trigger("change",this)},get_line_employee_id:function(){return this.employee_id},get_line_employee:function(){var t={};return this.employee_id&&(t=_.findWhere(this.medical.all_employees,{id:this.employee_id})),t},set_consumables:function(t){this.consumable_ids=t,this.trigger("change",this)},get_consumable_ids:function(){return this.consumable_ids},get_consumable_display:function(){var t="";return'<span class="badge badge-info">'+this.consumable_ids.length+"</span>"},export_Common:function(){return{duration:this.duration,session_count:this.get_session_count(),analytic_tag_ids:this.analytic_tag_ids,analytic_account_id:this.analytic_account_id,is_medical_service:this.is_medical_service,pricelist_item_id:this.pricelist_item_id,apply_ins_disc:this.apply_ins_disc,insurance_disc:this.insurance_disc,patient_share:this.patient_share,patient_share_limit:this.patient_share_limit,is_insurance_applicable:this.is_insurance_applicable,ins_fixed:this.ins_fixed,share_limit_type:this.share_limit_type,related_pkg_id:this.related_pkg_id,price_unit_orig:this.get_price_unit_orig(),approved_price_unit:this.get_approved_price_unit(),ins_price_unit:this.get_ins_price_unit(),employee_id:this.get_line_employee_id(),is_tip:this.is_tip,consumable_ids:this.consumable_ids,start_time:this.start_time,end_time:this.end_time}},export_as_JSON:function(){var t=g.export_as_JSON.apply(this,arguments);return _.extend(t,this.export_Common(),{})},export_for_printing:function(){var t=g.export_for_printing.call(this);return _.extend(t,this.export_Common(),{})}}),h});