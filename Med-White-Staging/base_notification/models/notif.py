# coding: utf-8

import logging
import re
import copy
import dateutil.relativedelta as relativedelta

import functools

from operator import attrgetter

from collections import defaultdict

from datetime import timedelta, datetime, date as DATE
from odoo.tools.safe_eval import safe_eval
from werkzeug import urls

from odoo import _, api, fields, models, tools
from odoo.addons.mail.models.mail_template import format_date
from odoo.exceptions import UserError
from odoo.modules.registry import Registry

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


class SMSTemplate(models.Model):
    _name = "sms.sms.template"
    _description = "SMS Template"

    name = fields.Char('Title', required=True)
    model_id = fields.Many2one('ir.model', string='Applies To', required=True)
    model = fields.Char(string='Model', related='model_id.model')
    body_text = fields.Text("Template", required=True)
    active = fields.Boolean('Active', default=True)
    code = fields.Char("Code")
    language = fields.Selection([('en', 'English'), ('ar', 'Arabic')], default='en')

    @api.model
    def render(self, ids=[]):
        return self._render_sms_template(self.body_text, self.model, ids)

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
            'web_base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
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


class Recipient(models.Model):
    _name = "notif.recipient"
    _description = "Emails"

    name = fields.Char('Recipient', required=True,
                       help="Recipeint Type is manual then Email or Recipient Number, Otherwise Field Name")
    recipient_type = fields.Selection([
        ("number", 'Number'), ("email", 'Email'), ("field_phone", "Phone Record Fields"),
        ("field_email", "Email Record Fields")],
        default="number", string="Recipient Type", required=True)
    notify_id = fields.Many2one('notif.trigger', string='Email Notify')


class CustomDoamin(models.Model):
    _name = 'custom.domain'
    _description = "Custom Domain"

    custom_field = fields.Char('Field', required=True)
    operator = fields.Char('Operator', required=True)
    # custom_value = fields.Char('Value', required=True)
    custom_value = fields.Selection([
        ('computed_date', 'Computed Date'),
        ('computed_datetime', 'Computed Date and Time')
    ], required=True, string="Value", default="computed_date")
    duration = fields.Integer(default=0)
    dur_period = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ], string='Duration Period')

    # option = fields.Selection([("none", "N/A"), ("code")], default="none")
    # code = fields.Text("Code", default="# result = computed_date + relativedelta(days=1)")
    notify_id = fields.Many2one('notif.trigger', string="Email", )


