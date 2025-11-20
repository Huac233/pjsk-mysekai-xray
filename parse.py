# run this file with the following command:
# pip install loguru msgspec msgpack mitmproxy pycryptodome
# mitmweb --mode wireguard -s parse.py --set ignore_hosts=icloud.com.cn --set ignore_hosts=apple.com
import os
import sys
import asyncio
import json
import base64
import io
from pathlib import Path
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE

import mitmproxy.http
from msgpack import unpackb
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from loguru import logger
import msgspec
from msgspec import Struct

# Fill these two thing first with format like: b"put_string_here" 
AES_KEY = b"THE_KEY"
AES_IV = b"THE_IV"

class GridSize(Struct):
    width: int
    depth: int
    height: int

class MysekaiFixtureTagGroup(Struct):
    id: int
    mysekaiFixtureTagId1: int
    mysekaiFixtureTagId2: int = None
    mysekaiFixtureTagId3: int = None

class ModelItem(Struct, kw_only=True):
    id: int
    mysekaiFixtureType: str
    name: str
    pronunciation: str
    flavorText: str
    seq: int
    gridSize: GridSize
    mysekaiFixtureMainGenreId: int = None
    mysekaiFixtureSubGenreId: int = None
    mysekaiFixtureHandleType: str
    mysekaiSettableSiteType: str
    mysekaiSettableLayoutType: str
    mysekaiFixturePutType: str
    mysekaiFixtureAnotherColors: list
    mysekaiFixturePutSoundId: int
    mysekaiFixtureFootstepId: int = None
    mysekaiFixtureTagGroup: MysekaiFixtureTagGroup = None
    isAssembled: bool
    isDisassembled: bool
    mysekaiFixturePlayerActionType: str
    isGameCharacterAction: bool
    assetbundleName: str

class UserMysekaiSiteHarvestFixture(Struct):
    mysekaiSiteHarvestFixtureId: int
    positionX: int
    positionZ: int
    hp: int
    userMysekaiSiteHarvestFixtureStatus: str

class UserMysekaiSiteHarvestResourceDrop(Struct):
    resourceType: str
    resourceId: int
    positionX: int
    positionZ: int
    hp: int
    seq: int
    mysekaiSiteHarvestResourceDropStatus: str
    quantity: int

SUPER_RARE_ITEM = {
    'mysekai_material': [5, 12, 20, 24, 64, 65],
    'mysekai_item': [],
    'mysekai_fixture': [121],
    'mysekai_music_record': [],
    'mysekai_blueprint': []
}

RARE_ITEM = {
    'mysekai_material': [11, 32, 33, 34, 61, 62, 63],
    'mysekai_item': [7],
    'mysekai_fixture': [118, 119, 120],
    'mysekai_music_record': [],
    'mysekai_blueprint': []
}

ITEM_NAMES = {
    'mysekai_material': {
        5: "夕桐",
        12: "钻石", 
        20: "四叶草",
        24: "空白的音色",
        11: "闪耀石英",
        32: "蓝天海玻璃",
        33: "月光石",
        34: "流星碎片",
        61: "雪之结晶",
        62: "最棒斧子的斧刃",
        63: "最棒十字镐的镐尖", 
        64: "雷光石", 
        65: "彩虹玻璃"
    },
    'mysekai_item': {
        7: "设计图碎片"
    },
    'mysekai_fixture': {
        118: "阔叶树的树苗",
        119: "针叶树的树苗",
        120: "热带树的树苗",
        121: "夕桐的树苗"
    },
    'mysekai_music_record': {},
    'mysekai_blueprint': {}
}

SITE_ID = {
    1: "マイホーム",
    2: "1F",
    3: "2F",
    4: "3F",
    5: "初始空地",
    6: "心愿沙滩",
    7: "烂漫花田",
    8: "忘却之所",
}

