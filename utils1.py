import re
import discord
import fn_api
import random

from functools import lru_cache
from discord import Embed
from database import get_creator_id

creative = '<:cr:1265623417269387266>'
uefn = '<:ue:1265623460575445025>'
ccu = '<:xx:1265623949442678857>'
lego = '<:lg:1265623343563014195>'
roket = '<:rr:1265623289460555827>'
fallguys = '<:bean:1265623237346201622>'

colour = random.randint(0x2b2d31, 0x2b2d31) #0x2c2f33
colour2 = random.randint(0xc47501, 0xc47501)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def clean_filename(filename):
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w\.-]', '', filename)
    filename = re.sub(r'[\U00010000-\U0010ffff]', '', filename)
    return filename

def remove_newline(string):
    return string.replace("\n", "")

def format_number_with_commas(number):
    if number >= 1000:
        formatted_number = "{:,.0f}".format(number)
    else:
        formatted_number = str(number)
    return formatted_number

async def create_user_channel(guild, user, colour):
    category = discord.utils.get(guild.categories, name="Private Channels")
    if not category:
        category = await guild.create_category("Private Channels")
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),user: discord.PermissionOverwrite(read_messages=True)}
    channel = await guild.create_text_channel(user.name, category=category, overwrites=overwrites)
    await channel.set_permissions(guild.default_role, read_messages=False)
    role = discord.utils.get(guild.roles, name='Private Channel')
    await user.add_roles(role)
    await channel.send(embed=Embed(description=f"**{user.mention}, your private channel has been created!**",color=colour))
    return channel

async def create_user_channel2(guild, user, colour):
    category = discord.utils.get(guild.categories, name="Private Channels 2")
    if not category:
        category = await guild.create_category("Private Channels 2")
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),user: discord.PermissionOverwrite(read_messages=True)}
    channel = await guild.create_text_channel(user.name, category=category, overwrites=overwrites)
    await channel.set_permissions(guild.default_role, read_messages=False)
    role = discord.utils.get(guild.roles, name='Private Channel')
    await user.add_roles(role)
    await channel.send(embed=Embed(description=f"**{user.mention}, your private channel has been created!**",color=colour))
    return channel

# Helper methods to split up the processing
def _get_image(metadata):
    image = metadata.get('image_url')
    if not image:
        image_urls = metadata.get('image_urls')
        if isinstance(image_urls, dict):
            image = image_urls.get('url')
        elif isinstance(image_urls, list):
            for item in image_urls:
                if url := item.get('url'):
                    image = url
                    break
    return image

# Cache for creator data
@staticmethod
@lru_cache(maxsize=1000)
def get_cached_creator_data(creator_code: str):
    return fn_api.slug(code=creator_code)

# Cache for creator maps
@staticmethod
@lru_cache(maxsize=1000)
def get_cached_creator_maps(creator_id: str):
    return fn_api.creatormaps(creator=creator_id)

async def _get_creator_data(creator_code: str):
    """Get cached creator data asynchronously"""
    try:
        data = get_cached_creator_data(creator_code)
        json_value, status_code = data
        return json_value if status_code == 200 else None
    except Exception:
        return None

async def _get_creator_maps(creator_code: str):
    """Get cached creator maps asynchronously"""
    try:
        data = await _get_creator_data(creator_code)
        if not data:
            return None
        maps = get_cached_creator_maps(data['id'])
        return maps.json() if maps.status_code == 200 else None
    except Exception:
        return None

async def _get_islands_batch(batch):
    """Get island data for a batch of codes"""
    try:
        return fn_api.island_more(island=batch)
    except Exception:
        return []

def _get_xp_status(metadata):
    """Optimized XP status check"""
    if xp_data := metadata.get('dynamicXp', {}):
        if xp_phase := xp_data.get('calibrationPhase'):
            return {
                'LiveXp': "<:xp:1068731097506127902>",
                'DataGathering': "<:xp2:1068732482381430784>"
            }.get(xp_phase, "<:xp2:1068732482381430784>")
    return "<:xp2:1068732482381430784>"

async def _get_ratings(metadata):
    if ratings := metadata.get('ratings', {}).get('boards'):
        rating_list = [
            f'**{rating_info["rating"]}**'
            for rating_info in ratings.values()
            if rating_info.get('rating')
        ]
        return ', '.join(rating_list) if rating_list else '**None**'
    return '**None**'

