# -*- coding: utf-8 -*-
"""
THE TREND EDIT — 수집·분석 엔진

실행:  python collect.py            (RSS 수집 → 분류 → 분석 → data/data.js 생성)
옵션:  python collect.py --no-ai    (ANTHROPIC_API_KEY 가 있어도 AI 요약을 건너뜀)

처리 순서
  1) sources.py 의 공식 RSS 를 순서대로 요청 (매체별 성공/실패 상태 기록)
  2) 제목·링크·발행일·대표 이미지·미리보기 문구만 저장 (기사 전문은 저장하지 않음)
  3) 발행일을 확인할 수 없는 항목은 게시하지 않음
  4) 관심사 태그·브랜드 자동 분류, 비슷한 제목끼리 묶어 중복 통합
  5) 트렌드 랭킹·브랜드 증감·국가별 비교·일간/주간/월간 리포트 계산
  6) (선택) ANTHROPIC_API_KEY 가 있으면 해외 기사 한국어 요약·키워드, 리포트 해설 생성
  7) data/store.json(누적 저장소) 과 data/data.js(대시보드용) 저장

외부 라이브러리 없이 파이썬 표준 라이브러리만 사용한다.
"""
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from sources import SOURCES
from taxonomy import BRANDS, TAGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORE_PATH = os.path.join(DATA_DIR, "store.json")
OUTPUT_JS = os.path.join(DATA_DIR, "data.js")

RETENTION_DAYS = 90          # 아카이브 보관 기간
SNIPPET_LEN = 220            # 미리보기 문구 최대 길이 (전문 복제 방지)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendEditReader/1.0 (personal RSS reader)"
KST = timezone(timedelta(hours=9))

# AI 설정 (키가 없으면 자동으로 꺼짐)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
SUMMARY_MODEL = os.environ.get("TREND_SUMMARY_MODEL", "claude-haiku-5-5")
REPORT_MODEL = os.environ.get("TREND_REPORT_MODEL", "claude-sonnet-5-5")
AI_MAX_NEW_PER_RUN = 120     # 한 번 실행에 요약할 최대 기사 수 (비용 상한)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


