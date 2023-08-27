# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict
from yaml import safe_load

Datum = TypedDict(
    "Datum",
    {"compute method": str, "duration": int | float, "frames": int, "points": int},
)


def main():
    log: dict[datetime, Datum] = safe_load(
        Path("SheepIt Render Farm.yml").read_text()
    )["log"]
    for date, datum in log.items():
        date = date - timedelta(seconds=datum["duration"])
        with Path(f"../{date.year}/{date.year}-0{date.month}.journal").open(
            "at"
        ) as file:
            file.write(
                f"""
{date.year}-0{date.month}-{date.day} SheepIt Render Farm  ; activity: compute, compute: {datum["compute method"]}, duration: PT{datum["duration"]}S, time: {date.strftime("%H:%M:%S")}, timezone: UTC+08:00
    assets:digital:SheepIt Render Farm:polyipseity  {datum["points"]} SheepIt_Render_Farm_points
    revenues:compute:SheepIt Render Farm
    (assets:digital:SheepIt Render Farm:polyipseity)  {datum["frames"]} frames
"""
            )


if __name__ == "__main__":
    main()
