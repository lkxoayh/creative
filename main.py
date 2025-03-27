import database
import fn_api
import asyncio
import threading
import time
import json

from utils.api import Api
from flask import Flask, render_template_string, request, jsonify, abort, send_from_directory
from database import get_all_creators, get_creator_name, get_creator_id, get_all_creators_with_none, insert_creator
from utils1 import remove_newline, _get_image, _get_creator_data, _get_xp_status, get_cached_sac, get_cached_island, get_cache_info_creators_multiple, get_cached_creator_info

app = Flask(__name__)

islands_data = [
    {"name": "", "image": "", "code": "", "creator": "Creator A"},
    {"name": "", "image": "", "code": ""},
    {"name": "", "image": "", "code": ""},
    {"name": "", "image": "", "code": ""},
]

name_creator = ""

with open("./index.html", "r", encoding="utf-8") as file:
    HTML_TEMPLATE = file.read()

DEFAULT_LOGO = "https://cdn2.unrealengine.com/t-ui-creatorprofile-default-256x256-8d5feae6bc8e.png"
DEFAULT_BANNER = "https://cdn2.unrealengine.com/t-ui-creatorprofile-banner-fallbackerror-1920x1080-3f830cc95018.png"

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory('static/fonts', filename)

@app.route('/api/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('/css', filename)

def get_logo_and_banner_url(creator: str, dev: str | None):
    """
    Fetch and return the creator's avatar, bio, socials, and banner.
    Caches the result for efficiency.
    """
    # Fetch the cached creator information
    avatar_url, bio, follow, socials, banner_url = get_cached_creator_info(creator)

    if dev:
        return avatar_url, bio, follow, socials, banner_url

    return avatar_url, banner_url

def info_creators_multiple(user_ids):
    creators_data = get_cache_info_creators_multiple(tuple(user_ids))
    print(creators_data)
    return creators_data

@app.route('/search_creator')
def search_creator():
    time.sleep(0.1)
    query = request.args.get('name', '').strip().lower()
    creators = get_all_creators_with_none()
    matching_creators = []

    # Find matching creators based on the query
    for name, cid in creators.items():
        if not name or len(matching_creators) > 97:
            break

        if query in name:
            print(name)
            matching_creators.append({'name': name, 'id': cid})
            
    # Check sac event
    slug_data = _get_creator_data(query)
    if slug_data:
        if not any(creator['name'] == query for creator in matching_creators):
            matching_creators.append({'name': query, 'id': slug_data['id']})
            insert_creator(query, slug_data['id'])
        
    if not matching_creators:
        slug_data = _get_creator_data(query)
        print(slug_data)
        if slug_data:
            matching_creators.append({'name': query, 'id': slug_data['id']})
            insert_creator(query, slug_data['id'])

    if not matching_creators:
        return jsonify({"message": "No creators found"}), 404

    creator_ids = [creator['id'] for creator in matching_creators]

    if len(creator_ids) == 1:  # Single creator
        logo, bio, follow, socials, banner = get_logo_and_banner_url(creator_ids[0], "dev")
        for creator in matching_creators:
            creator["logo"] = logo
            creator["banner"] = banner
            creator['bio'] = bio
            creator['follow'] = follow
            creator['socials'] = socials
    else:  # Multiple creators
        creators_data = info_creators_multiple(creator_ids)

        if 'results' not in creators_data:
            return jsonify({"message": "Unexpected response format for creators data"}), 500
        
        creators_data_list = creators_data['results']
        creators_data_dict = {creator['playerId']: creator for creator in creators_data_list}
        
        for creator in matching_creators:
            creator_data = creators_data_dict.get(creator['id'], {})
            print(creator_data)
            creator["logo"] = creator_data.get("images", {}).get("avatar", DEFAULT_LOGO)

    return jsonify(matching_creators)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/live-ccu/<string:creatorid>', methods=['GET'])
def get_live_ccu_for_creator(creatorid):
    min_play_count = -1

    island_xx = fn_api.creatormaps(creator=creatorid)
    links = island_xx['links']
    
    island_codes = [{"mnemonic": f"{x['linkCode']}"} for x in links]
    island_data = fn_api.island_more1(island=island_codes)
    
    data_json = [
        {
            "code": island['mnemonic'],
            "name": remove_newline(island['metadata']['title']),
            "image": _get_image(island['metadata']),
        }
        for island in island_data
    ]
    
    for island in data_json:
        matching_link = next((link for link in links if link['linkCode'] == island['code']), None)
        
        if matching_link and matching_link["globalCCU"] >= min_play_count:
            count = matching_link["globalCCU"]
            island['ccu'] = "0" if count == -1 else f"{round(count / 1000, 1)}K" if count >= 1000 else str(count)
    
    if not data_json:
        abort(404, description="Creator not found or no islands associated.")
    
    return jsonify(data_json)

def get_featured_islands(creator_page):
    """Extract featured islands from a creator page"""
    for panel in creator_page.panels:
        if panel.panel_name == "Featured":
            return panel.first_page.results
    return []

def get_creator_picks(creator_page):
    """Extract creator picks from a creator page"""
    for panel in creator_page.panels:
        if panel.panel_name == "CreatorPicks":
            return panel.first_page.results
    return []

def format_ccu(ccu: int) -> str:
    """Format CCU (Concurrent Users) for display"""
    if ccu == -1:
        return "0"
    elif ccu >= 1000:
        return f"{round(ccu / 1000, 1)}K"
    else:
        return str(ccu)
    
def parse_creator_page(json_data):
    """Parse creator page JSON and extract island information"""
    # Load the JSON if it's a string
    data = json_data
    
    # Initialize the result dictionary
    result = {
        "featured": 'None',
        "picks": 'None'
    }
    
    # Process each panel
    panels = data.get("panels", [])
    for panel in panels:
        panel_name = panel.get("panelName", "")
        first_page = panel.get("firstPage", {})
        islands = first_page.get("results", [])
        
        # Determine which list to add to
        if panel_name == "Featured" and islands:
            target_list = []
            result["featured"] = target_list
        elif panel_name == "CreatorPicks" and islands:
            target_list = []
            result["picks"] = target_list
        else:
            continue
        
        # Add islands to the appropriate list
        for island in islands:
            island_info = {
                "code": island.get("linkCode", ""),
                "ccu": format_ccu(island.get("globalCCU", -1)),
            }
            target_list.append(island_info)
    
    return result

@app.route('/creator/<string:name>')
def creator(name):
    global name_creator
    
    name_creator = name
    creator_id = get_creator_id(name)
    if creator_id == None: 
        creator_id = _get_creator_data(name)['id']
        print(creator_id)
        insert_creator(name, creator_id)
        
    logo, bio, follow, socials, banner = get_logo_and_banner_url(creator_id, "dev")
    
    follow_display = f"{round(follow/1000, 1)}K" if follow >= 1000 else str(follow)
    creator_page = fn_api.creatorpage_disco(creator_id)
    data = parse_creator_page(creator_page)
    
    dev = {
        'featured': 'None',
        'picks': 'None'
    }
    
    if data['featured'] != 'None':
        island_codes = [{"mnemonic": f"{x['code']}"} for x in data['featured']]
        info = fn_api.island_more1(island=island_codes)
        for island in info:
            # Find matching island in data['featured'] list
            matching_island = next((x for x in data['featured'] if x['code'] == island['mnemonic']), None)
            ccu_value = matching_island['ccu'] if matching_island else "0"
            dev['featured'] = []
            dev['featured'].append({
                'code': island['mnemonic'],
                'name': remove_newline(island['metadata']['title']),
                'image': _get_image(island['metadata']),
                'ccu': ccu_value
            })
    if data['picks'] != 'None':
        island_codes = [{"mnemonic": f"{x['code']}"} for x in data['picks']]
        info = fn_api.island_more1(island=island_codes)
        for island in info:
            # Find matching island in data['picks'] list
            matching_island = next((x for x in data['picks'] if x['code'] == island['mnemonic']), None)
            ccu_value = matching_island['ccu'] if matching_island else "0"
            
            dev['picks'] = []
            dev['picks'].append({
                'code': island['mnemonic'],
                'name': remove_newline(island['metadata']['title']),
                'image': _get_image(island['metadata']),
                'ccu': ccu_value
            })
        
    context = {
        "creator": dev,
        "creatorlogo": logo,
        "creatorbanner": banner,
        "creator_id": creator_id,
        'creatorfollow': follow_display,
        'islands': [],
        "island": socials,
        'name_creator': name_creator
    }
    with open("./testing.html", "r", encoding="utf-8") as file:
        dev = file.read()
    return render_template_string(dev, **context)

@app.route('/islands/<string:name>', methods=['POST'])
def update_island(name):
    global islands_data, name_creator
    
    name_creator = name
    data = request.get_json()
    islands_data = data
    return jsonify({"message": f"Island updated successfully."}), 200

@app.route('/database')
def creatordatabase():
    creators = get_all_creators()
    
    # Generate creator cards instead of table rows
    creator_cards = ""
    for name, creator_id in creators.items():
        creator_cards += f"""
        <div class="creator-card">
            <div class="creator-avatar">
                <img src="{DEFAULT_LOGO}" alt="{name}'s avatar">
            </div>
            <div class="creator-name">{name}</div>
            <div class="creator-id">{creator_id}</div>
        </div>
        """
    
    # Create HTML with f-string instead of .format()
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Creators Database</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #0a1525;
            color: #ffffff;
        }}
        .header {{
            background-color: #0a1525;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e293b;
        }}
        .tab {{
            display: inline-block;
            padding: 8px 16px;
            background-color: #132236;
            border-radius: 20px;
            margin-right: 10px;
            font-weight: bold;
        }}
        .active {{
            background-color: #ffffff;
            color: #0a1525;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #ffffff;
            margin-bottom: 20px;
        }}
        .count {{
            font-size: 16px;
            color: #8b949e;
            margin-bottom: 30px;
        }}
        .creator-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }}
        .creator-card {{
            background-color: #132236;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: transform 0.2s;
            overflow: hidden;
        }}
        .creator-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}
        .creator-avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        .creator-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .creator-name {{
            font-weight: bold;
            margin-bottom: 5px;
            text-align: center;
        }}
        .creator-id {{
            font-size: 12px;
            color: #8b949e;
            text-align: center;
            word-break: break-all;
        }}
        .search-bar {{
            padding: 10px;
            margin-bottom: 20px;
        }}
        .search-input {{
            width: 100%;
            max-width: 300px;
            padding: 10px 15px;
            border-radius: 20px;
            border: none;
            background-color: #1e293b;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="tab">ISLANDS (48)</div>
            <div class="tab active">CREATORS ({len(creators)})</div>
        </div>
    </div>
    
    <div class="container">
        <h1>Creators Results</h1>
        <div class="count">Total Creators: {len(creators)}</div>
        
        <div class="search-bar">
            <input type="text" placeholder="Search creators..." class="search-input" id="searchInput">
        </div>
        
        <div class="creator-grid" id="creatorGrid">
            {creator_cards}
        </div>
    </div>
    
    <script>
        // Simple search functionality
        document.getElementById('searchInput').addEventListener('keyup', function() {{
            const searchValue = this.value.toLowerCase();
            const creatorCards = document.querySelectorAll('.creator-card');
            
            creatorCards.forEach(card => {{
                const creatorName = card.querySelector('.creator-name').textContent.toLowerCase();
                const creatorId = card.querySelector('.creator-id').textContent.toLowerCase();
                
                if (creatorName.includes(searchValue) || creatorId.includes(searchValue)) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    return html_content

@app.route("/island/<code>")
def island_detail(code):
    min_play_count = 1
    
    # Cache for the island metadata
    car = get_cached_island(island_code=code)
    metadata = car.get('metadata', {})
    creator_id = car['accountId']
    type = car.get('linkType')
    
    if type == 'valkyrie:application':
        type = "UEFN"
    else:
        type = "FNC"
    
    support_code = metadata.get("supportCode", "None")
    
    # Cache for SAC result
    sac_result = get_cached_sac(support_code)
    
    island_program = sac_result[1] != 200 and support_code != "None"
    if island_program:
        insert_creator(support_code, car["accountId"])

    # Cache for creator logo, bio, socials, and banner
    logo, bio, follow, socials, banner = get_logo_and_banner_url(creator_id, "dev")
    
    if tags := car.get('descriptionTags'):
        if not tags == ['']:
            tags1 = []
            for tag in car.get('descriptionTags'):
                tagsq = tag.upper()
                tags1.append(tagsq)
    
    creation_date = (car.get('published') or car.get('created') or 'Unknown').split('T')[0]
    last_update = (car.get('lastActivatedDate') or car.get('created', 'Unknown')).split('T')[0]
    
    # Cache for islands data
    islands = fn_api.creatormaps(creator_id)
    links = islands['links']
    
    # Get island data efficiently
    island_codes = [
        {"mnemonic": link['linkCode'], "plays": link["globalCCU"]}
        for link in links
        if len(link['linkCode']) == 14
    ]
    
    islands1 = fn_api.island_more1(island=island_codes)
    
    play_counts = 0
    for island in islands1:
        for link in links:
            if link['linkCode'] == island['mnemonic'] and link["globalCCU"] >= min_play_count:
                if island['mnemonic'] == code:
                    play_counts = link["globalCCU"]
                    
    count_display = f"{round(play_counts/1000, 1)}K" if play_counts >= 1000 else str(play_counts)
    
    text = metadata.get('tagline', 'Unknown Island')
    
    # Split by newlines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Extract island name (first line)
    name = lines[0] if lines else "Unknown Island"
    
    # Extract description (all lines except the first)
    description = "\n".join(lines[1:]) if len(lines) > 1 else ""
    
    # Create taglines from the description
    taglines = []
    for line in description.split('\n'):
        if line:
            if len(line) > 50:
                # Split long lines into shorter taglines
                words = line.split()
                current_tagline = ""
                for word in words:
                    if len(current_tagline + " " + word) <= 50:
                        current_tagline += " " + word if current_tagline else word
                    else:
                        taglines.append(current_tagline)
                        current_tagline = word
                if current_tagline:
                    taglines.append(current_tagline)
            else:
                taglines.append(line)
    
    # Initialize the island object
    island = {
        "tagline": taglines,
        "name": metadata.get('title', 'Unknown Island'),
        "xp_status": _get_xp_status(metadata),
        "image": _get_image(metadata),
        "type": type,
        "code": code,
        "creator": {
            "name": support_code,
            "logo": logo,
            "bio": bio,
            "social": socials
        },
        "description": "",
        "release_date": creation_date,
        "updated_date": last_update,
        "player_count": count_display,
        "tags": tags1,
        "max_players": "16",
        "peak_24h": "0",  # Default value
        "peak_all_time": "0"  # Default value
    }
    
    if video_uuid := metadata.get('video_vuid'):
        island["video_uuid"] = video_uuid
        island["m3u8_url"] = f"https://cdn-0001.qstv.on.epicgames.com/{video_uuid}/master.m3u8"
    
    print(island)

    if island:
        with open("./island.html", "r", encoding="utf-8") as file:
            ISLAND_TEMPLATE = file.read()
        return render_template_string(ISLAND_TEMPLATE, island=island, code=code)
    else:
        return "Island not found", 404

if __name__ == '__main__':
    thread = threading.Thread(target=fn_api.create_task, daemon=True)
    thread.start()
    app.run(host="0.0.0.0",debug=True)
