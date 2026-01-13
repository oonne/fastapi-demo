"""文本转订单的 Prompt 模板"""
from langchain_core.prompts import PromptTemplate

# 文本转订单的 Prompt 模板
# 这个模板可以根据需要调整，支持从文本中提取商品信息
TEXT_TO_ORDER_PROMPT_TEMPLATE = """你是一个专业的订单信息提取助手。请从用户输入的文本中提取商品信息，并按照指定的JSON格式输出。

## 任务要求：
1. 从文本中识别所有商品信息，包括商品名称、数量、单位、价格（如果有）、备注（如果有）
2. 支持识别多个商品，商品之间可能用顿号（、）、逗号（，）、空格等分隔
3. 如果文本中没有明确的价格信息，price字段设置为null（不是0或空字符串）
4. 如果文本中没有备注信息，remark字段设置为null（不是空字符串）
5. 数量默认为1，如果没有明确指定数量
6. 数量可以是整数或小数（浮点数），需要正确识别和处理：
   - 直接的小数表达：如"1.5斤"、"2.3个"等，直接提取为对应的数字
   - 中文表达的小数：需要转换为数字，常见转换规则：
     * "半" = 0.5（如"一斤半" = 1.5，"半斤" = 0.5）
     * "一两" = 0.1（在"斤"单位下）
     * "二两" = 0.2（在"斤"单位下）
     * "三两" = 0.3（在"斤"单位下）
     * "四两" = 0.4（在"斤"单位下）
     * "五两" = 0.5（在"斤"单位下）
     * 其他类似的中文表达也需要正确转换
7. 单位需要从文本中提取，如"斤"、"个"、"件"、"包"等
8. 如果输入文本无法识别出任何商品信息（如只是问候语、无关内容等），products数组可以返回空数组 []

## 输出格式要求：
必须严格按照以下JSON格式输出，不要添加任何额外的说明文字：
```json
{{
  "products": [
    {{
      "name": "商品名称",
      "quantity": 数量（整数或小数）,
      "unit": "单位",
      "price": 价格（浮点数，如果没有则为null）,
      "remark": "备注"（如果没有则为null）
    }}
  ]
}}
```

## 示例：
输入："猪肉一斤"
输出：
```json
{{
  "products": [
    {{
      "name": "猪肉",
      "quantity": 1,
      "unit": "斤",
      "price": null,
      "remark": null
    }}
  ]
}}
```

输入："猪肉一斤、牛肉三斤"
输出：
```json
{{
  "products": [
    {{
      "name": "猪肉",
      "quantity": 1,
      "unit": "斤",
      "price": null,
      "remark": null
    }},
    {{
      "name": "牛肉",
      "quantity": 3,
      "unit": "斤",
      "price": null,
      "remark": null
    }}
  ]
}}
```

输入："苹果5个，每个10元"
输出：
```json
{{
  "products": [
    {{
      "name": "苹果",
      "quantity": 5,
      "unit": "个",
      "price": 10.0,
      "remark": null
    }}
  ]
}}
```

输入："牛肉1.5斤"
输出：
```json
{{
  "products": [
    {{
      "name": "牛肉",
      "quantity": 1.5,
      "unit": "斤",
      "price": null,
      "remark": null
    }}
  ]
}}
```

输入："牛肉一斤半"
输出：
```json
{{
  "products": [
    {{
      "name": "牛肉",
      "quantity": 1.5,
      "unit": "斤",
      "price": null,
      "remark": null
    }}
  ]
}}
```

输入："猪肉半斤、牛肉二两"
输出：
```json
{{
  "products": [
    {{
      "name": "猪肉",
      "quantity": 0.5,
      "unit": "斤",
      "price": null,
      "remark": null
    }},
    {{
      "name": "牛肉",
      "quantity": 0.2,
      "unit": "斤",
      "price": null,
      "remark": null
    }}
  ]
}}
```

输入："你好，今天天气不错"
输出：
```json
{{
  "products": []
}}
```

## 用户输入：
{user_input}

请提取商品信息并输出JSON格式：
"""

# 创建 PromptTemplate 实例
text_to_order_prompt = PromptTemplate(
    input_variables=["user_input"],
    template=TEXT_TO_ORDER_PROMPT_TEMPLATE,
)
