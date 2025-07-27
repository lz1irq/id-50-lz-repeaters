#!/usr/bin/env python3

import dataclasses
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


@dataclasses.dataclass
class RepeaterData:

    name: str
    subname: str
    callsign: str
    gw_callsign: str
    rx_freq: float
    shift_dir: str
    shift_freq: float
    mode: str
    tone_use: str
    tone_freq: str
    rpt1use: str
    location: str
    latitude: float
    longitude: float
    utc_offset: str


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

def parse_json_repeaters(path: str) -> list[RepeaterData]:
    """Parse JSON repeater data into objects."""
    with open(path, "r", encoding="UTF-8") as reps_file:
        repeaters = json.load(reps_file)
    output = []

    for name, data in repeaters["repeaters"].items():
        callsign = data["callsign"]
        rep_modes = list(data["mode"].keys())
        if not any(mode in rep_modes for mode in SELECT_MODES):
            continue
        mode = "FM"
        gw_callsign = ""
        if tone_freq := data.get("tone", ""):
            tone_freq = f"{tone_freq}Hz"
        if "dstar" in rep_modes:
            gw_callsign = dstar_callsign(callsign, "G")
            callsign = dstar_callsign(callsign, dstar_freq_suffix(data["tx"]))
            mode = "DV"

        output.append(
            RepeaterData(
                name=name,
                subname=transliterate(data['loc']),
                callsign=callsign,
                gw_callsign=gw_callsign,
                rx_freq=data["rx"],
                shift_dir="DUP-" if data["rx"] >  data["tx"] else "DUP+",
                shift_freq=abs(data["tx"] - data["rx"]),
                mode=mode,
                tone_use="TSQL" if tone_freq else "OFF",
                tone_freq=tone_freq,
                rpt1use="YES" if "dstar" in rep_modes else "NO",
                location="Approximate",
                latitude=data['lat'],
                longitude=data['lon'],
                utc_offset="+3:00",
            )
        )
    return output


def main():
    repeaters = sorted(
        parse_json_repeaters("reps.json"),
        key=lambda repeater: repeater.name
    )

    print(CSV_HEADER)
    for rep in repeaters:
        print(
            f"1,LZ,{rep.name},{rep.subname},{rep.callsign},{rep.gw_callsign},{rep.rx_freq},"
            f"{rep.shift_dir},{rep.shift_freq:.6f},{rep.mode},{rep.tone_use},{rep.tone_freq},"
            f"{rep.rpt1use},Approximate,{rep.latitude},{rep.longitude},+3:00"
        )

if __name__ == "__main__":
    main()