# ─────────────────────────────────────────────────────────────
# 1. 수집
# ─────────────────────────────────────────────────────────────
def fetch(url, timeout=40, retries=2):
    """해외 서버(GitHub Actions)에서 국내 매체는 응답이 느릴 수 있어 대기 시간을 넉넉히 두고 1회 재시도."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return res.read()
        except urllib.error.HTTPError:
            raise  # 403 등 차단은 재시도해도 같으므로 바로 실패 처리
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(3)


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def first_img_src(raw_html):
    if not raw_html:
        return None
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", raw_html, flags=re.I)
    return html.unescape(m.group(1)) if m else None


def parse_date(text):
    """RFC822(RSS) 또는 ISO8601(Atom) 날짜를 UTC datetime 으로. 실패하면 None."""
    if not text:
        return None
    text = text.strip()
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def text_of(el, path):
    found = el.find(path, NS)
    return found.text if found is not None and found.text else ""


def parse_feed(raw, source):
    """RSS 2.0 / Atom 을 공통 형식의 기사 목록으로 변환."""
    # 일부 피드의 잘못된 제어문자 제거
    raw = re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", raw).lstrip()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        if "unbound prefix" not in str(e):
            raise
        # 선언 없이 쓰인 네임스페이스 접두어(일부 국내 매체 피드)를 임시로 선언하고 다시 파싱
        declared = set(re.findall(rb"xmlns:([\w\-]+)=", raw))
        used = set(re.findall(rb"</?([A-Za-z][\w\-]*):[A-Za-z]", raw)) - declared - {b"xml"}
        known = {k.encode(): v.encode() for k, v in NS.items()}
        decl = b"".join(b' xmlns:%s="%s"' % (p, known.get(p, b"urn:x-" + p)) for p in used)
        raw = re.sub(rb"<(rss|feed)\b", lambda m: m.group(0) + decl, raw, count=1)
        root = ET.fromstring(raw)
    items = root.findall(".//item")
    is_atom = False
    if not items:
        items = root.findall(".//atom:entry", NS)
        is_atom = True
    if not items and root.tag.lower() == "html":
        raise ValueError("RSS가 아닌 HTML 페이지가 응답함")

    out = []
    for it in items:
        if is_atom:
            title = text_of(it, "atom:title")
            link_el = it.find("atom:link[@rel='alternate']", NS)
            if link_el is None:
                link_el = it.find("atom:link", NS)
            link = link_el.get("href") if link_el is not None else ""
            date = parse_date(text_of(it, "atom:published") or text_of(it, "atom:updated"))
            desc_raw = text_of(it, "atom:summary") or text_of(it, "atom:content")
        else:
            title = text_of(it, "title")
            link = text_of(it, "link").strip() or text_of(it, "guid").strip()
            date = parse_date(text_of(it, "pubDate") or text_of(it, "dc:date"))
            desc_raw = text_of(it, "description") or text_of(it, "content:encoded")

        # 대표 이미지: media:content → media:thumbnail → enclosure → 본문 첫 이미지
        img = None
        for path in ("media:content", "media:group/media:content", "media:thumbnail"):
            el = it.find(path, NS)
            if el is not None and el.get("url") and (el.get("medium") in (None, "image") or "image" in (el.get("type") or "image")):
                img = el.get("url")
                break
        if not img:
            enc = it.find("enclosure")
            if enc is not None and "image" in (enc.get("type") or ""):
                img = enc.get("url")
        if not img:
            img = first_img_src(desc_raw) or first_img_src(text_of(it, "content:encoded"))
        if img and img.startswith("//"):
            img = "https:" + img
        if img and not img.startswith("http"):
            img = None

        title = strip_html(title)
        link = (link or "").strip()
        if not title or not link.startswith("http"):
            continue
        out.append({
            "title": title,
            "url": link,
            "date": date,
            "img": img,
            "snippet": strip_html(desc_raw)[:SNIPPET_LEN],
            "source": source["id"],
        })
    return out


def collect_source(source):
    """매체 1곳 수집. (기사 목록, 상태 dict) 반환."""
    status = {"id": source["id"], "ok": False, "fetched": 0, "skipped_no_date": 0, "error": None}
    if not source.get("feed"):
        status["error"] = source.get("note") or "RSS 없음"
        return [], status
    try:
        items = parse_feed(fetch(source["feed"]), source)
    except Exception as e:  # 네트워크·파싱 오류는 매체 상태에만 기록하고 계속 진행
        status["error"] = f"{type(e).__name__}: {str(e)[:120]}"
        return [], status
    now = datetime.now(timezone.utc)
    valid = []
    for a in items:
        # 발행일이 없거나 하루 이상 미래인 항목은 '검증되지 않은 정보'로 보고 제외
        if a["date"] is None or a["date"] > now + timedelta(days=1):
            status["skipped_no_date"] += 1
            continue
        valid.append(a)
    status.update(ok=True, fetched=len(valid))
    return valid, status


# ─────────────────────────────────────────────────────────────
# 2. 분류 (태그·브랜드)
# ─────────────────────────────────────────────────────────────
def _compile_tag_patterns():
    compiled = []
    for tag_id, _label, words in TAGS:
        parts = []
        for w in words:
            if re.search(r"[A-Za-z]", w):
                parts.append(r"(?<![A-Za-z])" + re.escape(w.strip()) + r"(?![A-Za-z])")
            else:
                parts.append(re.escape(w))
        compiled.append((tag_id, re.compile("|".join(parts), re.I)))
    return compiled


def _compile_brand_patterns():
    compiled = []
    for name, en, local in BRANDS:
        parts = [r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])" for w in en]
        parts += [re.escape(w) for w in local]
        compiled.append((name, re.compile("|".join(parts))))  # 대소문자 구분
    return compiled


TAG_PATTERNS = _compile_tag_patterns()
BRAND_PATTERNS = _compile_brand_patterns()
# 'AI' 같은 짧은 대문자 약어는 대소문자 구분이 필요해서 따로 처리
CASE_SENSITIVE_TAG_WORDS = {"tech": re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])")}


def classify(article):
    text = f"{article['title']} {article.get('snippet', '')}"
    tags = []
    for tag_id, pat in TAG_PATTERNS:
        if tag_id == "tech":
            # 'ai' 소문자 오탐을 피하려고 tech 는 AI(대문자)만 별도 확인
            words_wo_ai = pat.pattern.replace(r"(?<![A-Za-z])AI(?![A-Za-z])|", "")
            if re.search(words_wo_ai, text, re.I) or CASE_SENSITIVE_TAG_WORDS["tech"].search(text):
                tags.append(tag_id)
        elif pat.search(text):
            tags.append(tag_id)
    brands = [name for name, pat in BRAND_PATTERNS if pat.search(text)]
    return tags, brands


# ─────────────────────────────────────────────────────────────
# 3. 중복 통합 (비슷한 제목 묶기)
# ─────────────────────────────────────────────────────────────
STOPWORDS = set("""the a an and or of to in on for with at by from is are was were be this that these those
its it as into new how why what who when your you our their his her best more most just about after over
now first top look here all can will has have off out up""".split())


def title_tokens(title):
    words = re.findall(r"[A-Za-z][A-Za-z'’\-]{2,}|[가-힣]{2,}|[぀-ヿ一-鿿]{2,}", title.lower())
    return {w for w in words if w not in STOPWORDS}


def assign_clusters(articles):
    """72시간 안에 발행된 다른 매체 기사 중 제목 단어가 50% 이상 겹치면 같은 이슈로 묶는다."""
    ordered = sorted(articles, key=lambda a: a["date"])
    for a in ordered:
        a["_tok"] = title_tokens(a["title"])
        a["cluster"] = a["id"]
    for i, a in enumerate(ordered):
        if len(a["_tok"]) < 3:
            continue
        for b in ordered[max(0, i - 400):i]:
            if b["source"] == a["source"] or len(b["_tok"]) < 3:
                continue
            if (a["date"] - b["date"]) > timedelta(hours=72):
                continue
            inter = len(a["_tok"] & b["_tok"])
            if inter >= 3 and inter / len(a["_tok"] | b["_tok"]) >= 0.5:
                a["cluster"] = b["cluster"]
                break
    sizes = defaultdict(set)
    for a in ordered:
        sizes[a["cluster"]].add(a["source"])
    for a in ordered:
        a["cluster_size"] = len(sizes[a["cluster"]])
        a.pop("_tok", None)


# ─────────────────────────────────────────────────────────────
# 4. 트렌드 분석
# ─────────────────────────────────────────────────────────────
PHRASE_STOP = {"The", "A", "An", "This", "These", "How", "Why", "What", "When", "Our", "Your", "Here", "Best", "All", "Is", "In", "On", "Of", "And", "For", "To", "With", "At", "By"}


PHRASE_STOP |= set("""Are Was Were Be It Its From Into Over After Before Just Now Get Gets Got Make Makes Made Buy Shop Sale Deal Deals
Can Will Has Have Had Not More Most Every Ever Our We You He She They Who Where Which Than Then That Them Their There
Top Day Days Year Years Today Look Looks Inside Meet Why Need Want Like Love Real Big First Last Next One Two Three
Should Could Would Gift Gifts Guide Review Reviewed Things Way Ways Out Up Off Up About Exclusive Watch Read See""".split())


# 이슈라기보다 배경 정보인 지명·플랫폼명 (랭킹에서 제외)
GENERIC_PHRASES = {"New York", "Los Angeles", "San Francisco", "Hong Kong", "United States", "United Kingdom",
                   "South Korea", "New York City", "Getty Images", "Fashion Week", "Read More", "Continue Reading"}


def capitalized_phrases(text):
    """'Paris Fashion Week', 'Anthony Vaccarello' 같은 고유명사 구(2~4단어)를 뽑는다.
    잡음이 섞이지만, 랭킹에는 2개 이상 매체에서 나온 구만 올라가므로 대부분 걸러진다."""
    phrases = set()
    for segment in re.split(r"[.,:;!?|()\"“”—–]+", text):
        run = []
        for w in re.findall(r"[A-Za-z][\w'’&\-]*", segment) + ["."]:
            is_name = w[0].isupper() and w not in PHRASE_STOP and (len(w) > 1)
            if is_name:
                run.append(re.sub(r"['’]s$", "", w))  # 소유격 's 제거
            else:
                if 2 <= len(run) <= 4:
                    phrases.add(" ".join(run))
                run = []
    return phrases


def entities_of(article, tag_label):
    """랭킹에 쓰는 '이슈 후보': 브랜드 + 관심사 태그 + 고유명사 구 + AI 키워드."""
    ents = set()
    for b in article.get("brands", []):
        ents.add(("brand", b))
    for t in article.get("tags", []):
        ents.add(("topic", tag_label[t]))
    brand_names = set(article.get("brands", []))
    for p in capitalized_phrases(f"{article['title']}. {article.get('snippet', '')}"):
        if p not in brand_names and p not in GENERIC_PHRASES:
            ents.add(("issue", p))
    for k in article.get("ai", {}).get("keywords", []) or []:
        ents.add(("issue", k))
    return ents


def window_stats(articles, start, end, tag_label):
    """기간 [start, end) 동안 이슈별 '보도한 매체 수'와 '기사 수'."""
    src_by_ent = defaultdict(set)
    cnt_by_ent = Counter()
    for a in articles:
        if start <= a["date"] < end:
            for e in entities_of(a, tag_label):
                src_by_ent[e].add(a["source"])
                cnt_by_ent[e] += 1
    return src_by_ent, cnt_by_ent


# 수집을 처음 시작한 시각. RSS 는 최근 N건만 주므로, 이 시각 이전 구간은 데이터가 덜 쌓여 있다.
FIRST_RUN = None


def comparable(now, days):
    """직전 비교 구간 전체를 실제로 수집하고 있었는지. 아니면 증감을 계산하지 않는다(부풀려진 '급상승' 방지)."""
    return FIRST_RUN is not None and now - timedelta(days=2 * days) >= FIRST_RUN


def ranking(articles, now, days, tag_label, kinds=("brand", "issue"), top=10, min_sources=2):
    cur_s, cur_c = window_stats(articles, now - timedelta(days=days), now, tag_label)
    prev_s, prev_c = window_stats(articles, now - timedelta(days=2 * days), now - timedelta(days=days), tag_label)
    has_prev = comparable(now, days)
    rows = []
    for e, srcs in cur_s.items():
        if e[0] not in kinds or len(srcs) < min_sources:
            continue
        cur, prev = cur_c[e], prev_c.get(e, 0)
        rows.append({
            "kind": e[0], "name": e[1],
            "sources": len(srcs), "count": cur,
            "prev": prev if has_prev else None,
            "delta": (cur - prev) if has_prev else None,
            "delta_pct": round((cur - prev) / prev * 100, 1) if has_prev and prev else None,
            # 점수: 여러 매체가 다룰수록 가중 (매체 수 × 3 + 기사 수)
            "score": len(srcs) * 3 + cur,
        })
    rows.sort(key=lambda r: (-r["score"], -r["sources"], r["name"]))
    return rows[:top]


def brand_movers(articles, now, tag_label, days=7, top=15):
    rows = ranking(articles, now, days, tag_label, kinds=("brand",), top=200, min_sources=1)
    most = sorted(rows, key=lambda r: (-r["count"], -r["sources"]))[:top]
    if not comparable(now, days):
        # 비교 데이터가 쌓이기 전에는 '급상승'을 비워 둔다
        return {"most": most, "rising": [], "comparable": False}
    rising = sorted([r for r in rows if r["count"] >= 2 and r["delta"] > 0], key=lambda r: (-r["delta"], -r["count"]))[:top]
    return {"most": most, "rising": rising, "comparable": True}


def topic_share(articles, now, days, tag_label):
    """관심사 카테고리별 기사 비중 (기간 내)."""
    start = now - timedelta(days=days)
    sub = [a for a in articles if a["date"] >= start]
    c = Counter(tag_label[t] for a in sub for t in a.get("tags", []))
    return [{"name": k, "count": v, "pct": round(v / len(sub) * 100, 1) if sub else 0} for k, v in c.most_common()]


def region_compare(articles, now, tag_label, source_map, days=7):
    out = {}
    start = now - timedelta(days=days)
    for region in ("KR", "US", "JP", "EU"):
        sub = [a for a in articles if source_map[a["source"]]["region"] == region and a["date"] >= start]
        tag_c = Counter(tag_label[t] for a in sub for t in a.get("tags", []))
        brand_c = Counter(b for a in sub for b in a.get("brands", []))
        out[region] = {
            "articles": len(sub),
            "sources": len({a["source"] for a in sub}),
            "topics": tag_c.most_common(8),
            "brands": brand_c.most_common(8),
        }
    return out


def build_report(articles, now, days, label, tag_label, source_map):
    start = now - timedelta(days=days)
    sub = [a for a in articles if a["date"] >= start]
    prev = [a for a in articles if now - timedelta(days=2 * days) <= a["date"] < start]
    by_section = Counter(source_map[a["source"]]["section"] for a in sub)
    # 가장 많은 매체가 함께 다룬 이슈(묶음) 상위 5개
    clusters = defaultdict(list)
    for a in sub:
        clusters[a["cluster"]].append(a)
    top_clusters = sorted(clusters.values(), key=lambda g: (-len({x["source"] for x in g}), -len(g)))[:5]
    return {
        "label": label, "days": days,
        "from": start.isoformat(), "to": now.isoformat(),
        "articles": len(sub),
        "prev_articles": len(prev) if comparable(now, days) else None,
        "by_section": dict(by_section),
        "topics": topic_share(articles, now, days, tag_label)[:8],
        "trends": ranking(articles, now, days, tag_label, top=10),
        "brands": brand_movers(articles, now, tag_label, days=days, top=8),
        "top_stories": [{
            "title": g[0]["title"], "url": g[0]["url"], "source": g[0]["source"],
            "date": g[0]["date"].isoformat(), "sources": sorted({x["source"] for x in g}),
        } for g in top_clusters if g],
        "ai_commentary": None,
    }


# ─────────────────────────────────────────────────────────────
# 5. (선택) Claude API — 한국어 요약·키워드, 리포트 해설
# ─────────────────────────────────────────────────────────────
def call_claude(model, prompt, max_tokens=4000):
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body, method="POST",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        data = json.loads(res.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def extract_json(text):
    m = re.search(r"\[.*\]|\{.*\}", text, flags=re.S)
    return json.loads(m.group(0)) if m else None


def ai_summarize(articles, source_map):
    """해외(영어·일본어) 기사 중 아직 요약이 없는 것만 10개씩 묶어 요약."""
    todo = [a for a in articles if not a.get("ai") and source_map[a["source"]]["lang"] != "ko"]
    todo.sort(key=lambda a: a["date"], reverse=True)
    todo = todo[:AI_MAX_NEW_PER_RUN]
    done = 0
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        payload = [{"id": a["id"], "source": source_map[a["source"]]["name"], "title": a["title"], "preview": a["snippet"]} for a in batch]
        prompt = (
            "다음은 해외 패션·라이프스타일 매체 RSS의 제목과 미리보기 문구다. 각 항목에 대해 아래 JSON 배열만 출력하라.\n"
            '[{"id": "...", "title_ko": "자연스러운 한국어 제목", "summary_ko": "미리보기에 있는 사실만으로 1~2문장 요약", '
            '"keywords": ["핵심 키워드 2~4개 (브랜드·인물·이슈명은 원어 표기 유지)"]}]\n'
            "규칙: 미리보기에 없는 사실을 추측하거나 덧붙이지 말 것. 정보가 부족하면 summary_ko 를 짧게 쓸 것.\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        try:
            result = extract_json(call_claude(SUMMARY_MODEL, prompt)) or []
        except Exception as e:
            print(f"  [AI] 요약 실패 (배치 {i // 10 + 1}): {e}")
            continue
        by_id = {r.get("id"): r for r in result if isinstance(r, dict)}
        for a in batch:
            r = by_id.get(a["id"])
            if r:
                a["ai"] = {
                    "title_ko": r.get("title_ko", "")[:200],
                    "summary_ko": r.get("summary_ko", "")[:400],
                    "keywords": [str(k)[:40] for k in (r.get("keywords") or [])][:4],
                    "model": SUMMARY_MODEL,
                }
                done += 1
    return done


def ai_commentary(report, source_map):
    trends = ", ".join(
        f"{t['name']}({t['sources']}개 매체, {t['count']}건" + (f", 직전 대비 {t['delta']:+d})" if t["delta"] is not None else ")")
        for t in report["trends"])
    prev_txt = f"{report['prev_articles']}건" if report["prev_articles"] is not None else "비교 데이터 없음(수집 초기)"
    stories = "\n".join(f"- [{source_map[s['source']]['name']}] {s['title']} ({len(s['sources'])}개 매체)" for s in report["top_stories"])
    prompt = (
        f"아래는 지난 {report['label']} 동안 국내외 패션·라이프스타일 매체 RSS를 집계한 통계다. "
        "이 통계와 헤드라인에 근거해서만 한국어로 4~6문장의 트렌드 해설을 써라. "
        "통계에 없는 수치나 사실은 만들지 말고, 해석이 들어가는 문장은 '~로 보인다'처럼 표현하라.\n\n"
        f"기사 수: {report['articles']}건 (직전 동일 기간 {prev_txt})\n"
        f"카테고리 비중: {', '.join(t['name'] + ' ' + str(t['count']) + '건' for t in report['topics'])}\n"
        f"이슈 랭킹: {trends}\n주요 보도:\n{stories}"
    )
    return {"text": call_claude(REPORT_MODEL, prompt, max_tokens=1200).strip(), "model": REPORT_MODEL}


# ─────────────────────────────────────────────────────────────
# 6. 저장
# ─────────────────────────────────────────────────────────────
def load_store():
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH, encoding="utf-8") as f:
            store = json.load(f)
        for a in store["articles"].values():
            a["date"] = datetime.fromisoformat(a["date"])
        return store
    return {"articles": {}, "first_run": datetime.now(timezone.utc).isoformat()}


def save_store(store):
    serial = {**store, "articles": {k: {**a, "date": a["date"].isoformat()} for k, a in store["articles"].items()}}
    tmp = STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(serial, f, ensure_ascii=False)
    os.replace(tmp, STORE_PATH)


def compact(a):
    """대시보드용으로 필드명을 줄인 기사."""
    row = {"id": a["id"], "s": a["source"], "t": a["title"], "u": a["url"], "d": a["date"].isoformat(),
           "x": a["snippet"], "tg": a.get("tags", []), "br": a.get("brands", []),
           "c": a["cluster"], "cs": a.get("cluster_size", 1)}
    if a.get("img"):
        row["img"] = a["img"]
    if a.get("ai"):
        row["ai"] = {"t": a["ai"].get("title_ko"), "s": a["ai"].get("summary_ko"), "k": a["ai"].get("keywords")}
    return row


def main():
    # Windows 콘솔(cp949)에서도 한글·특수문자 출력 때문에 멈추지 않도록
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    use_ai = bool(ANTHROPIC_API_KEY) and "--no-ai" not in sys.argv
    os.makedirs(DATA_DIR, exist_ok=True)
    source_map = {s["id"]: s for s in SOURCES}
    tag_label = {t[0]: t[1] for t in TAGS}
    store = load_store()
    now = datetime.now(timezone.utc)
    global FIRST_RUN
    FIRST_RUN = datetime.fromisoformat(store["first_run"])

    print(f"[1/5] RSS 수집: {sum(1 for s in SOURCES if s.get('feed'))}개 매체")
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(collect_source, SOURCES))

    statuses, new_count = [], 0
    prev_status = store.get("source_status", {})
    for (items, st), src in zip(results, SOURCES):
        for a in items:
            aid = hashlib.sha1(a["url"].encode("utf-8")).hexdigest()[:16]
            a["id"] = aid
            if aid in store["articles"]:
                old = store["articles"][aid]
                old.update(title=a["title"], img=a["img"] or old.get("img"), snippet=a["snippet"])
            else:
                a["first_seen"] = now.isoformat()
                store["articles"][aid] = a
                new_count += 1
        last_ok = now.isoformat() if st["ok"] else prev_status.get(src["id"], {}).get("last_ok")
        st["last_ok"] = last_ok
        statuses.append(st)
        mark = "OK " if st["ok"] else ("-- " if not src.get("feed") else "ERR")
        print(f"  {mark} {src['name']:<22} {st['fetched']:>4}건  {st['error'] or ''}")
    store["source_status"] = {s["id"]: s for s in statuses}

    # 보관 기간 지난 기사 정리
    cutoff = now - timedelta(days=RETENTION_DAYS)
    store["articles"] = {k: a for k, a in store["articles"].items() if a["date"] >= cutoff}
    articles = list(store["articles"].values())
    print(f"[2/5] 신규 {new_count}건 / 누적 {len(articles)}건 (최근 {RETENTION_DAYS}일)")

    print("[3/5] 분류·중복 통합")
    for a in articles:
        a["tags"], a["brands"] = classify(a)
    assign_clusters(articles)

    if use_ai:
        print("[4/5] AI 한국어 요약")
        n = ai_summarize(articles, source_map)
        print(f"  요약 완료 {n}건")
    else:
        print("[4/5] AI 요약 건너뜀 (ANTHROPIC_API_KEY 없음 또는 --no-ai)")

    print("[5/5] 트렌드 분석·리포트")
    reports = {
        "daily": build_report(articles, now, 1, "24시간", tag_label, source_map),
        "weekly": build_report(articles, now, 7, "7일", tag_label, source_map),
        "monthly": build_report(articles, now, 30, "30일", tag_label, source_map),
    }
    if use_ai:
        for key, rep in reports.items():
            try:
                rep["ai_commentary"] = ai_commentary(rep, source_map)
            except Exception as e:
                print(f"  [AI] {key} 해설 실패: {e}")

    history_days = (now - min((a["date"] for a in articles), default=now)).days
    output = {
        "generated_at": now.isoformat(),
        "first_run": store.get("first_run"),
        "history_days": history_days,
        "ai_enabled": use_ai,
        "retention_days": RETENTION_DAYS,
        "tags": [{"id": t[0], "label": t[1]} for t in TAGS],
        "sources": [{**{k: s[k] for k in ("id", "name", "section", "region", "lang", "site")},
                     "feed": s.get("feed"), "note": s.get("note"),
                     "status": store["source_status"].get(s["id"])} for s in SOURCES],
        "trends": {"day": ranking(articles, now, 1, tag_label), "week": ranking(articles, now, 7, tag_label),
                   "comparable_week": comparable(now, 7)},
        "topics": topic_share(articles, now, 7, tag_label),
        "brands": brand_movers(articles, now, tag_label),
        "regions": region_compare(articles, now, tag_label, source_map),
        "reports": reports,
        "articles": [compact(a) for a in sorted(articles, key=lambda a: a["date"], reverse=True)],
    }
    save_store(store)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("// collect.py 가 자동 생성하는 파일입니다. 직접 수정하지 마세요.\n")
        f.write("window.TREND_DATA = ")
        json.dump(output, f, ensure_ascii=False, default=str)
        f.write(";\n")
    size_kb = os.path.getsize(OUTPUT_JS) / 1024
    print(f"완료: {OUTPUT_JS} ({size_kb:,.0f} KB) — index.html 을 열어 확인하세요.")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"소요 시간 {time.time() - t0:,.1f}초")
