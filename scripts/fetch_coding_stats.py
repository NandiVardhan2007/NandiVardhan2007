#!/usr/bin/env python3
"""
Fetch live stats for LeetCode, CodeChef, HackerRank, and GeeksforGeeks and
save them to data/coding_stats.json.

If an upstream platform temporarily fails or rate-limits, previously cached
values from data/coding_stats.json are preserved so cards never blank out.
"""
import datetime
import json
import os
import re

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "coding_stats.json")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

HANDLES = {
    "leetcode": os.environ.get("LEETCODE_USER", "Nandu_2007_"),
    "codechef": os.environ.get("CODECHEF_USER", "nandu_2007"),
    "hackerrank": os.environ.get("HACKERRANK_USER", "nandu_2007"),
    "gfg": os.environ.get("GFG_USER", "nandu07"),
}


def fetch_leetcode(handle: str) -> dict:
    r = requests.post(
        "https://leetcode.com/graphql",
        headers={
            "Content-Type": "application/json",
            "Origin": "https://leetcode.com",
            "Referer": f"https://leetcode.com/u/{handle}/",
            "User-Agent": UA,
        },
        json={
            "query": (
                "query($u:String!){ matchedUser(username:$u){ username profile{ranking} "
                "submitStats: submitStatsGlobal{ acSubmissionNum{difficulty count submissions} "
                "totalSubmissionNum{difficulty count submissions} } "
                "userCalendar{ totalActiveDays streak } } }"
            ),
            "variables": {"u": handle},
        },
        timeout=15,
    )
    if r.ok:
        user = (r.json().get("data") or {}).get("matchedUser")
        if user:
            ac = {x["difficulty"]: x for x in user["submitStats"]["acSubmissionNum"]}
            tot = {x["difficulty"]: x for x in user["submitStats"]["totalSubmissionNum"]}
            ac_subs = ac.get("All", {}).get("submissions", 0)
            tot_subs = tot.get("All", {}).get("submissions", 0)
            acc = f"{(ac_subs / tot_subs * 100):.1f}%" if tot_subs else "0.0%"
            rank = user.get("profile", {}).get("ranking")
            return {
                "username": handle,
                "solved": ac.get("All", {}).get("count", 0),
                "easy": ac.get("Easy", {}).get("count", 0),
                "medium": ac.get("Medium", {}).get("count", 0),
                "hard": ac.get("Hard", {}).get("count", 0),
                "ranking": f"#{rank:,}" if rank else "Unranked",
                "acceptance": acc,
                "streak": user.get("userCalendar", {}).get("streak", 0),
                "active_days": user.get("userCalendar", {}).get("totalActiveDays", 0),
            }

    # Mirror fallback
    m = requests.get(f"https://leetcode-api-faisalshohag.vercel.app/{handle}", timeout=15)
    m.raise_for_status()
    d = m.json()
    ac_subs = (d.get("matchedUserStats", {}).get("acSubmissionNum") or [{}])[0].get("submissions", 0)
    tot_subs = (d.get("totalSubmissions") or [{}])[0].get("submissions", 0)
    acc = f"{(ac_subs / tot_subs * 100):.1f}%" if tot_subs else "0.0%"
    rank = d.get("ranking")
    return {
        "username": handle,
        "solved": int(d.get("totalSolved", 0)),
        "easy": int(d.get("easySolved", 0)),
        "medium": int(d.get("mediumSolved", 0)),
        "hard": int(d.get("hardSolved", 0)),
        "ranking": f"#{int(rank):,}" if rank else "Unranked",
        "acceptance": acc,
        "streak": 0,
        "active_days": 0,
    }


def fetch_codechef(handle: str) -> dict:
    r = requests.get(f"https://www.codechef.com/users/{handle}", headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    html = r.text
    rating_m = re.search(r'class="rating-number"[^>]*>([\s\S]*?)</div>', html, re.I)
    rating = int(re.search(r"(\d+)", rating_m.group(1)).group(1)) if rating_m and re.search(r"(\d+)", rating_m.group(1)) else 0
    div_m = re.search(r'class="rating-number"[^>]*>[\s\S]*?</div>\s*<div>\(([^)]+)\)</div>', html, re.I)
    division = div_m.group(1).strip() if div_m else ""
    star_m = re.search(r'class="rating-star"[^>]*>([\s\S]*?)</div>', html, re.I)
    stars = len(re.findall(r"&#9733;|★", star_m.group(1))) if star_m else 0
    ranks_m = re.search(r'class="rating-ranks"[^>]*>([\s\S]*?)</div>', html, re.I)
    ranks = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ranks_m.group(1))).strip() if ranks_m else ""
    g_m = re.search(r"(\d+)\s*Global Rank", ranks, re.I)
    c_m = re.search(r"(\d+)\s*Country Rank", ranks, re.I)
    solved_m = re.search(r"Total Problems Solved:\s*(\d+)", html, re.I)
    return {
        "username": handle,
        "rating": rating,
        "stars": stars,
        "division": division,
        "solved": int(solved_m.group(1)) if solved_m else 0,
        "global_rank": f"#{int(g_m.group(1)):,}" if g_m else "Unranked",
        "country_rank": f"#{int(c_m.group(1)):,}" if c_m else "Unranked",
    }


def fetch_hackerrank(handle: str) -> dict:
    b_res = requests.get(f"https://www.hackerrank.com/rest/hackers/{handle}/badges", headers={"User-Agent": UA}, timeout=15)
    b_res.raise_for_status()
    models = b_res.json().get("models") or []
    badges = [
        {
            "name": str(m.get("badge_name") or "Domain"),
            "stars": int(m.get("stars") or 0),
            "solved": int(m.get("solved") or 0),
        }
        for m in models
        if (m.get("stars") or 0) > 0 or (m.get("solved") or 0) > 0
    ]
    badges.sort(key=lambda x: (-x["stars"], -x["solved"]))

    certs = 0
    try:
        c_res = requests.get(
            f"https://www.hackerrank.com/community/v1/test_results/hacker_certificates?username={handle}",
            headers={"User-Agent": UA},
            timeout=15,
        )
        if c_res.ok:
            certs = len(c_res.json().get("data") or [])
    except Exception:
        pass

    return {
        "username": handle,
        "badges": badges,
        "total_solved": sum(b["solved"] for b in badges),
        "top_stars": max((b["stars"] for b in badges), default=0),
        "certificates": certs,
    }


def fetch_gfg(handle: str) -> dict:
    r = requests.get(
        f"https://authapi.geeksforgeeks.org/api-get/user-profile-info/?handle={handle}",
        headers={"User-Agent": UA},
        timeout=15,
    )
    r.raise_for_status()
    d = r.json().get("data") or {}
    if not d:
        raise ValueError("empty GFG data")
    inst_rank = d.get("institute_rank")
    return {
        "username": handle,
        "score": int(d.get("score") or 0),
        "solved": int(d.get("total_problems_solved") or 0),
        "institute_rank": f"#{int(inst_rank):,}" if inst_rank is not None else "Unranked",
    }


def load_existing() -> dict:
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


if __name__ == "__main__":
    prev = load_existing()
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    fetchers = {
        "leetcode": fetch_leetcode,
        "codechef": fetch_codechef,
        "hackerrank": fetch_hackerrank,
        "gfg": fetch_gfg,
    }
    for key, fn in fetchers.items():
        try:
            out[key] = fn(HANDLES[key])
            print(f"{key}: OK ({out[key]})")
        except Exception as e:
            print(f"{key}: fallback to cached ({e})")
            if key in prev:
                out[key] = prev[key]

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT_PATH}")