class EmailNotify(models.Model):
    _name = "notif.trigger"
    _description = "Trigger Notifications"

    def _default_cron(self):
        cron = self.env.ref("mail_notification.ir_cron_daily_notification", False)
        return cron

    name = fields.Char('Name', required=True)
    ir_cron_id = fields.Many2one('ir.cron', string="Related Cron", default=_default_cron)
    model_id = fields.Many2one('ir.model', string="Model", required=True)
    model_name = fields.Char('Model Name', related='model_id.model', readonly=True, store=True)
    domain = fields.Char('Filter', default='[]')
    custom_domain_ids = fields.One2many('custom.domain', 'notify_id', stirng='Custom Filter')
    recipient_ids = fields.One2many('notif.recipient', 'notify_id', string='Emails')
    template_id = fields.Many2one(
        'mail.template', 'Email Template', ondelete='set null',
        domain="[('model_id', '=', model_id)]",
    )
    msg_template_id = fields.Many2one(
        'sms.sms.template', 'SMS Template', ondelete='set null',
        domain="[('model_id', '=', model_id)]",
    )
    is_multiple = fields.Boolean('Mail Per Record', default=True)
    force_send = fields.Boolean("Force Send",
                                help="If True, system will send email immediately, otherwise with cron job of mail management.")
    auto_delete = fields.Boolean(related="template_id.auto_delete")
    send_mail = fields.Boolean('Send Mail ?')
    sms_config_id = fields.Many2one('sms.config', string='SMS Configuration', requried=True)
    send_sms = fields.Boolean('Send SMS ?')
    keep_sms_history = fields.Boolean('Keep SMS History ?')
    on_action = fields.Selection(
        [('cron', 'On Scheduled Action'), ('create', 'On Creation Of Records'),
         ('write', 'On Updation Of Records'), ('unlink', 'On Deleting Records')],
        default='cron', required=True)
    active = fields.Boolean(default=True)
    trigger_once = fields.Boolean("Trigger Only Once Per Record ?")
    custom_domain_str = fields.Char("Test Domain (Compare UTC Now)", compute="_compute_custom_domain_str")

    # which fields have an impact on the registry
    CRITICAL_FIELDS = ['model_id', 'active', 'on_action']

    @api.model
    def create(self, vals):
        record = super(EmailNotify, self).create(vals)
        self.sudo()._update_registry()
        return record

    def write(self, vals):
        res = super(EmailNotify, self).write(vals)
        if set(vals).intersection(self.CRITICAL_FIELDS):
            self.sudo()._update_registry()
        return res

    def unlink(self):
        res = super(EmailNotify, self).unlink()
        self.sudo()._update_registry()
        return res

    def _update_registry(self):
        """ Update the registry after a modification on action rules. """
        if self.env.registry.ready and not self.env.context.get('import_file'):
            # for the sake of simplicity, simply force the registry to reload
            self._cr.commit()
            self.env.reset()
            registry = Registry.new(self._cr.dbname)
            registry.registry_invalidated = True

    def _compute_custom_domain_str(self):
        for rec in self:
            rec.custom_domain_str = rec.prepare_domain()

    def _get_computed_date(self, dt=None, params={}):
        if not dt:
            return None
        computed_d = dt + timedelta(**params)
        if isinstance(dt, datetime):
            computed_d = computed_d.replace(second=0, microsecond=0)
        return computed_d

    def prepare_domain(self, dt=None):
        if not dt:
            dt = datetime.now()
        self.ensure_one()
        computed_value = {
            'computed_date': dt.date(),
            'computed_datetime': dt
        }
        record_domain = []
        for line in self.sudo().custom_domain_ids:
            computed_d = computed_value[line.custom_value]
            if line.duration and line.dur_period:
                computed_d = self._get_computed_date(computed_d, {line.dur_period: line.duration})

            str_computed_d = (line.custom_value == 'computed_date') \
                and fields.Date.to_string(computed_d) \
                or fields.Datetime.to_string(computed_d)

            domain = [line.custom_field, line.operator, str_computed_d]
            record_domain += [domain]
        return record_domain

    def process_notif(self, cur_records=None):
        """
            - Filter Notifications to Execute by checking conditions
        """
        dt = datetime.now()
        for notif in self.sudo():
            RecordModel = self.env[notif.model_name].sudo()
            record_domain = safe_eval(notif.domain or [])

            if cur_records:
                record_domain += [('id', 'in', cur_records.ids)]
            record_domain += notif.prepare_domain(dt)
            filtered_records = RecordModel.sudo().search(record_domain)
            _logger.info("\n___ %s :: \n_____ Domain : %s\n_____ Records: %s ", notif.name, record_domain,
                         filtered_records)
            if filtered_records:
                if notif.send_sms:
                    notif.sudo()._do_sms(filtered_records)
                if notif.send_mail:
                    notif.sudo()._do_mail(filtered_records)

    def is_valid_email(self, email):
        return bool(re.match("^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", email))

    def parse_number(self, text):
        number = text or ''
        if number and len(number) == 8:
            number = '965' + text
        elif number and len(number) == 9:
            number = '96' + text
        elif number and len(number) == 10:
            number = '9' + text
        return number

    def get_contact_list(self, records):
        numbers = []
        emails = []

        for notif in self:
            for recevier in notif.recipient_ids:
                if recevier.recipient_type == 'number':
                    if recevier.name.isdigit():
                        field_value = notif.parse_number(recevier.name)
                        if field_value:
                            numbers.append(field_value)
                elif recevier.recipient_type == 'field_phone':
                    for rec in records:
                        field_value = attrgetter(recevier.name)(self.env[notif.model_id.model].browse([rec.id]))
                        field_value = notif.parse_number(field_value)
                        if field_value:
                            numbers.append(field_value)
                elif recevier.recipient_type == 'email':
                    if notif.is_valid_email(recevier.name):
                        emails.append(recevier.name)
                elif recevier.recipient_type == 'field_email':
                    for rec in records:
                        field_value = attrgetter(recevier.name)(self.env[notif.model_id.model].browse([rec.id]))
                        if field_value:
                            emails.append(field_value)

        numbers = ",".join(list(filter(lambda l: l, numbers)))
        return {'emails': emails, 'numbers': numbers}

    def _do_sms(self, records):
        """ Empty for API
        """
        self.ensure_one()

    def btn_process_notif(self):
        # records = self.env[self.model_id.model].search([])
        # notifs = self.env['notif.trigger']._get_notifs(records, self.on_action)
        # self.with_env(notifs.env)
        self.with_context(old_values=None).process_notif()

    def _do_mail(self, records):
        """ Empty for API
        """
        self.ensure_one()
        # recipient_ids = self.recipient_ids.mapped("name") or []
        # emails = ",".join(recipient_ids)
        if self.is_multiple:
            for rec in records:
                recipients = self.sudo().get_contact_list(rec)
                emails = recipients.get('emails')
                self.template_id.send_mail(
                    res_id=rec.id,
                    force_send=self.force_send,
                    email_values={
                        'subject': self.name,
                        'email_to': emails,
                    })
        else:
            recipients = self.sudo().get_contact_list(records)
            emails = recipients.get('emails')
            self.template_id.with_context(records=records).send_mail(
                res_id=records[0].id,
                force_send=self.force_send,
                email_values={
                    'subject': self.name,
                    'email_to': emails,
                })

    def _get_notifs(self, records, action):
        if '__action_done' not in self._context:
            self = self.with_context(__action_done={})
        domain = [('model_name', '=', records._name), ('on_action', '=', action)]
        notifs = self.with_context(active_test=True).search(domain)
        return notifs.with_env(self.env)

    def _register_hook(self):

        def make_create():
            @api.model
            def create(self, vals, **kw):
                notifs = self.env['notif.trigger']._get_notifs(self, 'create')
                # retrieve the notification to possibly execute
                # call original method
                record = create.origin(self.with_env(notifs.env), vals, **kw)
                # check postconditions, and execute notifs on the records that satisfy them
                notifs.with_context(old_values=None).process_notif(record)
                return record.with_env(self.env)

            return create

        def make_write():
            #
            # Note: we patch method _write() instead of write() in order to
            # catch updates made by field recomputations.
            #
            def _write(self, vals, **kw):
                # retrieve the notification to possibly execute
                notifs = self.env['notif.trigger']._get_notifs(self, 'write')
                records = self.with_env(notifs.env)
                _write.origin(records, vals, **kw)
                notifs.with_context(old_values=None).process_notif(records)
                return records.with_env(self.env)

            return _write

        def make_unlink():
            """ Instanciate an unlink method that processes notification. """

            def unlink(self, **kwargs):
                # retrieve the notification to possibly execute
                notifs = self.env['notif.trigger']._get_notifs(self, 'unlink')
                records = self.with_env(notifs.env)
                # check conditions, and execute actions on the records that satisfy them
                records = self.with_env(notifs.env)
                notifs.with_context(old_values=None).process_notif(records)
                return unlink.origin(self, **kwargs)

            return unlink

        patched_models = defaultdict(set)

        def patch(model, name, method):
            """ Patch method `name` on `model`, unless it has been patched already. """
            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        # retrieve all actions, and patch their corresponding model
        for base_notif in self.with_context({}).search([]):
            Model = self.env.get(base_notif.model_name)

            if Model is None:
                _logger.warning("Notification with ID %d depends on model %s" %
                                (base_notif.id,
                                 base_notif.model_name))
                continue
            if base_notif.on_action == 'create':
                patch(Model, 'create', make_create())

            elif base_notif.on_action == 'write':
                patch(Model, '_write', make_write())

            elif base_notif.on_action == 'unlink':
                patch(Model, 'unlink', make_unlink())
