# -*- coding: UTF-8 -*-

import base64
import calendar
import xlsxwriter
from io import BytesIO
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InsuranceReportWizard(models.TransientModel):
    _name = 'insurance.report.wizard'
    _description = 'Insurance Report Wizard'

    def _default_from_date(self):
        return fields.Date.today() - relativedelta(months=1, days=-1)

    def _default_clinc_ids(self):
        login_user_id = self.env.user.id
        clinics = self.env['medical.clinic'].search([('user_ids', 'in', login_user_id)])
        return clinics

    from_date = fields.Date(default=_default_from_date, required=True)
    to_date = fields.Date(default=lambda self: fields.Date.today(), required=True)
    insurance_company_ids = fields.Many2many(
        'res.partner', 'res_partner_insurance_company_ids_rel',
        string='Insurance Companies',
        domain="[('is_insurance_company', '=', True), ('parent_id', '=', False)]")
    insurance_sub_company_ids = fields.Many2many(
        'res.partner', 'res_partner_insurance_sub_company_ids_rel',
        string='Insurance Sub Companies',
        domain="[('is_insurance_company', '=', True), ('parent_id', '!=', False)]")
    clinic_ids = fields.Many2many('medical.clinic', string='Clinics', required="True")
    invoice_status = fields.Selection([('draft', 'Only Draft'), ('posted', 'Only Posted'), ('both', 'Both (Draft & Posted)')], string="Invoice Status", default='both')
    filename = fields.Binary()
    include_no_records = fields.Boolean("Include Even Zero Records")
    allow_clinic_ids = fields.Many2many('medical.clinic', 'insurance_wizard_id', 'clinic_id', default=_default_clinc_ids)

    @api.onchange('insurance_company_ids')
    def _onchange_insurance_company_ids(self):
        sub_company_domain = [('is_insurance_company', '=', True)]
        if self.insurance_company_ids:
            sub_company_domain.extend([('parent_id', 'in', self.insurance_company_ids.ids)])
        else:
            sub_company_domain.extend([('parent_id', '!=', False)])

        return {
            'value': {
                'insurance_sub_company_ids': [],
            },
            'domain': {
                'insurance_sub_company_ids': sub_company_domain
            }
        }

    def print_excel(self):
        AccMove = self.env['account.move']
        insurance_companies = self.insurance_company_ids
        insurance_sub_companies = self.insurance_sub_company_ids
        do_consider_parent = True
        Partner = self.env['res.partner']

        if not insurance_companies and not insurance_sub_companies:
            insurance_companies = Partner.search([('is_insurance_company', '=', True), ('parent_id', '=', False)])
            insurance_sub_companies = Partner.search([('is_insurance_company', '=', True), ('parent_id', '!=', False)])
        elif insurance_companies and not insurance_sub_companies:
            insurance_sub_companies = Partner.search([('is_insurance_company', '=', True), ('parent_id', 'in', insurance_companies.ids)])
        elif not insurance_companies and insurance_sub_companies:
            insurance_companies = insurance_sub_companies.mapped('parent_id')
            do_consider_parent = False

        DOMAIN = [
            ('invoice_date', '>=', self.from_date),
            ('invoice_date', '<=', self.to_date),
            ('is_insurance_invoice', '=', True),
            ('type', 'in', ['out_refund', 'out_invoice'])
            # ('insurance_card_id.main_company_id', 'in', insurance_companies.ids),
            # ('insurance_card_id.insurance_company_id', 'in', insurance_sub_companies.ids)
        ]

        if self.clinic_ids:
            DOMAIN.extend([('branch_id', 'in', self.clinic_ids.ids)])

        if self.invoice_status == 'both':
            DOMAIN.extend([('insurance_card_id', '!=', False), ('state', '!=', 'cancel')])
        else:
            DOMAIN.extend([('insurance_card_id', '!=', False), ('state', '=', self.invoice_status)])

        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        def get_date_format(dt):
            return dt.strftime(date_format) if dt else ''

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        bi_18_center = workbook.add_format({'bold': True, 'italic': True, 'font_size': '16', 'align': 'center'})
        b_14_center = workbook.add_format({'bold': True, 'font_size': '14', 'align': 'center'})

        month_title = "%s - %s" % (get_date_format(self.from_date), get_date_format(self.to_date))

        columns = {
            'al_ahleia_ins': ['No.', 'Name', 'Arabic Name', 'File No.', 'Reference', 'Date', 'Invoice No.', 'Total Amount', 'After 20% Dis', 'Patient Paid Amount', 'Net Claim', 'Branch'],
            'metlife_alico': ['ClaimFormNo', 'OnSet Date', 'MedWhite Invoice Number', 'Reference', 'Patient ID', 'Name', 'Arabic Name', 'Seq No.', 'Svc Code', 'Svc Description', 'Svc Date', 'End Date', 'Scv Units', 'Claim Amt', 'Discount', 'Copay', 'Coins', 'Net Amt', 'Approval No.', 'Branch'],
            'national_takaful': ['No.', 'Name', 'Arabic Name', 'File No.', 'Reference', 'The Date', 'The Amount', 'Discount Amount', 'Deductible', 'The Net', 'Branch'],
            'mednet': ['S.No.', 'Member Name', 'Arabic Name', 'Card No', 'Policy Name/Ins. Company', 'Invoice No', 'Reference', 'Invoice Date', 'Gross Amount', 'Discount', 'Co Payment/Member Part', 'Net Amount', 'Branch'],
            'gulf_takaful': ['No.', 'Date', 'Patient Name/English', 'Patient Name/Arabic', 'File No.', 'Reference', 'Card #', 'Invo. #', 'Procedure', 'Total', 'Deductible', 'Discount', 'Net Amount', 'Policy Holder', 'Branch'],
            'bahrain_kuwait_insurance': ['Date', 'Patient Name/English', 'Patient Name/Arabic', 'File No.', 'Reference', 'Card #', 'Member No', 'Invo. #', 'Procedure', 'Total', 'Deductible', 'Discount', 'Net Amount', 'Policy Holder', 'Branch'],
            'kuwait_ins': ['S.No.', 'Name', 'Arabic Name', 'File No.', 'Invoice No.', 'Reference', 'Procedure', 'Treatment Date', 'Gross Amount', 'Paid Deductible at Hospital', '18% Discount ', 'Net Claimed Amount', 'Company Name', 'Branch'],
            'gig': ['SR.No.', 'Product', 'Incident #', 'Auth #', 'PreInvoice #', 'Civil ID', 'Member ID', 'Member Name', 'Arabic Name', 'Auth Date', 'FILE NO.', 'Reference', 'Invoice No.', 'Incident Type', 'Claim Amount', 'Exceeding Limit Amount', 'Discount Amount', 'Co-Payment and Deductable', 'Net Amount', 'Branch'],
            'wapmed': ['Insurance Co Name', 'UHID / WAPK.', 'Civil ID Number', 'EEA NO.', 'PATIENT NAME/ENGLISH', 'PATIENT NAME/ARABIC', 'Invoice DATE', 'CLAIM NO.', 'SCAN REFRENCE NUMBER', 'File No. / MRD', 'Reference', 'Invoice Number', 'Department (OP / Dental / Maternity / IP / Opthal)', 'Diagnosis (Optional)', 'Service Type', 'Service  gross Amount', 'Deductible', 'Total Discount', 'Net Payable Amount', 'Branch'],
            'globemed': ['Sr NO', 'Insurance Co', 'Transaction Date ', 'Patient Name/English', 'Patient Name/Arabic', 'Patient Mobile number ', 'Reference', 'Individual Number', 'CID Number', 'Medical file No', 'Invoice No.', 'ICD/diseasr', "Dr'name", 'SSNBR # ', 'MCN ', 'Service code', 'Service Description', 'Unit Price Before Approval', 'Unit Price', 'Total Price', 'Commercial Disc', 'Patient Part', 'NET AMT', '2% Service Fees', 'Net Recievable', 'Branch'],
            'nas': ['S.No', 'Invoice Nbr', 'File No', 'Reference', 'Txn Date', 'Beneficiary Name', 'Arabic Name',  'Card Nbr', 'Authorization No.', 'Insurance Co Name', 'Claim Amount', 'Exceeding Limit Amount', 'Discount Amount', 'Deductable Amount', 'Net Amount', 'Branch'],
            'saudi_arabian_ins_co_saico': ['Sr.No', 'Patient Name/English', 'Patient Name/Arabic', 'Approval #', 'Ticket No', 'File No.', 'Reference', 'Date', 'Invoice No.', 'Treatment Amount', 'After  20% Discount', 'Deductible Amount', 'Net Amount', 'Doctor Name', 'Branch'],
        }

        def _generate_columns(company_name, worksheet, at_row):
            sheet_columns = columns.get(company_name)

            for at_col in range(len(sheet_columns)):
                column = sheet_columns[at_col]
                worksheet.set_column(at_row, at_col, column['size'])
                worksheet.write(at_row, at_col, column['label'], column['format'])

        x_total = x_comm_disc = x_patient_share = x_net = 0

        def _get_app_lines(invoice):
            # lines = invoice.medical_order_id.line_ids.filtered(lambda l: l.pricelist_item_id and l.qty > 0)
            lines = invoice.invoice_line_ids.filtered(lambda l: l.medical_order_line_id.pricelist_item_id and l.quantity > 0)
            return lines

        def _get_totals(lines, after_comm_disc=False, match_net=False, invoice=False):

            nonlocal x_total
            nonlocal x_comm_disc
            nonlocal x_patient_share
            nonlocal x_net

            total = comm_disc = patient_share = net = 0

            for line in lines:
                apu = line.medical_order_line_id.approved_price_unit
                qty = line.quantity

                total += apu * qty
                if after_comm_disc:
                    comm_disc += (apu * (1 - line.medical_order_line_id.insurance_disc / 100)) * qty
                else:
                    comm_disc += (apu * line.medical_order_line_id.insurance_disc / 100) * qty
                patient_share += line.medical_order_line_id.price_unit * qty

                if match_net:
                    net += total - comm_disc - patient_share
                else:
                    net += line.medical_order_line_id.ins_price_unit * qty

            if invoice and invoice.type == 'out_refund':
                total = total * -1
                comm_disc = comm_disc * -1
                patient_share = patient_share * -1
                net = net * -1

            x_total += total
            x_comm_disc += comm_disc
            x_patient_share += patient_share
            x_net += net

            return total, comm_disc, patient_share, net

        summary_dict = {
            'al_ahleia_ins': {'title': 'AL Ahleia Ins', 'lines': []},
            'metlife_alico': {'title': 'Metlife Alico', 'lines': []},
            'national_takaful': {'title': 'National Takaful', 'lines': []},
            'mednet': {'title': 'MEDNET', 'lines': []},
            'gulf_takaful': {'title': 'Gulf Takaful', 'lines': []},
            'bahrain_kuwait_insurance': {'title': 'BAHRAIN KUWAIT INSURANCE', 'lines': []},
            'kuwait_ins': {'title': 'KUWAIT Ins', 'lines': []},
            'gig': {'title': 'GIG', 'lines': []},
            'wapmed': {'title': 'WAPMED', 'lines': []},
            'globemed': {'title': 'GLOBEMED', 'lines': []},
            'nas': {'title': 'NAS', 'lines': []},
            'saudi_arabian_ins_co_saico': {'title': 'SAUDI ARABIAN Ins SAICO', 'lines': []},
        }

        for mic in insurance_companies:

            sub_companies = insurance_sub_companies.filtered(lambda c: c.parent_id == mic)

            if not sub_companies and do_consider_parent:
                sub_companies = mic
                target_field = 'insurance_card_id.main_company_id'
            else:
                target_field = 'insurance_card_id.insurance_company_id'

            for ic in sub_companies:
                ic_appointments = AccMove.search(DOMAIN + [(target_field, '=', ic.id)], order="invoice_date")

                sheet_name = ''
                if ic.parent_id:
                    sheet_name += mic.name + ' - '
                sheet_name += ic.name
                ins_report_format = mic.ins_report_format
                sheet_name = (sheet_name or 'Ins. Report')[:31]

                worksheet = False
                header_at = 4
                at_row = 5
                if not ins_report_format:
                    raise UserError(_("Report doesn't configured for `%s`") % (mic.name))

                x_total = x_comm_disc = x_patient_share = x_net = 0

                # AL AHLIA
                if ins_report_format == 'al_ahleia_ins':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)

                    # title
                    worksheet.merge_range(1, 0, 1, 8, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 8, "%s Claim Report" % (ic.name), bi_18_center)
                    worksheet.merge_range(3, 0, 3, 8, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name

                        total, comm_disc, patient_share, net = _get_totals(
                            _get_app_lines(invoice), after_comm_disc=True, invoice=invoice)

                        col = 0
                        worksheet.write(at_row, col, cnt+1)
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')
                        col += 1
                        worksheet.write(at_row, col, file_no or '')
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')
                        col += 1
                        worksheet.write(at_row, col, inv_no or '')
                        col += 1
                        worksheet.write(at_row, col, total)
                        col += 1
                        worksheet.write(at_row, col, comm_disc)
                        col += 1
                        worksheet.write(at_row, col, patient_share)
                        col += 1
                        worksheet.write(at_row, col, net)
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 6
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # METLIFE ALICO
                if ins_report_format == 'metlife_alico':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 16, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 16, "%s  Claim Report %s" % (ic.name, month_title), bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)

                    # header
                    header_at = 4

                    # data
                    at_row = 5
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name
                        # Customer Req. To Add 1 month
                        # end_date = appointment.start_time + relativedelta(months=1)
                        inv_dt = invoice.invoice_date
                        end_date = inv_dt + relativedelta(month=1)
                        # end_date = type(end_date)(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])
                        apt_end_date = get_date_format(end_date)
                        ins_approval_no = appointment.ins_approval_no
                        ins_ref = appointment.ins_ref

                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # No.
                        for line in _get_app_lines(invoice):
                            qty = line.quantity
                            total, comm_disc, patient_share, net = _get_totals(line, invoice=invoice)

                            col = 0
                            worksheet.write(at_row, col, ins_ref)  # ClaimFormNo
                            col += 1
                            worksheet.write(at_row, col, apt_date or '')  # OnSet Date
                            col += 1
                            worksheet.write(at_row, col, inv_no or '')  # Med White Invoice Number
                            col += 1
                            worksheet.write(at_row, col, invoice.ref or '')  # Invoice Ref
                            col += 1
                            worksheet.write(at_row, col, file_no or '')  # Patient ID
                            col += 1
                            worksheet.write(at_row, col, patient_name or '')  # Name
                            col += 1
                            worksheet.write(at_row, col, patient_ar_name or '')  # Arabic
                            col += 1
                            worksheet.write(at_row, col, 1)  # Seq No.
                            col += 1
                            worksheet.write(at_row, col, line.product_id.default_code or '')  # Svc Code
                            col += 1
                            worksheet.write(at_row, col, line.product_id.name or '')  # Svc Description
                            col += 1
                            worksheet.write(at_row, col, apt_date or '')  # Svc Date
                            col += 1
                            worksheet.write(at_row, col, apt_end_date or '')  # End Date
                            col += 1
                            worksheet.write(at_row, col, qty or '')  # Svc Units
                            col += 1
                            worksheet.write(at_row, col, total)  # Claim Amt
                            col += 1
                            worksheet.write(at_row, col, comm_disc)  # Discount
                            col += 1
                            worksheet.write(at_row, col, patient_share)  # Copay
                            col += 1
                            worksheet.write(at_row, col, '0.000')  # Coins
                            col += 1
                            worksheet.write(at_row, col, net)  # Net Amt
                            col += 1
                            worksheet.write(at_row, col, ins_approval_no)  # Approval No.
                            col += 1
                            worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                            at_row += 1

                    # footer
                    at_row += 1
                    col = 12
                    worksheet.merge_range(at_row, 0, at_row, col, 'Total', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '0', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '', b_14_center)

                # NATIONAL TAKAFUL X
                if ins_report_format == 'national_takaful':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 9, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 9, ic.name, bi_18_center)
                    worksheet.merge_range(3, 0, 3, 9, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name

                        total, comm_disc, patient_share, net = _get_totals(
                            _get_app_lines(invoice), invoice=invoice)
                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # No.
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Name
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No.
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Invoice Ref.
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # The Date
                        col += 1
                        worksheet.write(at_row, col, total)  # The Amount
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount Amount
                        # Customer Asked: No ned 15%, 10%, 5 K.D. Column
                        # Instead Add Deductible Column
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # 15%
                        col += 1
                        worksheet.write(at_row, col, net)  # 10%
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 7
                    worksheet.merge_range(at_row, 0, at_row, col, 'The total before disc.', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.merge_range(at_row, col, at_row, col + 1, 'The total after', b_14_center)
                    col += 2
                    worksheet.write(at_row, col, x_net, b_14_center)

                # MEDNET
                if ins_report_format == 'mednet':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 9, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 9, "%s CLAIMS STATEMENT" % ic.name, bi_18_center)
                    worksheet.merge_range(3, 0, 3, 9, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        ins_card = invoice.insurance_card_id
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name
                        total, comm_disc, patient_share, net = _get_totals(
                            _get_app_lines(invoice), invoice=invoice)

                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # S.No.
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Member Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Member Name Arabic
                        col += 1
                        worksheet.write(at_row, col, ins_card.name or '')  # Card No
                        col += 1
                        worksheet.write(at_row, col, ic.name or '')  # Policy Name/Ins. Company
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invoice No
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Invoice Ref
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # Invoice Date
                        col += 1
                        worksheet.write(at_row, col, total)  # Gross Amount
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Co Payment/Member Part
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Amount
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 7
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # GULF TAKAFUL
                if ins_report_format == 'gulf_takaful':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 12, ic.name, bi_18_center)
                    worksheet.merge_range(2, 0, 2, 12, "Med White", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 12, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        ins_card = invoice.insurance_card_id

                        lines = _get_app_lines(invoice)
                        total, comm_disc, patient_share, net = _get_totals(
                            lines, match_net=False, invoice=invoice)

                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # No.
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # Date
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Patient Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Patient Arabic Name
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No.
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref
                        col += 1
                        worksheet.write(at_row, col, ins_card.name or '')  # Card #
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invo. #
                        # col += 1
                        # worksheet.write(at_row, col, '' or '')  # Cons.
                        col += 1
                        worksheet.write(at_row, col, '\n'.join(lines.mapped('product_id.name')) or '')  # Procedure
                        col += 1
                        worksheet.write(at_row, col, total)  # Total
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Deductible
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Amount
                        col += 1
                        worksheet.write(at_row, col, ic.name or '')  # Policy Holder
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    col = 8
                    at_row += 1
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '', b_14_center)

                # BAHRAIN KUWAIT INSURANCE X
                if ins_report_format == 'bahrain_kuwait_insurance':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 11, sheet_name, bi_18_center)
                    worksheet.merge_range(2, 0, 2, 11, "Med White", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 11, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name
                        ins_card = invoice.insurance_card_id

                        lines = _get_app_lines(invoice)
                        total, comm_disc, patient_share, net = _get_totals(
                            lines, invoice=invoice)
                        col = 0
                        worksheet.write(at_row, col, apt_date or '')  # Date
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Patient Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Patient Arabic Name
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No.
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Invoice Ref
                        col += 1
                        worksheet.write(at_row, col, ins_card.name or '')  # Card #
                        col += 1
                        worksheet.write(at_row, col, '')  # Member No
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invo. #
                        col += 1
                        worksheet.write(at_row, col, '\n'.join(lines.mapped('product_id.name')) or '')  # Procedure
                        col += 1
                        worksheet.write(at_row, col, total)  # Total
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Deductible
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Amount
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Policy Holder
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    col = 9
                    at_row += 1
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # KUWAIT INSURANCE
                if ins_report_format == 'kuwait_ins':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 10, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 10, "%s  Claim Report" % ic.name, bi_18_center)
                    worksheet.merge_range(3, 0, 3, 10, month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name

                        lines = _get_app_lines(invoice)
                        total, comm_disc, patient_share, net = _get_totals(lines, invoice=invoice)
                        col = 1
                        worksheet.write(at_row, col, cnt+1)  # S.No.
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Name
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No.
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invoice No.
                        col += 1
                        worksheet.write(at_row, col, '\n'.join(lines.mapped('product_id.name')) or '')  # Procedure
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # Treatment Date
                        col += 1
                        worksheet.write(at_row, col, total)  # Gross Amount
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Paid Deductible at Hospital
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # 18% Discount
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Claimed Amount
                        col += 1
                        worksheet.write(at_row, col, ic.name or '')  # Company Name
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 8
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '', b_14_center)

                # GIG
                if ins_report_format == 'gig':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 16, "Out-patient Statement of Accounts", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 16, "Med White", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 16, "%s Claims for the %s" % (ic.name, month_title), bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient = appointment.partner_id
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        ins_approval_no = appointment.ins_approval_no
                        ins_ticket_no = appointment.ins_ticket_no
                        ins_ref = appointment.ins_ref
                        ins_member = appointment.ins_member

                        total, comm_disc, patient_share, net = _get_totals(
                            _get_app_lines(invoice), invoice=invoice)

                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # SR.No.
                        col += 1
                        worksheet.write(at_row, col, ic.name or '')  # Product
                        col += 1
                        worksheet.write(at_row, col, ins_approval_no)  # Incident #
                        col += 1
                        worksheet.write(at_row, col, ins_ticket_no)  # Auth #
                        col += 1
                        worksheet.write(at_row, col, ins_ref)  # PreInvoice #
                        col += 1
                        worksheet.write(at_row, col, patient.civil_code or '')  # Civil ID
                        col += 1
                        worksheet.write(at_row, col, ins_member)  # Member ID
                        col += 1
                        worksheet.write(at_row, col, patient.name)  # Member Name
                        col += 1
                        worksheet.write(at_row, col, patient.ar_name)  # Member Name
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # Auth Date
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # FILE NO.
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref.
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invoice No.
                        col += 1
                        worksheet.write(at_row, col, 'Dental')  # Incident Type
                        col += 1
                        worksheet.write(at_row, col, total)  # Claim Amount
                        col += 1
                        worksheet.write(at_row, col, '')  # Exceeding Limit Amount
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount Amount
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Co-Payment and Deductable
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Amount
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 13
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '0', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # WAPMED
                if ins_report_format == 'wapmed':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 16, "Med White", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 16, ic.name, bi_18_center)
                    worksheet.merge_range(3, 0, 3, 16, "STATEMENT OF ACCOUNT FOR %s" % month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient = appointment.partner_id
                        file_no = appointment.file_no
                        # apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name

                        ins_approval_no = appointment.ins_approval_no
                        ins_ticket_no = appointment.ins_ticket_no
                        ins_ref = appointment.ins_ref
                        ins_card = invoice.insurance_card_id

                        lines = _get_app_lines(invoice)
                        total, comm_disc, patient_share, net = _get_totals(lines, invoice=invoice)
                        col = 0
                        worksheet.write(at_row, col, ic.name or '')  # Insurance Co Name
                        col += 1
                        worksheet.write(at_row, col, ins_card.name or '')  # UHID / WAPK.
                        col += 1
                        worksheet.write(at_row, col, patient.civil_code or '')  # Civil ID Number
                        col += 1
                        worksheet.write(at_row, col, ins_approval_no)  # EEA NO.
                        col += 1
                        worksheet.write(at_row, col, patient.name or '')  # PATIENT NAME
                        col += 1
                        worksheet.write(at_row, col, patient.ar_name or '')  # PATIENT ARABIC NAME
                        col += 1
                        worksheet.write(at_row, col, get_date_format(invoice.invoice_date) or '')  # Invoice DATE
                        col += 1
                        worksheet.write(at_row, col, cnt+1)  # CLAIM NO.
                        col += 1
                        worksheet.write(at_row, col, ins_ref)  # SCAN REFRENCE NUMBER
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No. / MRD
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invoice Number
                        col += 1
                        worksheet.write(at_row, col, 'Dental')  # Department (OP / Dental / Maternity / IP / Opthal)
                        col += 1
                        worksheet.write(at_row, col, '')  # Diagnosis (Optional)
                        col += 1
                        worksheet.write(at_row, col, ', '.join(lines.mapped('product_id.name')))  # Service Type
                        col += 1
                        worksheet.write(at_row, col, total)  # Service  gross Amount
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Deductible
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Total Discount
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Payable Amount
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    at_row += 1
                    col = 14
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # GLOBEMED
                if ins_report_format == 'globemed':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 16, "Out-patient Statement of Accounts", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 16, "Med White", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 16, month_title, bi_18_center)
                    worksheet.merge_range(4, 0, 4, 16, ic.name, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)
                    worksheet.set_row(4, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    x_service_disc = x_subtotal = 0
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient = appointment.partner_id
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name
                        doctor = appointment.resource_id
                        ins_card = invoice.insurance_card_id
                        main_comp = ins_card.main_company_id
                        ins_approval_no = appointment.ins_approval_no
                        ins_ticket_no = appointment.ins_ticket_no
                        # ins_ref = appointment.ins_ref

                        worksheet.write(at_row, 0, cnt+1)  # Sr NO
                        for line in _get_app_lines(invoice):
                            # total, comm_disc, patient_share, net = _get_totals(line, invoice=invoice)
                            qty = line.quantity
                            approved_price_unit = line.medical_order_line_id.approved_price_unit
                            unit_price_before_approval = line.medical_order_line_id.price_unit_orig

                            total = line.medical_order_line_id.approved_price_unit * qty
                            comm_disc = (total * main_comp.report_commercial_disc) / 100
                            service_disc = (total * main_comp.report_service_fees) / 100
                            patient_share = line.medical_order_line_id.price_unit * qty
                            net = total - comm_disc - patient_share
                            net_service_disc = net - service_disc

                            if invoice and invoice.type == 'out_refund':
                                patient_share = patient_share * -1
                                approved_price_unit = approved_price_unit * -1
                                unit_price_before_approval = unit_price_before_approval * -1
                                total = total * -1
                                comm_disc = comm_disc * -1
                                service_disc = service_disc * -1
                                net = net * -1

                                net_service_disc = net_service_disc * -1

                            x_total += total
                            x_comm_disc += comm_disc
                            x_patient_share += patient_share
                            x_subtotal += (net - service_disc)
                            x_service_disc += service_disc
                            x_net += net

                            col = 1
                            worksheet.write(at_row, col, ins_card.insurance_company_id.name or '')  # Insurance Co
                            col += 1
                            worksheet.write(at_row, col, apt_date or '')  # Transaction Date
                            col += 1
                            worksheet.write(at_row, col, patient.name or '')  # Patient Name
                            col += 1
                            worksheet.write(at_row, col, patient.ar_name or '')  # Pattient Arebic Name
                            col += 1
                            worksheet.write(at_row, col, patient.mobile or patient.phone or '')  # Patient Mobile number
                            col += 1
                            worksheet.write(at_row, col, invoice.ref or '')  # Invoice Ref
                            col += 1
                            worksheet.write(at_row, col, ins_card.name)  # Individual Number
                            col += 1
                            worksheet.write(at_row, col, patient.civil_code or '')  # CID Number
                            col += 1
                            worksheet.write(at_row, col, file_no or '')  # Medical file No
                            col += 1
                            worksheet.write(at_row, col, invoice.name or '')  # Invoice No.
                            col += 1
                            worksheet.write(at_row, col, 'K08.9')  # ICD/diseasr
                            col += 1
                            worksheet.write(at_row, col, doctor.name or '')  # Dr'name
                            col += 1
                            worksheet.write(at_row, col, ins_approval_no)  # SSNBR #
                            col += 1
                            worksheet.write(at_row, col, ins_ticket_no)  # MCN
                            col += 1
                            worksheet.write(at_row, col, line.product_id.default_code or '')  # Service code
                            col += 1
                            worksheet.write(at_row, col, line.product_id.name or '')  # Service Description
                            col += 1
                            worksheet.write(at_row, col, unit_price_before_approval)  # Unit Price Before Approval
                            col += 1
                            worksheet.write(at_row, col, approved_price_unit)  # Unit Price
                            col += 1
                            worksheet.write(at_row, col, total)  # Total Price
                            col += 1
                            worksheet.write(at_row, col, comm_disc)  # Commercial Disc
                            col += 1
                            worksheet.write(at_row, col, patient_share)  # Patient Part
                            col += 1
                            worksheet.write(at_row, col, net)  # NET AMT
                            col += 1
                            worksheet.write(at_row, col, service_disc)  # 2% Service Fees
                            col += 1
                            worksheet.write(at_row, col, net_service_disc)  # Net Recievable
                            col += 1
                            worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                            at_row += 1

                    # footer
                    at_row += 1
                    col = 18
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, round(x_service_disc, 4), b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_subtotal, b_14_center)

                # NAS
                if ins_report_format == 'nas':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 12, "Out-patient Statement of Accounts", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 12, "Med White", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 12, "%s Claims for the %s" % (ic.name, month_title), bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        ins_card = invoice.insurance_card_id
                        inv_no = invoice.name

                        total, comm_disc, patient_share, net = _get_totals(
                            _get_app_lines(invoice), invoice=invoice)

                        col = 0
                        worksheet.write(at_row, col, cnt+1)  # S.No
                        col += 1
                        worksheet.write(at_row, col, invoice.name or '')  # Invoice Nbr
                        col += 1
                        worksheet.write(at_row, col, file_no or '')  # File No
                        col += 1
                        worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref
                        col += 1
                        worksheet.write(at_row, col, apt_date or '')  # Txn Date
                        col += 1
                        worksheet.write(at_row, col, patient_name or '')  # Beneficiary Name
                        col += 1
                        worksheet.write(at_row, col, patient_ar_name or '')  # Beneficiary Name
                        col += 1
                        worksheet.write(at_row, col, ins_card.name or '')  # Card Nbr
                        col += 1
                        worksheet.write(at_row, col, appointment.ins_ticket_no)  # Authorization No.
                        col += 1
                        worksheet.write(at_row, col, ic.name or '')  # Insurance Co Name
                        col += 1
                        worksheet.write(at_row, col, total)  # Claim Amount
                        col += 1
                        worksheet.write(at_row, col, 0.000)  # Exceeding Limit Amount
                        col += 1
                        worksheet.write(at_row, col, comm_disc)  # Discount Amount
                        col += 1
                        worksheet.write(at_row, col, patient_share)  # Deductable Amount
                        col += 1
                        worksheet.write(at_row, col, net)  # Net Amount
                        col += 1
                        worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                        at_row += 1

                    # footer
                    col = 9
                    worksheet.merge_range(at_row, 0, at_row, col, 'TOTAL', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '0', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)

                # SAICO
                if ins_report_format == 'saudi_arabian_ins_co_saico':
                    if len(ic_appointments) == 0 and not self.include_no_records:
                        continue
                    worksheet = workbook.add_worksheet(sheet_name)
                    # title
                    worksheet.merge_range(1, 0, 1, 11, "Med Whie", bi_18_center)
                    worksheet.merge_range(2, 0, 2, 11, "Insurance Claim Report", bi_18_center)
                    worksheet.merge_range(3, 0, 3, 11, ic.name + month_title, bi_18_center)
                    worksheet.set_row(1, 20)
                    worksheet.set_row(2, 20)
                    worksheet.set_row(3, 20)

                    # header
                    header_at = 5

                    # data
                    at_row = 6
                    for cnt in range(0, len(ic_appointments)):
                        invoice = ic_appointments[cnt]
                        appointment = invoice.medical_order_id
                        patient_name = appointment.partner_id.name
                        patient_ar_name = appointment.partner_id.ar_name
                        file_no = appointment.file_no
                        apt_date = get_date_format(invoice.invoice_date)
                        inv_no = invoice.name
                        doctor = appointment.resource_id
                        ins_approval_no = appointment.ins_approval_no
                        ins_ticket_no = appointment.ins_ticket_no
                        ins_ref = appointment.ins_ref

                        worksheet.write(at_row, 0, cnt+1)  # Sr.No

                        for line in _get_app_lines(invoice):
                            total, comm_disc, patient_share, net = _get_totals(line, invoice=invoice)
                            col = 1
                            worksheet.write(at_row, col, patient_name or '')  # Patient Name
                            col += 1
                            worksheet.write(at_row, col, patient_ar_name or '')  # Patient Arabic Name
                            col += 1
                            worksheet.write(at_row, col, ins_approval_no)  # Approval #
                            col += 1
                            worksheet.write(at_row, col, ins_ticket_no)  # Ticket No
                            col += 1
                            worksheet.write(at_row, col, file_no or '')  # File No.
                            col += 1
                            worksheet.write(at_row, col, invoice.ref or '')  # Inv Ref
                            col += 1
                            worksheet.write(at_row, col, apt_date or '')  # Date
                            col += 1
                            worksheet.write(at_row, col, inv_no or '')  # Invoice No.
                            col += 1
                            worksheet.write(at_row, col, total)  # Treatment Amount
                            col += 1
                            worksheet.write(at_row, col, comm_disc)  # After  20% Discount
                            col += 1
                            worksheet.write(at_row, col, patient_share)  # Deductible Amount
                            col += 1
                            worksheet.write(at_row, col, net)  # Net Amount
                            col += 1
                            worksheet.write(at_row, col, doctor.name or '')  # Doctor Name
                            col += 1
                            worksheet.write(at_row, col, invoice.clinic_id.name or '')  # Branch Name
                            at_row += 1

                    # footer
                    col = 8
                    at_row += 1
                    worksheet.merge_range(at_row, 0, at_row, col, 'NET CLAIMED AMOUNT KD:', b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_total, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_comm_disc, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_patient_share, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, x_net, b_14_center)
                    col += 1
                    worksheet.write(at_row, col, '', b_14_center)

                # For Summary
                ins_invoices = ic_appointments.filtered(lambda inv: inv.type == 'out_invoice')
                refund_invoices = ic_appointments.filtered(lambda inv: inv.type == 'out_refund')
                summary_dict[ins_report_format]['lines'].append([
                    ic.name, len(ins_invoices) - len(refund_invoices), x_total, x_comm_disc, x_patient_share, x_net])

                headers_names = columns.get(ins_report_format)
                header_line = []
                for cnt in range(0, len(headers_names)):
                    h_name = headers_names[cnt]
                    # worksheet.write(header_at, cnt, h_name, b_14_center)
                    header_line.append({'name': h_name, 'larg': 0, 'col': {}})

                table = []
                for h in header_line:
                    col = {}
                    col['header'] = h['name']
                    col.update(h['col'])
                    table.append(col)

                # at_row += 1

                if worksheet:
                    t = worksheet.add_table(header_at, 0, at_row-1, len(header_line) - 1, {
                        # 'total_row': 1,
                        'columns': table,
                        'style': 'Table Style Light 9',
                    })

        summary_headers_names = [
            "Sr #", "Insurance Company", "Total Claim's", "Gross Amount",
            "Commercial Discount Applied", "Member Share Paid @ Clinic",
            "Net Amount Claimed"]

        for summary in summary_dict.values():
            if not summary['lines']:
                continue
            title = summary['title']
            worksheet = workbook.add_worksheet("%s Summary Of Claims" % title)
            worksheet.merge_range(0, 0, 0, 6, "Med White", bi_18_center)
            worksheet.merge_range(1, 0, 1, 6, 'Summary of %s Claims' % title, bi_18_center)
            worksheet.merge_range(2, 0, 2, 6, 'Net Claimed Amount For %s for Each Insurance Group' % month_title, bi_18_center)
            worksheet.set_row(0, 20)
            worksheet.set_row(1, 20)
            worksheet.set_row(2, 20)

            totals = [0, 0, 0, 0, 0]
            at_row = 4
            for line in summary['lines']:
                col = 1
                worksheet.write(at_row, 0, at_row-3, b_14_center)
                for val in line:
                    worksheet.write(at_row, col, val)
                    if col > 1:
                        totals[col-2] += val
                    col += 1
                at_row += 1

            at_row += 1
            worksheet.merge_range(at_row, 0, at_row, 1, "TOTAL", b_14_center)
            for c_idx in range(2, 7):
                worksheet.write(at_row, c_idx, totals[c_idx-2], b_14_center)

            header_line = []
            for cnt in range(0, len(summary_headers_names)):
                h_name = summary_headers_names[cnt]
                header_line.append({'name': h_name, 'larg': 0, 'col': {}})

            table = []
            for h in header_line:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)

            worksheet.add_table(3, 0, at_row-1, len(header_line) - 1, {
                'total_row': 1,
                'columns': table,
                'style': 'Table Style Light 9',
            })
        workbook.close()

        file_base = base64.b64encode(fp.getvalue())
        fp.close()
        self.filename = file_base

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/Insurance_Sheet_%s.xls?download=true' % (self._name, self.id, month_title.replace('/', '-')),
            'target': 'new',
            'close_on_report_download': True,
        }
