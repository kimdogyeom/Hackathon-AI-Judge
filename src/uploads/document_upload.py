from typing import Optional, Any

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output

from src.config.config import s3_client


class DocumentUpload(Runnable):

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:

        # s3 클라이언트 접근

        return