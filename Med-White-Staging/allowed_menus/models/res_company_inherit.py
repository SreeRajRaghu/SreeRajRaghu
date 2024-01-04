from odoo import fields, models, api, tools


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    user_id = fields.Many2one('res.users')

    @api.model
    @api.returns('self')
    def get_user_roots(self):
        if self.env.user.id == 2:
            return super(IrUiMenu, self).get_user_roots()
        menu = self.env.user.company_ids.mapped('allowed_menu_ids') if not self.env.user.mapped('allowed_menu_ids') \
            else self.env.user.mapped('allowed_menu_ids')
        return menu

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        # retrieve all menus, and determine which ones are visible
        context = {'ir.ui.menu.full_list': True}
        menus = self.with_context(context).search([('id', 'not in', self.env.user.mapped('notallowed_menu_ids').ids)])
        groups = self.env.user.groups_id
        if not debug:
            groups = groups - self.env.ref('base.group_no_one')
        # first discard all menus with groups the user does not have
        menus = menus.filtered(
            lambda menu: not menu.groups_id or menu.groups_id & groups)

        # take apart menus that have an action
        action_menus = menus.filtered(lambda m: m.action and m.action.exists())
        folder_menus = menus - action_menus
        visible = self.browse()

        # process action menus, check whether their action is allowed
        access = self.env['ir.model.access']
        MODEL_GETTER = {
            'ir.actions.act_window': lambda action: action.res_model,
            'ir.actions.report': lambda action: action.model,
            'ir.actions.server': lambda action: action.model_id.model,
        }
        for menu in action_menus:
            get_model = MODEL_GETTER.get(menu.action._name)
            if not get_model or not get_model(menu.action) or \
                    access.check(get_model(menu.action), 'read', False):
                # make menu visible, and its folder ancestors, too
                visible += menu
                menu = menu.parent_id
                while menu and menu in folder_menus and menu not in visible:
                    visible += menu
                    menu = menu.parent_id
        return set(visible.ids)


class IrActionsCustom(models.Model):
    _inherit = 'ir.actions.actions'

    user_id = fields.Many2one('res.users')

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'model_name')
    def get_bindings(self, model_name):
        res = super(IrActionsCustom, self).get_bindings(model_name)
        if res.get('report'):
            restricted_actions = self.env.user.mapped('notallowed_act_ids') if self.env.user.id != 2 else None
            if restricted_actions:
                res['report'] = list(filter(lambda s: s['id'] not in restricted_actions.ids, res['report']))
        return res


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    allowed_menu_ids = fields.Many2many('ir.ui.menu', domain=[('parent_id', '=', False)])


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_menu_ids = fields.Many2many('ir.ui.menu','allowed_menu_ids_profile', 'allowed_menu_ids', domain=[('parent_id', '=', False)])
    notallowed_menu_ids = fields.Many2many('ir.ui.menu', domain=[('parent_id', '!=', False)])
    notallowed_act_ids = fields.Many2many('ir.actions.actions', domain=[('type', '=', 'ir.actions.report')])



