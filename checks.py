"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

from exceptions import *


def user_with_bot_check(interaction, guild_bot):
    user_vc = interaction.user.voice
    bot_vc_id = guild_bot.vc.channel.id if guild_bot.vc else None

    if user_vc is None:
        raise UserNotInVCError()

    if bot_vc_id is None:
        raise BotNotInVCError()

    if user_vc.channel.id == bot_vc_id:
        return True
    else:
        raise DifferentChannelsError()
