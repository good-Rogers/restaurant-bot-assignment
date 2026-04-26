from agents import Agent, ModelSettings, RunContextWrapper

from guardrails import restaurant_output_guardrail
from models import RestaurantContext
from tools import (
    RestaurantToolUsageLoggingHooks,
    allergy_safe_suggestions,
    dietary_menu_suggestions,
    explain_dish,
    get_menu_overview,
)


def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    당신은 레스토랑의 메뉴 안내 담당입니다.
    {wrapper.context.guest_name} 손님을 응대하고 있습니다.

    역할:
    - 메뉴를 설명합니다
    - 재료와 알레르기 정보를 정확히 안내합니다
    - 채식, 비건, 식단 요청을 반영해 메뉴를 추천합니다

    규칙:
    - 한국어로 자연스럽게 응답합니다
    - 메뉴와 관련 없는 주제를 끌어오지 않습니다
    - 답변은 보통 2~5문장 안에서 끝내고, 필요한 경우에만 목록을 사용합니다
    - 채식 메뉴 질문에는 첫 문장을 "네, 채식 메뉴가 있습니다."로 시작합니다
    - 채식, 비건, 글루텐프리, 알레르기 질문에는 추측하지 말고 반드시 도구를 사용해 확인한 뒤 답합니다
    """


menu_agent = Agent(
    name="menu_agent",
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        temperature=0,
        tool_choice="auto",
        parallel_tool_calls=False,
    ),
    handoff_description="메뉴, 재료, 채식 메뉴, 비건 메뉴, 알레르기 문의를 담당합니다.",
    instructions=dynamic_menu_agent_instructions,
    tools=[
        get_menu_overview,
        explain_dish,
        allergy_safe_suggestions,
        dietary_menu_suggestions,
    ],
    hooks=RestaurantToolUsageLoggingHooks(),
    output_guardrails=[restaurant_output_guardrail],
)
