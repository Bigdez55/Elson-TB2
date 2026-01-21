"""
Seed script for educational content, learning paths, and trading permissions.
Run this script to populate the database with comprehensive educational content.

Usage:
    python -m app.db.seed_education
"""

import sys
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.education import (
    CompletionRequirement,
    ContentLevel,
    ContentType,
    EducationalContent,
    LearningPath,
    LearningPathItem,
    TradingPermission,
    UserPermission,
    content_prerequisites,
)


def clear_existing_data(db: Session):
    """Clear all existing educational data."""
    print("Clearing existing educational data...")

    # Delete in order of dependencies
    db.query(LearningPathItem).delete()
    db.execute(
        content_prerequisites.delete()
    )  # Use Table.delete() for association table
    db.query(UserPermission).delete()
    db.query(TradingPermission).delete()
    db.query(LearningPath).delete()
    db.query(EducationalContent).delete()

    db.commit()
    print("✓ Existing data cleared")


def seed_beginner_content(db: Session) -> dict:
    """Seed beginner-level educational content."""
    print("\nSeeding beginner content...")

    content_items = []

    # 1. Introduction to Stock Trading (Module)
    content_items.append(
        EducationalContent(
            title="Introduction to Stock Trading",
            slug="intro-stock-trading",
            description="Learn the fundamentals of stock trading, including what stocks are, how markets work, and basic terminology.",
            content_type=ContentType.MODULE,
            level=ContentLevel.BEGINNER,
            completion_requirement=CompletionRequirement.TIME,
            estimated_minutes=30,
            min_age=13,
            importance_level=10,
            content_path="/education/modules/intro-stock-trading",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 2. Understanding Market Orders (Article)
    content_items.append(
        EducationalContent(
            title="Understanding Market Orders",
            slug="understanding-market-orders",
            description="Learn about different order types: market orders, limit orders, stop orders, and when to use each one.",
            content_type=ContentType.ARTICLE,
            level=ContentLevel.BEGINNER,
            completion_requirement=CompletionRequirement.TIME,
            estimated_minutes=15,
            min_age=13,
            importance_level=9,
            content_path="/education/articles/market-orders",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 3. Stock Market Basics Quiz
    content_items.append(
        EducationalContent(
            title="Stock Market Basics Quiz",
            slug="stock-market-basics-quiz",
            description="Test your knowledge of basic stock market concepts and terminology.",
            content_type=ContentType.QUIZ,
            level=ContentLevel.BEGINNER,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=10,
            min_age=13,
            importance_level=8,
            passing_score=70,
            content_path="/education/quizzes/stock-basics",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 4. Reading Stock Charts (Video)
    content_items.append(
        EducationalContent(
            title="Reading Stock Charts - Basics",
            slug="reading-stock-charts",
            description="Visual guide to understanding stock price charts, including candlesticks, volume, and basic patterns.",
            content_type=ContentType.VIDEO,
            level=ContentLevel.BEGINNER,
            completion_requirement=CompletionRequirement.TIME,
            estimated_minutes=20,
            min_age=13,
            importance_level=7,
            content_path="/education/videos/stock-charts",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 5. Risk Management Fundamentals (Module)
    content_items.append(
        EducationalContent(
            title="Risk Management Fundamentals",
            slug="risk-management-fundamentals",
            description="Learn how to protect your investments through proper risk management, position sizing, and diversification.",
            content_type=ContentType.MODULE,
            level=ContentLevel.BEGINNER,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=25,
            min_age=13,
            importance_level=10,
            passing_score=80,
            content_path="/education/modules/risk-management",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # Add all content to database
    for item in content_items:
        db.add(item)

    db.commit()

    # Refresh to get IDs
    for item in content_items:
        db.refresh(item)

    print(f"✓ Added {len(content_items)} beginner content items")

    return {
        "intro_stock_trading": content_items[0],
        "market_orders": content_items[1],
        "basics_quiz": content_items[2],
        "stock_charts": content_items[3],
        "risk_management": content_items[4],
    }


def seed_intermediate_content(db: Session) -> dict:
    """Seed intermediate-level educational content."""
    print("\nSeeding intermediate content...")

    content_items = []

    # 1. Technical Analysis Introduction (Module)
    content_items.append(
        EducationalContent(
            title="Technical Analysis Introduction",
            slug="technical-analysis-intro",
            description="Learn to analyze stock price movements using technical indicators like moving averages, RSI, and MACD.",
            content_type=ContentType.MODULE,
            level=ContentLevel.INTERMEDIATE,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=45,
            min_age=16,
            importance_level=8,
            passing_score=75,
            content_path="/education/modules/technical-analysis",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 2. Fundamental Analysis Basics (Module)
    content_items.append(
        EducationalContent(
            title="Fundamental Analysis Basics",
            slug="fundamental-analysis-basics",
            description="Understand company financials, P/E ratios, earnings reports, and how to evaluate stock value.",
            content_type=ContentType.MODULE,
            level=ContentLevel.INTERMEDIATE,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=40,
            min_age=16,
            importance_level=8,
            passing_score=75,
            content_path="/education/modules/fundamental-analysis",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 3. Portfolio Diversification Strategies (Article)
    content_items.append(
        EducationalContent(
            title="Portfolio Diversification Strategies",
            slug="portfolio-diversification",
            description="Learn advanced diversification techniques across sectors, asset classes, and risk profiles.",
            content_type=ContentType.ARTICLE,
            level=ContentLevel.INTERMEDIATE,
            completion_requirement=CompletionRequirement.TIME,
            estimated_minutes=25,
            min_age=16,
            importance_level=7,
            content_path="/education/articles/diversification",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 4. Options Trading Basics (Interactive)
    content_items.append(
        EducationalContent(
            title="Options Trading Basics",
            slug="options-trading-basics",
            description="Interactive guide to understanding call and put options, including strategies and risk management.",
            content_type=ContentType.INTERACTIVE,
            level=ContentLevel.INTERMEDIATE,
            completion_requirement=CompletionRequirement.INTERACTION,
            estimated_minutes=50,
            min_age=18,
            importance_level=9,
            content_path="/education/interactive/options-basics",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    for item in content_items:
        db.add(item)

    db.commit()

    for item in content_items:
        db.refresh(item)

    print(f"✓ Added {len(content_items)} intermediate content items")

    return {
        "technical_analysis": content_items[0],
        "fundamental_analysis": content_items[1],
        "diversification": content_items[2],
        "options_basics": content_items[3],
    }


def seed_advanced_content(db: Session) -> dict:
    """Seed advanced-level educational content."""
    print("\nSeeding advanced content...")

    content_items = []

    # 1. Advanced Options Strategies (Module)
    content_items.append(
        EducationalContent(
            title="Advanced Options Strategies",
            slug="advanced-options-strategies",
            description="Master complex options strategies like spreads, straddles, iron condors, and butterfly spreads.",
            content_type=ContentType.MODULE,
            level=ContentLevel.ADVANCED,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=60,
            min_age=18,
            importance_level=7,
            passing_score=80,
            content_path="/education/modules/advanced-options",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 2. Algorithmic Trading Concepts (Module)
    content_items.append(
        EducationalContent(
            title="Algorithmic Trading Concepts",
            slug="algorithmic-trading",
            description="Introduction to automated trading, backtesting strategies, and understanding trading algorithms.",
            content_type=ContentType.MODULE,
            level=ContentLevel.ADVANCED,
            completion_requirement=CompletionRequirement.QUIZ,
            estimated_minutes=55,
            min_age=18,
            importance_level=8,
            passing_score=85,
            content_path="/education/modules/algo-trading",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 3. Market Psychology and Sentiment (Article)
    content_items.append(
        EducationalContent(
            title="Market Psychology and Sentiment Analysis",
            slug="market-psychology",
            description="Understand how market psychology, sentiment indicators, and behavioral finance affect trading decisions.",
            content_type=ContentType.ARTICLE,
            level=ContentLevel.ADVANCED,
            completion_requirement=CompletionRequirement.TIME,
            estimated_minutes=30,
            min_age=18,
            importance_level=6,
            content_path="/education/articles/market-psychology",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    for item in content_items:
        db.add(item)

    db.commit()

    for item in content_items:
        db.refresh(item)

    print(f"✓ Added {len(content_items)} advanced content items")

    return {
        "advanced_options": content_items[0],
        "algo_trading": content_items[1],
        "market_psychology": content_items[2],
    }


def seed_learning_paths(
    db: Session,
    beginner_content: dict,
    intermediate_content: dict,
    advanced_content: dict,
):
    """Create structured learning paths."""
    print("\nSeeding learning paths...")

    paths = []

    # 1. Beginner Trading Path
    beginner_path = LearningPath(
        title="Beginner Trading Path",
        slug="beginner-trading-path",
        description="Complete guide for new traders. Learn the fundamentals of stock trading and risk management.",
        min_age=13,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(beginner_path)
    db.commit()
    db.refresh(beginner_path)

    # Add items to beginner path
    beginner_items = [
        LearningPathItem(
            learning_path_id=beginner_path.id,
            content_id=beginner_content["intro_stock_trading"].id,
            order=1,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=beginner_path.id,
            content_id=beginner_content["market_orders"].id,
            order=2,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=beginner_path.id,
            content_id=beginner_content["stock_charts"].id,
            order=3,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=beginner_path.id,
            content_id=beginner_content["risk_management"].id,
            order=4,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=beginner_path.id,
            content_id=beginner_content["basics_quiz"].id,
            order=5,
            is_required=True,
        ),
    ]

    for item in beginner_items:
        db.add(item)

    paths.append(beginner_path)

    # 2. Intermediate Trader Path
    intermediate_path = LearningPath(
        title="Intermediate Trader Path",
        slug="intermediate-trader-path",
        description="Advance your trading knowledge with technical and fundamental analysis.",
        min_age=16,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(intermediate_path)
    db.commit()
    db.refresh(intermediate_path)

    intermediate_items = [
        LearningPathItem(
            learning_path_id=intermediate_path.id,
            content_id=intermediate_content["technical_analysis"].id,
            order=1,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=intermediate_path.id,
            content_id=intermediate_content["fundamental_analysis"].id,
            order=2,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=intermediate_path.id,
            content_id=intermediate_content["diversification"].id,
            order=3,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=intermediate_path.id,
            content_id=intermediate_content["options_basics"].id,
            order=4,
            is_required=False,  # Optional for intermediate
        ),
    ]

    for item in intermediate_items:
        db.add(item)

    paths.append(intermediate_path)

    # 3. Options Trading Path
    options_path = LearningPath(
        title="Options Trading Mastery",
        slug="options-trading-mastery",
        description="Master options trading from basics to advanced strategies. Requires 18+ years old.",
        min_age=18,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(options_path)
    db.commit()
    db.refresh(options_path)

    options_items = [
        LearningPathItem(
            learning_path_id=options_path.id,
            content_id=intermediate_content["options_basics"].id,
            order=1,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=options_path.id,
            content_id=advanced_content["advanced_options"].id,
            order=2,
            is_required=True,
        ),
        LearningPathItem(
            learning_path_id=options_path.id,
            content_id=advanced_content["market_psychology"].id,
            order=3,
            is_required=False,
        ),
    ]

    for item in options_items:
        db.add(item)

    paths.append(options_path)

    db.commit()

    print(f"✓ Added {len(paths)} learning paths with items")

    return {
        "beginner_path": beginner_path,
        "intermediate_path": intermediate_path,
        "options_path": options_path,
    }


def seed_prerequisites(
    db: Session,
    beginner_content: dict,
    intermediate_content: dict,
    advanced_content: dict,
):
    """Set up content prerequisites."""
    print("\nSeeding content prerequisites...")

    prerequisite_data = []

    # Quiz requires module completion
    prerequisite_data.append(
        {
            "content_id": beginner_content["basics_quiz"].id,
            "prerequisite_id": beginner_content["intro_stock_trading"].id,
        }
    )

    # Intermediate requires beginner completion
    prerequisite_data.append(
        {
            "content_id": intermediate_content["technical_analysis"].id,
            "prerequisite_id": beginner_content["basics_quiz"].id,
        }
    )

    prerequisite_data.append(
        {
            "content_id": intermediate_content["fundamental_analysis"].id,
            "prerequisite_id": beginner_content["basics_quiz"].id,
        }
    )

    # Options require intermediate knowledge
    prerequisite_data.append(
        {
            "content_id": intermediate_content["options_basics"].id,
            "prerequisite_id": intermediate_content["technical_analysis"].id,
        }
    )

    # Advanced options require basic options
    prerequisite_data.append(
        {
            "content_id": advanced_content["advanced_options"].id,
            "prerequisite_id": intermediate_content["options_basics"].id,
        }
    )

    # Algo trading requires technical analysis
    prerequisite_data.append(
        {
            "content_id": advanced_content["algo_trading"].id,
            "prerequisite_id": intermediate_content["technical_analysis"].id,
        }
    )

    # Insert into association table
    for prereq in prerequisite_data:
        db.execute(content_prerequisites.insert().values(prereq))

    db.commit()

    print(f"✓ Added {len(prerequisite_data)} prerequisite relationships")


def seed_permissions(db: Session, paths: dict, beginner_content: dict):
    """Create trading permissions linked to educational requirements."""
    print("\nSeeding trading permissions...")

    permissions = []

    # 1. Stock Trading Permission (Beginner)
    permissions.append(
        TradingPermission(
            name="Stock Trading Permission",
            description="Allows user to trade stocks in live mode. Requires completion of beginner trading course.",
            permission_type="trade_stocks",
            requires_guardian_approval=True,  # For users under 18
            min_age=13,
            required_learning_path_id=paths["beginner_path"].id,
            required_score=70,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 2. Options Trading Permission (Advanced)
    permissions.append(
        TradingPermission(
            name="Options Trading Permission",
            description="Allows user to trade options. Requires 18+ and completion of options trading course.",
            permission_type="trade_options",
            requires_guardian_approval=False,
            min_age=18,
            required_learning_path_id=paths["options_path"].id,
            required_score=80,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 3. Margin Trading Permission (Advanced)
    permissions.append(
        TradingPermission(
            name="Margin Trading Permission",
            description="Allows margin trading with borrowed funds. Requires 21+ and intermediate trading knowledge.",
            permission_type="trade_margin",
            requires_guardian_approval=False,
            min_age=21,
            required_learning_path_id=paths["intermediate_path"].id,
            required_score=85,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # 4. Algorithmic Trading Permission
    permissions.append(
        TradingPermission(
            name="Algorithmic Trading Permission",
            description="Allows automated trading strategies. Requires completion of algorithmic trading course.",
            permission_type="trade_algorithmic",
            requires_guardian_approval=False,
            min_age=18,
            required_content_id=beginner_content["risk_management"].id,
            required_score=90,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )

    for perm in permissions:
        db.add(perm)

    db.commit()

    print(f"✓ Added {len(permissions)} trading permissions")


def main():
    """Main seed function."""
    print("=" * 80)
    print("  EDUCATION SYSTEM SEED SCRIPT")
    print("=" * 80)

    db = SessionLocal()

    try:
        # Clear existing data
        clear_existing_data(db)

        # Seed content
        beginner_content = seed_beginner_content(db)
        intermediate_content = seed_intermediate_content(db)
        advanced_content = seed_advanced_content(db)

        # Seed learning paths
        paths = seed_learning_paths(
            db, beginner_content, intermediate_content, advanced_content
        )

        # Seed prerequisites
        seed_prerequisites(db, beginner_content, intermediate_content, advanced_content)

        # Seed permissions
        seed_permissions(db, paths, beginner_content)

        print("\n" + "=" * 80)
        print("  ✅ SEED SCRIPT COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nSummary:")
        print(
            f"  - Educational Content: {len(beginner_content) + len(intermediate_content) + len(advanced_content)} items"
        )
        print(f"  - Learning Paths: {len(paths)}")
        print(f"  - Trading Permissions: 4")
        print(f"  - Prerequisites: 6 relationships")
        print("\nNext Steps:")
        print("  1. Restart the backend server to pick up changes")
        print("  2. Visit http://localhost:8000/api/v1/education/content to verify")
        print("  3. Check the Learn page in the frontend\n")

    except Exception as e:
        print(f"\n❌ Error during seed: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
