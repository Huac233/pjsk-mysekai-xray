# run this file with the following command:
# pip install loguru msgspec msgpack pycryptodome
# python mysekai_analyzer.py /path/to/your/mysekai_file

# Fill these two thing first with format like: b'put_string_here' 
AES_KEY = b'THE_KEY'
AES_IV = b'THE_IV'

import os, sys
import argparse

from msgpack import packb, unpackb
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

import json, textwrap, time, base64
from pathlib import Path
from typing import List, Optional

from loguru import logger
import msgspec
from msgspec import Struct as BaseModel

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss.SSSSSS}</green> | <level>{message}</level>")

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
        
        # 直接处理每个地图数据，不使用 msgspec
        for i, map_data in enumerate(harvest_maps_data):
            # 确保有 mysekaiSiteId
            if "mysekaiSiteId" not in map_data:
                continue
                
            site_id = map_data["mysekaiSiteId"]
            site_name = SITE_ID.get(site_id, f"未知站点 {site_id}")
            
            mp_detail = []
            
            # 处理 fixtures
            fixtures = map_data.get("userMysekaiSiteHarvestFixtures", [])
            for fixture in fixtures:
                if fixture.get("userMysekaiSiteHarvestFixtureStatus") == "spawned":
                    mp_detail.append({
                        "location": (fixture.get("positionX", 0), fixture.get("positionZ", 0)),
                        "fixtureId": fixture.get("mysekaiSiteHarvestFixtureId", 0),
                        "reward": {}
                    })
            
            # 处理 resource drops
            drops = map_data.get("userMysekaiSiteHarvestResourceDrops", [])
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
                    
                    #检查是否是重要物品
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
                    
                    break
            
            processed_map[site_name] = mp_detail
        
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

def process_mysekai_file(file_path: str):
    """处理mysekai文件"""
    
    try:
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
       
        decrypted_data = decrypt(file_content, AES_KEY, AES_IV)
        unpacked_data = unmsgpack(decrypted_data)
        
        # 解析地图数据
        result, rare_items = parse_map(unpacked_data)
        
        # 输出结果
        logger.info("| Find Harvest Maps Info")
        
        for k, v in result.items():
            logger.info(f"| Site: {k} \n {json.dumps(v)}")

        if rare_items:
            logger.info("=" * 60)
            logger.info("重要掉落物发现！")
            logger.info("=" * 60)
            for item in rare_items:
                logger.info(f"地图: {item['site_name']}")
                logger.info(f"位置: {item['location']}")
                logger.info(f"采集点: {item['fixture_id']}")
                logger.info(f"物品: {item['item_name']} (ID: {item['item_id']})")
                logger.info(f"数量: {item['quantity']}")
                logger.info("-" * 40)
        else:
            logger.info("未发现重要掉落物")
            
        return result, rare_items
        
    except Exception as e:
        logger.error(f"处理文件时发生错误: {e}")
        raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='解析mysekai文件')
    parser.add_argument('file', nargs='?', default='mysekai', 
                       help='mysekai文件路径 (默认: mysekai)')
    args = parser.parse_args()
    
    file_path = args.file
    
    # 检查文件是否存在
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
