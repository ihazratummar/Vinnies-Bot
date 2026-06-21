from discord.ext import commands

class NotTicketChannel(commands.CheckFailure):
    pass

def in_ticket_channel():
    def predicate(ctx):
        if ctx.guild is None:
            raise NotTicketChannel("This command can only be used in a server.")
        if not ctx.channel.name.startswith("gambling-"):
            raise NotTicketChannel("Gambling commands can only be used in ticket channels (channels starting with 'gambling-').")
        return True
    return commands.check(predicate)
