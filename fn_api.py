from typing import Any
import requests
import aiohttp
import socket
import ssl
import json
import time
import asyncio
from asyncio import create_task

session = requests.Session()

super_token = ''
super_token2 = ''
no_eg1_token = ''
public_token = ''

version = ''
digits = ''
user_agent = ''

client_id = '1cf9d8e3f28f4f79934c4189adcb42f0'
client_id2 = 'bf9b186dfe93492a86a2ce038b81acdd'

disco_token = ""

def get_island_data(island):
    global super_token, user_agent
    response = session.get(url=f'https://content-service.bfda.live.use1a.on.epicgames.com/api/content/v2/gen-package/link/{island}',headers={'cookie': f'content-service:access_token={super_token};', 'User-Agent': user_agent})
    print(response.json())
    island_data_version = response.json()['resolved']['root']['version']
    island_data_module = response.json()['resolved']['root']['moduleId']
    for x in response.json()['content']:
        if x['version'] == island_data_version:
            artifactKey = x['artifactKey']
    return artifactKey, island_data_module, island_data_version

def get_base_url(artifactKey):
    global super_token, user_agent
    response = session.get(url=f'https://content-service.bfda.live.use1a.on.epicgames.com/api/content/v2/artifact/{artifactKey}/cooked-content?{version}.{digits}&jobPlatform=Windows&wait=false',headers={'cookie': f'content-service:access_token={super_token};', 'User-Agent': user_agent})
    print(response.json())
    status = response.json()['status']
    if status == 'cooked':
        base = response.json()['output']['baseUrl']
        url_base = response.json()['output']['baseUrl'] + 'alt/plugin.manifest?FullInstall=true'
        cookJobId = response.json()['cookJobId']
        return status, url_base, cookJobId, base
    else:
        return status, None, None, None

def island_data(link):
    global super_token
    response = session.get(f'https://content-service.bfda.live.use1a.on.epicgames.com/admin/api/content/link/{link}', headers={'cookie': f'content-service:access_token={super_token};'})
    return response.json()

def access_discovery(branch):
    q = session.get(
            url=f'https://fngw-mcp-gc-livefn.ol.epicgames.com/fortnite/api/discovery/accessToken/{branch}',
            headers={
                "Authorization": f"bearer {super_token}",
                "User-Agent": f"{user_agent}"
        }
    ).json()
    
    return q['token']
    
def discoveryextra():
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/{client_id2}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token2}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Frontend",
            "revision": -1,
            "partyMemberIds": [f"{client_id2}"],
            "matchmakingRegion": f"EU"
        }
    ).json()
    return w

def discovery():
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/{client_id}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Frontend",
            "revision": -1,
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU",
            "platform": "Windows"
        }
    ).json()
    #print(w)
    return w

def discoveryv2():
    from requests.structures import CaseInsensitiveDict

    url = f"https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v2/discovery/surface/CreativeDiscoverySurface_Frontend?appId=Fortnite&stream=%2B%2BFortnite%2BRelease-{version}"
    #print(url)

    headers = CaseInsensitiveDict()
    headers["X-Epic-Access-Token"] = disco_token
    headers["Authorization"] = f"Bearer {super_token}"
    #print(super_token)
    headers["Content-Type"] = "application/json"
    #headers["User-Agent"] = "Fortnite/++Fortnite+Release-29.10-CL-32567225 Windows/10.0.19045.1.256.64bit"

    data = {
        "playerId": "cf92d8822f0448f68da3558e1815d806",
        "partyMemberIds": ["cf92d8822f0448f68da3558e1815d806"],
        "accountLevel": 60,
        "battlepassLevel": 25,
        "locale": "en",
        "matchmakingRegion": "EU",
        "platform": "Windows",
        "isCabined": False,
        "ratingAuthority": "PEGI",
        "rating": "PEGI_AGE_12"
    }

    headers["Content-Length"] = "367"

    resp = session.post(url, headers=headers, json=data).json()
    return resp

