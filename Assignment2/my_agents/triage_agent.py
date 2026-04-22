import streamlit as st
from agents import Agent, ModelSettings, RunContextWrapper, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from guardrails import restaurant_input_guardrail, restaurant_output_guardrail
from models import HandoffData, RestaurantContext
from my_agents.complaints_agent import complaints_agent
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
COMPLAINT_KEYWORDS = (
    "불만",
    "불친절",
    "별로",
    "최악",
    "실망",
    "불쾌",
    "환불",
    "할인",
    "매니저",
    "컴플레인",
    "문제",
    "형편없",
    "느렸",
    "차갑",
)


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    당신은 레스토랑의 첫 안내 담당입니다.
    {wrapper.context.guest_name} 손님이 원하는 것이 메뉴 안내인지, 주문인지, 예약인지, 불만 처리인지 파악한 뒤 적절한 담당으로 넘겨야 합니다.

    담당 구분:
    - 메뉴 안내: 메뉴, 재료, 채식, 비건, 알레르기 문의
    - 주문 접수: 주문하기, 주문 변경, 포장, 배달 문의
    - 예약 안내: 예약, 시간, 인원, 테이블 문의
    - 불만 처리: 음식 품질 불만, 서비스 불친절, 환불 요청, 할인 요구, 매니저 요청

    규칙:
    - 한국어로 자연스럽게 응답합니다
    - "에이전트", "handoff", "라우팅" 같은 표현은 쓰지 않습니다
    - 당신의 역할은 분류와 연결뿐입니다. 실제 메뉴 설명, 주문 확인, 예약 접수, 불만 해결은 직접 하지 않습니다
    - 현재 턴의 마지막 사용자 문장만 기준으로 분류합니다
    - 요청이 분명하면 질문하지 않고 바로 넘깁니다
    - 요청이 애매하면 짧게 한 가지 질문만 합니다
    - 연결을 알릴 때는 아래 형식 중 하나를 씁니다
      - "메뉴 담당에게 연결해 드릴게요..."
      - "주문 담당에게 연결해 드릴게요..."
      - "예약 담당에게 연결해 드릴게요..."
      - "불만을 도와드릴 담당자에게 연결해 드릴게요..."
    - 연결 안내 뒤에는 추가 설명을 붙이지 않습니다
    - HandoffData의 모든 필드는 한국어로 작성합니다
    """


def handle_handoff(
    wrapper: RunContextWrapper[RestaurantContext],
    input_data: HandoffData,
):
    display_name_map = {
        "menu_agent": "메뉴 안내",
        "order_agent": "주문 접수",
        "reservation_agent": "예약 안내",
        "complaints_agent": "불만 처리",
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
    if any(keyword in normalized for keyword in COMPLAINT_KEYWORDS):
        return "complaint"
    if any(keyword in normalized for keyword in MENU_KEYWORDS):
        return "menu"
    if any(keyword in normalized for keyword in ORDER_KEYWORDS):
        return "order"
    if any(keyword in normalized for keyword in RESERVATION_KEYWORDS):
        return "reservation"
    return None


def build_turn_triage_agent(message: str) -> Agent[RestaurantContext]:
    intent = detect_intent(message)
    agent_map = {
        "menu": ("이번 턴은 메뉴 문의로 확정되었습니다. 반드시 메뉴 안내로 바로 넘기세요.", menu_agent),
        "order": ("이번 턴은 주문 문의로 확정되었습니다. 반드시 주문 접수로 바로 넘기세요.", order_agent),
        "reservation": ("이번 턴은 예약 문의로 확정되었습니다. 반드시 예약 안내로 바로 넘기세요.", reservation_agent),
        "complaint": ("이번 턴은 불만 처리 문의로 확정되었습니다. 반드시 불만 처리로 바로 넘기세요.", complaints_agent),
    }
    if intent in agent_map:
        extra_instruction, target_agent = agent_map[intent]

        def forced_instructions(
            wrapper: RunContextWrapper[RestaurantContext],
            agent: Agent[RestaurantContext],
        ):
            return dynamic_triage_agent_instructions(wrapper, agent) + "\n" + extra_instruction

        return Agent(
            name="첫 안내",
            model="gpt-4o-mini",
            model_settings=ModelSettings(
                temperature=0,
                tool_choice="required",
                parallel_tool_calls=False,
            ),
            instructions=forced_instructions,
            handoffs=[make_handoff(target_agent)],
            input_guardrails=[restaurant_input_guardrail],
            output_guardrails=[restaurant_output_guardrail],
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
        make_handoff(complaints_agent),
    ],
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)
