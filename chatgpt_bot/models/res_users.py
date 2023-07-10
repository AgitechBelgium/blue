# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _


class Users(models.Model):
    _inherit = 'res.users'

    initialized = fields.Boolean()

    def _init_messaging(self):
        if not self.initialized and self._is_internal():
            self._init_chatgpt_bot()
        return super()._init_messaging()

    def _init_chatgpt_bot(self):
        self.ensure_one()
        chatgpt_bot_id = self.env['ir.model.data']._xmlid_to_res_id("chatgpt_bot.partner_chatgpt_bot")
        channel_info = self.env['mail.channel'].channel_get([chatgpt_bot_id, self.partner_id.id])
        channel = self.env['mail.channel'].browse(channel_info['id'])

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        settings_action = self.env.ref('base_setup.action_general_configuration').read()[0]
        setting_url = base_url + f'/web#action={settings_action.get("id")}&model=res.config.settings&view_type=form&cids=1&menu_id={self.env.ref("base.menu_administration").id}#chatgpt'
        message = _("Hello,<br/>Welcome to the ChatGPT Bot channel. "
                    "This channel is accessible to all users to communicate with Chatgpt.<br/><br/>"
                    f"Please setup your key <a target='_blank' href='{setting_url}'>here</a> in order to enable this conversation.")
        channel.sudo().message_post(body=message, author_id=chatgpt_bot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
        self.sudo().initialized = True
        return channel