def parse_map(user_data: dict):
    """解析地图数据，提取稀有物品、唱片和设计图纸信息"""
    if "updatedResources" not in user_data or "userMysekaiHarvestMaps" not in user_data["updatedResources"]:
        raise ValueError("Missing required data structure")
    
    harvest_maps_data = user_data["updatedResources"]["userMysekaiHarvestMaps"]
    
    unlocked_music_ids = set()
    if "userMysekaiMusicRecords" in user_data["updatedResources"]:
        for record in user_data["updatedResources"]["userMysekaiMusicRecords"]:
            unlocked_music_ids.add(record["mysekaiMusicRecordId"])
    
    unlocked_blueprint_ids = set()
    if "userMysekaiBlueprints" in user_data["updatedResources"]:
        for blueprint in user_data["updatedResources"]["userMysekaiBlueprints"]:
            unlocked_blueprint_ids.add(blueprint["mysekaiBlueprintId"])
    
    processed_map = {}
    rare_items_found = []
    super_rare_items_found = []
    music_records_found = []
    blueprints_found = []
    
    for map_data in harvest_maps_data:
        if "mysekaiSiteId" not in map_data:
            continue
            
        site_id = map_data["mysekaiSiteId"]
        site_name = SITE_ID.get(site_id, f"未知站点 {site_id}")
        
        mp_detail = []
        
        fixtures = map_data.get("userMysekaiSiteHarvestFixtures", [])
        for fixture in fixtures:
            if fixture.get("userMysekaiSiteHarvestFixtureStatus") == "spawned":
                mp_detail.append({
                    "location": (fixture.get("positionX", 0), fixture.get("positionZ", 0)),
                    "fixtureId": fixture.get("mysekaiSiteHarvestFixtureId", 0),
                    "reward": {}
                })
        
        drops = map_data.get("userMysekaiSiteHarvestResourceDrops", [])
        for drop in drops:
            pos = (drop.get("positionX", 0), drop.get("positionZ", 0))
            for item in mp_detail:
                if item["location"] != pos:
                    continue
                
                resource_type = drop.get("resourceType", "")
                resource_id = drop.get("resourceId", 0)
                quantity = drop.get("quantity", 0)
                
                item["reward"].setdefault(resource_type, {})
                item["reward"][resource_type][resource_id] = item["reward"][resource_type].get(resource_id, 0) + quantity
                
                if (resource_type in SUPER_RARE_ITEM and int(resource_id) in SUPER_RARE_ITEM[resource_type]):
                    item_name = ITEM_NAMES.get(resource_type, {}).get(int(resource_id), f"未知{resource_type} {resource_id}")
                    super_rare_items_found.append({
                        'site_name': site_name,
                        'location': pos,
                        'fixture_id': item["fixtureId"],
                        'item_type': resource_type,
                        'item_id': int(resource_id),
                        'item_name': item_name,
                        'quantity': quantity
                    })
                
                if (resource_type in RARE_ITEM and int(resource_id) in RARE_ITEM[resource_type]):
                    item_name = ITEM_NAMES.get(resource_type, {}).get(int(resource_id), f"未知{resource_type} {resource_id}")
                    rare_items_found.append({
                        'site_name': site_name,
                        'location': pos,
                        'fixture_id': item["fixtureId"],
                        'item_type': resource_type,
                        'item_id': int(resource_id),
                        'item_name': item_name,
                        'quantity': quantity
                    })
                
                if resource_type == "mysekai_music_record":
                    music_id = int(resource_id)
                    item_name = ITEM_NAMES.get(resource_type, {}).get(music_id, f"歌曲{music_id}")
                    is_unlocked = music_id in unlocked_music_ids
                    music_records_found.append({
                        'site_name': site_name,
                        'location': pos,
                        'fixture_id': item["fixtureId"],
                        'music_id': music_id,
                        'music_name': item_name,
                        'quantity': quantity,
                        'is_unlocked': is_unlocked
                    })
                
                if resource_type == "mysekai_blueprint":
                    blueprint_id = int(resource_id)
                    is_unlocked = blueprint_id in unlocked_blueprint_ids
                    blueprints_found.append({
                        'site_name': site_name,
                        'location': pos,
                        'fixture_id': item["fixtureId"],
                        'blueprint_id': blueprint_id,
                        'quantity': quantity,
                        'is_unlocked': is_unlocked
                    })
                
                break
        
        processed_map[site_name] = mp_detail
    
    return processed_map, rare_items_found, super_rare_items_found, music_records_found, blueprints_found

def unmsgpack(data: bytes) -> dict:
    return unpackb(data, strict_map_key=False) if len(data) > 0 else {}

def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), 16)
    return plaintext

def copy_log_to_clipboard(log_content):
    """将日志内容复制到粘贴板"""
    try:
        import pyperclip
        pyperclip.copy(log_content)
        print("日志内容已复制到粘贴板")
    except ImportError:
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(log_content)
            win32clipboard.CloseClipboard()
            print("日志内容已复制到粘贴板")
        except ImportError:
            print("无法复制到粘贴板，请安装pyperclip或pywin32模块")

def start_http_server():
    import subprocess
    import webbrowser
    
    cmd = [sys.executable, "-c", """
import http.server
import socketserver
import signal
import sys

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def signal_handler(sig, frame):
    print("\\n正在关闭服务器...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class MyTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"HTTP服务器已启动: http://localhost:{PORT}")

try:
    with MyTCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\n服务器已关闭")
    sys.exit(0)
"""]

    subprocess.Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
    webbrowser.open(f"http://localhost:8000")
    print("浏览器已自动打开，HTTP服务器在新控制台中运行")

