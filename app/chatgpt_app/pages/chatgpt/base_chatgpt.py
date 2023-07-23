from typing import List, Tuple

import streamlit as st
from chatgpt_app.openai_api_cost_handler import StreamlitCostCalcHandler, TokenCostProcess
from chatgpt_app.pages.base import BasePage
from chatgpt_app.session import StreamlistSessionManager
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage, SystemMessage


class BaseChatGPTPage(BasePage):
    def init_page(self) -> None:
        st.header(f"{self.title}  🤗")
        st.sidebar.title("Options")

    def select_model(self) -> ChatOpenAI:
        model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
        if model == "GPT-3.5":
            model_name = "gpt-3.5-turbo"
        else:
            model_name = "gpt-4"

        # スライダーを追加し、temperatureを0から2までの範囲で選択可能にする
        # 初期値は0.0、刻み幅は0.1とする
        temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.0, step=0.01)

        llm = ChatOpenAI(  # type: ignore
            temperature=temperature,
            model_name=model_name,
            streaming=True,
        )
        return llm

    def init_messages(self, sm: StreamlistSessionManager) -> None:
        clear_button = st.sidebar.button("Clear Conversation", key="clear")
        if clear_button or len(sm.get_messages()) == 0:
            sm.clear_messages()
            sm.clear_costs()
            sm.add_message(SystemMessage(content="You are a helpful assistant."))

    def get_streaming_answer(self, llm: ChatOpenAI, messages: List[BaseMessage]) -> Tuple[str, float]:
        token_cost_process = TokenCostProcess(llm.model_name)
        st_callback = StreamlitCostCalcHandler(st.container(), token_cost_process)
        answer = llm(messages, callbacks=[st_callback]).content
        cost = token_cost_process.total_cost
        return answer, cost