def discovery_collection(collection_key):
    """
    Get discovery data for a specific collection
    
    Available collection keys:
    - LEGO: CreativeDiscoverySurface_Nested_Collab_LEGO
    - FallGuys: CreativeDiscoverySurface_Nested_Collab_FallGuys
    - TMNT: CreativeDiscoverySurface_Nested_Collab_TMNT
    - RocketRacing: CreativeDiscoverySurface_Nested_Collab_RocketRacing
    """
    from requests.structures import CaseInsensitiveDict

    url = f"https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v2/discovery/surface/{collection_key}?appId=Fortnite&stream=%2B%2BFortnite%2BRelease-{version}"
    
    headers = CaseInsensitiveDict()
    headers["X-Epic-Access-Token"] = disco_token
    headers["Authorization"] = f"Bearer {super_token}"
    headers["Content-Type"] = "application/json"

    data = {
        "playerId": "cf92d8822f0448f68da3558e1815d806",
        "partyMemberIds": ["cf92d8822f0448f68da3558e1815d806"],
        "accountLevel": 60,
        "battlepassLevel": 25,
        "locale": "en",
        "matchmakingRegion": "EU",
        "platform": "Windows",
        "isCabined": False,
        "ratingAuthority": "PEGI",
        "rating": "PEGI_AGE_12"
    }

    resp = session.post(url, headers=headers, json=data)
    return resp.json()

def discovery_lego():
    """Get discovery data for LEGO collection"""
    return discovery_collection("CreativeDiscoverySurface_Nested_Collab_LEGO")

def discovery_fallguys():
    """Get discovery data for Fall Guys collection"""
    return discovery_collection("CreativeDiscoverySurface_Nested_Collab_FallGuys")

def discovery_tmnt():
    """Get discovery data for TMNT collection"""
    return discovery_collection("CreativeDiscoverySurface_Nested_Collab_TMNT")

def discovery_rocketracing():
    """Get discovery data for Rocket Racing collection"""
    return discovery_collection("CreativeDiscoverySurface_Nested_Collab_RocketRacing")

def discopageextra(testcohors, panel_name, index):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/page/{client_id2}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token2}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Frontend",
            "panelName": f"{panel_name}",
            "pageIndex": int(index),
            "revision": -1,
            "testCohorts": [f"{testcohors}"],
            "partyMemberIds": [f"{client_id2}"],
            "matchmakingRegion": "EU"
        }
    ).json()
    return w

def discopage(testcohors, panel_name, index):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/page/{client_id}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Frontend",
            "panelName": f"{panel_name}",
            "pageIndex": int(index),
            "revision": -1,
            "testCohorts": [f"{testcohors}"],
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU"
        }
    ).json()
    return w

def discopagev2(testcohors, panel_name, index):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v2/discovery/surface/CreativeDiscoverySurface_Frontend/page?appId=Fortnite&stream=%2B%2BFortnite%2BRelease-{version}',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "X-Epic-Access-Token": disco_token,
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "testVariantName": testcohors,
            "panelName": panel_name,
            "pageIndex": int(index),
            "playerId": f"{client_id}",
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU",
            "platform": "Windows",
            "isCabined": False,
            "ratingAuthority": "USK",
            "rating": "USK_AGE_12"
        }
    ).json()
    return w

def browser():
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/{client_id}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Browse",
            "revision": -1,
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU"
        }
    ).json()
    return w

def browserv2():
    from requests.structures import CaseInsensitiveDict

    url = f"https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v2/discovery/surface/CreativeDiscoverySurface_Browse?appId=Fortnite&stream=%2B%2BFortnite%2BRelease-{version}"

    headers = CaseInsensitiveDict()
    headers["X-Epic-Access-Token"] = disco_token
    headers["Authorization"] = f"Bearer {super_token}"
    headers["Content-Type"] = "application/json"

    data = """
    {
        "playerId": "cf92d8822f0448f68da3558e1815d806",
        "partyMemberIds": ["cf92d8822f0448f68da3558e1815d806"],
        "accountLevel": 1,
        "battlepassLevel": 1,
        "locale": "en",
        "matchmakingRegion": "EU",
        "platform": "Windows",
        "isCabined": false,
        "ratingAuthority": "PEGI",
        "rating": "PEGI_AGE_12"
    }
    """

    resp = session.post(url, headers=headers, data=data).json()
    return resp

