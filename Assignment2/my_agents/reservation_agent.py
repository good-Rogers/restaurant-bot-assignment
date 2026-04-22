from agents import Agent, RunContextWrapper

from guardrails import restaurant_output_guardrail
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
    - 예약을 처음 시작하는 턴이면 인원수와 희망 날짜를 함께 물어봅니다
    - 날짜와 인원까지 받은 뒤에 시간을 묻습니다
    - 답변은 짧고 서비스 문장처럼 들리게 작성합니다
    """


reservation_agent = Agent(
    name="reservation_agent",
    model="gpt-4o-mini",
    handoff_description="예약 접수, 예약 변경, 날짜와 시간, 인원 확인을 담당합니다.",
    instructions=dynamic_reservation_agent_instructions,
    tools=[
        check_reservation_availability,
        create_reservation,
    ],
    hooks=RestaurantToolUsageLoggingHooks(),
    output_guardrails=[restaurant_output_guardrail],
)
