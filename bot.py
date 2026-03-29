import re
from urllib.parse import quote, unquote

import discord

TOKEN = os.environ.get('DISCORD_TOKEN', '')
KANAL_ID = 1487580690987090063

def parse_link(raw):
    raw = raw.strip()

    agent_param = re.search(r'[?&]url=([^&\s]+)', raw)
    if agent_param:
        raw = unquote(agent_param.group(1))

    m = re.search(r'shop(\d+)\.v\.weidian\.com/item\.html\?.*?itemID=(\d+)', raw, re.I)
    if m:
        return {'platform': 'weidian', 'item_id': m.group(2), 'shop_id': m.group(1)}

    m = re.search(r'weidian\.com/item\.html\?.*?itemID=(\d+)', raw, re.I)
    if m:
        return {'platform': 'weidian', 'item_id': m.group(1)}

    m = re.search(r'(?:item\.)?taobao\.com/item\.htm\?.*?id=(\d+)', raw, re.I)
    if m:
        return {'platform': 'taobao', 'item_id': m.group(1)}

    m = re.search(r'detail\.1688\.com/offer/(\d+)\.html', raw, re.I)
    if m:
        return {'platform': '1688', 'item_id': m.group(1)}

    m = re.search(r'1688\.com/offer/(\d+)', raw, re.I)
    if m:
        return {'platform': '1688', 'item_id': m.group(1)}

    # ACBuy
    m = re.search(r'acbuy\.com/product\?id=(\d+)&source=(WD|TB|ALI)', raw, re.I)
    if m:
        platform_map = {'WD': 'weidian', 'TB': 'taobao', 'ALI': '1688'}
        return {'platform': platform_map[m.group(2).upper()], 'item_id': m.group(1)}

    # USFans: /product/3/{id} lub /product/2/{id}
    m = re.search(r'usfans\.com/product/(\d+)/(\d+)', raw, re.I)
    if m:
        plat_map = {'1': 'taobao', '2': 'taobao', '3': 'weidian', '4': '1688'}
        return {'platform': plat_map.get(m.group(1), 'weidian'), 'item_id': m.group(2), 'usfans_type': m.group(1)}

    # LitBuy: /products/details?id={id}&channel=WEIDIAN|TAOBAO
    m = re.search(r'litbuy\.com/products/details\?id=(\d+)&channel=(WEIDIAN|TAOBAO|ALI)', raw, re.I)
    if m:
        plat_map = {'WEIDIAN': 'weidian', 'TAOBAO': 'taobao', 'ALI': '1688'}
        return {'platform': plat_map.get(m.group(2).upper(), 'weidian'), 'item_id': m.group(1)}

    return None

def build_direct(p):
    if p['platform'] == 'weidian':
        if p.get('shop_id'):
            return f"https://shop{p['shop_id']}.v.weidian.com/item.html?itemID={p['item_id']}"
        return f"https://weidian.com/item.html?itemID={p['item_id']}"
    if p['platform'] == 'taobao':
        return f"https://item.taobao.com/item.htm?id={p['item_id']}"
    if p['platform'] == '1688':
        return f"https://detail.1688.com/offer/{p['item_id']}.html"
    return None

def enc(p):
    return quote(build_direct(p), safe='')

def build_kakobuy(p):
    return f"https://www.kakobuy.com/item/details?url={enc(p)}&affcode=supreme"

def build_acbuy(p):
    src = {'weidian': 'WD', 'taobao': 'TB', '1688': 'ALI'}.get(p['platform'], 'WD')
    return f"https://www.acbuy.com/product?id={p['item_id']}&source={src}&u=KL5R26"

def build_usfans(p):
    type_map = {'weidian': '3', 'taobao': '2', '1688': '4'}
    t = type_map.get(p['platform'], '3')
    return f"https://www.usfans.com/product/{t}/{p['item_id']}?ref=RFGVYE"

def build_litbuy(p):
    channel_map = {'weidian': 'WEIDIAN', 'taobao': 'TAOBAO', '1688': 'ALI'}
    channel = channel_map.get(p['platform'], 'WEIDIAN')
    return f"https://litbuy.com/products/details?id={p['item_id']}&channel={channel}&inviteCode=6EZJ7TR67"

AGENTS = [
    {'label': 'KakoBuy', 'emoji': '🛒', 'build': build_kakobuy},
    {'label': 'ACBuy',   'emoji': '🟦', 'build': build_acbuy},
    {'label': 'USFans',  'emoji': '🇺🇸', 'build': build_usfans},
    {'label': 'LitBuy',  'emoji': '💡', 'build': build_litbuy},
]

PLATFORM_CONFIG = {
    'weidian': {'name': 'Weidian', 'color': discord.Color.from_rgb(0, 180, 216),  'emoji': '🏪'},
    'taobao':  {'name': 'Taobao',  'color': discord.Color.from_rgb(255, 107, 0),  'emoji': '🛒'},
    '1688':    {'name': '1688',    'color': discord.Color.from_rgb(204, 68, 255), 'emoji': '🏭'},
}

URL_REGEX = re.compile(r'https?://[^\s<>]+')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Zalogowano jako {client.user}')
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name='linki rep | weidian/taobao/1688'
    ))

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != KANAL_ID:
        return

    urls = URL_REGEX.findall(message.content)
    if not urls:
        return

    for url in urls:
        parsed = parse_link(url)
        if not parsed:
            continue

        cfg = PLATFORM_CONFIG.get(parsed['platform'], {
            'name': parsed['platform'],
            'color': discord.Color.blurple(),
            'emoji': '🔗'
        })

        embed = discord.Embed(
            title=f"{cfg['emoji']} Przekonwertowany link",
            description=f"**Platforma:** {cfg['name']}\n**Item ID:** `{parsed['item_id']}`",
            color=cfg['color']
        )
        embed.set_footer(text='Rep Link Converter')

        view = discord.ui.View()
        for agent in AGENTS:
            try:
                agent_url = agent['build'](parsed)
                view.add_item(discord.ui.Button(
                    label=f"{agent['emoji']} {agent['label']}",
                    url=agent_url,
                    style=discord.ButtonStyle.link
                ))
            except Exception:
                pass

        await message.reply(embed=embed, view=view)
        break

client.run(TOKEN)
