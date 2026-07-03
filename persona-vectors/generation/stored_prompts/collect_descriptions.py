import json
from pathlib import Path


def main():
    here = Path(__file__).parent
    descriptions = {}

    for folder in sorted(here.iterdir()):
        if not folder.is_dir():
            continue
        desc_file = folder / "trait_description.json"
        if not desc_file.exists():
            continue
        with open(desc_file) as f:
            descriptions[folder.name] = json.load(f)

    out = here / "trait_descriptions.json"
    with open(out, "w") as f:
        json.dump(descriptions, f, indent=2)
    print(f"Wrote {len(descriptions)} traits to {out}")


if __name__ == "__main__":
    main()
