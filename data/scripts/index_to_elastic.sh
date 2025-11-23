#!/bin/bash
# ElasticSearch 인덱싱 스크립트 (Mac/Linux)
# 다운로드한 데이터를 ElasticSearch에 인덱싱합니다.

echo "📊 ElasticSearch 인덱싱 시작..."
echo "================================"
echo "⚠️  주의: ElasticSearch가 실행 중이어야 합니다."
echo ""

# ElasticSearch 연결 확인
if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo "❌ ElasticSearch가 실행되지 않았습니다."
    echo "   다음 명령어로 실행하세요:"
    echo "   docker-compose -f docker/docker-compose.yml up -d elasticsearch"
    exit 1
fi

echo "✅ ElasticSearch 연결 확인 완료"
echo ""

# Python 모듈로 실행
python -m data.scripts.index_to_elastic

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 인덱싱 완료!"
    echo "================================"
else
    echo ""
    echo "❌ 인덱싱 실패. 오류를 확인하세요."
    exit 1
fi
