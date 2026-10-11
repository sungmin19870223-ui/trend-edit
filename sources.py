# -*- coding: utf-8 -*-
"""
매체 등록부 (Source Registry)

- section : global_fashion(해외 패션) / korea_fashion(국내 패션) / lifestyle(종합 트렌드)
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

    # ── 종합 트렌드 ─────────────────────────────────────────
    {"id": "time",         "name": "TIME",             "section": "lifestyle", "region": "US", "lang": "en", "site": "https://time.com",                 "feed": "https://time.com/feed/"},
    {"id": "verge",        "name": "The Verge",        "section": "lifestyle", "region": "US", "lang": "en", "site": "https://www.theverge.com",         "feed": "https://www.theverge.com/rss/index.xml"},
    {"id": "hodinkee",     "name": "Hodinkee",         "section": "lifestyle", "region": "US", "lang": "en", "site": "https://www.hodinkee.com",         "feed": "https://www.hodinkee.com/articles/rss.xml"},
    {"id": "robb",         "name": "Robb Report",      "section": "lifestyle", "region": "US", "lang": "en", "site": "https://robbreport.com",           "feed": "https://robbreport.com/feed/"},
    {"id": "coolhunting",  "name": "Cool Hunting",     "section": "lifestyle", "region": "US", "lang": "en", "site": "https://coolhunting.com",          "feed": "https://coolhunting.com/feed/"},
    {"id": "wallpaper",    "name": "Wallpaper*",       "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.wallpaper.com",        "feed": "https://www.wallpaper.com/feeds/all"},
    {"id": "monocle",      "name": "Monocle",          "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://monocle.com",              "feed": "https://monocle.com/feed/"},
    {"id": "dezeen",       "name": "Dezeen",           "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.dezeen.com",           "feed": "https://www.dezeen.com/feed/"},
    {"id": "designboom",   "name": "designboom",       "section": "lifestyle", "region": "EU", "lang": "en", "site": "https://www.designboom.com",       "feed": "https://www.designboom.com/feed/"},
]
