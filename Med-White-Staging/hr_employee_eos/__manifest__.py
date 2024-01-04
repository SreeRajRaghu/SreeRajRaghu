# coding: utf-8
{
    "name": "Employee End Of Service",
    "version": "13.0.2",
    "author": "Sismatix",
    "category": "hr",
    "website": "http://sismatix.com",
    "depends": [
        'hr_payroll',
        'hr_default',
        'hr_holidays',
    ],
    "data": [
        "security/ir.model.access.csv",
        'data/hr_data.xml',
        "data/data.xml",
        "data/cron.xml",
        "views/hr_views.xml",
        "views/res_config_views.xml",
        "views/report_eos.xml",
    ],
}
