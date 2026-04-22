from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def get_all_data(self, days=1):
        """返回统一格式的列表"""
        pass