// 场景配置
const SCENES = {
    scene1: {
        name: "初始空地",
        physicalWidth: 33.333,
        offsetX: 0,
        offsetY: -40,
        imagePath: "img/grassland.png",
        xDirection: 'x-',
        yDirection: 'y-',
        reverseXY: true,
    },
    scene2: {
        name: "烂漫花田",
        physicalWidth: 24.806,
        offsetX: -62.015,
        offsetY: 20.672,
        imagePath: "img/flowergarden.png",
        xDirection: 'x-',
        yDirection: 'y-',
        reverseXY: true,
    },
    scene3: {
        name: "心愿沙滩",
        physicalWidth: 20.513,
        offsetX: 0,
        offsetY: 80,
        imagePath: "img/beach.png",
        xDirection: 'x+',
        yDirection: 'y-',
        reverseXY: false,
    },
    scene4: {
        name: "忘却之所",
        physicalWidth: 21.333,
        offsetX: 0,
        offsetY: -106.667,
        imagePath: "img/memorialplace.png",
        xDirection: 'x+',
        yDirection: 'y-',
        reverseXY: false,
    }
};

// 站点到场景映射
const SITE_TO_SCENE = {
    "初始空地": "scene1",
    "烂漫花田": "scene2",
    "心愿沙滩": "scene3",
    "忘却之所": "scene4"
};

// 采集点颜色配置
const FIXTURE_COLORS = {
    111: '#f9f9f9',
    112: '#f9f9f9',
    1001: '#da6d42',
    1002: '#da6d42',
    1003: '#da6d42',
    1004: '#da6d42',
    2001: '#878685',
    2002: '#d5750a',
    2003: '#d5d5d5',
    2004: '#a7c7cb',
    2005: '#9933cc',
    2006: '#878685',
    3001: '#c95a49',
    4001: '#f8729a',
    4002: '#f8729a',
    4003: '#f8729a',
    4004: '#f8729a',
    4005: '#f8729a',
    4006: '#f8729a',
    4007: '#f8729a',
    4008: '#f8729a',
    4009: '#f8729a',
    4010: '#f8729a',
    4011: '#f8729a',
    4012: '#f8729a',
    4013: '#f8729a',
    4014: '#f8729a',
    4015: '#f8729a',
    4016: '#f8729a',
    4017: '#f8729a',
    5001: '#f6f5f2',
    5002: '#f6f5f2',
    5003: '#f6f5f2',
    5004: '#f6f5f2',
    5101: '#f6f5f2',
    5102: '#f6f5f2',
    5103: '#f6f5f2',
    5104: '#f6f5f2',
    6001: '#6f4e37',
    7001: '#a5d9ff',
    8001: '#f8729a',
    8002: '#f8729a'
};