def browserpage(testcohors, panel_name):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/page/{client_id}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Browse",
            "panelName": f"{panel_name}",
            "pageIndex": 0,
            "revision": -1,
            "testCohorts": [f"{testcohors}"],
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU"
        }
    ).json()
    return w

def browserpage1(testcohors, panel_name):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/discovery/surface/page/{client_id}?appId=Fortnite',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "surfaceName": "CreativeDiscoverySurface_Browse",
            "panelName": f"{panel_name}",
            "pageIndex": 1,
            "revision": -1,
            "testCohorts": [f"{testcohors}"],
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU"
        }
    ).json()
    return w

def browserpagev2(testcohors, panel_name, index):
    w = session.post(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v2/discovery/surface/CreativeDiscoverySurface_Browse/page?appId=Fortnite&stream=%2B%2BFortnite%2BRelease-{version}',
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"bearer {super_token}",
            "Content-Type": "application/json",
            "X-Epic-Access-Token": disco_token,
            "Host": "fn-service-discovery-live-public.ogs.live.on.epicgames.com",
            "User-Agent": f"{user_agent}"
            },
        json={
            "testVariantName": testcohors,
            "panelName": panel_name,
            "pageIndex": int(index),
            "playerId": f"{client_id}",
            "partyMemberIds": [f"{client_id}"],
            "matchmakingRegion": "EU",
            "platform": "Windows",
            "isCabined": False,
            "ratingAuthority": "USK",
            "rating": "USK_AGE_12"
        }
    ).json()
    return w

def island_more(island: Any):
    w = session.post(
        url='https://links-public-service-live.ol.epicgames.com/links/api/fn/mnemonic?ignoreFailures=true',
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {super_token}"
        },
        json=island
    ).json()
    return w

def island(island_code):
    w = session.get(
        url=f"https://links-public-service-live.ol.epicgames.com/links/api/fn/mnemonic/{island_code}",
        headers={
            "Authorization": f"Bearer {super_token}",
            "Content-Type": "application/json"
        }
    ).json()
    return w

def island2(island_code):
    host = "links-public-service-live.ol.epicgames.com"
    port = 443

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    context = ssl.create_default_context()
    ssl_sock = context.wrap_socket(sock, server_hostname=host)
    ssl_sock.connect((host, port))
    request = f"GET /links/api/fn/mnemonic/{island_code} HTTP/1.1\r\n" \
            f"Host: {host}\r\n" \
            f"Authorization: Bearer {super_token}\r\n" \
            f"Content-Type: application/json\r\n" \
            f"\r\n"

    ssl_sock.send(request.encode())
    response = ssl_sock.recv(4096).decode()
    ssl_sock.close()
    response_json = json.loads(response.split("\r\n\r\n")[1])

    return response_json

"""def GetTokenPublic():
    resp = session.post(url='https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token',data="grant_type=client_credentials&token_type=eg1", headers={"Host": "account-public-service-prod.ol.epicgames.com","Accept": "*/*","Accept-Encoding": "deflate, gzip","Content-Type": "application/x-www-form-urlencoded","Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="}).json()
    return resp['access_token']"""

def GetUserAgents(public_token):
    catalog = session.get(
        url='https://lightswitch-public-service-prod.ol.epicgames.com/lightswitch/api/service/Fortnite/status',
        headers={
            "Authorization": f"Bearer {public_token}"
        }
    ).json()
    buildid = session.get(
        url=f'https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/public/assets/v2/platform/Windows/namespace/fn/catalogItem/{catalog["launcherInfoDTO"]["catalogItemId"]}/app/Fortnite/label/Live',
        headers={
            "Authorization": f"Bearer {public_token}"
        }
    ).json()
    return buildid['elements'][0]['buildVersion']

def GetTokenPC():
    token = session.post(
        url='https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token',
        headers={
            "Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="
        },
        data={
            "grant_type": "device_auth",
            "device_id": "4b87e278a8a4487085a8d49946957912",
            "account_id": "1cf9d8e3f28f4f79934c4189adcb42f0",
            "secret": "WL33ML7CS6MJSJBXLZC5EHTJPDGVLDH7",
            "token_type": "eg1"
        }
    ).json()
    return token['access_token']

