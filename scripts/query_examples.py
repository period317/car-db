"""cardb.sqlite 예시 조회. 실행: python -I scripts/query_examples.py"""
import sqlite3, os
db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "unified", "cardb.sqlite")
c = sqlite3.connect(db)

print("1) 최대혜택 상위 5 (원):")
for r in c.execute("SELECT brand_ko, model, max_benefit_krw FROM records WHERE max_benefit_krw IS NOT NULL ORDER BY max_benefit_krw DESC LIMIT 5"):
    print("  ", r)

print("2) 3천만원 이하 신차 (가격 있는 레코드):")
for r in c.execute("SELECT brand_ko, model, price_krw FROM records WHERE category='price' AND price_krw<=30000000 ORDER BY price_krw LIMIT 8"):
    print("  ", r)

print("3) 카테고리별 건수:")
for r in c.execute("SELECT category, COUNT(*) FROM records GROUP BY category"):
    print("  ", r)

print("4) 데이터 없는 브랜드:")
for r in c.execute("SELECT id, brand_ko FROM brands WHERE has_data=0"):
    print("  ", r)