def _build_base_description(car, metadata, xp):
    # Get last update date safely
    last_update = car.get('lastActivatedDate', car.get('created', 'Unknown')).split('T')[0]
    
    # Get creation date safely
    creation_date = (
        car.get('published') or 
        car.get('created') or 
        'Unknown'
    ).split('T')[0]

    return [
        metadata.get('tagline', ' '),
        '',
        f'`Creator:` **{car.get("creatorName") or metadata.get("supportCode")}**',
        f'`Creator ID:` **{car["accountId"]}**',
        f'`Island Code:` **{car["mnemonic"]}**',
        f'`XP Status:` **{xp}**',
        f'`Discovery Status:` **{":white_check_mark:" if car["moderationStatus"] == "Approved" else ":x:" if car["moderationStatus"] == "Denied" else car["moderationStatus"]}**',
        f'`Listed on Profile:` **{car.get("discoveryIntent") == "PUBLIC"}**',
        f'`Version:` **{car["version"]}**',
        f'`Last Update:` **{last_update}**',
        f'`Creation:` **{creation_date}**'
    ]

def _add_uefn_fields(base_desc, car, metadata):
    base_desc.extend([
        f'`Mode:` **{metadata["mode"]}**',
        f'`Project ID:` **{metadata["projectId"]}**',
        f'`Island Type:` **UEFN** {uefn}'
    ])
    
    if category := car.get('linkCategory'):
        if emoji := {
            'FALL GUYS': fallguys,
            'LEGO': lego,
            'Rocket Racing': roket
        }.get(category):
            base_desc.append(f'`Island Category:` **{category}** {emoji}')
    
    if lobby_img := metadata.get('lobby_background_image_urls', {}).get('url'):
        base_desc.append(f'`Lobby IMG:` **[link]({lobby_img})**')
    
    if video_uuid := metadata.get('video_vuid'):
        base_desc.append(f'`Video ID:` **{video_uuid}**')

def _add_fnc_fields(base_desc, metadata, car):
    base_desc.extend([
        f'`Island Type:` **{metadata.get("islandType", "None").replace("CreativePlot:", "")}** {creative}',
        f'`Active:` **{car["active"]}**',
        f'`Island:` **FNC**'
    ])
    
def get_ccu_change_emoji(old_ccu, new_ccu):
    if new_ccu > old_ccu:
        return "📈"
    elif new_ccu < old_ccu:
        return "📉"
    return "➡️"
    
# Cache for creator data
_creator_cache = {}

def _get_creator_data(creator_code: str) -> dict:
    """Get creator data with caching for common creators"""
    # Check cache first
    if creator_code in _creator_cache:
        return _creator_cache[creator_code]

    creator_mapping = {
        'iconicstudio': ('77cb1f71a6514c8d8a6bf89e8d61e5f2', 'iconicstudio'),
        'iconicstudiob': ('bf1cdc7ab1c94383a89ced1dfd2c759b', 'iconicstudiob'),
        'creativeroyale': ('77cb1f71a6514c8d8a6bf89e8d61e5f2', 'creativeroyale'),
        'icon': ('111dff485f12416f9b86c09342cf899e', 'icon'),
        'lego': ('ebb30d1ce01f487986ac37abfd18d50b', 'lego'),
        'epic': ('63ba52bf92554227820f4dd0a8cc6845', 'epic'),
        'team_fh': ('1a8e38dd87c74e0cb6adbcf34b2c74ee', 'team_fh'),
        'p': ('79491e3fe5cf41b180d148c3cfc778d4', 'Prettyboy'),
        'pp': ('1b95428c278245f6a09f22323710830b', 'Team Pretty Boy'),
        '3121': ('6f33e42edbb34a59909e5dc5badae1bf', 'Code Traki'),
        '0': ('79491e3fe5cf41b180d148c3cfc778d4', 'Prettyboy'),
    }

    result = None
    if len(creator_code) > 30:
        result = {'id': creator_code}
    elif creator_data := creator_mapping.get(creator_code):
        result = {'id': creator_data[0]}
    elif get_creator_id(creator_code):
        result = {"id": f"{get_creator_id(creator_code)}"}
    else:
        # Try API lookup for unknown creators
        response = fn_api.slug(code=creator_code)
        json_value, status_code = response
        if status_code == 200:
            result = json_value

    print(result)
    # Cache the result if we found something
    if result:
        _creator_cache[creator_code] = result

    return result

