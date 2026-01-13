"""文本转订单任务实现"""
import json
import re
from typing import Dict, Any, List
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
    
    # 上下文长度限制配置（字符数，保守估算）
    # 通义千问模型的上下文窗口约为8000 tokens，考虑到prompt模板和输出，预留安全余量
    # 中文字符通常1个字符≈1-2个tokens，这里按1.5倍估算，设置安全阈值为3000字符
    MAX_INPUT_LENGTH = 3000  # 单次处理的最大输入长度（字符数）
    CHUNK_SIZE = 2500  # 分块大小（字符数），略小于MAX_INPUT_LENGTH以留出安全余量
    
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
        
        # 如果 products 为空数组，直接返回（允许空数组）
        if len(output["products"]) == 0:
            logger.info(f"未识别到商品信息: task_id={self.task_id}")
            return {"products": []}
        
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
    
    def _estimate_token_count(self, text: str) -> int:
        """
        估算文本的token数量（粗略估算）
        
        对于中文文本，通常：
        - 1个中文字符 ≈ 1-2个tokens
        - 1个英文字符/单词 ≈ 0.5-1个tokens
        
        这里使用保守估算：字符数 * 1.5
        
        Args:
            text: 输入文本
            
        Returns:
            int: 估算的token数量
        """
        return int(len(text) * 1.5)
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        将长文本智能分块，优先按商品分隔符（顿号、逗号等）分割
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 文本块列表
        """
        # 如果文本长度小于等于CHUNK_SIZE，直接返回
        if len(text) <= self.CHUNK_SIZE:
            return [text]
        
        chunks = []
        # 商品分隔符：顿号、逗号、换行符、分号等
        separators = ['、', '，', ',', '\n', '；', ';', '。']
        
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            # 计算当前块的结束位置
            chunk_end = min(current_pos + self.CHUNK_SIZE, text_length)
            
            # 如果已经是最后一块，直接添加剩余文本
            if chunk_end >= text_length:
                remaining_text = text[current_pos:].strip()
                if remaining_text:
                    chunks.append(remaining_text)
                break
            
            # 尝试在分隔符处分割，找到最接近chunk_end的分隔符
            best_split_pos = chunk_end
            for sep in separators:
                # 从chunk_end向前查找分隔符
                sep_pos = text.rfind(sep, current_pos, chunk_end)
                if sep_pos != -1 and sep_pos > current_pos:
                    # 找到分隔符，在分隔符后分割（包含分隔符）
                    best_split_pos = sep_pos + len(sep)
                    break
            
            # 如果没找到合适的分隔符，尝试向后查找（最多向后查找500字符）
            if best_split_pos == chunk_end:
                for sep in separators:
                    sep_pos = text.find(sep, chunk_end, min(chunk_end + 500, text_length))
                    if sep_pos != -1:
                        best_split_pos = sep_pos + len(sep)
                        break
            
            # 提取当前块
            chunk = text[current_pos:best_split_pos].strip()
            if chunk:
                chunks.append(chunk)
            
            current_pos = best_split_pos
        
        return chunks if chunks else [text]
    
    async def _process_text_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """
        处理单个文本块
        
        Args:
            chunk: 文本块
            chunk_index: 当前块索引（从0开始）
            total_chunks: 总块数
            
        Returns:
            Dict[str, Any]: 解析后的商品列表
        """
        # 使用 prompt 模板格式化输入
        formatted_prompt = text_to_order_prompt.format(user_input=chunk)
        
        logger.debug(
            f"处理文本块 {chunk_index + 1}/{total_chunks}: "
            f"长度={len(chunk)}, 内容预览={chunk[:50]}..."
        )
        
        # 调用 LLM 模型
        llm_result = await llm_service.invoke(
            [{"role": "user", "content": formatted_prompt}],
            model_key="qwen-plus"
        )
        
        # 从 LLM 返回结果中提取 JSON
        raw_output = self._extract_json_from_text(llm_result)
        
        # 校验并规范化输出格式
        validated_output = self._validate_output_format(raw_output)
        
        return validated_output
    
    def _merge_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个文本块的处理结果
        
        Args:
            chunk_results: 各文本块的处理结果列表
            
        Returns:
            Dict[str, Any]: 合并后的结果
        """
        merged_products = []
        
        for chunk_result in chunk_results:
            if "products" in chunk_result and isinstance(chunk_result["products"], list):
                merged_products.extend(chunk_result["products"])
        
        return {"products": merged_products}
    
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
            # 检查文本长度，决定是否需要分块处理
            text_length = len(text)
            estimated_tokens = self._estimate_token_count(text)
            
            logger.info(
                f"文本长度检查: task_id={self.task_id}, "
                f"字符数={text_length}, 估算tokens={estimated_tokens}, "
                f"阈值={self.MAX_INPUT_LENGTH}"
            )
            
            # 如果文本长度超过阈值，使用分块处理
            if text_length > self.MAX_INPUT_LENGTH:
                logger.info(
                    f"文本长度超过阈值，启用分块处理: task_id={self.task_id}, "
                    f"文本长度={text_length}, 阈值={self.MAX_INPUT_LENGTH}"
                )
                
                # 将文本分块
                chunks = self._split_text_into_chunks(text)
                total_chunks = len(chunks)
                
                logger.info(
                    f"文本已分块: task_id={self.task_id}, "
                    f"总块数={total_chunks}, 各块长度={[len(c) for c in chunks]}"
                )
                
                # 更新进度
                await self.update_progress(ProgressUpdate(
                    info=f"正在处理文本块（共{total_chunks}块）",
                    status=TaskStatus.RUNNING
                ))
                
                # 处理每个文本块
                chunk_results = []
                for idx, chunk in enumerate(chunks):
                    await self.update_progress(ProgressUpdate(
                        info=f"正在处理第{idx + 1}/{total_chunks}块",
                        status=TaskStatus.RUNNING
                    ))
                    
                    chunk_result = await self._process_text_chunk(chunk, idx, total_chunks)
                    chunk_results.append(chunk_result)
                    
                    logger.debug(
                        f"文本块 {idx + 1}/{total_chunks} 处理完成: "
                        f"识别到{len(chunk_result.get('products', []))}个商品"
                    )
                
                # 合并所有块的结果
                validated_output = self._merge_chunk_results(chunk_results)
                
                logger.info(
                    f"分块处理完成: task_id={self.task_id}, "
                    f"总商品数量={len(validated_output['products'])}"
                )
            else:
                # 文本长度在阈值内，直接处理
                logger.debug(f"文本长度在阈值内，直接处理: text={text[:100]}...")
                
                # 使用 prompt 模板格式化输入
                formatted_prompt = text_to_order_prompt.format(user_input=text)
                
                # 调用 LLM 模型
                llm_result = await llm_service.invoke(
                    [{"role": "user", "content": formatted_prompt}],
                    model_key="qwen-plus"  # 此处切换模型
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
