# run this file with the following command:
# pip install loguru msgspec msgpack mitmproxy pycryptodome
# mitmweb --mode wireguard -s parse.py --set ignore_hosts=icloud.com.cn --set ignore_hosts=apple.com

# Fill these two thing first with format like: b'put_string_here' 
AES_KEY = b"THE_KEY"
AES_IV = b"THE_IV"

# You don't need to modify the following code if you don't care about it.
# assert AES_KEY == b'THE_KEY', "Please find and fill the AES_KEY by yourself!"
# assert AES_KEY == b'THE_IV', "Please find and fill the AES_IV by yourself!"

import os, sys

import mitmproxy.http
import mitmproxy.udp
import mitmproxy.tcp
import mitmproxy.dns
from msgpack import packb, unpackb
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

import asyncio

import json, textwrap, time, base64
from pathlib import Path
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE

from loguru import logger


import json
from pathlib import Path

from typing import List, Optional

import msgspec
from msgspec import Struct as BaseModel


class GridSize(BaseModel):
    width: int
    depth: int
    height: int


class MysekaiFixtureTagGroup(BaseModel):
    id: int
    mysekaiFixtureTagId1: int
    mysekaiFixtureTagId2: Optional[int] = None
    mysekaiFixtureTagId3: Optional[int] = None


class ModelItem(BaseModel, kw_only=True):
    id: int
    mysekaiFixtureType: str
    name: str
    pronunciation: str
    flavorText: str
    seq: int
    gridSize: GridSize
    mysekaiFixtureMainGenreId: Optional[int] = None
    mysekaiFixtureSubGenreId: Optional[int] = None
    mysekaiFixtureHandleType: str
    mysekaiSettableSiteType: str
    mysekaiSettableLayoutType: str
    mysekaiFixturePutType: str
    mysekaiFixtureAnotherColors: List
    mysekaiFixturePutSoundId: int
    mysekaiFixtureFootstepId: Optional[int] = None
    mysekaiFixtureTagGroup: Optional[MysekaiFixtureTagGroup] = None
    isAssembled: bool
    isDisassembled: bool
    mysekaiFixturePlayerActionType: str
    isGameCharacterAction: bool
    assetbundleName: str



class UserMysekaiSiteHarvestFixture(BaseModel):
    mysekaiSiteHarvestFixtureId: int
    positionX: int
    positionZ: int
    hp: int
    userMysekaiSiteHarvestFixtureStatus: str


class UserMysekaiSiteHarvestResourceDrop(BaseModel):
    resourceType: str
    resourceId: int
    positionX: int
    positionZ: int
    hp: int
    seq: int
    mysekaiSiteHarvestResourceDropStatus: str
    quantity: int


class Map(BaseModel, kw_only=True):
    mysekaiSiteId: int
    siteName: Optional[str] = None
    userMysekaiSiteHarvestFixtures: List[UserMysekaiSiteHarvestFixture]
    userMysekaiSiteHarvestResourceDrops: List[UserMysekaiSiteHarvestResourceDrop]

SUPER_RARE_ITEM = {
    'mysekai_material': [5, 12, 20, 24],  # 夕桐、钻石、四叶草、空白的音色
    'mysekai_item': [], 
    'mysekai_fixture': [],
    'mysekai_music_record': []
}

