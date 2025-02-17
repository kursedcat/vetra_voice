import disnake
from disnake.ext import commands, tasks
import random
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ALLOWED_ROLES = list(map(int, os.getenv("ALLOWED_ROLES").split(",")))  # Список ID ролей
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))  # ID лог-канала
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))

intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

love_statuses = [
    "💞 Любовь витает в воздухе!",
    "💖 Кто-то нашёл свою вторую половинку!",
    "💘 Лаврумы объединяют сердца!",
    "💓 Вместе навсегда!",
    "💗 Романтика на высоте!",
]

@tasks.loop(minutes=2)
async def change_status():
    """ Меняет статус бота каждые 2 минуты. """
    await bot.change_presence(activity=disnake.Game(random.choice(love_statuses)))


@bot.slash_command(description="Создать лавруму")
async def new_loveroom(
    inter: disnake.ApplicationCommandInteraction,
    user1: disnake.Member,
    user2: disnake.Member,
    category: disnake.CategoryChannel
):
    """ Создаёт лавруму с голосовым каналом. """
    
    # Проверяем, есть ли у пользователя разрешённая роль
    if not any(role.id in ALLOWED_ROLES for role in inter.author.roles):
        return await inter.response.send_message("❌ У вас нет доступа к этой команде!", ephemeral=True)

    heart_emojis = ["💞", "💖", "💘", "💓", "💗"]
    heart_emoji = random.choice(heart_emojis)

    room_name = f"{heart_emoji} · {user1.display_name} · {user2.display_name}"
    
    # Создаём голосовой канал в указанной категории
    voice_channel = await category.create_voice_channel(
        name=room_name,
        overwrites={
            inter.guild.default_role: disnake.PermissionOverwrite(connect=False),  # Запрещаем вход всем
            user1: disnake.PermissionOverwrite(connect=True),  # Даем доступ user1
            user2: disnake.PermissionOverwrite(connect=True),  # Даем доступ user2
            bot.user: disnake.PermissionOverwrite(connect=True, manage_channels=True)  # Даем доступ боту
        }
    )

    embed = disnake.Embed(
        title="💞 Лаврума создана!",
        description=f"Голосовой канал: {voice_channel.mention}\n"
                    f"👤 **Пара**: {user1.mention} + {user2.mention}\n"
                    f"🔒 Доступен только для вас двоих!",
        color=disnake.Color.from_rgb(255, 105, 180)  # Розовый цвет
    )
    embed.set_footer(text="Наслаждайтесь временем вместе! ❤️")

    await inter.response.send_message(embed=embed)

@bot.slash_command(description="Удалить лавруму (доступно только для указанных ролей)")
async def delete_loveroom(inter: disnake.ApplicationCommandInteraction, channel: disnake.VoiceChannel):
    """ Удаляет лавруму (голосовой канал) и отправляет лог в лог-канал. """

    # Проверяем, есть ли у пользователя разрешённая роль
    if not any(role.id in ALLOWED_ROLES for role in inter.author.roles):
        return await inter.response.send_message("❌ У вас нет доступа к этой команде!", ephemeral=True)

    channel_name = channel.name
    await channel.delete()

    embed = disnake.Embed(
        title="💔 Лаврума удалена!",
        description=f"Голосовой канал `{channel_name}` был удалён!",
        color=disnake.Color.red()
    )
    await inter.response.send_message(embed=embed)

    # Отправляем лог в лог-канал
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = disnake.Embed(
            title="📜 Лог удаления лаврумы",
            description=f"🔻 **Удалён канал**: `{channel_name}`\n"
                        f"👤 **Удалил**: {inter.author.mention}",
            color=disnake.Color.red()
        )
        await log_channel.send(embed=log_embed)

async def connect_to_voice():
    """ Подключает бота в голосовой канал. """
    await bot.wait_until_ready()
    guild = bot.guilds[0]  # Берём первый сервер, где бот есть
    voice_channel = guild.get_channel(VOICE_CHANNEL_ID)

    if voice_channel:
        if not bot.voice_clients:  # Если бот ещё не в голосовом канале
            await voice_channel.connect()
            print(f"Бот подключился к {voice_channel.name}")

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    change_status.start()
    await connect_to_voice()  # Подключаем бота в голосовой

@bot.event
async def on_voice_state_update(member, before, after):
    """ Если бот вылетел из войса — подключаем его обратно. """
    if member == bot.user and before.channel and not after.channel:
        await connect_to_voice()


bot.run(TOKEN)
