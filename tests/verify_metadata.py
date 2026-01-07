
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

spec = importlib.util.spec_from_file_location("create_episode_metadata", project_root / "src" / "20_create_episode_metadata.py")
module = importlib.util.module_from_spec(spec)
sys.modules["create_episode_metadata"] = module
spec.loader.exec_module(module)

generate_episode_title = module.generate_episode_title
generate_episode_description = module.generate_episode_description
generate_episode_tags = module.generate_episode_tags
detect_book_genre = module.detect_book_genre

def test_metadata_generation():
    print("=" * 60)
    print("🧪 Metadata Generation Verification")
    print("=" * 60)

    # Test Case 1: Korean Book (Novel)
    title_ko = "데미안"
    print(f"\n[Test Case 1] Korean Title: {title_ko}")
    
    # Mock book_info
    book_info_ko = {
        'author': '헤르만 헤세',
        'categories': ['소설', '독일문학']
    }
    
    print("-" * 30)
    print("1. Genre Detection")
    genre_ko, genre_en = detect_book_genre(title_ko, book_info_ko)
    print(f"Genre: {genre_ko} / {genre_en}")
    
    print("-" * 30)
    print("2. Title Generation")
    generated_title = generate_episode_title(title_ko, "ko", book_info_ko)
    print(f"Title: {generated_title}")
    
    print("-" * 30)
    print("3. Tags Generation")
    tags = generate_episode_tags(title_ko, "ko", book_info_ko)
    print(f"Tags ({len(tags)}): {', '.join(tags)}")
    
    print("-" * 30)
    print("4. Description Generation")
    desc = generate_episode_description(title_ko, "ko", 600.0, book_info_ko)
    print(f"Description:\n{desc[:300]}...\n(truncated)")


    # Test Case 2: English Book (Non-fiction)
    title_en = "Sapiens"
    print(f"\n\n[Test Case 2] English Title: {title_en}")
    
    book_info_en = {
        'author': 'Yuval Noah Harari',
        'categories': ['History', 'Anthropology', 'Non-fiction']
    }
    
    print("-" * 30)
    print("1. Genre Detection")
    genre_ko, genre_en = detect_book_genre(title_en, book_info_en)
    print(f"Genre: {genre_ko} / {genre_en}")
    
    print("-" * 30)
    print("2. Title Generation")
    generated_title_en = generate_episode_title(title_en, "en", book_info_en)
    print(f"Title: {generated_title_en}")
    
    print("-" * 30)
    print("3. Tags Generation")
    tags_en = generate_episode_tags(title_en, "en", book_info_en)
    print(f"Tags ({len(tags_en)}): {', '.join(tags_en)}")

    print("-" * 30)
    print("4. Description Generation")
    desc_en = generate_episode_description(title_en, "en", 600.0, book_info_en)
    print(f"Description:\n{desc_en[:300]}...\n(truncated)")

if __name__ == "__main__":
    test_metadata_generation()