ITEM_NAMES = {
    5: "夕桐",
    12: "钻石", 
    20: "四叶草",
    24: "空白的音色"
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

class ItemDetail(BaseModel):
    id: int
    seq: int
    mysekaiItemType: str
    name: str
    pronunciation: str
    description: str
    iconAssetbundleName: str




class MaterialDetail(BaseModel, kw_only=True):
    id: int
    seq: int
    mysekaiMaterialType: str
    name: str
    pronunciation: str
    description: str
    mysekaiMaterialRarityType: str
    iconAssetbundleName: str
    modelAssetbundleName: Optional[str] = None
    mysekaiSiteIds: List[int]
    mysekaiPhenomenaGroupId: Optional[int] = None




class HarvestObjectDetail(BaseModel):
    id: int
    mysekaiSiteHarvestFixtureType: str
    hp: int
    lastAttackStamina: int
    mysekaiSiteHarvestFixtureRarityType: str
    assetbundleName: str



def parse_map(user_data: dict):
    try:
        # 检查必要的数据结构
        if "updatedResources" not in user_data or "userMysekaiHarvestMaps" not in user_data["updatedResources"]:
            raise ValueError("Missing 'updatedResources' or 'userMysekaiHarvestMaps' in response data")
        
        harvest_maps_data = user_data["updatedResources"]["userMysekaiHarvestMaps"]
        
        processed_map = {}
        rare_items_found = []  # 新增：存储重要掉落物
        
        print(f"开始处理 {len(harvest_maps_data)} 个地图数据")
        
        # 直接处理每个地图数据，不使用 msgspec
        for i, map_data in enumerate(harvest_maps_data):
            # 确保有 mysekaiSiteId
            if "mysekaiSiteId" not in map_data:
                print(f"警告: 跳过第 {i} 个缺少 mysekaiSiteId 的地图数据")
                print(f"该数据包含的字段: {list(map_data.keys())}")
                continue
                
            site_id = map_data["mysekaiSiteId"]
            site_name = SITE_ID.get(site_id, f"未知站点 {site_id}")
            
            print(f"处理站点 {i+1}: {site_name} (ID: {site_id})")
            
            # 调试信息
            fixtures_count = len(map_data.get("userMysekaiSiteHarvestFixtures", []))
            drops_count = len(map_data.get("userMysekaiSiteHarvestResourceDrops", []))
            print(f"  - 有 {fixtures_count} 个fixtures, {drops_count} 个resource drops")
            
            mp_detail = []
            
            # 处理 fixtures
            fixtures = map_data.get("userMysekaiSiteHarvestFixtures", [])
            spawned_count = 0
            for fixture in fixtures:
                if fixture.get("userMysekaiSiteHarvestFixtureStatus") == "spawned":
                    mp_detail.append({
                        "location": (fixture.get("positionX", 0), fixture.get("positionZ", 0)),
                        "fixtureId": fixture.get("mysekaiSiteHarvestFixtureId", 0),
                        "reward": {}
                    })
                    spawned_count += 1
            
            print(f"  - 其中 {spawned_count} 个是 spawned 状态")
            
            # 处理 resource drops
            drops = map_data.get("userMysekaiSiteHarvestResourceDrops", [])
            matched_drops = 0
            for drop in drops:
                pos = (drop.get("positionX", 0), drop.get("positionZ", 0))
                for i in range(len(mp_detail)):
                    if mp_detail[i]["location"] != pos:
                        continue
                    
                    resource_type = drop.get("resourceType", "")
                    resource_id = drop.get("resourceId", 0)
                    quantity = drop.get("quantity", 0)
                    
                    mp_detail[i]["reward"].setdefault(resource_type, {})
                    mp_detail[i]["reward"][resource_type][resource_id] = \
                        mp_detail[i]["reward"][resource_type].get(resource_id, 0) + quantity
                    
                    # 新增：检查是否是重要物品 - 修复类型检查
                    if (resource_type in SUPER_RARE_ITEM and 
                        int(resource_id) in SUPER_RARE_ITEM[resource_type]):
                        item_name = ITEM_NAMES.get(int(resource_id), f"未知物品 {resource_id}")
                        rare_items_found.append({
                            'site_name': site_name,
                            'location': pos,
                            'fixture_id': mp_detail[i]["fixtureId"],
                            'item_type': resource_type,
                            'item_id': int(resource_id),
                            'item_name': item_name,
                            'quantity': quantity
                        })
                    
                    matched_drops += 1
                    break
            
            print(f"  - 成功匹配 {matched_drops} 个resource drops到fixtures")
            
            processed_map[site_name] = mp_detail
        
        print(f"处理完成，共解析 {len(processed_map)} 个站点")
        
        # 新增：返回重要掉落物信息
        return processed_map, rare_items_found
        
    except Exception as e:
        # 保存错误数据以便调试
        try:
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"error_data_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=4)
            print(f"错误数据已保存到: {filename}")
        except:
            pass
        
        raise RuntimeError(f"解析失败: {e}")


def unmsgpack(data: bytes) -> dict:
    return unpackb(data, strict_map_key=False) if len(data) > 0 else {}

def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext: bytes = unpad(cipher.decrypt(ciphertext), 16)
    return plaintext

def encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ciphertext: bytes = cipher.encrypt(pad(plaintext, 16))
    return ciphertext

class Inspector:
    def __init__(self):
        logger.remove()
        self.log = logger.opt(colors=True)
        self.raw_log = logger
        self.process = Popen([
            sys.executable, "-c", textwrap.dedent("""
                import sys
                sys.stdout.reconfigure(encoding='utf-8')
                for line in sys.stdin: # poor man's `cat`
                    sys.stderr.write(line)
                    sys.stderr.flush()
                """)],
            stdin = PIPE, 
            bufsize = 1, 
            universal_newlines = True,
            creationflags = CREATE_NEW_CONSOLE
        )
        logger.add(self.process.stdin,colorize=True, format="<green>{time:HH:mm:ss.SSSSSS}</green> <level>{message}</level>")
    
    def done(self):
        self.log.stop()
        self.process.communicate("bye\n")

    def response(self, flow: mitmproxy.http.HTTPFlow):
        print(flow.request.host_header)
        if flow.request.url.find("isForceAllReloadOnlyMysekai") == -1:
            return
        
        def process():
            self.log.info(f"<blue><b>[HTTP]</b></blue> <fg 128,128,128><b>{flow.request.method}</b></fg 128,128,128>: <C> {flow.request.url} </C>")
            self.log.info(f"| Request Raw: {flow.request.content[:100]}")
            try:
                req_decrypted = unmsgpack(decrypt(flow.request.content, AES_KEY, AES_IV))
                self.log.info(f"| Request Decrypted: {req_decrypted}")
            except:
                req_decrypted = base64.b64encode(flow.request.content).decode()
                self.log.info(f"| Unable to decrypted Request : {req_decrypted}")
            
            self.raw_log.info(f"| Response Raw: {flow.response.content[:100]}")
            try:
                res_decrypted = unmsgpack(decrypt(flow.response.content, AES_KEY, AES_IV))
                self.raw_log.info(f"| Response Decrypted: {str(res_decrypted)[:300]}")
            except:
                res_decrypted = base64.b64encode(flow.response.content).decode()
                self.raw_log.info(f"| Unable to decrypted Response: {str(res_decrypted)[:300]}")
                return

            mysekai_info = res_decrypted
            self.raw_log.info(str(mysekai_info.keys()))
            if "updatedResources" not in mysekai_info.keys() or \
                "userMysekaiHarvestMaps" not in mysekai_info["updatedResources"].keys():
                return
            
            self.raw_log.info(f"| Find Harvest Maps Info")
            
            # 修改：接收parse_map返回的重要掉落物信息
            result, rare_items = parse_map(mysekai_info)
            
            for k, v in result.items():
                self.raw_log.info(f"| Site: {k} \n {json.dumps(v)}")

            if rare_items:
                self.raw_log.info("=" * 60)
                self.raw_log.info("重要掉落物发现！")
                self.raw_log.info("=" * 60)
                for item in rare_items:
                    self.raw_log.info(f"地图: {item['site_name']}")
                    self.raw_log.info(f"位置: {item['location']}")
                    self.raw_log.info(f"采集点: {item['fixture_id']}")
                    self.raw_log.info(f"物品: {item['item_name']} (ID: {item['item_id']})")
                    self.raw_log.info(f"数量: {item['quantity']}")
                    self.raw_log.info("-" * 40)
            else:
                self.raw_log.info("未发现重要掉落物")
        
        asyncio.create_task(asyncio.to_thread(process))
        
addons = [
    Inspector()
]