def GetTokenPC2():
    token = session.post(
        url='https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token',
        headers={
            "Authorization": "basic MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
        },
        data={
            "grant_type": "device_auth",
            "device_id": "05ba4893567447a9b32c9b9e6faa8442",
            "account_id": "bf9b186dfe93492a86a2ce038b81acdd",
            "secret": "DQFT4LQTUMVBSFM4MEWMVDGK2M2NFGZZ",
            "token_type": "eg1"
        }
    ).json()
    return token['access_token']

def GetTokenPCNotEG1():
    r = session.post(
        url="https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",
        headers={
            "Authorization": "Basic M2Y2OWU1NmM3NjQ5NDkyYzhjYzI5ZjFhZjA4YThhMTI6YjUxZWU5Y2IxMjIzNGY1MGE2OWVmYTY3ZWY1MzgxMmU="
        },
        data={
            "grant_type": "device_auth",
            "device_id": "4b87e278a8a4487085a8d49946957912",
            "account_id": "1cf9d8e3f28f4f79934c4189adcb42f0",
            "secret": "WL33ML7CS6MJSJBXLZC5EHTJPDGVLDH7"
        }
    ).json()
    return r['access_token']

def GetTokenPublic():
    req = b"POST /account/api/oauth/token HTTP/1.1\r\nHost: account-public-service-prod.ol.epicgames.com\r\nAuthorization: Basic ZWM2ODRiOGM2ODdmNDc5ZmFkZWEzY2IyYWQ4M2Y1YzY6ZTFmMzFjMjExZjI4NDEzMTg2MjYyZDM3YTEzZmM4NGQ=\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 29\r\n\r\ngrant_type=client_credentials"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('account-public-service-prod.ol.epicgames.com', 443))
    sock = ssl.wrap_socket(sock)

    sock.send(req)
    response = b""
    data = sock.recv(4096)
    response += data
    start_index = response.find(b'{')
    end_index = response.rfind(b'}') + 1
    json_data = response[start_index:end_index].decode('utf-8')
    full = json.loads(json_data)

    access_token = full['access_token']
    return access_token

def slug(code):
    def make_https_request(url, headers):
        sock = socket.create_connection((url, 443))
        
        context = ssl.create_default_context()
        secure_sock = context.wrap_socket(sock, server_hostname=url)
        request = f"GET /affiliate/api/public/affiliates/slug/{code} HTTP/1.1\r\nHost: {url}\r\n"
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        secure_sock.sendall(request.encode())
        
        response = b""
        data = secure_sock.recv(4096)
        response += data
        return response

    def status_code(response):
        status_line = response.split(b"\r\n")[0]
        status_code = int(status_line.split()[1])
        return int(status_code)

    def json_paste(response):
        content = response.split(b'\r\n\r\n', 1)[1]
        data = json.loads(content)
        return data

    url = "affiliate-public-service-prod.ol.epicgames.com"
    code = code
    headers = {"Authorization": f"Bearer {public_token}"}

    response = make_https_request(url, headers)
    status = status_code(response)
    json_data = json_paste(response)

    result = (json_data, status)

    return result

"""def slug(code, token):
    w = session.get(url=f"https://affiliate-public-service-prod.ol.epicgames.com/affiliate/api/public/affiliates/slug/{code}",headers={"Authorization": f"Bearer {token}"})
    return w"""

@staticmethod
def creatormaps(creator):
    w = session.get(
        url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/creator/page/{creator}?playerId={client_id}&limit=99',
        headers={
            "Authorization": f"Bearer {super_token}"
        }
    ).json()
    return w

@staticmethod
async def creatormaps2(creator):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=f'https://fn-service-discovery-live-public.ogs.live.on.epicgames.com/api/v1/creator/page/{creator}?playerId={client_id}&limit=99',
            headers={"Authorization": f"Bearer {super_token}"}
        ) as response:
            await response.json()
            return response
        
