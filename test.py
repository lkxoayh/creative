import json
import fn_api
import asyncio
from utils1 import remove_newline, get_cached_sac
from database import insert_creator
import random
import itertools
import string

# Patch fn_api.create_task to prevent it from calling asyncio.run
# Original implementation causes "RuntimeError: asyncio.run() cannot be called from a running event loop"
fn_api.create_task = lambda: None

# We don't need to generate all possible letter combinations
# Instead, let's create more practical and efficient keyword generation
def get_keywords(count):
    """
    Generate a list of useful keywords for creator search without generating all possibilities.
    This is MUCH faster than the original approach, especially for count >= 4.
    """
    # Common word parts that might be in creator names
    common_prefixes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                      'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                      'th', 'ch', 'sh', 'wh', 'ph', 'st', 'gr', 'gl', 'pl', 'cl', 'bl',
                      'pro', 'pre', 'con', 'com', 'sub', 'sup', 'dis', 'mis', 'un', 'in', 'im']
    
    # Fortnite-specific terms and popular creator name parts
    fortnite_terms = [
        # Game-related terms
        'fort', 'nite', 'battle', 'royal', 'epic', 'game', 'play', 'win', 'victory',
        'build', 'edit', 'box', 'storm', 'zone', 'shield', 'heal', 'med', 'potion', 'slurp',
        'chest', 'drop', 'land', 'loot', 'skin', 'emote', 'dance', 'floss', 'dab', 'squad',
        'duo', 'solo', 'ranked', 'arena', 'comp', 'tour', 'event', 'cup', 'cash', 'prize',
        
        # Map locations and POIs
        'tilted', 'towers', 'pleasant', 'park', 'retail', 'row', 'salty', 'springs', 'lazy',
        'lake', 'loot', 'fatal', 'fields', 'moisty', 'mire', 'junk', 'junction', 'haunted',
        'hills', 'greasy', 'grove', 'dusty', 'depot', 'divot', 'paradise', 'palms', 'risky',
        'reels', 'shifty', 'shafts', 'snobby', 'shores', 'tomato', 'temple', 'town', 'wailing',
        'woods', 'mega', 'mall', 'polar', 'peak', 'frosty', 'flights', 'happy', 'hamlet',
        
        # Weapons and items
        'pump', 'shotgun', 'ar', 'rifle', 'smg', 'sniper', 'bolt', 'heavy', 'tac', 'tactical',
        'minigun', 'rocket', 'launcher', 'pistol', 'deagle', 'hand', 'cannon', 'drum', 'gun',
        'scar', 'burst', 'infantry', 'scoped', 'suppressed', 'silenced', 'hunting', 'thermal',
        
        # Player types and styles
        'sweat', 'tryhard', 'bot', 'noob', 'default', 'og', 'pro', 'elite', 'cracked',
        'goated', 'insane', 'crackhead', 'toxic', 'controller', 'kbm', 'console', 'pc',
        'switch', 'mobile', 'aim', 'assist', 'bloom', 'ping', 'zero', 'smurf', 'alt',
        
        # Creator/Streaming related
        'ttv', 'yt', 'youtube', 'twitch', 'fb', 'facebook', 'stream', 'streamer', 'content', 
        'creator', 'clip', 'montage', 'highlight', 'reel', 'frag', 'kill', 'elim', 'wipe',
        'squad', 'clutch', 'nasty', 'sick', 'fire', 'insane', 'nuts', 'cracked', 'goated',
        'broken', 'meta', 'op', 'nerf', 'buff', 'update', 'patch', 'season', 'chapter',
        'live', 'gaming', 'gamer', 'player', 'fan', 'clan', 'team', 'org', 'esport',
        
        # Popular Fortnite creator name elements
        'ninja', 'tfue', 'sypherpk', 'nickeh30', 'bugha', 'mongraal', 'clix', 'benjyfishy',
        'lazarbeam', 'fresh', 'lachlan', 'muselk', 'mrfreshasian', 'nickmercs', 'scoped',
        'ronaldo', 'noah', 'wolfiez', 'unknown', 'assault', 'aydan', 'ghost', 'nrg', 'faze', 
        'tsm', 'liquid', 'cloud', 'nate', 'hill', 'thief', 'khanada', 'stretch',
        'zayt', 'saf', 'bizzle', 'dubs', 'megga', 'commandment', 'edgey', 'cented', 'mrsavage',
        'mero', 'deyy', 'reverse', 'furious', 'beast', 'typical', 'gamer', 'ranger', 'royale',
        'ali', 'sypher', 'pk', 'nick', 'eh', 'tim', 'courage', 'drlupo',
        'cloakzy', 'chap', 'vivid', 'poach', 'nosh', 'calc', 'avery', 'slackes', 'illest',
        'reet', 'arkhram', 'rehx', 'epikwhale', 'stable', 'blake', 'keys', 'innocents'
    ]
    
    # Add some common username patterns (non-numeric only)
    username_patterns = [
        # Common letter sequences
        'xx', 'xxx', 'gg', 'ez', 'yt', 'ttv', 'fn', 'tv', 'igl',
        'abc', 'xyz', 'qwerty', 'wasd', 'asd', 'zxc',
        
        # Common username prefixes (alphabetic only)
        'mr', 'ms', 'miss', 'dr', 'prof', 'the', 'im', 'its', 'iam', 'real', 'not', 'fake',
        'official', 'og', 'thereal', 'original', 'best', 'top', 'elite', 'premium', 'prime', 
        'gold', 'silver', 'bronze', 'iron', 'diamond', 'emerald', 'ruby', 'champion'
    ]
    
    # Also add all single letters
    all_letters = list(string.ascii_lowercase)
    
    # Generate random letter combinations (no numbers)
    random_combinations = []
    for _ in range(min(150, count * 15)):  # Generate more random combinations to compensate for removed numeric variants
        length = random.randint(2, count)
        random_combo = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
        random_combinations.append(random_combo)
    
    # Combine all sources of keywords (excluding numeric variants)
    keywords = common_prefixes + fortnite_terms + username_patterns + all_letters + random_combinations
    
    # Ensure uniqueness and randomize order
    unique_keywords = list(set(keywords))
    random.shuffle(unique_keywords)
    
    print(f"Generated {len(unique_keywords)} unique alphabetic keywords for search")
    return unique_keywords

