# -*- coding: UTF-8 -*-
from anyio import Path
from asyncio import gather, run
from collections import defaultdict
from data import DATA, Data, Datum
from itertools import pairwise

ACCOUNT = "assets:digital:SheepIt Render Farm:polyipseity"
COMMODITY = "SheepIt_Render_Farm_points"
FRAMES = "frames"
TIMEZONE = "UTC+08:00"


class Datum2(Datum):
    framesDiff: int
    pointsDiff: int


Data2 = dict[str, Datum2]


async def main(data: Data):
    data2 = process(data)
    months = defaultdict[str, Data2](Data2)
    for date, datum in data2.items():
        months["-".join(date.split("-")[:2])][date] = datum
    await gather(*map(gen_file, months.values()))


def process(data: Data) -> Data2:
    return {
        cur[0]: {
            **cur[1],
            "framesDiff": cur[1]["frames"] - prev[1]["frames"],
            "pointsDiff": cur[1]["points"] - prev[1]["points"],
        }
        for prev, cur in pairwise(data.items())
    }


async def gen_file(data: Data2):
    data = dict(sorted(data.items(), key=lambda datum: datum[0]))
    entries = list[str]()
    date, datum = next(iter(data.items()))
    path = Path(f'{"-".join(date.split("-")[:2])}.journal')
    entries.append(
        f"""{date} opening balances  ; time: 00:00:00, timezone: {TIMEZONE}
    {ACCOUNT}  {datum["points"] - datum["pointsDiff"]} {COMMODITY} = {datum["points"] - datum["pointsDiff"]} {COMMODITY}
    equity:opening/closing balances
    ({ACCOUNT})  {datum["frames"] - datum["framesDiff"]} {FRAMES} = {datum["frames"] - datum["framesDiff"]} {FRAMES}"""
    )
    for date, datum in data.items():
        entries.append(
            f"""{date} SheepIt Render Farm  ; activity: compute, timezone: {TIMEZONE}
    {ACCOUNT}  {datum["pointsDiff"]} {COMMODITY} = {datum["points"]} {COMMODITY}
    {"revenues:compute:SheepIt Render Farm" if datum["pointsDiff"] > 0 else "expenses:compute:SheepIt Render Farm" if datum["pointsDiff"] < 0 else ""}
    ({ACCOUNT})  {datum["framesDiff"]} {FRAMES} = {datum["frames"]} {FRAMES}"""
        )
    entries.append(
        f"""{date} closing balances  ; time: 23:59:59, timezone: {TIMEZONE}
    {ACCOUNT}  {-datum["points"]} {COMMODITY} = 0 {COMMODITY}
    equity:opening/closing balances
    ({ACCOUNT})  {-datum["frames"]} {FRAMES} = 0 {FRAMES}"""
    )

    entries.append("")
    write = "\n\n".join(entries)
    async with await path.open("w+t") as file:
        await file.write(write)


if __name__ == "__main__":
    run(main(DATA))
