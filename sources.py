# -*- coding: utf-8 -*-
"""
매체 등록부 (Source Registry)

- section : global_fashion(해외 패션) / korea_fashion(국내 패션·매거진) / lifestyle(라이프스타일)
            korea_culture(국내 문화·엔터) / korea_current(국내 시사)
- retention : (선택) 보관 일수. 하루 수십~수백 건씩 나오는 일간지·통신사는 짧게 둬 데이터 크기를 관리한다.
- region  : 국가별 비교에 쓰는 '보도 매체의 소재지' (KR / US / JP / EU)
- feed    : 공식 RSS 주소. None 이면 '수집 불가 매체'로 표시만 하고 링크만 제공한다.
- note    : 수집 불가 사유 등 메모

RSS 응답 여부는 2026-10-11 실제 요청으로 확인했다. 매체 사정으로 바뀔 수 있으므로
collect.py 실행 결과의 '매체 현황' 탭에서 매번 상태를 다시 확인한다.
"""

SOURCES = [
    # ── 해외 패션 ───────────────────────────────────────────
    {"id": "vogue",        "name": "Vogue",            "section": "global_fashion", "region": "US", "lang": "en", "site": "https://www.vogue.com",            "feed": "https://www.vogue.com/feed/rss"},
    {"id": "gq",           "name": "GQ",               "section": "global_fashion", "region": "US", "lang": "en", "site": "https://www.gq.com",               "feed": "https://www.gq.com/feed/rss"},
    {"id": "hypebeast",    "name": "Hypebeast",        "section": "global_fashion", "region": "US", "lang": "en", "site": "https://hypebeast.com",            "feed": "https://hypebeast.com/feed"},
    {"id": "wwd",          "name": "WWD",              "section": "global_fashion", "region": "US", "lang": "en", "site": "https://wwd.com",                  "feed": "https://wwd.com/feed/"},
    {"id": "bof",          "name": "Business of Fashion", "section": "global_fashion", "region": "EU", "lang": "en", "site": "https://www.businessoffashion.com", "feed": "https://www.businessoffashion.com/arc/outboundfeeds/rss/"},
    {"id": "highsnobiety", "name": "Highsnobiety",     "section": "global_fashion", "region": "EU", "lang": "en", "site": "https://www.highsnobiety.com",     "feed": "https://www.highsnobiety.com/feed/"},
    {"id": "dazed",        "name": "Dazed",            "section": "global_fashion", "region": "EU", "lang": "en", "site": "https://www.dazeddigital.com",     "feed": "https://www.dazeddigital.com/rss"},
    {"id": "hypebeast_jp", "name": "Hypebeast Japan",  "section": "global_fashion", "region": "JP", "lang": "ja", "site": "https://hypebeast.com/jp",         "feed": "https://hypebeast.com/jp/feed"},
    {"id": "fashionsnap",  "name": "FASHIONSNAP",      "section": "global_fashion", "region": "JP", "lang": "ja", "site": "https://www.fashionsnap.com",      "feed": "https://www.fashionsnap.com/rss.xml"},
    {"id": "popeye",       "name": "POPEYE",           "section": "global_fashion", "region": "JP", "lang": "ja", "site": "https://popeyemagazine.jp",        "feed": "https://popeyemagazine.jp/feed/"},

    # ── 국내 패션 ───────────────────────────────────────────
    {"id": "vogue_kr",     "name": "보그 코리아",       "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.vogue.co.kr",          "feed": "https://www.vogue.co.kr/feed/"},
    {"id": "wkorea",       "name": "W Korea",          "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.wkorea.com",           "feed": "https://www.wkorea.com/feed/"},
    {"id": "gq_kr",        "name": "GQ 코리아",         "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.gqkorea.co.kr",        "feed": "https://www.gqkorea.co.kr/feed/"},
    {"id": "esquire_kr",   "name": "에스콰이어 코리아",  "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.esquirekorea.co.kr",   "feed": "https://www.esquirekorea.co.kr/rss"},
    {"id": "elle_kr",      "name": "엘르 코리아",       "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.elle.co.kr",           "feed": "https://www.elle.co.kr/rss"},
    {"id": "bazaar_kr",    "name": "하퍼스 바자 코리아", "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.harpersbazaar.co.kr",  "feed": "https://www.harpersbazaar.co.kr/rss"},
    {"id": "allure_kr",    "name": "얼루어 코리아",      "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.allurekorea.com",      "feed": "https://www.allurekorea.com/feed/"},
    {"id": "hypebeast_kr", "name": "Hypebeast Korea",  "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://hypebeast.kr",             "feed": "https://hypebeast.kr/feed"},
    {"id": "ktnews",       "name": "한국섬유신문",       "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.ktnews.com",           "feed": "https://www.ktnews.com/rss/allArticle.xml"},
    {"id": "musinsa",      "name": "무신사 매거진",      "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.musinsa.com",          "feed": None,
     "note": "공개 RSS/API 없음 (2026-10-11 확인). 자동 수집하지 않고 링크만 제공."},
    # 2026-11-17 추가 (국내 월간 매거진)
    {"id": "marie_kr",     "name": "마리끌레르 코리아",  "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.marieclairekorea.com", "feed": "https://www.marieclairekorea.com/feed/"},
    {"id": "cosmo_kr",     "name": "코스모폴리탄 코리아", "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.cosmopolitan.co.kr",   "feed": "https://www.cosmopolitan.co.kr/rss"},
    {"id": "dazed_kr",     "name": "데이즈드 코리아",    "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.dazedkorea.com",       "feed": "https://www.dazedkorea.com/rss"},
    {"id": "noblesse",     "name": "노블레스",          "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.noblesse.com",         "feed": "https://www.noblesse.com/rss"},
    {"id": "arena_kr",     "name": "아레나 옴므 플러스", "section": "korea_fashion", "region": "KR", "lang": "ko", "site": "https://www.arenakorea.com",       "feed": None,
     "note": "RSS 주소 응답 없음 (2026-11-17 확인). 링크만 제공."},

    # ── 국내 문화·엔터 (2026-11-17 추가) ───────────────────
    {"id": "yna_culture",  "name": "연합뉴스 문화",      "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.yna.co.kr/culture",    "feed": "https://www.yna.co.kr/rss/culture.xml", "retention": 14},
    {"id": "donga_culture","name": "동아일보 문화",      "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.donga.com/news/Culture", "feed": "https://rss.donga.com/culture.xml", "retention": 14},
    {"id": "chosun_culture","name": "조선일보 문화·라이프", "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.chosun.com/culture-life/", "feed": "https://www.chosun.com/arc/outboundfeeds/rss/category/culture-life/?outputType=xml", "retention": 14},
    {"id": "khan_culture", "name": "경향신문 문화",      "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.khan.co.kr/culture",   "feed": "https://www.khan.co.kr/rss/rssdata/culture_news.xml", "retention": 14},
    {"id": "mk_culture",   "name": "매일경제 문화",      "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.mk.co.kr/news/culture/", "feed": "https://www.mk.co.kr/rss/30000023/", "retention": 14},
    {"id": "mhns",         "name": "문화뉴스",          "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.mhns.co.kr",           "feed": "https://www.mhns.co.kr/rss/allArticle.xml", "retention": 14},
    {"id": "ize",          "name": "아이즈(ize)",       "section": "korea_culture", "region": "KR", "lang": "ko", "site": "https://www.ize.co.kr",            "feed": "https://www.ize.co.kr/rss/allArticle.xml", "retention": 14},
    {"id": "cine21",       "name": "씨네21",            "section": "korea_culture", "region": "KR", "lang": "ko", "site": "http://www.cine21.com",            "feed": None,
     "note": "공개 RSS가 비어 있음 (2026-11-17 확인). 링크만 제공."},

    # ── 국내 시사 (2026-11-17 추가) ─────────────────────────
    {"id": "sisajournal",  "name": "시사저널",          "section": "korea_current", "region": "KR", "lang": "ko", "site": "https://www.sisajournal.com",      "feed": "https://www.sisajournal.com/rss/allArticle.xml", "retention": 14},
    {"id": "weekly_khan",  "name": "주간경향",          "section": "korea_current", "region": "KR", "lang": "ko", "site": "https://weekly.khan.co.kr",        "feed": "https://weekly.khan.co.kr/rss/rssdata/total_news.xml", "retention": 14},
    {"id": "mediatoday",   "name": "미디어오늘",        "section": "korea_current", "region": "KR", "lang": "ko", "site": "https://www.mediatoday.co.kr",     "feed": "https://www.mediatoday.co.kr/rss/allArticle.xml", "retention": 14},
    {"id": "sisain",       "name": "시사IN",            "section": "korea_current", "region": "KR", "lang": "ko", "site": "https://www.sisain.co.kr",         "feed": None,
     "note": "공개 RSS가 2024년 6월 이후 갱신되지 않음 (2026-11-17 확인). 링크만 제공."},
    {"id": "h21",          "name": "한겨레21",          "section": "korea_current", "region": "KR", "lang": "ko", "site": "https://h21.hani.co.kr",           "feed": None,
     "note": "RSS에 발행일이 없어 게시 기준을 충족하지 못함 (2026-11-17 확인). 링크만 제공."},

    # ── 종합 트렌드 ─────────────────────────────────────────
    {"id": "time",         "name": "TIME",             "section": "lifestyle", "region": "US", "lang": "en", "site": "https://time.com",                 "feed": "https://time.com/feed/"},
    {"id": "verge",        "name": "The Verge",        "section": "lifestyle", "region": "US", "lang": "en", "site": "https://www.theverge.com",         "feed": "https://www.theverge.com/rss/index.xml"},
    {"id": "hodinkee",     "name": "Hodinkee",         "section": "lifestyle", "region": "US", "lang": "en", "site": "https://www.hodinkee.com",         "feed": "https://www.hodinkee.com/articles/rss.xml"},
    {"id": "robb",         "name": "Robb Report",      "section": "lifestyle", "region": "US", "lang": "en", "site": "https://robbreport.com",           "feed": "https://robbreport.com/feed/"},
    {"id": "coolhunting",  "name": "Cool Hunting",     "section": "lifestyle", "region": "US", "lang": "en", "site": "https://coolhunting.com",          "feed": "https://coolhunting.com/feed/"},
    {"id": "wallpaper",    "name": "Wallpaper*",       "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.wallpaper.com",        "feed": "https://www.wallpaper.com/feeds/all"},
    {"id": "monocle",      "name": "Monocle",          "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://monocle.com",              "feed": "https://monocle.com/feed/"},
    {"id": "dezeen",       "name": "Dezeen",           "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.dezeen.com",           "feed": "https://www.dezeen.com/feed/"},
    # 국내 라이프스타일 (2026-11-17 추가)
    {"id": "theedit",      "name": "디에디트",          "section": "lifestyle", "region": "KR", "lang": "ko", "site": "https://the-edit.co.kr",           "feed": "https://the-edit.co.kr/feed"},
    {"id": "mdesign",      "name": "월간 디자인",        "section": "lifestyle", "region": "KR", "lang": "ko", "site": "https://mdesign.designhouse.co.kr", "feed": "https://mdesign.designhouse.co.kr/rss"},
    {"id": "travelnbike",  "name": "트래블바이크뉴스",    "section": "lifestyle", "region": "KR", "lang": "ko", "site": "https://www.travelnbike.com",      "feed": "https://www.travelnbike.com/rss/allArticle.xml", "retention": 30},
    {"id": "designboom",   "name": "designboom",       "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.designboom.com",       "feed": "https://www.designboom.com/feed/"},
]
