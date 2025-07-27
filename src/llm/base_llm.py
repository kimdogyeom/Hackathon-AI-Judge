# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    모든 LLM 서비스의 기반이 될 추상 기본 클래스.
    """

    @abstractmethod
    def invoke(self, *args, **kwargs):
        """
        LLM 모델을 호출합니다.
        구현 클래스에서 필요한 인자를 자유롭게 정의합니다.
        """
        pass