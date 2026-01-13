"""文本转订单任务实现"""
import json
import re
from typing import Dict, Any
from app.tasks.base import BaseTask
from app.schemas.task import ProgressUpdate
from app.constant.task_status import TaskStatus
from app.utils.logger import get_logger
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode
from app.services.llm_service import llm_service
from app.tasks.text_to_order.prompt import text_to_order_prompt

logger = get_logger("app")


class TextToOrderTask(BaseTask):
    """文本转订单任务"""
    
    def _validate_product_format(self, product: Dict[str, Any]) -> None:
        """
        校验单个商品格式
        
        Args:
            product: 商品字典
            
        Raises:
            CustomException: 格式不正确时抛出异常
        """
        required_fields = ["name", "quantity", "unit"]
        for field in required_fields:
            if field not in product:
                raise CustomException(
                    code=ErrorCode.OUTPUT_FORMAT_ERROR,
                    message=f"商品格式错误：缺少必需字段 '{field}'"
                )
        
        # 校验 name 必须是字符串且不为空
        if not isinstance(product["name"], str) or not product["name"].strip():
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="商品格式错误：name 必须是非空字符串"
            )
        
        # 校验 quantity 必须是数字（整数或浮点数）且大于0
        if not isinstance(product["quantity"], (int, float)):
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="商品格式错误：quantity 必须是数字（整数或小数）"
            )
        if product["quantity"] <= 0:
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="商品格式错误：quantity 必须大于0"
            )
        
        # 校验 unit 必须是字符串且不为空
        if not isinstance(product["unit"], str) or not product["unit"].strip():
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="商品格式错误：unit 必须是非空字符串"
            )
        
        # 校验 price：如果存在，必须是数字（int或float）或 None/null
        if "price" in product:
            price = product["price"]
            if price is not None and not isinstance(price, (int, float)):
                raise CustomException(
                    code=ErrorCode.OUTPUT_FORMAT_ERROR,
                    message="商品格式错误：price 必须是数字或 null"
                )
        
        # 校验 remark：如果存在，必须是字符串或 None/null
        if "remark" in product:
            remark = product["remark"]
            if remark is not None and not isinstance(remark, str):
                raise CustomException(
                    code=ErrorCode.OUTPUT_FORMAT_ERROR,
                    message="商品格式错误：remark 必须是字符串或 null"
                )
    
    def _validate_output_format(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        校验并规范化输出格式
        
        Args:
            output: LLM 返回的原始输出
            
        Returns:
            Dict[str, Any]: 规范化后的输出
            
        Raises:
            CustomException: 格式不正确时抛出异常
        """
        # 检查是否有 products 字段
        if "products" not in output:
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="输出格式错误：缺少 'products' 字段"
            )
        
        # 检查 products 是否为列表
        if not isinstance(output["products"], list):
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="输出格式错误：'products' 必须是数组"
            )
        
        # 检查 products 是否为空
        if len(output["products"]) == 0:
            raise CustomException(
                code=ErrorCode.OUTPUT_FORMAT_ERROR,
                message="输出格式错误：'products' 数组不能为空"
            )
        
        # 规范化每个商品
        normalized_products = []
        for idx, product in enumerate(output["products"]):
            if not isinstance(product, dict):
                raise CustomException(
                    code=ErrorCode.OUTPUT_FORMAT_ERROR,
                    message=f"输出格式错误：products[{idx}] 必须是对象"
                )
            
            # 校验商品格式
            self._validate_product_format(product)
            
            # 规范化商品数据
            normalized_product = {
                "name": product["name"].strip(),
                "quantity": product["quantity"],
                "unit": product["unit"].strip(),
                "price": product.get("price") if product.get("price") is not None else None,
                "remark": product.get("remark") if product.get("remark") is not None else None,
            }
            
            normalized_products.append(normalized_product)
        
        return {"products": normalized_products}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON 内容
        
        Args:
            text: 包含 JSON 的文本
            
        Returns:
            Dict[str, Any]: 解析后的 JSON 字典
            
        Raises:
            CustomException: 解析失败时抛出异常
        """
        # 尝试直接解析整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块中的 JSON（支持多行）
        # 先尝试匹配 ```json ... ``` 格式
        json_block_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # 尝试匹配 ``` ... ``` 格式（没有 json 标记）
        code_block_pattern = r'```\s*(\{.*?\})\s*```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # 尝试匹配第一个完整的 JSON 对象（支持多行）
        # 使用更智能的方法：找到第一个 { 和最后一个匹配的 }
        brace_start = text.find('{')
        if brace_start != -1:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
            
            if brace_end != -1:
                json_str = text[brace_start:brace_end + 1]
                try:
                    return json.loads(json_str.strip())
                except json.JSONDecodeError:
                    pass
        
        # 如果都失败了，抛出异常
        raise CustomException(
            code=ErrorCode.TASK_EXECUTION_FAILED,
            message="无法从 LLM 返回结果中提取有效的 JSON 数据"
        )
    
    async def execute(self) -> Dict[str, Any]:
        """
        执行文本转订单任务
        
        返回说明：
        - 成功时：返回的字典会直接作为 output 保存到任务中，并通过回调发送
        - 失败时：抛出异常，TaskExecutor 会自动捕获并保存为 {"error": "错误信息"}
        
        Returns:
            Dict[str, Any]: 任务执行结果，会直接作为 output 保存
            
        Raises:
            Exception: 任务执行失败时抛出异常，会被 TaskExecutor 捕获并处理
        """
        logger.info(f"开始执行文本转订单任务: task_id={self.task_id}")
        
        # 获取输入参数
        text = self.task_params.get("text", "")
        merchantId = self.task_params.get("merchantId", "")
        customerId = self.task_params.get("customerId", "")
        
        # 校验输入值
        if not text:
            raise CustomException(
                code=ErrorCode.INPUT_FORMAT_ERROR,
                message="文本内容不能为空",
            )
        if not merchantId:
            raise CustomException(
                code=ErrorCode.INPUT_FORMAT_ERROR,
                message="商户ID不能为空",
            )
        
        # 开始处理
        await self.update_progress(ProgressUpdate(
            info="开始识别订单信息",
            status=TaskStatus.RUNNING
        ))
        
        try:
            # 使用 prompt 模板格式化输入
            formatted_prompt = text_to_order_prompt.format(user_input=text)
            
            logger.debug(f"调用 LLM 解析文本: text={text[:100]}...")
            
            # 调用 LLM 模型
            llm_result = await llm_service.invoke(
                [{"role": "user", "content": formatted_prompt}],
                model_key="qwen-turbo"  # 指定使用 qwen-turbo 模型
            )
            
            logger.debug(f"LLM 返回结果: {llm_result[:200]}...")
            
            # 从 LLM 返回结果中提取 JSON
            raw_output = self._extract_json_from_text(llm_result)
            
            # 校验并规范化输出格式
            validated_output = self._validate_output_format(raw_output)
            
            logger.info(
                f"文本转订单解析成功: task_id={self.task_id}, "
                f"商品数量={len(validated_output['products'])}"
            )
            
            # 最终进度更新
            await self.update_progress(ProgressUpdate(info="处理完成"))
            
            logger.info(f"文本转订单任务完成: task_id={self.task_id}")
            
            # 返回任务结果
            return validated_output
            
        except CustomException:
            # CustomException 直接抛出
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            raise CustomException(
                code=ErrorCode.INPUT_FORMAT_ERROR,
                message=f"LLM 返回结果格式错误，无法解析 JSON: {str(e)}"
            )
        except Exception as e:
            logger.error(f"文本转订单任务执行失败: {str(e)}", exc_info=True)
            raise CustomException(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"文本转订单任务执行失败: {str(e)}"
            )
