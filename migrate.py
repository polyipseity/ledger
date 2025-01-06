from glob import iglob
from os import renames
from pathlib import Path


def main():
    for journal in iglob(
        "**/index.journal",
        root_dir=".",
        recursive=True,
    ):
        comps = journal.split("\\")
        name = comps[0]
        if len(comps) >= 3:
            year = comps[1]
            Path(journal).write_text(
                Path(journal).read_text().replace(".journal", f"/{name}.journal")
            )
            renames(journal, f"ledger/{year}/{name}.journal")
        else:
            renames(journal, f"ledger/{name}.journal")
            # edit the text yourself


if __name__ == "__main__":
    main()
