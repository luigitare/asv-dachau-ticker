#!/usr/bin/env python3
# Ticker-Index aus dem BVV/SAMS-Ticker-Backend bauen (gleiche Formate wie das HA-Skript).
import json, sys, os

raw = json.load(open("ticker-raw.json", encoding="utf-8"))
states = {}
for s in (raw.get("matchStates") or {}).values():
    u = s.get("matchUuid")
    if u:
        states[u] = s

days_out, used, total = [], set(), 0
for day in raw.get("matchDays") or []:
    ms_out = []
    for m in day.get("matches") or []:
        slim = {"id": m.get("id"),
                "teamDescription1": m.get("teamDescription1"),
                "teamDescription2": m.get("teamDescription2")}
        if m.get("team1"):
            slim["t1i"] = m["team1"]
        if m.get("team2"):
            slim["t2i"] = m["team2"]
        slim["date"] = m.get("date")
        slim["matchSeries"] = m.get("matchSeries")
        st = states.get(m.get("id"))
        if st:
            slim["st"] = 1 if st.get("started") else 0
            slim["fi"] = 1 if st.get("finished") else 0
            sp = st.get("setPoints") or {}
            slim["sp1"] = sp.get("team1") or 0
            slim["sp2"] = sp.get("team2") or 0
        ms_out.append(slim)
        used.add(m.get("matchSeries"))
        total += 1
    days_out.append({"matches": ms_out})

if total < 200:
    print("ABBRUCH: nur %d Matches (<200)" % total)
    sys.exit(1)

ser = raw.get("matchSeries") or {}
ligen = {u: {"n": ser[u].get("name"), "g": ser[u].get("gender"), "c": ser[u].get("class")}
         for u in used if u in ser and ser[u].get("name")}
idx_str = json.dumps({"matchDays": days_out, "ligen": ligen},
                     separators=(",", ":"), ensure_ascii=False)

asv = {}
for day in raw.get("matchDays") or []:
    for m in day.get("matches") or []:
        t1 = m.get("teamDescription1") or ""
        t2 = m.get("teamDescription2") or ""
        if "ASV Dachau" in t1 or "ASV Dachau" in t2:
            e = asv.setdefault(m.get("matchSeries"), {"spiele": 0, "asvTeams": [], "gegner": []})
            e["spiele"] += 1
            for name in (t1, t2):
                if "ASV Dachau" in name and name not in e["asvTeams"]:
                    e["asvTeams"].append(name)
                if name not in e["gegner"]:
                    e["gegner"].append(name)
wliste = [{"wettbewerb": u, "liga": ser.get(u, {}).get("name"), "spiele": e["spiele"],
           "asvTeams": e["asvTeams"], "gegnerBeispiele": e["gegner"][:4]}
          for u, e in sorted(asv.items(), key=lambda kv: (ser.get(kv[0], {}).get("name") or ""))]
wett_str = json.dumps({"stand": "automatisch generiert (GitHub Action)", "wettbewerbe": wliste},
                      indent=2, ensure_ascii=False)

changed = False
for path, content in (("ticker-index.json", idx_str), ("asv-wettbewerbe.json", wett_str)):
    if os.path.exists(path) and open(path, encoding="utf-8").read() == content:
        print(path + ": unveraendert")
    else:
        open(path, "w", encoding="utf-8").write(content)
        print(path + ": neu geschrieben")
        changed = True

print("STATS: matches=%d ligen=%d asvWettbewerbe=%d changed=%s" % (total, len(ligen), len(wliste), changed))
