import asyncio

import dotenv
import streamlit as st
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner

from guardrails import input_guardrail_agent
from models import RestaurantContext
from my_agents.triage_agent import build_turn_triage_agent

dotenv.load_dotenv()


BLOCKED_INPUT_REPLY = (
    "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. "
    "메뉴를 확인하거나, 예약하거나, 음식을 주문하거나, 서비스 불편을 접수할 수 있어요."
)


HANDOFF_MESSAGES = {
    "menu_agent": {
        "triage": "Triage: 메뉴 담당에게 연결해 드릴게요...",
        "ui": "메뉴 전문가에게 연결합니다...",
    },
    "order_agent": {
        "triage": "Triage: 주문 담당에게 연결해 드릴게요...",
        "ui": "주문 담당자에게 연결합니다...",
    },
    "reservation_agent": {
        "triage": "Triage: 예약 담당에게 연결해 드릴게요...",
        "ui": "예약 전문가에게 연결합니다...",
    },
    "complaints_agent": {
        "triage": "Triage: 불만을 도와드릴 담당자에게 연결해 드릴게요...",
        "ui": "불만 처리 담당자에게 연결합니다...",
    },
}


guest_context = RestaurantContext(
    guest_name="Guest",
)

if "ui_history" not in st.session_state:
    st.session_state["ui_history"] = []


def paint_history():
    for message in st.session_state["ui_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_assistant_turn(
    triage_line: str,
    handoff_line: str,
    specialist_response: str,
) -> str:
    parts = []
    if triage_line:
        parts.append(triage_line)
    if handoff_line:
        parts.append(handoff_line)
    if specialist_response:
        parts.append(specialist_response)
    return "\n\n".join(parts)


st.title("어서 오세요.")
st.caption("메뉴 안내, 주문, 예약, 불만 접수를 도와드릴게요.")

paint_history()


async def run_agent(message: str):
    with st.chat_message("ai"):
        assistant_placeholder = st.empty()
        direct_response = ""
        triage_line = ""
        handoff_line = ""
        specialist_response = ""
        turn_triage_agent = build_turn_triage_agent(message)
        current_agent_name = turn_triage_agent.name
        handoff_started = False

        try:
            stream = Runner.run_streamed(
                turn_triage_agent,
                message,
                context=guest_context,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        if handoff_started:
                            specialist_response += event.data.delta
                            content = render_assistant_turn(
                                triage_line=triage_line,
                                handoff_line=handoff_line,
                                specialist_response=specialist_response,
                            )
                            assistant_placeholder.markdown(content.replace("$", "\\$"))
                        else:
                            direct_response += event.data.delta
                            assistant_placeholder.markdown(
                                direct_response.replace("$", "\\$")
                            )
                elif event.type == "agent_updated_stream_event":
                    if current_agent_name != event.new_agent.name:
                        current_agent_name = event.new_agent.name
                        handoff_started = True
                        handoff_message = HANDOFF_MESSAGES.get(
                            event.new_agent.name,
                            {
                                "triage": f"Triage: {event.new_agent.name} 담당에게 연결해 드릴게요...",
                                "ui": f"{event.new_agent.name}에게 연결합니다...",
                            },
                        )
                        direct_response = ""
                        triage_line = handoff_message["triage"]
                        handoff_line = handoff_message["ui"]
                        specialist_response = ""
                        content = render_assistant_turn(
                            triage_line=triage_line,
                            handoff_line=handoff_line,
                            specialist_response="",
                        )
                        assistant_placeholder.markdown(content)
        except InputGuardrailTripwireTriggered:
            result = await Runner.run(input_guardrail_agent, message, context=guest_context)
            blocked_content = BLOCKED_INPUT_REPLY
            with st.sidebar:
                st.write(f"⛔ 입력 가드레일 차단: {result.final_output.reason}")
            assistant_placeholder.markdown(blocked_content)
            st.session_state["ui_history"].append(
                {"role": "assistant", "content": blocked_content}
            )
            return
        except OutputGuardrailTripwireTriggered:
            blocked_content = "정중하고 안전한 안내만 드릴 수 있어요. 메뉴, 주문, 예약, 불만 처리와 관련된 요청으로 다시 말씀해 주세요."
            assistant_placeholder.markdown(blocked_content)
            st.session_state["ui_history"].append(
                {"role": "assistant", "content": blocked_content}
            )
            return

        if handoff_started:
            final_content = render_assistant_turn(
                triage_line=triage_line,
                handoff_line=handoff_line,
                specialist_response=specialist_response,
            )
        else:
            final_content = direct_response

        if final_content:
            st.session_state["ui_history"].append(
                {"role": "assistant", "content": final_content}
            )


message = st.chat_input("메뉴, 주문, 예약, 불만 중 무엇을 도와드릴까요?")

if message:
    with st.chat_message("user"):
        st.write(message)
    st.session_state["ui_history"].append({"role": "user", "content": message})
    asyncio.run(run_agent(message))


with st.sidebar:
    st.subheader("대화 메모리")
    reset = st.button("Reset memory")
    if reset:
        st.session_state["ui_history"] = []
    memory_items = st.session_state["ui_history"]
    st.caption(f"저장된 항목 수: {len(memory_items)}")
    with st.expander("메모리 보기"):
        st.write(memory_items)
