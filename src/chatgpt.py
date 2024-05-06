import openai
from discord.ext import commands
from discord.commands import slash_command, option, OptionChoice
from discord import ApplicationContext, Embed, Colour

from config.auth import GUILD_IDS, OPENAI_API_KEY


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        openai.api_key = OPENAI_API_KEY

    @slash_command(
        name="chat", description="Post query to ChatGPT", guild_ids=GUILD_IDS
    )
    @option("query", description="Prompt", required=True)
    @option(
        "model",
        description="Choose a GPT model",
        required=False,
        choices=[
            OptionChoice(name="GPT-3.5 Turbo", value="gpt-3.5-turbo-0125"),
            OptionChoice(name="GPT-3.5 Turbo 16k", value="gpt-3.5-turbo-16k"),
            OptionChoice(name="GPT-4", value="gpt-4"),
            OptionChoice(name="GPT-4 Turbo", value="gpt-4-turbo"),
        ],
    )
    async def chat(
        self, ctx: ApplicationContext, query: str, model: str = "gpt-4-turbo"
    ):
        await ctx.defer()  # Acknowledge the interaction immediately - reply can take some time
        try:
            response = openai.chat.completions.create(
                model=model, messages=[{"role": "user", "content": query}]
            )
            response_text = (
                response.choices[0].message.content
                if response.choices
                else "No response."
            )
            await ctx.followup.send(
                embed=Embed(
                    title="ChatGPT Response",
                    description=response_text,
                    color=Colour.blue(),
                )
            )
        except Exception as e:
            await ctx.followup.send(
                embed=Embed(title="Error", description=str(e), color=Colour.red())
            )
