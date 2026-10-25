"""视频评估模块

该模块实现了对教育视频的多维度评估功能。
主要功能包括：
- 从元素布局、吸引力、逻辑流畅度、准确性深度、视觉一致性五个维度评估视频
- 支持单个视频评估和批量视频评估
- 支持并行处理以提高评估效率
- 生成详细的评估报告和反馈
"""

import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from threading import Lock

from gpt_request import request_gemini_with_video
from prompts import get_prompt_aes
from utils import extract_answer_from_response, eva_video_list


@dataclass
class EvaluationResult:
    """评估结果数据类
    
    包含视频在各个维度的评分、总体评分和详细反馈。
    
    Attributes:
        element_layout: 元素布局评分（0-20）
        attractiveness: 吸引力评分（0-20）
        logic_flow: 逻辑流畅度评分（0-20）
        accuracy_depth: 准确性深度评分（0-20）
        visual_consistency: 视觉一致性评分（0-20）
        overall_score: 总体评分（0-100）
        detailed_feedback: 详细反馈文本
        knowledge_point: 知识点名称
    """
    element_layout: float
    attractiveness: float
    logic_flow: float
    accuracy_depth: float
    visual_consistency: float
    overall_score: float
    detailed_feedback: str
    knowledge_point: str = ""


class VideoEvaluator:
    """视频评估器
    
    该类负责对教育视频进行多维度评估，使用MLLM模型
    分析视频的质量和教育效果。
    """
    
    def __init__(self, request_gemini_function):
        """初始化视频评估器
        
        Args:
            request_gemini_function: Gemini视频API请求函数
        """
        self.request_gemini_with_video = request_gemini_function
        self._progress_lock = Lock()

    def evaluate_video(self, video_path: str, knowledge_point: str, log_id: str = None) -> EvaluationResult:
        """评估单个教学视频
        
        使用MLLM模型对视频进行多维度评估，包括元素布局、吸引力、
        逻辑流畅度、准确性深度和视觉一致性。
        
        Args:
            video_path: 视频文件路径
            knowledge_point: 知识点描述（用于针对性评估）
            log_id: 日志ID
            
        Returns:
            EvaluationResult: 包含详细评估结果的对象
        """
        evaluation_prompt = get_prompt_aes(knowledge_point)

        try:
            response = self.request_gemini_with_video(
                prompt=evaluation_prompt, video_path=video_path, log_id=log_id, max_tokens=10000, max_retries=3
            )
            result = self._parse_evaluation_response(response)
            result.knowledge_point = knowledge_point
            return result

        except Exception as e:
            print(f"Error during video evaluation: {str(e)}")
            return self._create_error_result(str(e))

    def evaluate_video_batch(
        self, video_list: List[Dict[str, Any]], log_id: str = None, max_workers: int = 3, use_parallel: bool = True
    ) -> List[EvaluationResult]:
        """批量评估多个教学视频（支持并行处理）
        
        Args:
            video_list: 视频列表，每个元素包含 {'path': str, 'knowledge_point': str}
            log_id: 日志ID
            max_workers: 最大并行工作线程数（建议2-5以避免API调用频率问题）
            use_parallel: 是否使用并行处理，默认为True
            
        Returns:
            List[EvaluationResult]: 评估结果列表（与输入顺序相同）
        """
        if not use_parallel or len(video_list) == 1:
            return self._evaluate_video_batch_sequential(video_list, log_id)

        return self._evaluate_video_batch_parallel(video_list, log_id, max_workers)

    def _evaluate_video_batch_sequential(self, video_list: List[Dict[str, Any]], log_id: str = None) -> List[EvaluationResult]:
        """顺序评估视频批次
        
        按顺序逐个评估视频，适用于少量视频或需要避免API调用频率限制的情况。
        
        Args:
            video_list: 视频列表
            log_id: 日志ID
            
        Returns:
            List[EvaluationResult]: 评估结果列表
        """
        results = []

        for i, video_info in enumerate(video_list):
            video_path = video_info.get("path", "")
            knowledge_point = video_info.get("knowledge_point", "")

            if not knowledge_point:
                print(f"警告：视频 {i+1} 缺少知识点信息，可能影响评估准确性")

            print(f"正在评估视频 {i+1}/{len(video_list)}: {video_path}")
            print(f"知识点：{knowledge_point}")

            result = self.evaluate_video(
                video_path=video_path, knowledge_point=knowledge_point, log_id=f"{log_id}_video_{i+1}" if log_id else None
            )

            results.append(result)

    def _evaluate_video_batch_parallel(
        self, video_list: List[Dict[str, Any]], log_id: str = None, max_workers: int = 3
    ) -> List[EvaluationResult]:
        """并行评估视频批次
        
        使用线程池并行评估多个视频，提高评估效率。
        显示实时进度和预计完成时间。
        
        Args:
            video_list: 视频列表
            log_id: 日志ID
            max_workers: 最大并行工作线程数
            
        Returns:
            List[EvaluationResult]: 评估结果列表
        """
        print(f"开始并行评估 {len(video_list)} 个视频，使用 {max_workers} 个工作线程...")

        results = [None] * len(video_list)
        completed_count = 0
        start_time = time.time()

        def evaluate_single_video(index: int, video_info: Dict[str, Any]) -> tuple:
            """评估单个视频的包装函数
            
            Args:
                index: 视频索引
                video_info: 视频信息字典
                
            Returns:
                tuple: (索引, 评估结果, 错误信息)
            """
            video_path = video_info.get("path", "")
            knowledge_point = video_info.get("knowledge_point", "")

            if not knowledge_point:
                with self._progress_lock:
                    print(f"警告：视频 {index+1} 缺少知识点信息，可能影响评估准确性")

            try:
                result = self.evaluate_video(
                    video_path=video_path, knowledge_point=knowledge_point, log_id=f"{log_id}_video_{index+1}" if log_id else None
                )
                return index, result, None
            except Exception as e:
                error_result = self._create_error_result(f"并行评估错误: {str(e)}")
                return index, error_result, str(e)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(evaluate_single_video, i, video_info): i for i, video_info in enumerate(video_list)
            }
            for future in as_completed(future_to_index):
                try:
                    index, result, error = future.result()
                    results[index] = result

                    with self._progress_lock:
                        completed_count += 1
                        elapsed_time = time.time() - start_time
                        avg_time_per_video = elapsed_time / completed_count
                        eta = avg_time_per_video * (len(video_list) - completed_count)

                        print(f"已完成 {completed_count}/{len(video_list)} " f"(耗时: {elapsed_time:.1f}s, 预计剩余: {eta:.1f}s)")

                        if error:
                            print(f"警告：视频 {index+1} 评估遇到错误: {error}")
                        else:
                            video_path = video_list[index].get("path", "")
                            knowledge_point = video_list[index].get("knowledge_point", "")
                            print(
                                f"✓ 视频 {index+1}: {video_path} (知识点: {knowledge_point}) "
                                f"- 得分: {result.overall_score:.1f}/100"
                            )

                except Exception as e:
                    with self._progress_lock:
                        print(f"警告：处理视频 {index+1} 的未来结果时出错: {str(e)}")

        total_time = time.time() - start_time
        print(f"\n并行评估完成！总耗时: {total_time:.1f}s, 平均每个视频: {total_time/len(video_list):.1f}s")

        return results

    def _parse_evaluation_response(self, response: str) -> EvaluationResult:
        """解析MLLM的评估响应
        
        从API响应中提取JSON格式的评估数据，并构建EvaluationResult对象。
        如果无法解析JSON，则回退到文本提取方法。
        
        Args:
            response: API响应文本
            
        Returns:
            EvaluationResult: 评估结果对象
        """
        try:
            response = extract_answer_from_response(response=response)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                element_layout = float(data.get("element_layout", {}).get("score", 0))
                attractiveness = float(data.get("attractiveness", {}).get("score", 0))
                logic_flow = float(data.get("logic_flow", {}).get("score", 0))
                accuracy_depth = float(data.get("accuracy_depth", {}).get("score", 0))
                visual_consistency = float(data.get("visual_consistency", {}).get("score", 0))

                overall_score = element_layout + attractiveness + logic_flow + accuracy_depth + visual_consistency

                detailed_feedback = self._build_detailed_feedback(data)

                return EvaluationResult(
                    element_layout=element_layout,
                    attractiveness=attractiveness,
                    logic_flow=logic_flow,
                    accuracy_depth=accuracy_depth,
                    visual_consistency=visual_consistency,
                    overall_score=round(overall_score, 2),
                    detailed_feedback=detailed_feedback,
                )
            else:
                return self._extract_scores_from_text(response)

        except Exception as e:
            print(f"解析评估响应时出错: {str(e)}")
            return self._create_error_result(str(e))

    def _extract_scores_from_text(self, response: str) -> EvaluationResult:
        """从文本响应中提取分数（回退方法）
        
        当JSON解析失败时，使用正则表达式从文本中提取各维度的分数。
        这是一种备用的解析方法。
        
        Args:
            response: API响应文本
            
        Returns:
            EvaluationResult: 评估结果对象
        """
        patterns = {
            "element_layout": r"Element Layout.*?(\d+(?:\.\d+)?)",
            "attractiveness": r"Attractiveness.*?(\d+(?:\.\d+)?)",
            "logic_flow": r"Logic Flow.*?(\d+(?:\.\d+)?)",
            "accuracy_depth": r"Accuracy.*?Depth.*?(\d+(?:\.\d+)?)",
            "visual_consistency": r"Visual Consistency.*?(\d+(?:\.\d+)?)",
        }

        scores = {}
        for dimension, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                scores[dimension] = float(match.group(1))
            else:
                scores[dimension] = 0.0

        overall_score = (
            scores["element_layout"] * 0.2
            + scores["attractiveness"] * 0.2
            + scores["logic_flow"] * 0.2
            + scores["accuracy_depth"] * 0.2
            + scores["visual_consistency"] * 0.2
        )

        return EvaluationResult(
            element_layout=scores["element_layout"],
            attractiveness=scores["attractiveness"],
            logic_flow=scores["logic_flow"],
            accuracy_depth=scores["accuracy_depth"],
            visual_consistency=scores["visual_consistency"],
            overall_score=round(overall_score, 2),
            detailed_feedback=response,
        )

    def _build_detailed_feedback(self, data: Dict) -> str:
        """构建详细反馈
        
        从评估数据中提取各个维度的反馈，并组织成结构化的详细反馈文本。
        包括各维度评分和反馈、总体总结、优点和改进建议。
        
        Args:
            data: 评估数据字典，包含各维度的评分和反馈
            
        Returns:
            str: 格式化的详细反馈文本
        """
        feedback_sections = []
        dimensions = [
            ("Element Layout", "element_layout"),
            ("Attractiveness", "attractiveness"),
            ("Logic Flow", "logic_flow"),
            ("Accuracy & Depth", "accuracy_depth"),
            ("Visual Consistency", "visual_consistency"),
        ]

        for name, key in dimensions:
            section_data = data.get(key, {})
            score = section_data.get("score", 0)
            feedback = section_data.get("feedback", "No feedback provided")
            feedback_sections.append(f"**{name} ({score} points):**\n{feedback}")
        summary = data.get("summary", "")
        strengths = data.get("strengths", [])
        improvements = data.get("improvements", [])

        detailed_feedback = "\n\n".join(feedback_sections)

        if summary:
            detailed_feedback += f"\n\n**Overall Summary:**\n{summary}"

        if strengths:
            detailed_feedback += f"\n\n**Key Strengths:**\n" + "\n".join([f"• {s}" for s in strengths])

        if improvements:
            detailed_feedback += f"\n\n**Areas for Improvement:**\n" + "\n".join([f"• {i}" for i in improvements])

        return detailed_feedback

    def _create_error_result(self, error_message: str) -> EvaluationResult:
        """创建错误结果
        
        当评估过程中出现错误时，创建一个包含错误信息的评估结果对象。
        所有评分都设为0，详细反馈包含错误信息。
        
        Args:
            error_message: 错误信息文本
            
        Returns:
            EvaluationResult: 包含错误信息的评估结果对象
        """
        return EvaluationResult(
            element_layout=0.0,
            attractiveness=0.0,
            logic_flow=0.0,
            accuracy_depth=0.0,
            visual_consistency=0.0,
            overall_score=0.0,
            detailed_feedback=f"评估过程中出错: {error_message}",
        )

    def generate_evaluation_report(self, results: List[EvaluationResult], output_path: str = None) -> str:
        """生成评估报告
        
        根据评估结果列表生成详细的评估报告，包括每个视频的评分、
        各维度平均分和总体统计信息。可选择将报告保存到文件。
        
        Args:
            results: 评估结果列表
            output_path: 报告输出文件路径（可选）
            
        Returns:
            str: 生成的评估报告文本
        """
        if not results:
            return "由于评估过程中出现错误，无法生成报告。"

        total_videos = len(results)
        avg_scores = {
            "element_layout": sum(r.element_layout for r in results) / total_videos,
            "attractiveness": sum(r.attractiveness for r in results) / total_videos,
            "logic_flow": sum(r.logic_flow for r in results) / total_videos,
            "accuracy_depth": sum(r.accuracy_depth for r in results) / total_videos,
            "visual_consistency": sum(r.visual_consistency for r in results) / total_videos,
            "overall": sum(r.overall_score for r in results) / total_videos,
        }
        report = f"""# Evaluation Report

## Video Evaluation Results

"""

        for i, result in enumerate(results, 1):
            report += f"""### Video {i}
- **Learning topic**: {result.knowledge_point}
- **Overall Score**: {result.overall_score}/100
- Element Layout: {result.element_layout/20*100}
- Attractiveness: {result.attractiveness/20*100}
- Logic Flow: {result.logic_flow/20*100}
- Accuracy & Depth: {result.accuracy_depth/20*100}
- Visual Consistency: {result.visual_consistency/20*100}
---

## Overall Statistics
- **Total Number of Videos Evaluated**: {total_videos}
- **Average Overall Score**: {avg_scores['overall']:.2f}/100

## Average Scores per Dimension
- Element Layout: {avg_scores['element_layout']/20*100:.2f}
- Attractiveness: {avg_scores['attractiveness']/20*100:.2f}
- Logic Flow: {avg_scores['logic_flow']/20*100:.2f}
- Accuracy & Depth: {avg_scores['accuracy_depth']/20*100:.2f}
- Visual Consistency: {avg_scores['visual_consistency']/20*100:.2f}

"""
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"评估报告已保存到: {output_path}")

        return report


def evaluate_main():
    """评估主函数
    
    执行视频评估的主要流程：
    1. 从JSON文件加载知识点列表
    2. 创建视频评估器实例
    3. 获取待评估的视频列表
    4. 批量评估所有视频
    5. 生成并输出评估报告
    
    注意：使用前需要配置正确的文件路径和目录路径。
    """
    json_file = "json_files/long_video_topics_list.json"
    with open(json_file, "r", encoding="utf-8") as f:
        knowledge_points = json.load(f)

    evaluator = VideoEvaluator(request_gemini_with_video)

    video_list = eva_video_list(
        knowledge_points=knowledge_points,
        base_dir="CASES/Sep_ACL_Gemini",
    )

    batch_results = evaluator.evaluate_video_batch(video_list, max_workers=3, use_parallel=True)

    report = evaluator.generate_evaluation_report(batch_results, output_path=None)
    print(report)


if __name__ == "__main__":
    evaluate_main()