def get_creator_page(creator):
    host = "fn-service-discovery-live-public.ogs.live.on.epicgames.com"
    port = 443

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    context = ssl.create_default_context()
    ssl_sock = context.wrap_socket(sock, server_hostname=host)

    ssl_sock.connect((host, port))

    request = f"GET /api/v1/creator/page/{creator}?playerId={client_id}&limit=99 HTTP/1.1\r\n" \
            f"Host: {host}\r\n" \
            f"Authorization: Bearer {super_token}\r\n" \
            f"\r\n"

    ssl_sock.send(request.encode())

    response = b""
    data = ssl_sock.recv(65536)
    response += data

    headers, body = response.split(b"\r\n\r\n", 1)
    content_length = int(headers.split(b"Content-Length: ")[1].split(b"\r\n", 1)[0])
    actual_length = len(body)
    
    if not content_length == actual_length:
        # The payload size does not match
        while True:
            data = ssl_sock.recv(65536)
            response += data

            headers, body = response.split(b"\r\n\r\n", 1)
            content_length = int(headers.split(b"Content-Length: ")[1].split(b"\r\n", 1)[0])
            actual_length = len(body)

            if content_length == actual_length:
                break

    ssl_sock.close()
    start_index = response.find(b'{')
    end_index = response.rfind(b'}') + 1
    json_data = response[start_index:end_index].decode('utf-8')
    response_json = json.loads(json_data)

    return response_json

@staticmethod
async def island_more2(island):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=f'https://links-public-service-live.ol.epicgames.com/links/api/fn/mnemonic?ignoreFailures=true',
            headers={"Content-Type": "application/json","Authorization": f"Bearer {super_token}"},
            json=island
        ) as response:
            return await response.json()
        
def get_creator_search(creatorterm):
    global super_token, user_agent
    url = 'https://fn-service-discovery-search-live-public.ogs.live.on.epicgames.com/api/v1/creators/search?accountId=1cf9d8e3f28f4f79934c4189adcb42f0'
    json = {
        "creatorTerm": creatorterm
    }
    headers = {
        "Authorization": f"bearer {super_token}",
        "User-Agent": f"{user_agent}"
    }
    w = session.post(url, json=json, headers=headers)
    print(w.json())
    return w.json()['results']
        
def info_creators(creatorid):
    w = session.get(
        f"https://pops-api-live-public.ogs.live.on.epicgames.com/page/v1/{creatorid}?playerId={client_id}&locale=en",
        headers={"Authorization": f"Bearer {super_token}", "User-Agent": user_agent}
    )
    return w

def info_creators_multiple(creators):
    print(super_token)
    w = session.post(
        f"https://pops-api-live-public.ogs.live.on.epicgames.com/page/v1?playerId={client_id}&locale=en",
        headers={"Authorization": f"Bearer {super_token}", "User-Agent": user_agent, "X-Epic-Source-Client-Type": "fn-client"},
        json={"playerIds": creators}
    )
    return w.json()
        
def island_more1(island):
    w = session.post(
        url='https://links-public-service-live.ol.epicgames.com/links/api/fn/mnemonic?ignoreFailures=true',
        headers={
            "Authorization": f"Bearer {super_token}"
        },
        json=island
    )
    return w.json()

def verify_token(token):
    w = session.get(
        url='https://account-public-service-prod.ol.epicgames.com/account/api/oauth/verify',
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    return w.status_code

def delete_token(token):
    session.delete(
        url=f'https://account-public-service-prod.ol.epicgames.com/account/api/oauth/sessions/kill/{token}'
    )

async def teak_complet(): 
    while True:
        global super_token, super_token2, no_eg1_token, public_token, user_agent, version, digits, disco_token
        super_token = GetTokenPC()
        no_eg1_token = GetTokenPCNotEG1()
        public_token = GetTokenPublic()
        user_agent = session.get('http://192.168.1.34:8000/version').json()['version']
        #print(user_agent)
        version, digits = user_agent[user_agent.index("Release-") + len("Release-") : user_agent.index("-CL-")], user_agent[user_agent.index("CL-") + len("CL-") : user_agent.index(" W")]
        #print(version + digits)
        #disco_token = access_discovery(branch=f"++Fortnite+Release-{version}")
        print('Connected Fortnite Service !')
        await asyncio.sleep(3600)
    
def create_task():
    asyncio.run(teak_complet())

create_task()
