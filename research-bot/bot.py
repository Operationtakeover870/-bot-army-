#!/usr/bin/env python3
"""
Bot #3 — Brains.

One bot, one objective: answer any question by researching the open web
across multiple angles, then report back with cited sources.

Inputs:  a question string on the command line.
Outputs: a researched digest on stdout — findings, sources, research trail.

Tools it's allowed to use: keyless public web endpoints only
(Wikipedia API, DuckDuckGo Instant Answer API). No API keys anywhere.

Guardrails: read-only. It never sends, posts, edits, or deletes anything.
It never claims certainty it doesn't have — when sources disagree, or the
web is unreachable, it says so plainly.

Stop condition: after MAX_ANGLES search angles and MAX_ARTICLES article
reads it synthesizes and reports. It never loops.
"""

import html as htmlmod
import re
import sys
import time
from urllib.parse import quote_plus

import requests

USER_AGENT = "BotArmy-Brains/1.0 (keyless research bot)"
TIMEOUT = 15
REQUEST_PAUSE = 0.6
MAX_ANGLES = 4
MAX_ARTICLES = 6
MAX_CHARS_PER_PAGE = 8000

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "doing", "have", "has", "had", "having",
    "i", "me", "my", "you", "your", "he", "she", "it", "we", "they",
    "what", "which", "who", "whom", "whose", "when", "where", "why",
    "how", "that", "this", "these", "those", "am", "and", "or",
    "but", "if", "then", "else", "of", "at", "by", "for", "with",
    "about", "into", "to", "in", "on", "from", "as", "so",
    "can", "could", "should", "would", "will", "just", "please", "tell",
}


def log(msg):
    print("[brains] " + msg, file=sys.stderr)


def keywords_of(question):
    words = [w for w in re.findall(r"[a-zA-Z0-9']+", question.lower())
             if w not in STOPWORDS]
    return " ".join(words)


def search_angles(question):
    """Turn one question into several search angles."""
    q = question.strip()
    keywords = keywords_of(question)
    angles = [q]
    if keywords and keywords != q.lower():
        angles.append(keywords)
        angles.append("what is " + keywords)
        angles.append(keywords + " explained")
    seen, out = set(), []
    for a in angles:
        a = a.strip()
        if a and a.lower() not in seen:
            seen.add(a.lower())
            out.append(a)
    return out[:MAX_ANGLES]


def relevance(title, keywords):
    """Word-overlap score between an article title and the question keywords."""
    if not keywords:
        return 0.0
    tw = set(re.findall(r"[a-z0-9]+", title.lower()))
    return len(tw & set(keywords)) / len(keywords)


