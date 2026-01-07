# YouTube Metadata Generation Guide

This document explains how to generate SEO-optimized metadata (Title, Description, Tags) for YouTube videos in the BookReview-AutoMaker project.

## 1. Overview

Metadata is generated in JSON format (`*.metadata.json`) which is then used by the upload script (`src/09_upload_from_metadata.py`). There are two main styles of metadata generation:

1.  **Summary Style**: For standard 5-minute AI summary videos.
2.  **Episode Style (Ildangbaek)**: For long-form videos combining NotebookLM parts and infographics.

---

## 2. Episode Style Metadata (Ildangbaek)

Use `src/20_create_episode_metadata.py` for long-form episode videos.

### Basic Usage
```bash
# Korean metadata
python src/20_create_episode_metadata.py --title "책제목" --language ko

# English metadata
python src/20_create_episode_metadata.py --title "Book Title" --language en
```

### Key Features
-   **Dynamic Part Detection**: Automatically detects how many parts (Part 1, Part 2, etc.) are in the video by checking `assets/notebooklm/`.
-   **Smart Timestamps**: Generates accurate timestamps based on the actual video file length.
-   **Genre Detection**: Analyzes the book title and info to categorize as Novel, Poetry, Essay, or General Work.
-   **SEO Tag Optimization**:
    -   Includes trending tags for the current year (e.g., 2026).
    -   English metadata automatically filters out Korean characters for international SEO.
-   **Character Limits**: Ensures titles are under YouTube's 100-character limit.

### Arguments
-   `--title`: The book title (required).
-   `--language`: `ko` or `en` (default: `ko`).
-   `--video-path`: Manual override for video file path.
-   `--thumbnail-path`: Manual override for thumbnail path.
-   `--preview`: Print to console without saving to file.

---

## 3. Summary Style Metadata

Standard summary metadata is typically created during the video creation process in `src/08_create_and_preview_videos.py`.

### Basic Usage
When running the video creation script:
```bash
python src/08_create_and_preview_videos.py --title "Book Title" --lang both
```

### Key Features
-   **Channel Name**: "1DANG100" (일당백).
-   **Title Format**: `[핵심 요약] {Title} 핵심 정리 | [Summary] {Title} Book Review`.
-   **Auto-Translation**: Uses `src/utils/translations.py` to map English and Korean titles/authors.

---

## 4. Metadata File Format

The resulting JSON file looks like this:

```json
{
  "video_path": "output/Book_Title_full_episode_ko.mp4",
  "title": "[한국어] 책제목 책 리뷰 | [Korean] Book Title Book Review",
  "description": "0:00 - Part 1: 작가와 배경\n...",
  "tags": ["일당백", "책리뷰", "2026", ...],
  "language": "ko",
  "book_title": "책제목",
  "thumbnail_path": "output/Book_Title_thumbnail_ko.jpg",
  "video_duration": 827.49
}
```

---

## 5. Troubleshooting

-   **Thumbnail Not Found**: Ensure the thumbnail is in the `output/` folder and follows the naming convention: `{SafeTitle}_thumbnail_{ko/en}.jpg`.
-   **Metadata Mismatch**: If you change the video length, regenerate the metadata to ensure timestamps are accurate.
-   **Title Too Long**: The script will truncate titles with "..." if they exceed 100 characters.

---

## 6. Next Step: Uploading

Once the metadata is ready, upload it using:
```bash
python src/09_upload_from_metadata.py --privacy private --auto
```
