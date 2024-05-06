'''
Notes
---------------
May need to use this command to install pycord
python -m pip install --upgrade --no-deps --force-reinstall git+https://github.com/Pycord-Development/pycord
'''

from discord import Bot
from chatgpt import ChatGPT
from config.auth import BOT_TOKEN


if __name__ == '__main__':
    bot = Bot()
    bot.add_cog(ChatGPT(bot=bot))
    bot.run(BOT_TOKEN)