# -*- coding: utf-8 -*-

{
    'name': 'Boutiqaat Reports',
    'version': '13.0',
    'sequence': 1,
    'category': 'Sismatix-HR',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': ['boutiqaat_contract', 'hr_leave_payment'],
    'data': [
        'views/boutiqaat_report_wizard_views.xml',
        'views/salary_certificate_report.xml',
        'views/salary_continous_certificate_report.xml',
        'views/experience_certificate_report.xml',
        'views/end_of_service_3_months_report.xml',
        'views/termination_during_probation_period_report.xml',
        'views/resignation_during_probation_period_report.xml',
        'views/resignation_with_notice_period_report.xml',
        'views/resignation_without_notice_period_report.xml',
        'views/dismissal_order_report.xml',
        'views/dismissal_order_article_41A3_report.xml',
        'views/dismissal_order_article_41B1_report.xml',
        'views/dismissal_order_article_41B2_report.xml',
        'views/all_employee_accural_balance_report.xml',
        
        'views/warning_letter_report.xml',
        'views/subj_suspension_report.xml',
        'views/salary_increment_report.xml',
        'views/payment_request_report.xml',
        'views/leave_encashment_report_view.xml',
        # 'views/employee_encashment_report_view.xml',
        'views/employee_accural_balance_report.xml',
        'wizard/employee_accural_balance_wizard_view.xml',
    ],
}
