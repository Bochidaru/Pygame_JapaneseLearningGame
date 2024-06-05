import asyncio
import json
import platform
import sys
from urllib.parse import urlencode

INFO_GITHUB_LINK = "https://tank-king.github.io/projects/games/bug_invaders.json"


class WASMFetch:
    """
    WASM compatible request handler
    auto-detects emscripten environment and sends requests using JavaScript Fetch API
    """
    GET = 'GET'
    POST = 'POST'
    _js_code = ''
    _init = False

    def __init__(self):
        self.is_web = True if sys.platform == 'emscripten' else False
        if not self._init:
            self.init()
        self.debug = True
        self.get_result = None
        self.post_result = None
        self.domain = "null"
        if not self.is_web:
            try:
                import requests
                self.requests = requests
                try:
                    self.domain = requests.get(INFO_GITHUB_LINK, timeout=0.1).json()['leaderboard_url']
                except requests.ReadTimeout:
                    pass
                except requests.RequestException:
                    pass
            except ImportError:
                print('lol')
                pass
        else:
            self.window.eval('window.get_response = "null";')
            self.window.eval('window.post_response = "null";')
            self.window.eval('window.domain = "null"')
            self.window.eval(
                'window.http_get = function(url){ window.get_response = "loading"; fetch(url).then( function(response) {return response.json();}).then(function(data) { window.get_response = JSON.stringify(data);}).catch(function(err) { window.get_response = err; });}')
            self.window.eval(
                """window.http_post = function(url, data){ window.post_response = "loading"; fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json',}, body: JSON.stringify(data)}).then( function(response) {return response.json();}).then(function(data) { window.post_response = JSON.stringify(data);}).catch(function(err) { window.post_response = err; });}""")

            self.window.eval(
                """fetch(" """ + INFO_GITHUB_LINK + """ ").then(function(response){return response.json();}).then(function(data) {window.domain = data.leaderboard_url}).catch(function(err) {window.domain = err})""")

    def init(self):
        self.is_web = sys.platform in ('emscripten', 'wasi')
        # if self.is_web:
        #     platform.document.body.style.background = "#511309"

    @property
    def window(self):
        if self.is_web:
            return platform.window

    def get_domain(self):
        if self.is_web:
            return self.window.domain
        else:
            return self.domain

    @staticmethod
    def print(*args, default=True):
        try:
            for i in args:
                platform.window.console.log(i)
        except AttributeError:
            pass
        except Exception as e:
            return e
        if default:
            print(*args)

    # GET --------------------------------------------------------------------------------------------------------------
    async def pygbag_get(self, url, params=None, doseq=False):
        self.get_request(url, params, doseq)
        while self.get_response() == 'loading':
            await asyncio.sleep(0)
        return self.get_response()

    def get_request(self, url, params=None, doseq=False):
        if params is None:
            params = {}
        if self.is_web:
            query_string = urlencode(params, doseq=doseq)
            final_url = url + "?" + query_string
            self.window.eval(f'window.http_get("{final_url}")')
        else:
            self.get_result = self.requests.get(url, params=params).text
        return self.get_result

    def get_response(self):
        if self.is_web:
            return self.window.get_response
        else:
            return self.get_result

    # POST -------------------------------------------------------------------------------------------------------------
    async def pygbag_post(self, url, data=None):
        self.post_request(url, data)
        while self.post_response() == 'loading':
            await asyncio.sleep(0)
        return self.post_response

    def post_request(self, url, data=None):
        if data is None:
            data = {}
        if self.is_web:
            self.window.eval(f'window.http_post(\'{url}\', {json.dumps(data)})')
            print(json.dumps(data))
        else:
            self.post_result = self.requests.post(url, data).text
        return self.post_result

    def post_response(self):
        if self.is_web:
            return self.window.post_response
        else:
            return self.post_result


# async def main():
#     fetch = WASMFetch()
#     post_response = await fetch.pygbag_post("https://scoreunlocked.pythonanywhere.com/leaderboards/post/", data={
#         'developer': 'minhphuong04',
#         'leaderboard': 'japanese-typing-katakana',
#         'name': 'kienle198',
#         'score': '1000000',
#         'validation_data': ''})
#     print(post_response)
#     get_response = await fetch.pygbag_get("https://scoreunlocked.pythonanywhere.com/leaderboards/get", params={
#         'developer': 'minhphuong04',
#         'leaderboard': 'japanese-typing-hiragana'})
#     data = json.loads(get_response)
#     print(data)
#     leaderboard = data['leaderboard']
#     for name, score in leaderboard:
#         print(f'{name}: {score}')
#
# asyncio.run(main())
