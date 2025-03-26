import database
import fn_api
import asyncio
import threading
import time

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
                
    print(socials)
    
    follow_display = f"{round(follow/1000, 1)}K" if follow >= 1000 else str(follow)
        
    context = {
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

@app.route("/island/<code>")
def island_detail(code):
    min_play_count = 1
    
    # Cache for the island metadata
    car = get_cached_island(island_code=code)
    metadata = car.get('metadata', {})
    creator_id = car['accountId']
    
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
            tags = {", ".join(tags)}
    
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
    
    # Initialize the island object
    island = {
        "name": metadata.get('title', 'Unknown Island'),
        "xp": _get_xp_status(metadata),
        "image": _get_image(metadata),
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
        "tags": tags
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

def run_async_task():
    fn_api.create_task() # Run the async function
    print('test')

if __name__ == '__main__':
    thread = threading.Thread(target=run_async_task, daemon=True)
    thread.start()
    app.run(host="0.0.0.0",debug=True)
