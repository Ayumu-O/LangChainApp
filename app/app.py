import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.callbacks import get_openai_callback
from langchain.callbacks import StreamlitCallbackHandler
from copy import deepcopy


def init_page():
    st.set_page_config(page_title="My Great ChatGPT", page_icon="🤗")
    st.header("My Great ChatGPT 🤗")
    st.sidebar.title("Options")


def init_messages():
    clear_button = st.sidebar.button("Clear Conversation", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="You are a helpful assistant.")
        ]
        st.session_state.costs = []


def select_model():
    model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-4"

    # スライダーを追加し、temperatureを0から2までの範囲で選択可能にする
    # 初期値は0.0、刻み幅は0.1とする
    temperature = st.sidebar.slider(
        "Temperature:", min_value=0.0, max_value=2.0, value=0.0, step=0.01
    )

    return ChatOpenAI(
        temperature=temperature, model_name=model_name, streaming=True
    )


def get_answer(llm, messages, callbacks=None):
    with get_openai_callback() as cb:
        answer = llm(messages, callbacks=callbacks)
    return answer.content, cb.total_cost


def main():
    init_page()

    llm = select_model()
    init_messages()

    container = st.container()

    # コストの表示
    costs = deepcopy(st.session_state.get("costs", []))
    st.sidebar.markdown("## Costs")
    st.sidebar.markdown(f"**Total cost: ${sum(costs):.5f}**")

    # チャット履歴の表示
    messages = st.session_state.get("messages", [])
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(message.content)
            # コスト表示
            st.write(f"cost: ${costs.pop(0):.5f}")
        elif isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        else:  # isinstance(message, SystemMessage):
            st.write(f"System message: {message.content}")

    # ユーザーの入力を監視
    with container:
        with st.form(key="my_form", clear_on_submit=True):
            user_input = st.text_area(
                label="Message: ", key="input", height=100
            )
            submit_button = st.form_submit_button(label="Send")

    # NOTE: streamlit 1.26.0 待ち
    # if user_input := st.chat_input("聞きたいことを入力してね！"):
    if submit_button and user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        # with st.spinner("ChatGPT is typing ..."):
        #     answer, cost = get_answer(llm, st.session_state.messages)
        # streaming表示
        st.chat_message("user").markdown(user_input)
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            answer, cost = get_answer(llm, messages, callbacks=[st_callback])
        st.write(f"cost: ${cost:.5f}")
        st.session_state.messages.append(AIMessage(content=answer))
        st.session_state.costs.append(cost)


if __name__ == "__main__":
    main()
