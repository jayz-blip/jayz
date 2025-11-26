"""
OpenAI API를 사용한 챗봇 모듈
사내 게시판 정보를 컨텍스트로 활용합니다.
"""
import os
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatBot:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.conversation_history = []
        
    def get_response(self, user_message, board_context="", is_problem_query=False, responsible_person_info=None):
        """사용자 메시지에 대한 응답 생성"""
        try:
            # 시스템 프롬프트 설정
            system_prompt = """당신은 사내 업무를 도와주는 AI 어시스턴트입니다. 
사내 게시판의 정보를 참고하여 정확하고 도움이 되는 답변을 제공하세요.
게시판 정보가 제공된 경우, 그 정보를 바탕으로 답변하되, 
정보가 없는 경우 일반적인 업무 지식으로 답변하세요.
답변은 한국어로 작성하세요.

중요한 지침:
1. 게시글의 작성자 정보가 있는 경우, 답변에 반드시 작성자 이름을 포함하세요. 
   예: "박선미과장님이 이렇게 답변을 해주었다"와 같이 작성자 이름을 명시하세요.
2. 덧글 정보가 있는 경우, 덧글 작성자와 내용을 함께 언급하세요."""
            
            # 문제 관련 질문인 경우 추가 지침
            if is_problem_query:
                system_prompt += """
3. 문제나 어려운 케이스에 대한 질문일 때는, 비슷한 기간 내의 게시글 중에서 
   덧글 수가 많은 게시글을 우선적으로 참고하여 답변하세요. 
   덧글이 많이 달린 게시글일수록 논란이 되었던 문제이거나 복잡한 케이스일 가능성이 높습니다.
   하지만 기간 필터링이나 다른 조건보다 우선하지 말고, 단지 참고 우선순위만 높이세요."""
            
            # 담당자 정보가 있는 경우 추가
            if responsible_person_info:
                person_name = responsible_person_info.get('name', '')
                last_activity = responsible_person_info.get('last_activity', '')
                system_prompt += f"""
4. 담당자 문의에 대한 답변:
   - 최근 담당자: {person_name}
   - 최근 활동일: {last_activity}
   위 정보를 바탕으로 해당 카테고리/업체에 대한 담당자를 안내하세요."""
            
            # 컨텍스트가 있으면 추가
            if board_context:
                system_prompt += f"\n\n[사내 게시판 정보]\n{board_context[:3000]}\n\n위 정보를 참고하여 답변하세요."
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 대화 기록 추가
            messages.extend(self.conversation_history[-10:])  # 최근 10개만 유지
            
            # 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            assistant_message = response.choices[0].message.content
            
            # 대화 기록 업데이트
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"응답 생성 중 오류: {str(e)}")
            return f"죄송합니다. 오류가 발생했습니다: {str(e)}"
    
    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []
        logger.info("대화 기록 초기화")

