# -*- coding: utf-8 -*-

{
    'name': 'Boutiqaat HR Payslip',
    'version': '13.0.2',
    'category': 'Sismatix-HR',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': [
        'hr_contract',
        'payslip_emp_inputs',
        'boutiqaat_hr_base',
        'boutiqaat_contract',
        'hr_attendance_time',
        'ohrms_loan',
        'hr_employee_eos',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'data/boutiqaat_hr_payslip_india_data.xml',
        'data/boutiqaat_hr_payslip_kuwait_data.xml',
        'data/boutiqaat_hr_payslip_uae_data.xml',
        'data/kuwait_hourly_data.xml',
        'data/kuwait_daily_data.xml',
        'data/other_rules.xml',
        'views/payslip_report.xml',
        'views/report_payslip.xml',
        'views/payslip_views.xml',
        'views/structure_type_views.xml',
        'wizard/wizard_payslip_report_views.xml',
        'wizard/emp_salary_views.xml',
    ],
    'post_init_hook': '_update_basic_wage_rule',
}
