# run this file with the following command:
# pip install loguru msgspec msgpack pycryptodome
# python mysekai_analyzer.py /path/to/your/mysekai_file
# mysekai_analyzer.py
import os
import sys
import argparse
import json
import subprocess
from pathlib import Path

from msgpack import unpackb
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from loguru import logger
import msgspec
from msgspec import Struct

# Fill these two thing first with format like: b"put_string_here" 
AES_KEY = b"THE_KEY"
AES_IV = b"THE_IV"

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss.SSSSSS}</green> | <level>{message}</level>")

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
    """解析地图数据，提取稀有物品和唱片信息"""
    if "updatedResources" not in user_data or "userMysekaiHarvestMaps" not in user_data["updatedResources"]:
        raise ValueError("Missing required data structure")
    
    harvest_maps_data = user_data["updatedResources"]["userMysekaiHarvestMaps"]
    
    unlocked_music_ids = set()
    if "userMysekaiMusicRecords" in user_data["updatedResources"]:
        for record in user_data["updatedResources"]["userMysekaiMusicRecords"]:
            unlocked_music_ids.add(record["mysekaiMusicRecordId"])
    
    processed_map = {}
    rare_items_found = []
    super_rare_items_found = []
    music_records_found = []
    
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
                
                break
        
        processed_map[site_name] = mp_detail
    
    return processed_map, rare_items_found, super_rare_items_found, music_records_found

def unmsgpack(data: bytes) -> dict:
    return unpackb(data, strict_map_key=False) if len(data) > 0 else {}

def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), 16)
    return plaintext

def start_http_server():
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
    
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    webbrowser.open(f"http://localhost:8000")
    print("浏览器已自动打开，HTTP服务器在新控制台中运行")

def process_mysekai_file(file_path: str):
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
       
        decrypted_data = decrypt(file_content, AES_KEY, AES_IV)
        unpacked_data = unmsgpack(decrypted_data)
        
        result, rare_items, super_rare_items, music_records = parse_map(unpacked_data)
        
        logger.info("| Find Harvest Maps Info")
        
        for k, v in result.items():
            logger.info(f"| Site: {k} \n {json.dumps(v)}")

        if music_records:
            logger.info("=" * 60)
            logger.info("唱片发现")
            logger.info("=" * 60)
            for record in music_records:
                status = "[已获取]" if record['is_unlocked'] else "[新歌曲]"
                logger.info(f"{status}: {record['music_name']} (ID: {record['music_id']})")
                logger.info(f"  地图: {record['site_name']}")
                logger.info(f"  位置: {record['location']}")
                logger.info(f"  采集点: {record['fixture_id']}")
                logger.info(f"  数量: {record['quantity']}")
                logger.info("-" * 40)
        else:
            logger.info("未发现唱片")

        if rare_items:
            logger.info("=" * 60)
            logger.info("稀有物品统计")
            logger.info("=" * 60)
            
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
                logger.info(f"地图: {site_name}")
                total_count = sum(items.values())
                logger.info(f"  稀有物品总数: {total_count}")
                for item_name, count in items.items():
                    logger.info(f"  - {item_name}: {count}个")
                logger.info("-" * 40)
        else:
            logger.info("未发现稀有物品")

        if super_rare_items:
            logger.info("=" * 60)
            logger.info("重要掉落物发现！")
            logger.info("=" * 60)
            for item in super_rare_items:
                logger.info(f"地图: {item['site_name']}")
                logger.info(f"位置: {item['location']}")
                logger.info(f"采集点: {item['fixture_id']}")
                logger.info(f"物品: {item['item_name']} (ID: {item['item_id']})")
                logger.info(f"数量: {item['quantity']}")
                logger.info("-" * 40)
        else:
            logger.info("未发现重要掉落物")
        
        start_http_server()
            
        return result, rare_items, super_rare_items, music_records
        
    except Exception as e:
        logger.error(f"处理文件时发生错误: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='解析mysekai文件')
    parser.add_argument('file', nargs='?', default='mysekai', help='mysekai文件路径 (默认: mysekai)')
    args = parser.parse_args()
    
    file_path = args.file
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        sys.exit(1)
    
    try:
        process_mysekai_file(file_path)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()