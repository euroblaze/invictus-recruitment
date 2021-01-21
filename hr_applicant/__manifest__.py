{
    'name': 'HR Applicant',
    'version': '0.0.1',
    'category': 'Extra Tools',
    'summary': 'Custom Module',
    'sequence': '10',
    'license': 'GPL-3',
    'author': 'Sinisha',
    'maintainer': 'Sinisha',
    'website': 'test.com',
    'depends': ['base', 'website_partner', 'hr_recruitment', 'website_mail', 'website_form', 'website_calendar',
                'applicant_tracking_system', 'mail', 'crm', 'sale', 'website_profile', 'website_hr_recruitment', 'portal',],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/profiles.xml',
        'views/customer_order_view.xml',
        'views/profile_detail.xml',
        'views/mail.xml',
        'views/portal.xml',
        'views/hr_applicant.xml',
        'views/website_calendar.xml',
        'views/requested_cron.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
