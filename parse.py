import json
from pathlib import Path

from typing import List, Optional

import msgspec
from msgspec import Struct as BaseModel

import httpx

MYSEKAI_PROFILE_JSON_PATH: Path = Path("mysekai.json")

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

mysekaifixture = httpx.get("https://github.com/Sekai-World/sekai-master-db-diff/blob/main/mysekaiFixtures.json").text()
# mysekaifixture = Path("db/mysekaiFixtures.json").read_text(encoding="utf-8")

FIXTURE = msgspec.json.decode(mysekaifixture, type=List[ModelItem])


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


SITE_ID = {
    1: "マイホーム",
    2: "1F",
    3: "2F",
    4: "3F",
    5: "さいしょの原っぱ",
    6: "願いの砂浜",
    7: "彩りの花畑",
    8: "忘れ去られた場所",
}



class ItemDetail(BaseModel):
    id: int
    seq: int
    mysekaiItemType: str
    name: str
    pronunciation: str
    description: str
    iconAssetbundleName: str

mysekaiitems = httpx.get("https://github.com/Sekai-World/sekai-master-db-diff/raw/refs/heads/main/mysekaiItems.json").text()
# mysekaiitems = Path("db/mysekaiitems.json").read_text(encoding="utf-8")

ITEMS = msgspec.json.decode(mysekaiitems, type=List[ItemDetail])


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

mysekaimetarials = httpx.get("https://github.com/Sekai-World/sekai-master-db-diff/raw/refs/heads/main/mysekaiMaterials.json").text()
# mysekaimetarials = Path("db/mysekaiMaterials.json").read_text(encoding="utf-8")

METERIALS = msgspec.json.decode(mysekaimetarials, type=List[MaterialDetail])


class HarvestObjectDetail(BaseModel):
    id: int
    mysekaiSiteHarvestFixtureType: str
    hp: int
    lastAttackStamina: int
    mysekaiSiteHarvestFixtureRarityType: str
    assetbundleName: str

mysekaisiteharvestfixtures = httpx.get("https://github.com/Sekai-World/sekai-master-db-diff/raw/refs/heads/main/mysekaiSiteHarvestFixtures.json").text()
# mysekaimetarials = Path("db/mysekaiSiteHarvestFixtures.json").read_text(encoding="utf-8")

HARVEST_OBJECTS = msgspec.json.decode(mysekaimetarials, type=List[HarvestObjectDetail])


user_data = msgspec.json.decode(MYSEKAI_PROFILE_JSON_PATH.read_text(encoding="utf-8"))

assert user_data["updatedResources"]["userMysekaiHarvestMaps"]

harvest_maps: List[Map] = [ 
    msgspec.json.decode(msgspec.json.encode(mp), type=Map) for mp in user_data["updatedResources"]["userMysekaiHarvestMaps"]
]

for mp in harvest_maps:
    mp.siteName = SITE_ID[mp.mysekaiSiteId]

processed_map = {}
for mp in harvest_maps:
    print(f"Site: {mp.siteName}")
    mp_detail = []
    for fixture in mp.userMysekaiSiteHarvestFixtures:
        #  spawned
        #  harvested
        if fixture.userMysekaiSiteHarvestFixtureStatus == "spawned":
            mp_detail.append( 
                {
                    "location": (fixture.positionX, fixture.positionZ),
                    "fixtureId": fixture.mysekaiSiteHarvestFixtureId,
                    "reward": {}
                }
            )
        
    for drop in mp.userMysekaiSiteHarvestResourceDrops:
        pos = (drop.positionX, drop.positionZ)
        for i in range(0, len(mp_detail)):
            if mp_detail[i]["location"] != pos:
                continue
            
            # mysekai_material
            # mysekai_item
            # mysekai_fixture
            # mysekai_music_record
            mp_detail[i]["reward"].setdefault(drop.resourceType, {})
            mp_detail[i]["reward"][drop.resourceType][drop.resourceId] = \
                mp_detail[i]["reward"][drop.resourceType].get(drop.resourceId, 0) + drop.quantity
            break

    print(json.dumps(mp_detail))
