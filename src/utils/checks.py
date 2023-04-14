"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""
import discord

from .exceptions import *


def user_with_bot_check(interaction, guild_bot):
    user_vc = interaction.user.voice
    bot_vc_id = guild_bot.voice_client.channel.id if guild_bot.voice_client else None

    if user_vc is None:
        raise UserNotInVCError()

    if bot_vc_id is None:
        raise BotNotInVCError()

    if user_vc.channel.id == bot_vc_id:
        return True
    else:
        raise DifferentChannelsError()


class PermissionsCheck:
    db = None

    @staticmethod
    def get_member(interaction):
        user = interaction.user
        guild = interaction.guild
        member = guild.get_member(user.id)
        return member

    @classmethod
    def member_is_admin(cls, member):
        for role in member.roles:
            for permission in role.permissions:
                if permission[0] == 'moderate_members' and permission[1]:
                    return True
        return False

    @classmethod
    def interaction_is_admin(cls, interaction: discord.Interaction) -> bool:
        return interaction.permissions.administrator

    @classmethod
    def member_is_dj(cls, member):
        for role in member.roles:
            if role.name == 'dj':
                return True
        return False

    @classmethod
    def member_has_permissions(cls, member):
        return cls.member_is_admin(member) or cls.member_is_dj(member)

    @classmethod
    def interaction_has_permissions(cls, interaction: discord.Interaction):
        member = cls.get_member(interaction)
        return cls.member_is_dj(member) or cls.interaction_is_admin(interaction)
