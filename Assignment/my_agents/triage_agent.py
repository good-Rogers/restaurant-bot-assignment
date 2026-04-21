import streamlit as st
from agents import Agent, ModelSettings, RunContextWrapper, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from models import HandoffData, RestaurantContext
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


MENU_KEYWORDS = (
    "메뉴",
    "채식",
    "채색",
    "비건",
    "알레르기",
    "재료",
    "음식",
)
ORDER_KEYWORDS = (
    "주문",
    "포장",
    "배달",
    "테이크아웃",
)
RESERVATION_KEYWORDS = (
    "예약",
    "날짜",
    "시간",
    "인원",
    "테이블",
)


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    당신은 레스토랑의 첫 안내 담당입니다.
    {wrapper.context.guest_name} 손님이 원하는 것이 메뉴 안내인지, 주문인지, 예약인지 파악한 뒤 적절한 담당으로 넘겨야 합니다.

    메뉴 안내로 넘길 상황:
    - 메뉴 추천
    - 재료 질문
    - 채식, 비건, 알레르기 관련 문의

    주문 접수로 넘길 상황:
    - 주문하기
    - 주문 변경
    - 매장 식사 / 포장 관련 주문 문의

    예약 안내로 넘길 상황:
    - 테이블 예약
    - 예약 시간 확인
    - 예약 변경
    - 인원수와 좌석 요청

    규칙:
    - 한국어로 자연스럽게 응답합니다
    - "에이전트", "handoff", "라우팅" 같은 표현은 쓰지 않습니다
    - 당신의 역할은 분류와 연결뿐입니다. 메뉴 설명, 주문 확인, 예약 접수 같은 실제 답변은 직접 하지 않습니다
    - 현재 턴의 마지막 사용자 문장만 기준으로 분류합니다
    - 최신 문장에 다음 단어가 들어 있으면 해당 담당을 우선합니다
      - 메뉴 안내: 메뉴, 채식, 채색, 비건, 알레르기, 재료, 음식
      - 주문 접수: 주문, 포장, 배달, 테이크아웃
      - 예약 안내: 예약, 날짜, 시간, 인원, 테이블
    - 직전 턴이 예약이었더라도 현재 문장이 메뉴 문의면 메뉴 안내로 넘깁니다
    - 직전 턴이 메뉴 문의였더라도 현재 문장이 예약이면 예약 안내로 넘깁니다
    - 요청이 메뉴/주문/예약 중 하나로 분명하면, 직접 답하지 말고 즉시 해당 담당으로 넘깁니다
    - 손님의 최신 요청을 가장 우선해서 처리합니다
    - 이전에 예약이나 주문 이야기를 했더라도, 손님이 "그전에", "아니", "먼저", "잠깐"처럼 화제를 바꾸면 새로운 요청으로 취급합니다
    - 새 요청으로 넘어갔으면 이전 요청 내용을 이어서 답하지 않습니다
    - 애매하면 짧게 한 가지 질문만 합니다
    - 요청이 분명하면 질문하지 않고 바로 넘깁니다
    - 연결을 알릴 때는 "메뉴 관련 내용을 먼저 안내해드릴게요", "주문 관련 내용을 이어서 도와드릴게요", "예약 관련 내용을 이어서 도와드릴게요"처럼 한 문장만 짧게 말합니다
    - 연결 안내 뒤에는 추가 설명을 붙이지 않습니다
    - 그 다음 정확히 한 명의 담당으로 넘깁니다
    - HandoffData의 모든 필드는 한국어로 작성합니다

    예시:
    - 손님: "예약을 하고 싶어."
      답변: "예약 관련 내용을 이어서 도와드릴게요."
      그리고 바로 예약 안내로 넘깁니다.
    - 손님: "아, 그전에 채식 메뉴 있는지 알려줘."
      답변: "메뉴 관련 내용을 먼저 안내해드릴게요."
      그리고 바로 메뉴 안내로 넘깁니다.
    - 손님: "예약하고 싶어. 아, 그전에 채식 메뉴 알려줘."
      답변: "메뉴 관련 내용을 먼저 안내해드릴게요."
      그리고 바로 메뉴 안내로 넘깁니다.
    """


def handle_handoff(
    wrapper: RunContextWrapper[RestaurantContext],
    input_data: HandoffData,
):
    display_name_map = {
        "메뉴 안내": "메뉴 안내",
        "주문 접수": "주문 접수",
        "예약 안내": "예약 안내",
        "menu_agent": "메뉴 안내",
        "order_agent": "주문 접수",
        "reservation_agent": "예약 안내",
    }
    display_name = display_name_map.get(input_data.to_agent_name, input_data.to_agent_name)
    with st.sidebar:
        st.write(
            f"""
            ↪️ 연결 대상: {display_name}
            요청 유형: {input_data.request_type}
            연결 이유: {input_data.short_reason}
            요약: {input_data.short_summary}
            """
        )
def make_handoff(agent: Agent[RestaurantContext]):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


def detect_intent(message: str) -> str | None:
    normalized = message.strip().lower()
    if any(keyword in normalized for keyword in MENU_KEYWORDS):
        return "menu"
    if any(keyword in normalized for keyword in ORDER_KEYWORDS):
        return "order"
    if any(keyword in normalized for keyword in RESERVATION_KEYWORDS):
        return "reservation"
    return None


def build_turn_triage_agent(message: str) -> Agent[RestaurantContext]:
    intent = detect_intent(message)
    if intent == "menu":
        def forced_menu_instructions(
            wrapper: RunContextWrapper[RestaurantContext],
            agent: Agent[RestaurantContext],
        ):
            return (
                dynamic_triage_agent_instructions(wrapper, agent)
                + "\n이번 턴은 메뉴 문의로 확정되었습니다. 반드시 메뉴 안내로 바로 넘기세요."
            )

        return Agent(
            name="첫 안내",
            model="gpt-4o-mini",
            model_settings=ModelSettings(
                temperature=0,
                tool_choice="required",
                parallel_tool_calls=False,
            ),
            instructions=forced_menu_instructions,
            handoffs=[make_handoff(menu_agent)],
        )
    if intent == "order":
        def forced_order_instructions(
            wrapper: RunContextWrapper[RestaurantContext],
            agent: Agent[RestaurantContext],
        ):
            return (
                dynamic_triage_agent_instructions(wrapper, agent)
                + "\n이번 턴은 주문 문의로 확정되었습니다. 반드시 주문 접수로 바로 넘기세요."
            )

        return Agent(
            name="첫 안내",
            model="gpt-4o-mini",
            model_settings=ModelSettings(
                temperature=0,
                tool_choice="required",
                parallel_tool_calls=False,
            ),
            instructions=forced_order_instructions,
            handoffs=[make_handoff(order_agent)],
        )
    if intent == "reservation":
        def forced_reservation_instructions(
            wrapper: RunContextWrapper[RestaurantContext],
            agent: Agent[RestaurantContext],
        ):
            return (
                dynamic_triage_agent_instructions(wrapper, agent)
                + "\n이번 턴은 예약 문의로 확정되었습니다. 반드시 예약 안내로 바로 넘기세요."
            )

        return Agent(
            name="첫 안내",
            model="gpt-4o-mini",
            model_settings=ModelSettings(
                temperature=0,
                tool_choice="required",
                parallel_tool_calls=False,
            ),
            instructions=forced_reservation_instructions,
            handoffs=[make_handoff(reservation_agent)],
        )
    return triage_agent


triage_agent = Agent(
    name="첫 안내",
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        temperature=0,
        tool_choice="required",
        parallel_tool_calls=False,
    ),
    instructions=dynamic_triage_agent_instructions,
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)
