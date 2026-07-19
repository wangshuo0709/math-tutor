# -*- coding: utf-8 -*-
"""文心一言智能体 — 新版千帆 API（Bearer Token 鉴权）"""
import requests, json, re


class WenxinAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://qianfan.baidubce.com/v2/chat/completions"
        self.model = "ernie-4.5-turbo-32k"
        # 有效 JSON 转义符
        self._valid_escapes = frozenset('"\\/bfnrt')

    def chat(self, messages: list, temperature: float = 0.3) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def _extract_content(self, resp: dict) -> str:
        if "error" in resp:
            return ""
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def _fix_json_escapes(self, text: str) -> str:
        """修复 AI 返回的 JSON 中未转义的反斜杠（如 LaTeX \frac 等）"""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                nxt = text[i + 1]
                if nxt in self._valid_escapes:
                    # 已经是有效 JSON 转义，保留
                    result.append(text[i])
                    result.append(nxt)
                    i += 2
                elif nxt == 'u':
                    # \uXXXX 是有效 unicode 转义
                    result.append(text[i])
                    i += 1
                    # 复制后续 5 个字符 (\uXXXX)
                    while i < len(text) and len(result) < 6:
                        result.append(text[i])
                        i += 1
                else:
                    # 无效转义 → 双写反斜杠
                    result.append('\\\\')
                    result.append(nxt)
                    i += 2
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    def _clean_json(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = self._fix_json_escapes(text)
        return text.strip()

    def _parse_json(self, text: str):
        if not text:
            return None
        text = self._clean_json(text)
        try:
            return json.loads(text, strict=False)
        except json.JSONDecodeError:
            try:
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group(), strict=False)
            except (json.JSONDecodeError, Exception):
                pass
        return None

    def generate_question(self, kp: str, difficulty: int = 2, qtype: str = "单选题"):
        diff_map = {1: "容易", 2: "中等", 3: "较难"}
        prompt = (
            "你是一位高中数学老师。请出一道高一数学题目。\n\n"
            "要求：\n"
            f"- 知识点：{kp}\n"
            f"- 题型：{qtype}\n"
            f"- 难度：{diff_map.get(difficulty, '中等')}\n"
            "- 风格：接近新高考试卷风格\n\n"
            "请严格按以下 JSON 格式返回，注意 LaTeX 中的反斜杠要写成双反斜杠：\n"
            '{"question":"题目文本","options":["A. xxx","B. xxx","C. xxx","D. xxx"],'
            '"answer":"正确答案","explanation":"详细解析"}'
        )
        resp = self.chat([{"role": "user", "content": prompt}], temperature=0.3)
        return self._parse_json(self._extract_content(resp))

    def grade_answer(self, question: str, student_answer: str, correct_answer=None):
        prompt_lines = [
            "你是一位高中数学老师，请批改学生的数学答案。",
            "",
            "题目：" + question,
            "学生答案：" + student_answer,
        ]
        if correct_answer:
            prompt_lines.append("参考答案：" + correct_answer)
        prompt_lines.extend([
            "",
            '请按以下 JSON 格式返回：',
            '{"score":分数(满分10),"analysis":"错误分析","suggestion":"学习建议","is_correct":true/false}',
        ])
        resp = self.chat([{"role": "user", "content": "\n".join(prompt_lines)}], temperature=0.2)
        return self._parse_json(self._extract_content(resp))
