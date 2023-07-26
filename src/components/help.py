import discord
from settings import COMMANDS, COMMAND_NAMES
from random import choice


class Help:
    default_color_rgb = (194, 149, 76)
    default_color = discord.Color.from_rgb(*default_color_rgb)

    responses = [
        'We\'ve done our photosynthesis, have you?',
        'I tried to make a pencil with an eraser on both ends, but all I got was a really long Q-tip.',
        'My cat thinks she\'s the CEO of the house, demanding treats and belly rubs like a true business moggy.',
        'I asked my dog for relationship advice, and all he did was wag his tail and bark. I think he\'s trying to tell me something in Morse code.',
        'I accidentally wore my slippers to work today, and my boss said, \'You\'re really stepping up your casual Friday game.\'',
        'I told my computer a joke, but it just replied with \'ERROR 404: Humor not found.\'',
        'I tried to become a baker, but all my bread came out so flat, I could use it as a doormat for ants.',
        'I tried to impress my crush by juggling watermelons, but the only thing I caught was a trip to the emergency room.',
        'My brain has too many tabs open, and I can\'t find the one labeled \'Keys.\'',
        'My grandma joined Instagram and thought DM meant \'Delicious Muffins\' – she\'s been messaging celebrities her secret muffin recipes.',
        'I accidentally used hand sanitizer as hair gel, and now my hair is so spiky that I\'m auditioning for a punk rock band.',
        'My refrigerator and microwave are in a feud, but all I hear are cold microwave meals and heated arguments.',
        'I taught my pet parrot to speak binary, and now he won\'t stop saying \'01001000 01000101 01001100 01010000\' – I think he\'s trying to ask for help.',
        'I tried to make lemonade, but I accidentally squeezed the lemons so hard they filed for workers\' compensation.',
        'I told my GPS I was feeling lost, and it replied, \'You think you\'re lost? You should see how confused I get on roundabouts!\'',
        'I wore my shirt inside out all day, and when someone pointed it out, I told them I was just \'testing their attention to detail.\'',
        'Yes, these were written by ChatGPT... Except for the photosynthesis one.',
    ]

    button_commands = [
        ('⎇', 'Shuffle or unshuffle queue.'),
        ('◁', 'Go back one song.'),
        ('▉', 'Pause or unpause playing.'),
        ('▷', 'Skip currently playing song.'),
        ('⭯', 'Toggle between looping queue, looping a single song and not looping.'),
        ('✖', 'Clear the queue and stop playing.'),
        ('#', 'Disconnect Shteff from the voice channel.'),
        ('≡', 'Toggle song lyrics.'),
        ('+', 'Add the song to a personal playlist.'),
        ('S+', 'Add the song to a server playlist.')
    ]

    github_link = 'https://github.com/Mjolnir2425/Shteff'
    description = f'Shteff is a free and open source music bot. Source code is available at {github_link}, and is still in early-ish development.'

    @classmethod
    def get_buttons_content(cls):
        content = ''
        for name, description in cls.button_commands:
            content += f'`{name}` - {description}\n'
        return content

    @classmethod
    async def no_command(cls, interaction):
        embed = discord.Embed(
            title='Welcome to Shteff',
            description='This is the fucking manual. Read it. Please.\nTo get info about a specific command use `/help <command-name>`',
            color=cls.default_color
        )

        for command_type in COMMANDS.keys():
            embed.add_field(
                name=command_type,
                value=''.join(f'`{command_name}` ' for command_name in COMMANDS[command_type].keys()),
                inline=False
            )

        embed.add_field(
            name='About us',
            value=cls.description,
            inline=False
        )

        embed.set_footer(text=choice(cls.responses))

        await interaction.response.send_message(content='', embed=embed, ephemeral=True)

    @classmethod
    async def with_command(cls, interaction, command):
        command_info = {}
        for command_type in COMMANDS.keys():
            try:
                command_info = COMMANDS[command_type][command]
            except KeyError:
                continue

            embed = discord.Embed(
                title=f'`{command}`',
                description=command_info.get('short_description', 'An error occurred, cannot find command.'),
                color=cls.default_color
            )

            try:
                long_description = command_info['long_description']
            except KeyError:
                pass
            else:
                embed.add_field(
                    name='Details',
                    value=long_description,
                    inline=False
                )

            try:
                known_issues = command_info['known_issues']
            except KeyError:
                pass
            else:
                embed.add_field(
                    name='Known issues',
                    value=known_issues,
                    inline=False
                )

            embed.set_footer(text=choice(cls.responses))

            await interaction.response.send_message(content='', embed=embed, ephemeral=True)

    @classmethod
    async def missing_command(cls, interaction, command):
        embed = discord.Embed(
            title='Missing command',
            description=f'`{command}` doesn\'t seem to be a registered Shteff command. Use `/help` to see all commands.',
            color=cls.default_color
        )

        embed.set_footer(text=choice(cls.responses))

        await interaction.response.send_message(content='', embed=embed, ephemeral=True)

    @classmethod
    async def start_help_flow(cls, interaction: discord.Interaction, command: str):
        if command is None:
            await cls.no_command(interaction)
        elif command == 'buttons' or command in COMMAND_NAMES:
            await cls.with_command(interaction, command)
        else:
            await cls.missing_command(interaction, command)