async def _process_creator_islands(links: list, creator_code: str) -> list:
    """Process island data and create embeds"""
    embeds = []
    link_codes = [''] * 4
    message_last = [''] * 4
    total_plays = 0
    min_play_count = 1

    # Get island data efficiently
    island_codes = [
        {"mnemonic": link['linkCode'], "plays": link["globalCCU"]} 
        for link in links
        if len(link['linkCode']) == 14
    ]

    # Get island details
    islands = await fn_api.island_more2(island=island_codes)
    
    # Process play counts
    play_counts = []
    for island in islands:
        for link in links:
            if link['linkCode'] == island['mnemonic'] and link["globalCCU"] >= min_play_count:
                title = remove_newline(island['metadata']['title'])
                play_counts.append((link["globalCCU"], island['mnemonic'], title))
                total_plays += link["globalCCU"]

    # Sort by plays
    play_counts.sort(reverse=True)

    # Format island data
    for count, code, title in play_counts:
        count_display = f"{round(count/1000, 1)}K" if count >= 1000 else str(count)
        island_line = f"**`{code}` - *{title}* - {ccu} {count_display}**\n"
        
        # Add to first non-full embed
        for i in range(4):
            if len(link_codes[i]) < 1900:
                link_codes[i] += island_line
                message_last[i] = link_codes[i]
                break

    # Create embeds
    if not total_plays:
        embeds.append(Embed(
            title=f'{creator_code.capitalize()} Islands',
            description='Zero Plays 💀',
            color=colour
        ))
    else:
        # Format total plays
        total_plays_str = class_py.format_number_with_commas(total_plays)
        message_last[0] = f'\n**Overall CCU {ccu} {total_plays_str}**\n\n{message_last[0]}'
        
        # Create main embed
        embeds.append(Embed(
            title=f'{creator_code.capitalize()} Islands',
            description=message_last[0][:2000],
            color=colour
        ))

        # Create additional embeds if needed
        for i in range(1, 4):
            if message_last[i]:
                embeds.append(Embed(description=message_last[i][:2000], color=colour))
            else:
                embeds.append(Embed(description='**No more available.**', color=colour))
                break

    return embeds

# Cache for island data
@staticmethod
@lru_cache(maxsize=1000)
def get_cached_island(island_code: str):
    return fn_api.island(island_code=island_code)

# Cache for SAC status
@staticmethod
@lru_cache(maxsize=1000)
def get_cached_sac(support_code: str):
    return fn_api.slug(support_code)

@staticmethod
@lru_cache(maxsize=1000)
def get_cached_logo(support_code: str):
    return fn_api.slug(support_code)

DEFAULT_LOGO = "https://cdn2.unrealengine.com/t-ui-creatorprofile-default-256x256-8d5feae6bc8e.png"
DEFAULT_BANNER = "https://cdn2.unrealengine.com/t-ui-creatorprofile-banner-fallbackerror-1920x1080-3f830cc95018.png"

@staticmethod
@lru_cache(maxsize=10000)  # Cache the result for up to 1000 unique creator IDs
def get_cached_creator_info(creator: str):
    """
    Fetch and cache the creator's information like avatar, banner, bio, and socials.
    """
    result = fn_api.info_creators(creator)
    response_data = result.json()
    print(response_data)

    images = response_data.get('images', {})
    avatar_url = images.get("avatar", DEFAULT_LOGO)
    banner_url = images.get("banner", DEFAULT_BANNER)
    
    bio = response_data.get('bio') or ""
    social = response_data.get('social', {})
    
    follow = response_data.get('followerCount', 0)

    socials = {}
    socials['youtube'] = f'https://www.youtube.com/{social.get("youtube", "None")}' if social.get('youtube') else 'None'
    socials['twitter'] = f'https://twitter.com/{social.get("twitter", "None")}' if social.get('twitter') else 'None'
    socials['discord'] = f'https://discord.gg/{social.get("discord", "None")}' if social.get('discord') else 'None'
    socials['tiktok'] = f'https://www.tiktok.com/{social.get("tiktok", "None")}' if social.get('tiktok') else 'None'
    socials['instagram'] = f'https://www.instagram.com/{social.get("instagram", "None")}' if social.get('instagram') else 'None'

    return avatar_url, bio, follow, socials, banner_url

@staticmethod
@lru_cache(maxsize=1000)  # Cache the result for up to 1000 unique sets of user IDs
def get_cache_info_creators_multiple(user_ids):
    """
    Fetch and cache the data for multiple creators at once.
    This function caches the results for sets of creator IDs.
    """
    # Convert the list to a tuple to make it hashable for the cache key
    user_ids_tuple = tuple(user_ids)

    creators_data = fn_api.info_creators_multiple(user_ids_tuple)
    print(creators_data)
    return creators_data