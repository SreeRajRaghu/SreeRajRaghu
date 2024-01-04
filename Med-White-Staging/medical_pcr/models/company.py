
import logging
import copy
import dateutil.relativedelta as relativedelta

import functools

from datetime import datetime, date as DATE
# from odoo.tools.safe_eval import safe_eval
from werkzeug import urls

from odoo import _, api, fields, models, tools
from odoo.addons.mail.models.mail_template import format_date
from odoo.exceptions import UserError
# from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)


SISMATIX_DEFAULT_DATE_FORMAT = '%d/%m/%Y'
SISMATIX_DEFAULT_DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'


def validate_args(date_time, format, is_only_date):
    if not date_time:
        return False
    if not format and is_only_date:
        format = SISMATIX_DEFAULT_DATE_FORMAT
    elif not format:
        format = SISMATIX_DEFAULT_DATETIME_FORMAT
    else:
        format = format
    return format


def format_date_to_str(date_obj, format=False, is_date=False):
    if type(date_obj) == datetime or type(date_obj) == DATE:
        format = validate_args(date_obj, format, is_date)
    else:
        return False

    if not format:
        return False
    try:
        return date_obj.strftime(format)
    except Exception as e:
        print('Exception: >>>>>>>>>>>>>>>>>>>>>>>>>>>', e)
        _logger.debug('Error while converting datetime %s %s', date_obj, format, exc_info=True)
        return False


def format_tz(env, dt, format=False, tz=False):
    if not dt:
        return ''
    record_user_timestamp = env.user.sudo().with_context(tz=tz or env.user.sudo().tz or 'UTC')
    is_date = False
    if type(dt) == DATE:
        is_date = True
        dt = datetime.combine(dt, datetime.min.time())
    ts = fields.Datetime.context_timestamp(record_user_timestamp, dt)
    if env.context.get('use_babel'):
        from babel.dates import format_datetime
        return format_datetime(ts, format or 'medium', locale=env.context.get("lang") or 'en_US')
    date = format_date_to_str(ts, format, is_date)
    return u"%s" % (date)


def format_amount(env, amount, currency):
    fmt = "%.{0}f".format(currency.decimal_places)
    lang = env['res.lang']._lang_get(env.context.get('lang') or 'en_US')

    formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
        .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

    pre = post = u''
    if currency.position == 'before':
        pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
    else:
        post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

    return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)


try:
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,
        'relativedelta': lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class Company(models.Model):
    _inherit = "res.company"

    stamp_image = fields.Binary("Stamp")
    sign_image = fields.Binary("Signature")
    stamp_image_general = fields.Binary("Stamp (General)")
    sign_image_general = fields.Binary("Signature(General)")
    # company_code = fields.Selection(selection_add=[
    #     ('pcr', 'PCR')
    # ], string='Company Code')

    terms_form1 = fields.Html("Form 1")
    terms_form2 = fields.Html("Form 2")
    terms_form3 = fields.Html("Form 3")
    terms_form4 = fields.Html("Form 4")
    test_before_travel_days = fields.Integer("Test Before Tranvel Days")
    # auto_test_after_positive = fields.Integer("Auto Book Test After Positive", default=8)
    pcr_test_duration = fields.Integer("Position: PCR Test Duration between Appointments", default=8)
    pcr_condition_ids = fields.One2many(
        "pcr.appointment.condition", "company_id", string="PCR Next Appointment Conditions")

    def get_next_app_rule(self, order):
        self.ensure_one()
        result = self.env['pcr.appointment.condition']
        if not self.pcr_condition_ids:
            return result

        for rule in self.pcr_condition_ids.filtered(lambda o: o.next_appointment):
            if rule.pcr_appointments_type and rule.pcr_appointments_type != order.pcr_appointments_type:
                continue

            if rule.pcr_type and rule.pcr_type != order.pcr_type:
                continue

            if rule.pcr_result and rule.pcr_result != order.pcr_result:
                continue

            return rule
        return result

    @api.model
    def render_tmpl_form(self, form1, ids):
        if not form1 or not ids:
            return ''
        return self._render_sms_template(form1, 'medical.order', ids)[ids[0]]

    @api.model
    def _render_sms_template(self, template_txt, model, res_ids):
        multi_mode = True
        if isinstance(res_ids, int):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        records = self.env[model].browse(it for it in res_ids if it)
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'format_date': lambda date, format=False, context=self._context: format_date(self.env, date, format),
            'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(self.env, dt, tz, format),
            'format_amount': lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
            'user': self.env.user,
            'ctx': self._context,
            'web_base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'dbname': self._cr.dbname,
        }
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
                raise UserError(_("Failed to render template %r using values %r") % (template, variables))
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result
        return multi_mode and results or results[res_ids[0]]
