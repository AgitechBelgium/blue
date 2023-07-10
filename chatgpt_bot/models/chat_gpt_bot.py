# -*- coding: utf-8 -*-

import itertools
import random
import openai
from odoo.exceptions import UserError
from odoo import models, _


class ChatGPTBot(models.AbstractModel):
    _name = 'chat.gpt.bot'
    _description = 'Chat GPT Bot'

    def _call_chatgpt_api(self, record, values):
        """ Generate an answer for the user
        The logic will only be applied if ChatGPT Bot is in a chat with a loggedIn user.

         :param record: communication mail_channel where the current user and ChatGPT bot communication is present.
         :param values: pass the parameter form mail_thread for generate the answer
        """
        chatgptbot_id = self.env['ir.model.data']._xmlid_to_res_id("chatgpt_bot.partner_chatgpt_bot")
        if len(record) != 1 or values.get("author_id") == chatgptbot_id or values.get("message_type") != "comment":
            return
        if self._is_chatgpt_bot_pinged(values) or self._is_chatgpt_bot_in_private_channel(record):
            body = values.get("body", "").replace(u'\xa0', u' ').strip().lower().strip(".!")
            answer = self._get_answer_from_api(body)
            if answer:
                message_type = 'comment'
                subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
                record.with_context(mail_create_nosubscribe=True).sudo().message_post(body=answer, author_id=chatgptbot_id, message_type=message_type, subtype_id=subtype_id)

    def _get_answer_from_api(self, body):
        """
        In this method check the api_key and generate the response based on given body
        Get the body from parameter, and it will pass to the openai api (chatgpt) and get the response from api and return text part of that response to the mail_channel.
        """
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('chatgpt_bot.chatgpt_api_key')
        messages = [{
            "role" : "system",
            "content": body
        }]
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0,
                max_tokens=3000,
            )
            res = response['choices'][0]['text']
            return res
        except Exception as e:
            raise UserError(_(e))


    def _is_chatgpt_bot_pinged(self, values):
        chatgptbot_id = self.env['ir.model.data']._xmlid_to_res_id("chatgpt_bot.partner_chatgpt_bot")
        return chatgptbot_id in values.get('partner_ids', [])

    def _is_chatgpt_bot_in_private_channel(self, record):
        chatgptbot_id = self.env['ir.model.data']._xmlid_to_res_id("chatgpt_bot.partner_chatgpt_bot")
        if record._name == 'mail.channel' and record.channel_type == 'chat':
            return chatgptbot_id in record.with_context(active_test=False).channel_partner_ids.ids
        return False