# Original functions kept for reference but no longer used
def iter_all_strings_original():
    for size in itertools.count(1):
        for s in itertools.product(string.ascii_lowercase, repeat=size):
            yield "".join(s)
 
def get_keywords_original(count: int):
    letter_list = []
    for s in iter_all_strings_original():
        # print(s)
        letter_list.append(s)
        if s == 'z'*count:
            break
    return letter_list

class CreatorDiscovery:
    def __init__(self):
        # Event loop
        self.loop = asyncio.get_event_loop()
    
    async def run_search_creator_task(self):
        try:
            # Start the task but don't wait for it to complete
            await self.search_creator()
        except Exception as e:
            print(f"Error in run_search_creator_task: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying if there's an error

    async def search_creator(self):
        try:
            print('Starting creator search...')
            
            # Use our new optimized keyword generation (much faster)
            # Adjust the number based on how many keywords you want to search
            keywords = get_keywords(8)  # This will generate a reasonable number of keywords
            
            print(f"Searching through {len(keywords)} keywords")
            
            for keyword in keywords:
                try:
                    max_attempts = 1
                    attempts = 0
                    
                    while attempts < max_attempts:
                        try:
                            attempts += 1
                            print(f"Searching for creator with keyword: {keyword}")
                            
                            # Direct API call for the keyword
                            results = fn_api.get_creator_search(keyword)
                            
                            if not results or len(results) == 0:
                                print(f"No results for keyword: {keyword}")
                                break
                                
                            print(f"Found {len(results)} creator(s) for keyword: {keyword}")
                            
                            # Process list directly
                            creator_list = [creator['accountId'] for creator in results]
                            
                            # Limit the number of creators to process if there are too many
                            if len(creator_list) > 99:
                                print(f"Limiting results from {len(creator_list)} to 10")
                                creator_list = creator_list[:99]
                                
                            # Get creator info
                            info = fn_api.info_creators_multiple(creator_list)
                            
                            # Process each creator
                            for creator in info['results']:
                                try:
                                    insert_creator(creator['displayName'], creator['playerId'])
                                    print(f"Added creator: {creator['displayName']} ({creator['playerId']})")
                                except Exception as e:
                                    print(f"Error inserting creator {creator.get('displayName', 'unknown')}: {e}")
                            
                            break  # Successfully processed this keyword
                            
                        except Exception as e:
                            print(f"Error processing keyword {keyword}: {e}")
                            if attempts >= max_attempts:
                                print(f"Max attempts reached for {keyword}, moving to next keyword")
                                break
                            await asyncio.sleep(1)  # Short delay before retry
                
                except Exception as e:
                    print(f"Outer error processing keyword {keyword}: {e}")
                
                # Add a small delay between keywords to avoid rate limiting
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"Error in search_creator: {e}")
            
        print("Creator search completed")

async def main():
    discovery = CreatorDiscovery()
    
    try:
        print("Starting initialization...")
        
        # Directly create a task for the teak_complet coroutine instead of using create_task()
        # This avoids the asyncio.run() error
        token_refresh_task = asyncio.create_task(fn_api.teak_complet())
        
        print("API tokens initialized")
        print("Starting creator discovery service...")
        
        # Wait a moment for tokens to be set up
        await asyncio.sleep(2)
        
        # Testing creator search
        print("Testing creator search...")
        
        # Start the search_creator
        await discovery.run_search_creator_task()
        
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        print("Cleaning up resources...")

if __name__ == "__main__":
    # Run the async main function using asyncio.run
    # This creates a new event loop and properly handles cleanup
    asyncio.run(main())