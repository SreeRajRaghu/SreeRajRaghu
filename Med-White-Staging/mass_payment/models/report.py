# -*- encoding: UTF-8 -*

from odoo import api, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import config
from odoo.sql_db import TestCursor

import logging

from collections import OrderedDict

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_qweb_pdf(self, res_ids=None, data=None):
        if not data:
            data = {}
        data.setdefault('report_type', 'pdf')

        # In case of test environment without enough workers to perform calls to wkhtmltopdf,
        # fallback to render_html.
        if (tools.config['test_enable'] or tools.config['test_file']) and not self.env.context.get('force_report_rendering'):
            return self.render_qweb_html(res_ids, data=data)

        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        context = dict(self.env.context)
        if not config['test_enable']:
            context['commit_assetsbundle'] = True

        # Disable the debug mode in the PDF rendering in order to not split the assets bundle
        # into separated files to load. This is done because of an issue in wkhtmltopdf
        # failing to load the CSS/Javascript resources in time.
        # Without this, the header/footer of the reports randomly disapear
        # because the resources files are not loaded in time.
        # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2083
        context['debug'] = False

        # The test cursor prevents the use of another environnment while the current
        # transaction is not finished, leading to a deadlock when the report requests
        # an asset bundle during the execution of test scenarios. In this case, return
        # the html version.
        if isinstance(self.env.cr, TestCursor):
            return self.with_context(context).render_qweb_html(res_ids, data=data)[0]

        save_in_attachment = OrderedDict()
        if res_ids:
            # Dispatch the records by ones having an attachment and ones requesting a call to
            # wkhtmltopdf.
            Model = self.env[self.model]
            record_ids = Model.browse(res_ids)
            wk_record_ids = Model
            if self.attachment:
                for record_id in record_ids:
                    attachment = self.retrieve_attachment(record_id)
                    if attachment:
                        save_in_attachment[record_id.id] = self._retrieve_stream_from_attachment(attachment)
                    if not self.attachment_use or not attachment:
                        wk_record_ids += record_id
            else:
                wk_record_ids = record_ids
            res_ids = wk_record_ids.ids

        # A call to wkhtmltopdf is mandatory in 2 cases:
        # - The report is not linked to a record.
        # - The report is not fully present in attachments.
        if save_in_attachment and not res_ids:
            _logger.info('The PDF report has been generated from attachments.')
            return self._post_pdf(save_in_attachment), 'pdf'

        if self.get_wkhtmltopdf_state() == 'install':
            # wkhtmltopdf is not installed
            # the call should be catched before (cf /report/check_wkhtmltopdf) but
            # if get_pdf is called manually (email template), the check could be
            # bypassed
            raise UserError(_("Unable to find Wkhtmltopdf on this system. The PDF can not be created."))

        html = self.with_context(context).render_qweb_html(res_ids, data=data)[0]

        # Ensure the current document is utf-8 encoded.
        html = html.decode('utf-8')

        bodies, html_ids, header, footer, specific_paperformat_args = self.with_context(context)._prepare_html(html)

        if self.attachment and set(res_ids) != set(html_ids):
            raise UserError(_("The report's template '%s' is wrong, please contact your administrator. \n\n"
                "Can not separate file to save as attachment because the report's template does not contains the attributes 'data-oe-model' and 'data-oe-id' on the div with 'article' classname.") %  self.name)

        if res_ids and self.report_name == 'mass_payment.report_checkbook':
            doc = self.env[self.model].browse(res_ids[0])
            specific_paperformat_args['data-report-margin-top'] = doc.journal_id.top_margin
            specific_paperformat_args['data-report-margin-left'] = doc.journal_id.left_margin
            specific_paperformat_args['data-report-margin-right'] = doc.journal_id.right_margin
            specific_paperformat_args['data-report-margin-bottom'] = doc.journal_id.bottom_margin

        pdf_content = self._run_wkhtmltopdf(
            bodies,
            header=header,
            footer=footer,
            landscape=context.get('landscape'),
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=context.get('set_viewport_size'),
        )
        if res_ids:
            _logger.info('The PDF report has been generated for model: %s, records %s.' % (self.model, str(res_ids)))
            return self._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=html_ids), 'pdf'
        return pdf_content, 'pdf'

    @api.model
    def _build_wkhtmltopdf_args(
            self,
            paperformat_id,
            landscape,
            specific_paperformat_args=None,
            set_viewport_size=False):

        command_args = super(IrActionsReport, self)._build_wkhtmltopdf_args(
                                    paperformat_id,
                                    landscape,
                                    specific_paperformat_args,
                                    set_viewport_size)

        if specific_paperformat_args and specific_paperformat_args.get('data-report-margin-left'):
            command_args.extend(['--margin-left', str(specific_paperformat_args['data-report-margin-left'])])

        if specific_paperformat_args and specific_paperformat_args.get('data-report-margin-bottom'):
            command_args.extend(['--margin-bottom', str(specific_paperformat_args['data-report-margin-bottom'])])

        if specific_paperformat_args and specific_paperformat_args.get('data-report-margin-right'):
            command_args.extend(['--margin-right', str(specific_paperformat_args['data-report-margin-right'])])
        return command_args
