"""LangChain runnable builders for structured analysis."""

from langchain_core.prompts import ChatPromptTemplate

from .schemas import AIFileScanResult, AIFileSummary, AIProjectSummary


def build_file_analysis_chain(chat_model):
    """Create a file-analysis chain with structured output."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个代码安全扫描专家。"),
            ("human", "{prompt}"),
        ]
    )
    return prompt | chat_model.with_structured_output(AIFileScanResult)


def build_project_summary_chain(chat_model):
    """Create a project-summary chain with structured output."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个代码仓库架构分析专家。"),
            ("human", "{prompt}"),
        ]
    )
    return prompt | chat_model.with_structured_output(AIProjectSummary)


def build_file_summary_chain(chat_model):
    """Create a file-summary chain with structured output."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个代码文件解释器。"),
            ("human", "{prompt}"),
        ]
    )
    return prompt | chat_model.with_structured_output(AIFileSummary)
