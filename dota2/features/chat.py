from dota2.enums import EDOTAGCMsg, DOTAChatChannelType_t


class Chat(object):
    EVENT_CHAT_JOINED = 'chat_joined'
    """Joined chat channel
    :param message: `CMsgDOTAJoinChatChannelResponse <https://github.com/ValvePython/dota2/blob/ca75440adca20d852b9aec3917e4387466848d5b/protobufs/dota_gcmessages_client_chat.proto#L129>`_
    :type  message: proto message
    """
    EVENT_CHAT_MESSAGE = 'chat_message'
    """Received message from chat channel
    :param message: `CMsgDOTAChatMessage <https://github.com/ValvePython/dota2/blob/ca75440adca20d852b9aec3917e4387466848d5b/protobufs/dota_gcmessages_client_chat.proto#L86>`_
    :type  message: proto message
    """

    chat_channels = []

    def __init__(self):
        super(Chat, self).__init__()

        self.on(EDOTAGCMsg.EMsgGCJoinChatChannelResponse, self.__handle_chat_joined)
        self.on(EDOTAGCMsg.EMsgGCChatMessage, self.__handle_chat_message)

    def __handle_chat_joined(self, message):
        if self.verbose_debug:
            self._LOG.debug("Joined chat channel %s" % message.channel_name)

        self.chat_channels.append(message)
        self.emit(self.EVENT_CHAT_JOINED, message)

    def __handle_chat_message(self, message):
        channel = self.__get_channel_by_id(message.channel_id)

        if self.verbose_debug:
            self._LOG.debug("Received chat message from %s in channel %s" %
                            (message.persona_name, channel.channel_name))

        self.emit(self.EVENT_CHAT_MESSAGE,
                  channel.channel_name,
                  message.persona_name,
                  message.text,
                  message)

    def join_chat(self, channel_name, channel_type=DOTAChatChannelType_t.DOTAChannelType_Custom):
        """
        Sends a message to the Game Coordinator requesting to join a chat channel.

        :param channel_name: name of chat channel to join
        :type  channel_name: :class:`str`
        :param channel_type: type of chat channel (regional, lobby, etc)
        :type  channel_type: :class:`DOTAChannelType_Custom`
        """
        if self.verbose_debug:
            self._LOG.debug("Joining chat %s (type: %s)" % (channel_name, channel_type))

        command = {
            "channel_name": channel_name,
            "channel_type": channel_type,
        }
        self.send(EDOTAGCMsg.EMsgGCJoinChatChannel, command)

    def send_message(self, channel_name, channel_type, message):
        """
        Sends a message to the chat channel.

        :param channel_name: name of chat channel to send message to
        :type  channel_name: :class:`str`
        :param channel_type: type of chat channel (regional, lobby, etc)
        :type  channel_type: :class:`DOTAChannelType_Custom`
        :param message: text of the message to send to chat
        :type  message: :class:`str`
        """
        if self.verbose_debug:
            self._LOG.debug("Sending chat message to %s. Message: %s" %
                            (channel_name, message))

        channel = self.__get_channel_by_name(channel_name, channel_type)
        if not channel:
            if self.verbose_debug:
                self._LOG.debug("Cannot send message to a channel you have not joined.")
            return

        command = {
            "channel_id": channel.channel_id,
            "text": message,
        }
        self.send(EDOTAGCMsg.EMsgGCChatMessage, command)

    #
    # Shortcuts for working with lobby chats
    #

    def join_lobby_chat(self):
        """
        Shortcut function for joining lobby chats

        :param lobby_id: id of lobby to which chat we want to send message
        :type  lobby_id: :class:`str`
        """
        if not self.lobby:
            if self.verbose_debug:
                self._LOG.debug("Can't join lobby chat if you aren't in the lobby")
                return

        self.join_chat("Lobby_%s" % self.lobby.lobby_id,
                       DOTAChatChannelType_t.DOTAChannelType_Lobby)

    def send_lobby_message(self, message):
        """
        Shortcut function for sending messages to lobby chat

        :param lobby_id: id of lobby which chat we want to join
        :type  lobby_id: :class:`str`
        :param message: text of the message to send to lobby chat
        :type  message: :class:`str`
        """
        if not self.lobby:
            if self.verbose_debug:
                self._LOG.debug("Can't send message to lobby chat if you aren't in the lobby")
                return

        self.send_message("Lobby_%s" % self.lobby.lobby_id,
                          DOTAChatChannelType_t.DOTAChannelType_Lobby,
                          message)

    #
    # Helper functions to work with channel name/id
    #

    def __get_channel_by_name(self, channel_name, channel_type):
        channels = [c for c in self.chat_channels
                    if c.channel_name == channel_name and
                       (c.channel_type == channel_type or channel_type is None)]

        return channels[0] if channels else None

    def __get_channel_by_id(self, channel_id):
        channels = [c for c in self.chat_channels if c.channel_id == channel_id]

        return channels[0] if channels else None