// 物品纹理映射
const ITEM_TEXTURES = {
    mysekai_material: {
        "1": "./icon/Texture2D/item_wood_1.png",
        "2": "./icon/Texture2D/item_wood_2.png",
        "3": "./icon/Texture2D/item_wood_3.png",
        "4": "./icon/Texture2D/item_wood_4.png",
        "5": "./icon/Texture2D/item_wood_5.png",
        "6": "./icon/Texture2D/item_mineral_1.png",
        "7": "./icon/Texture2D/item_mineral_2.png",
        "8": "./icon/Texture2D/item_mineral_3.png",
        "9": "./icon/Texture2D/item_mineral_4.png",
        "10": "./icon/Texture2D/item_mineral_5.png",
        "11": "./icon/Texture2D/item_mineral_6.png",
        "12": "./icon/Texture2D/item_mineral_7.png",
        "13": "./icon/Texture2D/item_junk_1.png",
        "14": "./icon/Texture2D/item_junk_2.png",
        "15": "./icon/Texture2D/item_junk_3.png",
        "16": "./icon/Texture2D/item_junk_4.png",
        "17": "./icon/Texture2D/item_junk_5.png",
        "18": "./icon/Texture2D/item_junk_6.png",
        "19": "./icon/Texture2D/item_junk_7.png",
        "20": "./icon/Texture2D/item_plant_1.png",
        "21": "./icon/Texture2D/item_plant_2.png",
        "22": "./icon/Texture2D/item_plant_3.png",
        "23": "./icon/Texture2D/item_plant_4.png",
        "24": "./icon/Texture2D/item_tone_8.png",
        "32": "./icon/Texture2D/item_junk_8.png",
        "33": "./icon/Texture2D/item_mineral_8.png",
        "34": "./icon/Texture2D/item_junk_9.png",
        "35": "./icon/Texture2D/item_memoria_1.png",
        "36": "./icon/Texture2D/item_memoria_2.png",
        "37": "./icon/Texture2D/item_memoria_3.png",
        "38": "./icon/Texture2D/item_memoria_4.png",
        "39": "./icon/Texture2D/item_memoria_5.png",
        "40": "./icon/Texture2D/item_memoria_6.png",
        "41": "./icon/Texture2D/item_memoria_7.png",
        "42": "./icon/Texture2D/item_memoria_8.png",
        "43": "./icon/Texture2D/item_memoria_9.png",
        "44": "./icon/Texture2D/item_memoria_10.png",
        "45": "./icon/Texture2D/item_memoria_11.png",
        "46": "./icon/Texture2D/item_memoria_12.png",
        "47": "./icon/Texture2D/item_memoria_13.png",
        "48": "./icon/Texture2D/item_memoria_14.png",
        "49": "./icon/Texture2D/item_memoria_15.png",
        "50": "./icon/Texture2D/item_memoria_16.png",
        "51": "./icon/Texture2D/item_memoria_17.png",
        "52": "./icon/Texture2D/item_memoria_18.png",
        "53": "./icon/Texture2D/item_memoria_19.png",
        "54": "./icon/Texture2D/item_memoria_20.png",
        "55": "./icon/Texture2D/item_memoria_21.png",
        "56": "./icon/Texture2D/item_memoria_22.png",
        "57": "./icon/Texture2D/item_memoria_23.png",
        "58": "./icon/Texture2D/item_memoria_24.png",
        "59": "./icon/Texture2D/item_memoria_25.png",
        "60": "./icon/Texture2D/item_memoria_26.png",
        "61": "./icon/Texture2D/item_junk_10.png",
        "62": "./icon/Texture2D/item_junk_11.png",
        "63": "./icon/Texture2D/item_junk_12.png",
        "64": "./icon/Texture2D/item_mineral_9.png",
        "65": "./icon/Texture2D/item_mineral_10.png",
        "66": "./icon/Texture2D/item_junk_13.png",
        "72": "./icon/Texture2D/item_birthday_flower_6.png",
        "93": "./icon/Texture2D/item_junk_14.png",
    },
    mysekai_item: {
        "1": "./icon/Texture2D/item_blank_blueprint.png",
        "2": "./icon/Texture2D/item_surplus_blueprint.png",
        "5": "./icon/Texture2D/item_surplus_music_record.png",
        "6": "./icon/Texture2D/item_photofilm.png",
        "7": "./icon/Texture2D/item_blueprint_fragment.png",
    },
    mysekai_fixture: {
        "118": "./icon/Texture2D/mdl_non1001_before_sapling1_118.png",
        "119": "./icon/Texture2D/mdl_non1001_before_sapling1_119.png",
        "120": "./icon/Texture2D/mdl_non1001_before_sapling1_120.png",
        "121": "./icon/Texture2D/mdl_non1001_before_sapling1_121.png",
        "126": "./icon/Texture2D/mdl_non1001_before_sprout1_126.png",
        "127": "./icon/Texture2D/mdl_non1001_before_sprout1_127.png",
        "128": "./icon/Texture2D/mdl_non1001_before_sprout1_128.png",
        "129": "./icon/Texture2D/mdl_non1001_before_sprout1_129.png",
        "130": "./icon/Texture2D/mdl_non1001_before_sprout1_130.png",
        "474": "./icon/Texture2D/mdl_non1001_before_sprout1_474.png",
        "475": "./icon/Texture2D/mdl_non1001_before_sprout1_475.png",
        "476": "./icon/Texture2D/mdl_non1001_before_sprout1_476.png",
        "477": "./icon/Texture2D/mdl_non1001_before_sprout1_477.png",
        "478": "./icon/Texture2D/mdl_non1001_before_sprout1_478.png",
        "479": "./icon/Texture2D/mdl_non1001_before_sprout1_479.png",
        "480": "./icon/Texture2D/mdl_non1001_before_sprout1_480.png",
        "481": "./icon/Texture2D/mdl_non1001_before_sprout1_481.png",
        "482": "./icon/Texture2D/mdl_non1001_before_sprout1_482.png",
        "483": "./icon/Texture2D/mdl_non1001_before_sprout1_483.png"
    },
    mysekai_music_record: {},
    mysekai_blueprint: {}
};

// 稀有物品配置
const RARE_ITEM = {
    mysekai_material: [11, 32, 33, 34, 61, 62, 63],
    mysekai_item: [7],
    mysekai_fixture: [118, 119, 120],
    mysekai_music_record: [],
    mysekai_blueprint: []
};

const SUPER_RARE_ITEM = {
    mysekai_material: [5, 12, 20, 24, 64, 65],
    mysekai_item: [],
    mysekai_fixture: [121],
    mysekai_music_record: [],
    mysekai_blueprint: []
};

// 代理配置
const PROXY_CONFIG = {
    proxies: [
        'https://api.codetabs.com/v1/proxy?quest=',
        'https://corsproxy.io/?url=',
    ],
    currentProxyIndex: 0,
    getCurrentProxy: function() {
        return this.proxies[this.currentProxyIndex];
    },
    nextProxy: function() {
        this.currentProxyIndex = (this.currentProxyIndex + 1) % this.proxies.length;
        return this.getCurrentProxy();
    },
    setCustomProxy: function(customUrl) {
        if (customUrl && !this.proxies.includes(customUrl)) {
            this.proxies.unshift(customUrl);
            this.currentProxyIndex = 0;
        }
    }
};