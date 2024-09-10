from collections import defaultdict
from pathlib import Path

def main() -> None:
  depreciate = 0
  to_change = defaultdict[str, float](float)
  for year in range(2023, 2029):
    for month in range(12 if year == 2023 else 1, 12 if year == 2028 else 13):
      path = Path(f"{year}/{year}-{str(month).rjust(2, '0')}.journal")
      content = path.read_text()
      processing = False
      new_content = list[str]()
      old_depreciate = depreciate
      for line in content.splitlines():
        new_content.append(line)
        if processing:
          if "expenses:depreciation" in line:
            processing = False
            continue
          line = line.strip()
          parts = line.split(";", 1)
          if len(parts) == 2:
            part1, cmt = parts
          else:
            part1, cmt = parts[0], ""
          account, money_str = part1.split("  ", 1)
          account, money_str = account.strip(), money_str.strip()

          if "HKD" not in line:
            print(line)
            continue
          money = float(money_str.split(" ", 1)[0].replace(" ", ""))
          depreciate += money
          to_change[account] -= money

          new_content[-1] = f"    assets:depreciation  {money_str}  {cmt and ';'}{cmt}"
          continue
        if line.endswith("adjustment  ; activity: depreciation, time: 23:59:59, timezone: UTC+08:00"):
          processing = True
        elif line.startswith("    "):
          line = line.strip()
          parts = line.split(";", 1)
          if len(parts) == 2:
            part1, cmt = parts
          else:
            part1, cmt = parts[0], ""
          try:
            account, money_str = part1.split("  ", 1)
          except ValueError:
            continue
          account, money_str = account.strip(), money_str.strip()

          if account in to_change and "HKD" in line and "=" in line:
            money = float(money_str.split(" HKD", 1)[0].replace(" ", ""))
            if "0.00 HKD" not in line and "0.0 HKD" not in line and "0. HKD" not in line:
              new_money = round(money + to_change[account], 2)
              new_content[-1] = f"    {account}  {new_money:.2f} HKD = {new_money:.2f} HKD  {cmt and ';'}{cmt}"
            else:
              new_money = round(money - to_change[account], 2)
              new_content[-1] = f"    {account}  {new_money:.2f} HKD = 0.00 HKD  {cmt and ';'}{cmt}"

      if old_depreciate != 0:
        try:
          opening_balances_idx = next(a[0] for a in enumerate(new_content) if "opening balances  ;" in a[1])
        except StopIteration:
          pass
        else:
          new_content.insert(opening_balances_idx + 1, f"    assets:depreciation  {old_depreciate:.2f} HKD = {old_depreciate:.2f} HKD")
          pass 
      try:
        closing_balances_idx = next(a[0] for a in enumerate(new_content) if "closing balances  ;" in a[1])
      except StopIteration:
        pass
      else:
        new_content.insert(closing_balances_idx + 1, f"    assets:depreciation  {-depreciate:.2f} HKD = 0.00 HKD")
        pass
      path.write_text("\n".join(new_content))

if __name__ == "__main__":
  main()
