from glob import iglob
from os import renames


def main():
    for journal in iglob(
        "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789].journal",
        root_dir=".",
        recursive=True,
    ):
        comps = journal.split("\\")
        name = comps[0]
        year = comps[1]
        month = comps[2].removesuffix(".journal")
        renames(journal, f"ledger/{year}/{month}/{name}.journal")


if __name__ == "__main__":
    main()
