import streamlit as st
from agents import Agent, AgentHooks, RunContextWrapper, Tool, function_tool

from models import RestaurantContext


MENU_DATA = {
    "truffle mushroom risotto": {
        "category": "main",
        "price": "$19",
        "ingredients": "arborio rice, mushroom stock, parmesan, truffle oil, mushrooms",
        "tags": ["vegetarian"],
        "allergens": ["dairy"],
    },
    "garden pesto pasta": {
        "category": "main",
        "price": "$17",
        "ingredients": "pasta, basil pesto, cherry tomatoes, zucchini, parmesan",
        "tags": ["vegetarian"],
        "allergens": ["gluten", "dairy", "nuts"],
    },
    "grilled salmon plate": {
        "category": "main",
        "price": "$23",
        "ingredients": "salmon, lemon butter, asparagus, roasted potatoes",
        "tags": ["high-protein"],
        "allergens": ["fish", "dairy"],
    },
    "smoky barbecue burger": {
        "category": "main",
        "price": "$18",
        "ingredients": "beef patty, brioche bun, cheddar, onion jam, fries",
        "tags": [],
        "allergens": ["gluten", "dairy"],
    },
    "crispy cauliflower bites": {
        "category": "starter",
        "price": "$11",
        "ingredients": "cauliflower, rice flour batter, chili glaze",
        "tags": ["vegan"],
        "allergens": [],
    },
    "seasonal green salad": {
        "category": "starter",
        "price": "$10",
        "ingredients": "mixed greens, cucumber, radish, citrus vinaigrette",
        "tags": ["vegan", "gluten-free"],
        "allergens": [],
    },
    "dark chocolate tart": {
        "category": "dessert",
        "price": "$9",
        "ingredients": "dark chocolate, cream, tart shell, sea salt",
        "tags": ["dessert"],
        "allergens": ["gluten", "dairy", "egg"],
    },
}


@function_tool
def get_menu_overview(context: RestaurantContext, category: str = "all") -> str:
    normalized = category.lower().strip()
    items = []
    for dish, info in MENU_DATA.items():
        if normalized != "all" and info["category"] != normalized:
            continue
        tags = f" ({', '.join(info['tags'])})" if info["tags"] else ""
        items.append(f"- {dish.title()} {info['price']}{tags}")

    if not items:
        return f"'{category}' 카테고리의 메뉴를 찾지 못했습니다."

    category_label = "전체" if normalized == "all" else category
    return f"{category_label} 메뉴 안내:\n" + "\n".join(items)


@function_tool
def explain_dish(context: RestaurantContext, dish_name: str) -> str:
    key = dish_name.lower().strip()
    if key not in MENU_DATA:
        return f"'{dish_name}' 메뉴를 찾지 못했습니다."

    dish = MENU_DATA[key]
    tags = ", ".join(dish["tags"]) if dish["tags"] else "없음"
    allergens = ", ".join(dish["allergens"]) if dish["allergens"] else "없음"
    return (
        f"{dish_name.title()} 가격은 {dish['price']}입니다.\n"
        f"재료: {dish['ingredients']}.\n"
        f"특징: {tags}.\n"
        f"알레르기 정보: {allergens}."
    )


@function_tool
def allergy_safe_suggestions(
    context: RestaurantContext, allergy: str, dietary_preference: str = ""
) -> str:
    allergy_key = allergy.lower().strip()
    preference_key = dietary_preference.lower().strip()
    safe_items = []
    for dish, info in MENU_DATA.items():
        if allergy_key in [item.lower() for item in info["allergens"]]:
            continue
        if preference_key and preference_key not in [tag.lower() for tag in info["tags"]]:
            continue
        safe_items.append(f"- {dish.title()} ({info['price']})")

    if not safe_items:
        return f"{allergy}를 피하면서 '{dietary_preference or '일반'}' 조건에 맞는 메뉴를 찾지 못했습니다."

    preference_text = f", 그리고 {dietary_preference} 조건에 맞는" if dietary_preference else ""
    return f"{allergy}를 피할 수 있고{preference_text} 메뉴는 다음과 같습니다:\n" + "\n".join(safe_items)


@function_tool
def create_order_ticket(
    context: RestaurantContext, items: str, service_type: str = "매장", notes: str = ""
) -> str:
    notes_text = notes if notes else "없음"
    return (
        f"{context.guest_name}님의 주문 초안입니다.\n"
        f"- 이용 방식: {service_type}\n"
        f"- 주문 항목: {items}\n"
        f"- 요청 사항: {notes_text}\n"
        "최종 제출 전에 한 번 더 확인해 주세요."
    )


@function_tool
def confirm_order(
    context: RestaurantContext, items: str, estimated_minutes: int = 20
) -> str:
    return (
        f"{context.guest_name}님의 주문이 확인되었습니다.\n"
        f"주문 항목: {items}\n"
        f"예상 준비 시간: {estimated_minutes}분입니다."
    )


@function_tool
def check_reservation_availability(
    context: RestaurantContext, date: str, party_size: int
) -> str:
    if party_size >= 7:
        return (
            f"{date}에 {party_size}명 예약 가능 시간은 오후 6:30, 오후 8:15입니다. "
            "단체 예약은 카드 홀드가 필요합니다."
        )
    return f"{date}에 {party_size}명 예약 가능 시간은 오후 5:30, 오후 7:00, 오후 8:30입니다."


@function_tool
def create_reservation(
    context: RestaurantContext, name: str, party_size: int, date: str, time: str, notes: str = ""
) -> str:
    notes_text = notes if notes else "없음"
    return (
        f"예약이 확정되었습니다.\n"
        f"예약자명: {name}\n"
        f"인원: {party_size}명\n"
        f"날짜: {date}\n"
        f"시간: {time}\n"
        f"메모: {notes_text}"
    )


@function_tool
def offer_refund(context: RestaurantContext, reason: str) -> str:
    return (
        "환불 검토 요청이 접수되었습니다.\n"
        f"사유: {reason}\n"
        "영업일 기준 1~2일 안에 결제 내역을 확인한 뒤 안내드리겠습니다."
    )


@function_tool
def offer_discount(context: RestaurantContext, amount_percent: int = 50) -> str:
    return (
        f"다음 방문 시 사용 가능한 {amount_percent}% 할인 안내를 준비했습니다.\n"
        "원하시면 적용 방법을 바로 정리해드리겠습니다."
    )


@function_tool
def request_manager_callback(
    context: RestaurantContext, phone_or_email: str
) -> str:
    return (
        "매니저 콜백 요청을 접수했습니다.\n"
        f"연락처: {phone_or_email}\n"
        "가능한 빠르게 연락드릴 수 있도록 전달하겠습니다."
    )


@function_tool
def escalate_serious_issue(context: RestaurantContext, summary: str) -> str:
    return (
        "심각한 이슈로 분류해 매니저에게 즉시 전달했습니다.\n"
        f"요약: {summary}\n"
        "우선 확인 후 후속 조치를 안내드리겠습니다."
    )


class RestaurantToolUsageLoggingHooks(AgentHooks):
    async def on_tool_start(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 {agent.name}가 `{tool.name}` 실행을 시작했습니다.")

    async def on_tool_end(
        self,
        context: RunContextWrapper[RestaurantContext],
        agent: Agent[RestaurantContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 {agent.name}가 `{tool.name}` 실행을 마쳤습니다.")
            st.code(result)
