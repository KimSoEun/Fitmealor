from sqlalchemy import text

def test_meal_insert(db_session):
    db_session.execute(text("""
        INSERT INTO meal (canonical_name, is_active, calories, protein_g, carb_g, fat_g)
        VALUES ('pytest-meal', TRUE, 0, 0, 0, 0)
        ON CONFLICT DO NOTHING;
    """))
    rows = db_session.execute(text("SELECT COUNT(*) FROM meal")).scalar_one()
    assert rows >= 1