def wikipedia_opensearch(query, limit=5):
    """Keyless article discovery via Wikipedia's opensearch API.

    Returns [(title, url)] ordered by relevance.
    """
    api = "https://en.wikipedia.org/w/api.php"
    try:
        r = requests.get(api, params={
            "action": "opensearch", "search": query,
            "limit": limit, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        r.raise_for_status()
        _q, titles, _desc, urls = r.json()
    except (requests.RequestException, ValueError) as e:
        log("Wikipedia opensearch failed for %r: %s" % (query, e))
        return []
    time.sleep(REQUEST_PAUSE)
    return [(t, u) for t, u in zip(titles, urls) if t and u]


def wikipedia_fulltext(query, limit=5):
    """Fallback discovery via Wikipedia full-text search.

    Catches what opensearch's title matching misses.
    Returns [(title, url)].
    """
    api = "https://en.wikipedia.org/w/api.php"
    try:
        r = requests.get(api, params={
            "action": "query", "list": "search", "srsearch": query,
            "srlimit": limit, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
    except (requests.RequestException, ValueError) as e:
        log("Wikipedia full-text search failed for %r: %s" % (query, e))
        return []
    time.sleep(REQUEST_PAUSE)
    return [(h["title"], "https://en.wikipedia.org/?curid=" + str(h["pageid"]))
            for h in hits if h.get("title")]


def wikipedia_discover(query, limit=5):
    """opensearch first, full-text fallback when it comes back empty."""
    res = wikipedia_opensearch(query, limit)
    if not res:
        log("opensearch empty for %r, trying full-text" % query)
        res = wikipedia_fulltext(query, limit)
    return res


def wikipedia_extracts(titles):
    """Fetch intro extracts for article titles. Returns [(title, url, text)]."""
    api = "https://en.wikipedia.org/w/api.php"
    out = []
    for title in titles:
        try:
            r = requests.get(api, params={
                "action": "query", "prop": "extracts", "exintro": 1,
                "explaintext": 1, "redirects": 1, "titles": title,
                "format": "json",
            }, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if str(pid).startswith("-"):
                    continue  # missing page
                extract = (page.get("extract") or "").strip()
                if extract:
                    out.append((
                        page.get("title", title) + " — Wikipedia",
                        "https://en.wikipedia.org/?curid=" + str(pid),
                        extract[:MAX_CHARS_PER_PAGE],
                    ))
        except (requests.RequestException, ValueError) as e:
            log("Wikipedia extract failed for %r: %s" % (title, e))
        time.sleep(REQUEST_PAUSE)
    return out


def ddg_instant(query):
    """Best-effort instant answer via DuckDuckGo's keyless JSON API.

    Returns (title, url, text) or None. Often empty — never relied upon.
    """
    try:
        r = requests.get("https://api.duckduckgo.com/", params={
            "q": query, "format": "json", "no_html": 1, "skip_disambig": 1,
        }, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
    except (requests.RequestException, ValueError) as e:
        log("DuckDuckGo instant answer failed for %r: %s" % (query, e))
        return None
    time.sleep(REQUEST_PAUSE)
    abstract = (d.get("AbstractText") or "").strip()
    if abstract:
        return (
            (d.get("Heading") or "Instant answer") + " — DuckDuckGo",
            d.get("AbstractURL") or "https://duckduckgo.com/?q=" + quote_plus(query),
            abstract[:MAX_CHARS_PER_PAGE],
        )
    return None


def first_sentences(text, n=2, max_len=600):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text)]
    picked = [s for s in sents if len(s) > 25][:n]
    return htmlmod.unescape(" ".join(picked))[:max_len]


def dedupe_findings(findings):
    """Drop findings that mostly repeat words already reported."""
    seen_words, out = set(), []
    for text, src_idx in findings:
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        if not words:
            continue
        overlap = len(words & seen_words) / len(words)
        if overlap < 0.6:
            seen_words |= words
            out.append((text, src_idx))
    return out


def research(question):
    angles = search_angles(question)
    keywords = keywords_of(question).split()
    log("angles: %s" % " | ".join(angles))

    # Discover candidate articles across every angle, then keep the ones
    # whose titles best match the question keywords (opensearch alone
    # can return junk for full-sentence queries).
    pool, seen_urls = [], set()
    for ai, angle in enumerate(angles):
        for title, url in wikipedia_discover(angle):
            if url not in seen_urls:
                seen_urls.add(url)
                pool.append((title, url, ai))
    pool.sort(key=lambda x: (-relevance(x[0], keywords), x[2]))
    articles = [(t, u) for t, u, _ai in pool[:MAX_ARTICLES]]
    log("articles: %d (from %d candidates)"
        % (len(articles), len(pool)))

    evidence = []  # (title, url, text)
    evidence += wikipedia_extracts([t for t, _u in articles])

    ddg_hits = 0
    for angle in angles:
        hit = ddg_instant(angle)
        if hit and hit[2]:
            if hit[1] not in seen_urls:
                seen_urls.add(hit[1])
                evidence.append(hit)
                ddg_hits += 1

    return angles, evidence, len(articles), ddg_hits


def report(question, angles, evidence, n_articles, ddg_hits):
    lines = []
    lines.append("BRAINS — research digest")
    lines.append("Question: " + question)
    lines.append("")

    findings = []
    for i, (title, url, text) in enumerate(evidence, 1):
        snippet = first_sentences(text)
        if snippet:
            findings.append((snippet, i))
    findings = dedupe_findings(findings)[:8]

    lines.append("FINDINGS")
    if findings:
        for text, src_idx in findings:
            lines.append("- %s [%d]" % (text, src_idx))
    else:
        lines.append("- No usable findings — the sources came back empty.")
    lines.append("")
    lines.append("SOURCES")
    for i, (title, url, _text) in enumerate(evidence, 1):
        lines.append("[%d] %s" % (i, title))
        lines.append("    %s" % url)
    lines.append("")
    lines.append("RESEARCH TRAIL")
    lines.append("Angles tried (%d): %s" % (len(angles), " | ".join(angles)))
    lines.append("Articles read: %d (Wikipedia) + %d instant answers "
                 "(DuckDuckGo)" % (n_articles, ddg_hits))
    lines.append("Note: keyless sources only. Cross-check before acting on "
                 "anything important.")
    return "\n".join(lines)


def main(argv):
    if len(argv) < 2 or not " ".join(argv[1:]).strip():
        print('usage: python3 bot.py "your question"')
        return 2
    question = " ".join(argv[1:]).strip()
    try:
        angles, evidence, n_articles, ddg_hits = research(question)
    except KeyboardInterrupt:
        print("\nBrains stopped by user.")
        return 130
    if not evidence:
        print("Brains couldn't reach the web or find anything on that — "
              "check your connection and try again.")
        return 1
    print(report(question, angles, evidence, n_articles, ddg_hits))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
