#!/usr/bin/env python
"""
AgenticTravelRAG CLI Runner

터미널에서 직접 A.R.T Agent를 실행할 수 있는 CLI 스크립트입니다.

사용 예시:
    # 대화형 모드
    python scripts/run_agent.py --interactive
    
    # 단일 쿼리 실행
    python scripts/run_agent.py --query "파리에서 12월에 묵을 낭만적인 호텔 추천해줘"
    
    # 세션 ID 지정
    python scripts/run_agent.py --interactive --session-id my-session
"""

import argparse
import sys
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
import uuid
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드 (.env 파일)
env_path = project_root / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 환경 변수 로드 완료: {env_path}")
else:
    load_dotenv()
    print("⚠️  config/.env 파일을 찾을 수 없습니다. 시스템 환경 변수를 사용합니다.")

from src.core.workflow import ARTWorkflow
from src.core.state import AppState

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentCLI:
    """A.R.T Agent CLI 인터페이스"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Args:
            session_id: 세션 ID (없으면 자동 생성)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.workflow = ARTWorkflow()
        self.current_state: Optional[AppState] = None
        
        logger.info(f"🚀 A.R.T Agent 초기화 완료 (Session ID: {self.session_id})")
    
    async def run_single_query(self, query: str) -> str:
        """
        단일 쿼리를 실행하고 결과를 반환합니다.
        
        Args:
            query: 사용자 질문
            
        Returns:
            Agent의 응답
        """
        logger.info(f"📝 쿼리 실행: {query}")
        
        try:
            if self.current_state is None:
                # 첫 번째 쿼리
                result = await self.workflow.run(query, self.session_id)
            else:
                # 후속 대화
                result = await self.workflow.continue_conversation(
                    query, 
                    self.session_id, 
                    self.current_state
                )
            
            # 상태 저장
            self.current_state = result.get('state')
            
            # 응답 추출
            itinerary = result.get('itinerary', {})
            if isinstance(itinerary, dict):
                response = itinerary.get('summary', '응답을 생성할 수 없습니다.')
            else:
                response = str(itinerary) if itinerary else '응답을 생성할 수 없습니다.'
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 쿼리 실행 중 오류 발생: {e}", exc_info=True)
            return f"오류가 발생했습니다: {str(e)}"
    
    def run_interactive(self):
        """대화형 모드로 실행합니다."""
        print("\n" + "="*70)
        print("🌍 AgenticTravelRAG (A.R.T) - 대화형 모드")
        print("="*70)
        print(f"세션 ID: {self.session_id}")
        print("\n💡 사용 팁:")
        print("  - 여행 관련 질문을 자유롭게 입력하세요")
        print("  - 'quit', 'exit', 'q'를 입력하면 종료됩니다")
        print("  - 'clear'를 입력하면 대화 기록을 초기화합니다")
        print("="*70 + "\n")
        
        while True:
            try:
                # 사용자 입력 받기
                user_input = input("👤 You: ").strip()
                
                # 종료 명령어 체크
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 A.R.T를 이용해 주셔서 감사합니다!")
                    break
                
                # 대화 초기화 명령어
                if user_input.lower() == 'clear':
                    self.current_state = None
                    self.session_id = str(uuid.uuid4())
                    print(f"\n🔄 대화 기록이 초기화되었습니다. (새 세션 ID: {self.session_id})\n")
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 쿼리 실행 (비동기)
                print("\n🤖 A.R.T: ", end="", flush=True)
                response = asyncio.run(self.run_single_query(user_input))
                print(response)
                print()  # 빈 줄 추가
                
            except KeyboardInterrupt:
                print("\n\n👋 A.R.T를 이용해 주셔서 감사합니다!")
                break
            except Exception as e:
                logger.error(f"❌ 오류 발생: {e}", exc_info=True)
                print(f"\n⚠️  오류가 발생했습니다: {str(e)}\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="AgenticTravelRAG (A.R.T) CLI - 터미널에서 여행 플래너 Agent 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 대화형 모드로 실행
  python scripts/run_agent.py --interactive
  
  # 단일 쿼리 실행
  python scripts/run_agent.py --query "파리에서 12월에 묵을 낭만적인 호텔 추천해줘"
  
  # 세션 ID를 지정하여 대화 이어가기
  python scripts/run_agent.py --interactive --session-id abc123
  
  # 디버그 모드로 실행
  python scripts/run_agent.py --interactive --debug
        """
    )
    
    # 실행 모드
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='대화형 모드로 실행 (연속 대화 가능)'
    )
    mode_group.add_argument(
        '-q', '--query',
        type=str,
        help='단일 쿼리 실행 (한 번만 질문하고 종료)'
    )
    
    # 옵션
    parser.add_argument(
        '-s', '--session-id',
        type=str,
        help='세션 ID 지정 (없으면 자동 생성)'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='디버그 모드 활성화 (상세 로그 출력)'
    )
    
    args = parser.parse_args()
    
    # 디버그 모드 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔍 디버그 모드 활성화")
    
    # CLI 인스턴스 생성
    cli = AgentCLI(session_id=args.session_id)
    
    # 실행 모드에 따라 분기
    if args.interactive:
        cli.run_interactive()
    elif args.query:
        response = asyncio.run(cli.run_single_query(args.query))
        print(f"\n🤖 A.R.T: {response}\n")


if __name__ == "__main__":
    main()
