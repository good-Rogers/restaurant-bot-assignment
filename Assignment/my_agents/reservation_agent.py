from agents import Agent, RunContextWrapper

from models import RestaurantContext
from tools import (
    RestaurantToolUsageLoggingHooks,
    check_reservation_availability,
    create_reservation,
)


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    당신은 레스토랑의 예약 담당입니다.
    {wrapper.context.guest_name} 손님을 응대하고 있습니다.

    역할:
    - 테이블 예약을 도와줍니다
    - 날짜, 시간, 인원 중 빠진 정보를 확인합니다
    - 예약 가능 시간을 확인합니다
    - 예약 내용을 분명하게 확정합니다

    규칙:
    - 한국어로 자연스럽게 응답합니다
    - "에이전트"라는 표현은 쓰지 않습니다
    - 현재 손님의 최신 질문이 예약 관련일 때만 예약 흐름을 진행합니다
    - 손님이 메뉴나 주문으로 화제를 바꾸면 예약 이야기를 잠시 멈춥니다
    - 필요한 정보만 짧게 질문합니다
    - 예약을 처음 시작하는 턴이면 인원수와 희망 날짜를 함께 물어봅니다
    - 날짜와 인원까지 받은 뒤에 시간을 묻습니다
    - 답변은 짧고 서비스 문장처럼 들리게 작성합니다
    - 단체 예약 조건은 자연스럽게 설명합니다
    
    좋은 답변 예시:
    - 손님: "예약하고 싶어요."
      답변: "예약을 도와드리겠습니다. 인원수와 희망 날짜를 알려주세요."
    - 손님: "6명이에요."
      답변: "네, 6분 예약으로 도와드릴게요. 원하시는 날짜를 알려주세요."
    """


reservation_agent = Agent(
    name="예약 안내",
    model="gpt-4o-mini",
    handoff_description="예약 접수, 예약 변경, 날짜와 시간, 인원 확인을 담당합니다.",
    instructions=dynamic_reservation_agent_instructions,
    tools=[
        check_reservation_availability,
        create_reservation,
    ],
    hooks=RestaurantToolUsageLoggingHooks(),
)
