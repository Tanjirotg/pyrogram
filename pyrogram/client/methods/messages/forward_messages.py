# Pyrogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2017-2019 Dan Tès <https://github.com/delivrance>
#
# This file is part of Pyrogram.
#
# Pyrogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pyrogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from typing import Union, Iterable

import pyrogram
from pyrogram.api import functions, types
from ...ext import BaseClient


class ForwardMessages(BaseClient):
    async def forward_messages(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_ids: Union[int, Iterable[int]],
        disable_notification: bool = None,
        as_copy: bool = False,
        remove_caption: bool = False
    ) -> "pyrogram.Messages":
        """Forward messages of any kind.

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            from_chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the source chat where the original message was sent.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_ids (``iterable``):
                A list of Message identifiers in the chat specified in *from_chat_id* or a single message id.
                Iterators and Generators are also accepted.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            as_copy (``bool``, *optional*):
                Pass True to forward messages without the forward header (i.e.: send a copy of the message content).
                Defaults to False.

            remove_caption (``bool``, *optional*):
                If set to True and *as_copy* is enabled as well, media captions are not preserved when copying the
                message. Has no effect if *as_copy* is not enabled.
                Defaults to False.

        Returns:
            :obj:`Message` | :obj:`Messages`: In case *message_ids* was an integer, the single forwarded message is
            returned, otherwise, in case *message_ids* was an iterable, the returned value will be an object containing
            a list of messages, even if such iterable contained just a single element.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        is_iterable = not isinstance(message_ids, int)
        message_ids = list(message_ids) if is_iterable else [message_ids]

        if as_copy:
            forwarded_messages = []

            for chunk in [message_ids[i:i + 200] for i in range(0, len(message_ids), 200)]:
                messages = await self.get_messages(chat_id=from_chat_id, message_ids=chunk)  # type: pyrogram.Messages

                for message in messages.messages:
                    forwarded_messages.append(
                        await message.forward(
                            chat_id,
                            disable_notification=disable_notification,
                            as_copy=True,
                            remove_caption=remove_caption
                        )
                    )

            return pyrogram.Messages(
                client=self,
                total_count=len(forwarded_messages),
                messages=forwarded_messages
            ) if is_iterable else forwarded_messages[0]
        else:
            r = await self.send(
                functions.messages.ForwardMessages(
                    to_peer=await self.resolve_peer(chat_id),
                    from_peer=await self.resolve_peer(from_chat_id),
                    id=message_ids,
                    silent=disable_notification or None,
                    random_id=[self.rnd_id() for _ in message_ids]
                )
            )

            forwarded_messages = []

            users = {i.id: i for i in r.users}
            chats = {i.id: i for i in r.chats}

            for i in r.updates:
                if isinstance(i, (types.UpdateNewMessage, types.UpdateNewChannelMessage)):
                    forwarded_messages.append(
                        await pyrogram.Message._parse(
                        self, i.message,
                        users, chats
                    )
                )

            return pyrogram.Messages(
                client=self,
                total_count=len(forwarded_messages),
                messages=forwarded_messages
            ) if is_iterable else forwarded_messages[0]