class Inspector:
    def __init__(self):
        logger.remove()
        self.log = logger.opt(colors=True)
        self.raw_log = logger
        self.process = Popen([
            sys.executable, "-c", """
import sys
sys.stdout.reconfigure(encoding='utf-8')
for line in sys.stdin:
    sys.stderr.write(line)
    sys.stderr.flush()
"""],
            stdin=PIPE, 
            bufsize=1, 
            universal_newlines=True,
            creationflags=CREATE_NEW_CONSOLE
        )
        logger.add(self.process.stdin, colorize=True, format="<green>{time:HH:mm:ss.SSSSSS}</green> <level>{message}</level>")
        self.server_started = False
    
    def done(self):
        self.log.stop()
        self.process.communicate("bye\n")

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.request.url.find("isForceAllReloadOnlyMysekai") == -1:
            return
        
        async def process():
            log_buffer = io.StringIO()
            handler_id = logger.add(log_buffer, format="{time:HH:mm:ss.SSSSSS} | {message}")
            
            self.log.info(f"<blue><b>[HTTP]</b></blue> <fg 128,128,128><b>{flow.request.method}</b></fg 128,128,128>: <C> {flow.request.url} </C>")
            
            try:
                req_decrypted = unmsgpack(decrypt(flow.request.content, AES_KEY, AES_IV))
                self.log.info(f"| Request Decrypted: {req_decrypted}")
            except:
                req_decrypted = base64.b64encode(flow.request.content).decode()
                self.log.info(f"| Unable to decrypt Request: {req_decrypted}")
            
            self.raw_log.info(f"| Response Raw: {flow.response.content[:100]}")
            try:
                res_decrypted = unmsgpack(decrypt(flow.response.content, AES_KEY, AES_IV))
                self.raw_log.info(f"| Response Decrypted: {str(res_decrypted)[:300]}")
            except:
                res_decrypted = base64.b64encode(flow.response.content).decode()
                self.raw_log.info(f"| Unable to decrypt Response: {str(res_decrypted)[:300]}")
                logger.remove(handler_id)
                return

            mysekai_info = res_decrypted
            if "updatedResources" not in mysekai_info.keys() or "userMysekaiHarvestMaps" not in mysekai_info["updatedResources"].keys():
                logger.remove(handler_id)
                return
            
            self.raw_log.info("| Find Harvest Maps Info")
            
            result, rare_items, super_rare_items, music_records, blueprints = parse_map(mysekai_info)
            
            for k, v in result.items():
                self.raw_log.info(f"| Site: {k} \n {json.dumps(v)}")

            if music_records:
                self.raw_log.info("=" * 60)
                self.raw_log.info("唱片发现")
                self.raw_log.info("=" * 60)
                for record in music_records:
                    status = "[已获取]" if record['is_unlocked'] else "[新歌曲]"
                    self.raw_log.info(f"{status}: {record['music_name']} (ID: {record['music_id']})")
                    self.raw_log.info(f"  地图: {record['site_name']}")
                    self.raw_log.info(f"  位置: {record['location']}")
                    self.raw_log.info(f"  采集点: {record['fixture_id']}")
                    self.raw_log.info(f"  数量: {record['quantity']}")
                    self.raw_log.info("-" * 40)

            if blueprints:
                self.raw_log.info("=" * 60)
                self.raw_log.info("设计图纸发现")
                self.raw_log.info("=" * 60)
                for blueprint in blueprints:
                    status = "[已获取]" if blueprint['is_unlocked'] else "[新图纸]"
                    self.raw_log.info(f"{status}: 设计图纸 ID: {blueprint['blueprint_id']}")
                    self.raw_log.info(f"  地图: {blueprint['site_name']}")
                    self.raw_log.info(f"  位置: {blueprint['location']}")
                    self.raw_log.info(f"  采集点: {blueprint['fixture_id']}")
                    self.raw_log.info(f"  数量: {blueprint['quantity']}")
                    self.raw_log.info("-" * 40)

            if rare_items:
                self.raw_log.info("=" * 60)
                self.raw_log.info("稀有物品统计")
                self.raw_log.info("=" * 60)
                
                site_rare_counts = {}
                for item in rare_items:
                    site_name = item['site_name']
                    if site_name not in site_rare_counts:
                        site_rare_counts[site_name] = {}
                    
                    item_key = f"{item['item_name']}(ID:{item['item_id']})"
                    if item_key not in site_rare_counts[site_name]:
                        site_rare_counts[site_name][item_key] = 0
                    site_rare_counts[site_name][item_key] += item['quantity']
                
                for site_name, items in site_rare_counts.items():
                    self.raw_log.info(f"地图: {site_name}")
                    total_count = sum(items.values())
                    self.raw_log.info(f"  稀有物品总数: {total_count}")
                    for item_name, count in items.items():
                        self.raw_log.info(f"  - {item_name}: {count}个")
                    self.raw_log.info("-" * 40)
            else:
                self.raw_log.info("未发现稀有物品")

            if super_rare_items:
                self.raw_log.info("=" * 60)
                self.raw_log.info("重要掉落物发现！")
                self.raw_log.info("=" * 60)
                for item in super_rare_items:
                    self.raw_log.info(f"地图: {item['site_name']}")
                    self.raw_log.info(f"位置: {item['location']}")
                    self.raw_log.info(f"采集点: {item['fixture_id']}")
                    self.raw_log.info(f"物品: {item['item_name']} (ID: {item['item_id']})")
                    self.raw_log.info(f"数量: {item['quantity']}")
                    self.raw_log.info("-" * 40)
            else:
                self.raw_log.info("未发现重要掉落物")
            
            log_content = log_buffer.getvalue()
            copy_log_to_clipboard(log_content)
            logger.remove(handler_id)
            
            if not self.server_started:
                self.server_started = True
                await asyncio.to_thread(start_http_server)
        
        asyncio.create_task(process())
        
addons = [Inspector()]