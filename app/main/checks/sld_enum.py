from app.main.checks.base_check import BaseCheck, answer
from app.utils.parse_for_html import format_header
import re


class SldEnumCheck(BaseCheck):
    def __init__(self, presentation, pdf_id):
        super().__init__(presentation)
        self.pdf_id = pdf_id

    def check(self):
        error = []
        if self.presentation.slides[0].page_number[0] != -1:
            error.append(1)
        for i in range(1, len(self.presentation.slides)):
            if self.presentation.slides[i].page_number[0] != i + 1:
                error.append(i+1)
        if not error:
            return answer(True, "Пройдена!")
        else:
            error =  self.format_page_link(error)
            return answer(False, format_header('Не пройдена, проблемные слайды: {}'.format(', '.join(map(str, error)))), \
                                        'Убедитесь в корректности формата номеров слайдов')
