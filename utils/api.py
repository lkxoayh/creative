from base64        import b64decode, b64encode
from Cryptodome.Cipher import AES
from browser_cookie3 import chrome
from socket        import socket, AF_INET, SOCK_STREAM
from json          import loads
from urllib.parse  import quote, urlencode
from random        import randint
from tls_client    import Session, response
from execjs        import compile
import random

class Api:
    def __init__(this, userAgent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', cookies: dict = {}):
        this.cookies    = cookies
        this.userAgent  = userAgent
        this.client     = Session(client_identifier='chrome_109')
    
    def get_headers2(this, extra: dict = {}) -> dict:
        return {
            **extra,
            'authority'          : 'www.fortnite.com',
            'accept'             : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language'    : 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5',
            'sec-ch-ua'          : '"Brave";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile'   : '?0',
            'sec-ch-ua-platform' : '"Windows"',
            'sec-fetch-dest' : 'empty',
            'sec-fetch-user' : '1',
            'sec-fetch-site' : 'same-origin',
            'sec-gpc'        : '1',
            'cookie'         : this.cookies,
            'user-agent'     : this.userAgent
        }
    
    def get_headers3(this, extra: dict = {}) -> dict:
        return {
            **extra,
            'authority'          : 'fortnite.gg',
            'accept'             : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language'    : 'fr-FR,fr;q=0.5',
            'sec-ch-ua'          : '"Brave";v="123", "Not:A-Brand";v="8","Chromium";v="123"',
            'sec-ch-ua-mobile'   : '?0',
            'sec-ch-ua-platform' : '"Windows"',
            'sec-fetch-dest' : 'empty',
            'sec-fetch-user' : '1',
            'sec-fetch-site' : 'same-origin',
            'sec-gpc'        : '1',
            'cookie'         : this.cookies,
            'user-agent'     : this.userAgent
        }

    
    def fortnite_island(this, island_code: str) -> response:
        z = this.client.get(f'https://www.fortnite.com/creative/island-codes/{island_code}', headers = this.get_headers2(), cookies = this.cookies, allow_redirects=True)
        print(z.text, z.content)
        return z
    
    def fortnite_island(this, island_code: str) -> response:
        z = this.client.get(f'https://www.fortnite.com/creative/island-codes/{island_code}', headers = this.get_headers2(), cookies = this.cookies, allow_redirects=True)
        print(z.text, z.content)
        return z
    
    def fortnite_island1(this, island_code: str) -> response:
        z = this.client.get(
            f'https://www.fortnite.com/creative/island-codes/{island_code}',
            headers={
                'user-agent': this.userAgent
                },
            cookies=this.cookies,
            allow_redirects=True
        )
        
        print(f"Response status code: {z.status_code}")
        return z.text
    
    def fortnite_creator(this, creator: str) -> response:
        z = this.client.get(
            f'https://www.fortnite.com/@{creator}',
            headers={
                'user-agent': this.userAgent
                },
            cookies=this.cookies,
            allow_redirects=True
        )
        
        print(f"Response status code: {z.status_code}")
        return z.text
    
    def stats(this, url) -> response:
        z = this.client.get(
            url=url,
            headers={
                'user-agent': this.userAgent
                },
            cookies=this.cookies,
            allow_redirects=True
        )
        
        # Print the response status
        print(f"Response status code: {z.status_code}")
        
        return z.text

