# run this file with the following command:
# pip install loguru msgspec msgpack pycryptodome
# python mysekai_analyzer.py /path/to/your/mysekai_file

# Fill these two thing first with format like: b'put_string_here' 
AES_KEY = b"THE_KEY"
AES_IV = b"THE_IV"

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
    'mysekai_material': [5, 12, 20, 24, 64, 65],
    'mysekai_item': [],
    'mysekai_fixture': [121],
    'mysekai_music_record': []
}

RARE_ITEM = {
    'mysekai_material': [11, 32, 33, 34, 61, 62, 63],
    'mysekai_item': [7],
    'mysekai_fixture': [118, 119, 120],
    'mysekai_music_record': []
}

ITEM_NAMES = {
    'mysekai_material': {
        5: "夕桐",
        12: "钻石", 
        20: "四叶草",
        24: "空白的音色", 
        64: "雷光石", 
        65: "彩虹玻璃",
        11: "闪耀石英",
        32: "日光石",
        33: "月光石",
        34: "流星碎片",
        61: "最棒斧子的柄",
        62: "最棒斧子的斧刃",
        63: "最棒十字镐的镐尖"
    },
    'mysekai_item': {
        7: "设计图碎片"
    },
    'mysekai_fixture': {
        121: "夕桐的树苗",
        118: "阔叶树的树苗",
        119: "针叶树的树苗",
        120: "棕榈树的树苗"
    },
    'mysekai_music_record': {}
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
        
        # 获取已解锁的唱片ID列表
        unlocked_music_ids = set()
        if "userMysekaiMusicRecords" in user_data["updatedResources"]:
            for record in user_data["updatedResources"]["userMysekaiMusicRecords"]:
                unlocked_music_ids.add(record["mysekaiMusicRecordId"])
        
        processed_map = {}
        rare_items_found = []  # 存储稀有物品
        super_rare_items_found = []  # 存储超级稀有物品
        music_records_found = []  # 存储发现的唱片
        
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
                    
                    # 检查是否是超级稀有物品
                    if (resource_type in SUPER_RARE_ITEM and 
                        int(resource_id) in SUPER_RARE_ITEM[resource_type]):
                        item_name = ITEM_NAMES.get(resource_type, {}).get(
                            int(resource_id), 
                            f"未知{resource_type} {resource_id}"
                        )
                        super_rare_items_found.append({
                            'site_name': site_name,
                            'location': pos,
                            'fixture_id': mp_detail[i]["fixtureId"],
                            'item_type': resource_type,
                            'item_id': int(resource_id),
                            'item_name': item_name,
                            'quantity': quantity
                        })
                    
                    # 检查是否是稀有物品
                    if (resource_type in RARE_ITEM and 
                        int(resource_id) in RARE_ITEM[resource_type]):
                        item_name = ITEM_NAMES.get(resource_type, {}).get(
                            int(resource_id), 
                            f"未知{resource_type} {resource_id}"
                        )
                        rare_items_found.append({
                            'site_name': site_name,
                            'location': pos,
                            'fixture_id': mp_detail[i]["fixtureId"],
                            'item_type': resource_type,
                            'item_id': int(resource_id),
                            'item_name': item_name,
                            'quantity': quantity
                        })
                    
                    # 检查是否是唱片
                    if resource_type == "mysekai_music_record":
                        music_id = int(resource_id)
                        item_name = ITEM_NAMES.get(resource_type, {}).get(
                            music_id, 
                            f"歌曲{music_id}"
                        )
                        is_unlocked = music_id in unlocked_music_ids
                        music_records_found.append({
                            'site_name': site_name,
                            'location': pos,
                            'fixture_id': mp_detail[i]["fixtureId"],
                            'music_id': music_id,
                            'music_name': item_name,
                            'quantity': quantity,
                            'is_unlocked': is_unlocked
                        })
                    
                    break
            
            processed_map[site_name] = mp_detail
        
        # 返回处理后的地图数据、稀有物品、超级稀有物品和唱片信息
        return processed_map, rare_items_found, super_rare_items_found, music_records_found
        
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
        result, rare_items, super_rare_items, music_records = parse_map(unpacked_data)
        
        # 输出结果
        logger.info("| Find Harvest Maps Info")
        
        for k, v in result.items():
            logger.info(f"| Site: {k} \n {json.dumps(v)}")

        # 新增：显示唱片信息
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

        # 统计并显示各地图稀有物品数量
        if rare_items:
            logger.info("=" * 60)
            logger.info("稀有物品统计")
            logger.info("=" * 60)
            
            # 按地图分组统计
            site_rare_counts = {}
            for item in rare_items:
                site_name = item['site_name']
                if site_name not in site_rare_counts:
                    site_rare_counts[site_name] = {}
                
                item_key = f"{item['item_name']}(ID:{item['item_id']})"
                if item_key not in site_rare_counts[site_name]:
                    site_rare_counts[site_name][item_key] = 0
                site_rare_counts[site_name][item_key] += item['quantity']
            
            # 显示统计结果
            for site_name, items in site_rare_counts.items():
                logger.info(f"地图: {site_name}")
                total_count = sum(items.values())
                logger.info(f"  稀有物品总数: {total_count}")
                for item_name, count in items.items():
                    logger.info(f"  - {item_name}: {count}个")
                logger.info("-" * 40)
        else:
            logger.info("未发现稀有物品")

        # 超级稀有物品显示
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
            
        return result, rare_items, super_rare_items, music_records
        
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