{
    "name": "Dashboard",
    "version": "1.0",
    "author": 'Sismatix',
    'website': 'http://sistimax.com',
    "depends": ['web','hr','analytic'],
    "category": "Management",
    "data": [
        "security/dashboard_security.xml",
        "security/ir.model.access.csv",
        "data/dashboard_data.xml",
        "wizard/filter_dates.xml",
        "views/dashboard_view.xml",
        "views/res_config_view.xml",
        "views/assets.xml",
    ],
    'installable': True,
    'images': ['static/description/logo.png'],
}
