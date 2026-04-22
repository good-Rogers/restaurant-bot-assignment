from agents import Agent, RunContextWrapper

from guardrails import restaurant_output_guardrail
from models import RestaurantContext
from tools import RestaurantToolUsageLoggingHooks, confirm_order, create_order_ticket


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    당신은 레스토랑의 주문 담당입니다.
    {wrapper.context.guest_name} 손님을 응대하고 있습니다.

    역할:
    - 주문을 받습니다
    - 매장 식사인지 포장인지 확인합니다
    - 빠진 정보가 있으면 짧게 되묻습니다
    - 주문 내용을 정리하고 최종 확인을 받습니다

    규칙:
    - 한국어로 자연스럽게 응답합니다
    - 현재 손님의 최신 질문이 주문 관련일 때만 주문 이야기를 진행합니다
    - 한 번에 하나의 확인 질문만 합니다
    - 주문 확정 전에는 주문 내용을 다시 한 번 정리합니다
    """


order_agent = Agent(
    name="order_agent",
    model="gpt-4o-mini",
    handoff_description="주문 접수, 주문 변경, 주문 확인 요청을 담당합니다.",
    instructions=dynamic_order_agent_instructions,
    tools=[
        create_order_ticket,
        confirm_order,
    ],
    hooks=RestaurantToolUsageLoggingHooks(),
    output_guardrails=[restaurant_output_guardrail],
)
