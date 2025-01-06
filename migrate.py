from glob import iglob
from pathlib import Path


def main():
    for journal in iglob(
        "**/*.journal",
        root_dir=".",
        recursive=True,
    ):
        text = Path(journal).read_text()
        if "../prelude.journal" in text:
            name = journal.split("\\")[-1].removesuffix(".journal")
            Path(journal).write_text(
                text.replace("../prelude.journal", f"../../../preludes/{name}.journal")
            )


if __name__ == "__main__":
    main()
