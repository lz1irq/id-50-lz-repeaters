#!/usr/bin/env python3

import json
import pathlib
import re

#Group No	Group Name	Name	Sub Name	Repeater Call Sign	Gateway Call Sign	Frequency	Dup	Offset	Mode	TONE	Repeater Tone	RPT1USE	Position	Latitude	Longitude	UTC Offset
#1	Africa	Pretoria	S-Africa	ZS6PTA C	ZS6PTA G	145.712500	DUP-	0.600000	DV	OFF	88.5Hz	YES	Approximate	-25.692333	28.242333	+2:00

CSV_HEADER = "Group No,Group Name,Name,Sub Name,Repeater Call Sign,Gateway Call Sign,Frequency,Dup,Offset,Mode,TONE,Repeater Tone,RPT1USE,Position,Latitude,Longitude,UTC Offset"

SELECT_MODES = ["analog", "dstar"]

BG_LAT_MAP = {
        'А': 'A',
        'Б': 'B',
        'В': 'V',
        'Г': 'G',
        'Д': 'D',
        'Е': 'E',
        'Ж': 'ZH',
        'З': 'Z',
        'И': 'I',
        'Й': 'Y',
        'К': 'K',
        'Л': 'L',
        'М': 'M',
        'Н': 'N',
        'О': 'O',
        'П': 'P',
        'Р': 'R',
        'С': 'S',
        'Т': 'T',
        'У': 'U',
        'Ф': 'F',
        'Х': 'H',
        'Ц': 'TS',
        'Ч': 'CH',
        'Ш': 'SH',
        'Щ': 'SHT',
        'Ъ': 'A',
        'Ь': '',
        'Ю': 'YU',
        'Я': 'YA',
    }

def dstar_freq_suffix(freq: float) -> str:
    if 1240 <= freq <= 1300:
        return "A"
    if 430 <= freq <= 440:
        return "B"
    if 144 <= freq <= 146:
        return "C"
    raise ValueError(f"Unknown frequency {freq}")

def dstar_callsign(callsign: str, suffix: str) -> str:
    assert len(suffix) == 1
    if len(callsign) > 8:
        raise RuntimeError(f"{callsign=} too long")
    if len(callsign) == 8:
        return callsign
    padding = ' '*(8 - len(callsign) - 1)
    return f"{callsign}{padding}{suffix}"

def transliterate(text: str) -> str:
    text = re.sub(r'ИЯ', 'IA', text.upper())
    return ''.join(BG_LAT_MAP.get(char, char) for char in text)

def main():
    with open("reps.json", "r", encoding="UTF-8") as reps_file:
        repeaters = json.load(reps_file)

    print(CSV_HEADER)
    for name, data in repeaters["repeaters"].items():
        callsign = data["callsign"]
        rep_modes = list(data["mode"].keys())
        if not any(mode in rep_modes for mode in SELECT_MODES):
            continue
        mode = "FM"
        gw_callsign = ""
        rpt1use = "NO"
        tone = "OFF"
        if tone_freq := data.get("tone", ""):
            tone_freq = f"{tone_freq}Hz"
            tone = "TSQL"
        if "dstar" in rep_modes:
            gw_callsign = dstar_callsign(callsign, "G")
            callsign = dstar_callsign(callsign, dstar_freq_suffix(data["tx"]))
            mode = "DV"
            rpt1use = "YES"
        
        tx_freq = data["tx"]
        rx_freq = data["rx"]
        shift_dir = "DUP-" if rx_freq > tx_freq else "DUP+"
        shift_freq = abs(tx_freq - rx_freq)
        subname = transliterate(data['loc'])
        print(
            f"1,LZ,{name},{subname},{callsign},{gw_callsign},{rx_freq},"
            f"{shift_dir},{shift_freq:.6f},{mode},{tone},{tone_freq},"
            f"{rpt1use},Approximate,{data['lat']},{data['lon']},+3:00"
        )

if __name__ == "__main__":
    main()