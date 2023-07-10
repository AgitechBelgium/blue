# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    chatgpt_api_key = fields.Char(string="ChatGPT API Key", config_parameter="chatgpt_bot.chatgpt_api_key")


