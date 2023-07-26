from typing import Optional
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
from chatgpt_app.const import SessionKey
from chatgpt_app.logger import get_logger
from chatgpt_app.pages.chatgpt.base_chatgpt import BaseChatGPTPage
from chatgpt_app.session import StreamlistSessionManager
from langchain.schema import HumanMessage
from streamlit_extras.stoggle import stoggle

logger = get_logger(__name__)


class WebSummarizePage(BaseChatGPTPage):
    def init_messages(self, sm: StreamlistSessionManager) -> None:
        sm.clear_url_input()
        return super().init_messages(sm)

    def get_url_input(self) -> str:
        url = st.text_input("URL: ", key=SessionKey.URL_INPUT.name)
        return url

    def validate_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_content(self, url: str) -> Optional[str]:
        try:
            with st.spinner("Fetching Content ..."):
                response = requests.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                # fetch text from main (change the below code to filter page)
                if soup.main:
                    return soup.main.get_text()
                elif soup.article:
                    return soup.article.get_text()
                else:
                    return soup.body.get_text()
        except Exception:
            st.write("something wrong")
            return None

    def build_prompt(self, content: str, n_chars: int = 300) -> str:
        prompt = f"""以下はとあるWebページのコンテンツです。内容を{n_chars}字程度でわかりやすく要約してください。

========

{content[:1000]}

========

日本語で書いください。
"""
        return prompt

    def render(self) -> None:
        llm = self.base_components()

        url_container = st.container()
        response_container = st.container()
        summarize_length = st.sidebar.slider("Summarize Length:", min_value=50, max_value=1000, value=300, step=1)

        show_result = False
        with url_container:
            url = self.get_url_input()
            is_valid_url = self.validate_url(url)
            if not is_valid_url:
                st.write("Please input valid url")
            else:
                content = self.get_content(url)
                if content:
                    prompt = self.build_prompt(content, summarize_length)
                    self.sm.add_message(HumanMessage(content=prompt))
                    show_result = True

        if show_result:
            with response_container:
                st.markdown("## Summary")
                answer, cost = self.get_streaming_answer(llm, self.sm.get_messages())
                self.sm.add_cost(cost)
                st.markdown("---")
                st.markdown("## Original Text")
                stoggle("Original Text", content)

        costs = self.sm.get_costs()
        st.sidebar.markdown("## Costs")
        st.sidebar.markdown(f"**Total cost: ${sum(costs):.5f}**")
