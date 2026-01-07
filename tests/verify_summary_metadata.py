
import sys
from pathlib import Path
import importlib.util

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import 08_create_and_preview_videos.py
spec = importlib.util.spec_from_file_location("create_and_preview_videos", project_root / "src" / "08_create_and_preview_videos.py")
module = importlib.util.module_from_spec(spec)
sys.modules["create_and_preview_videos"] = module
spec.loader.exec_module(module)

generate_title = module.generate_title
generate_description = module.generate_description
generate_tags = module.generate_tags
detect_genre_tags = module.detect_genre_tags

def test_summary_metadata_generation():
    print("=" * 60)
    print("🧪 Summary Metadata Generation Verification (Default Mode)")
    print("=" * 60)

    # Test Case 1: Korean Book (Novel) - Default Mode
    title_ko = "데미안"
    print(f"\n[Test Case 1] Korean Title: {title_ko}")
    
    # Mock book_info
    book_info_ko = {
        'author': '헤르만 헤세',
        'categories': ['소설', '독일문학'],
        'description': '헤르만 헤세의 자전적 소설...'
    }
    
    print("-" * 30)
    print("1. Title Generation")
    # lang='ko' for Summary mode
    generated_title = generate_title(title_ko, "ko", author=book_info_ko['author'])
    print(f"Title: {generated_title}")
    
    print("-" * 30)
    print("2. Tags Generation")
    tags = generate_tags(title_ko, book_info_ko, "ko")
    print(f"Tags ({len(tags)}): {', '.join(tags)}")
    
    print("-" * 30)
    print("3. Description Generation")
    timestamps = {'summary_duration': 300, 'notebooklm_duration': 600}
    desc = generate_description(book_info_ko, "ko", title_ko, timestamps, author=book_info_ko['author'])
    print(f"Description:\n{desc[:500]}...\n(truncated)")


    # Test Case 2: English Book (Business) - Default Mode
    title_en = "Zero to One"
    print(f"\n\n[Test Case 2] English Title: {title_en}")
    
    book_info_en = {
        'author': 'Peter Thiel',
        'categories': ['Business', 'Economics', 'Startup'],
        'description': 'Notes on Startups, or How to Build the Future...'
    }
    
    print("-" * 30)
    print("1. Title Generation")
    # lang='en' for Summary mode
    generated_title_en = generate_title(title_en, "en", author=book_info_en['author'])
    print(f"Title: {generated_title_en}")
    
    print("-" * 30)
    print("2. Tags Generation")
    tags_en = generate_tags(title_en, book_info_en, "en")
    print(f"Tags ({len(tags_en)}): {', '.join(tags_en)}")

    print("-" * 30)
    print("3. Description Generation")
    timestamps = {'summary_duration': 300, 'notebooklm_duration': 600}
    desc_en = generate_description(book_info_en, "en", title_en, timestamps, author=book_info_en['author'])
    print(f"Description:\n{desc_en[:500]}...\n(truncated)")

if __name__ == "__main__":
    test_summary_metadata_generation()
