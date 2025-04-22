import json
from collections import defaultdict

VIDEO_LOG = "video/metadata.jsonl"


def load_entries():
    with open(VIDEO_LOG, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize_top_thumbnails(entries):
    summary = defaultdict(lambda: {"uses": 0, "views": 0})

    for entry in entries:
        stats = entry.get("thumbnail_stats", {})
        for thumb, data in stats.items():
            summary[thumb]["uses"] += data.get("uses", 0)
            summary[thumb]["views"] += data.get("views", 0)

    for thumb, data in summary.items():
        views = data["views"]
        uses = data["uses"]
        score = round(views / uses, 2) if uses > 0 else 0.0
        summary[thumb]["score"] = score

    # Sort by score descending
    top = sorted(summary.items(), key=lambda x: x[1]["score"], reverse=True)

    print("\n🎯 Top Performing Thumbnails:")
    for i, (thumb, data) in enumerate(top[:10]):
        print(f"{i+1:2d}. {thumb} — Score: {data['score']} | Views: {data['views']} | Uses: {data['uses']}")


if __name__ == "__main__":
    entries = load_entries()
    summarize_top_thumbnails(entries)
