"""根因分析领域服务"""
from collections import Counter
from typing import Optional

from ..models.evidence import Evidence
from ..models.root_cause import RootCause
from ..value_objects.confidence import Confidence


class RootCauseAnalyzer:
    """根因分析服务
    
    职责：
    1. 基于规则的根因推理
    2. 置信度计算
    3. 根因排序
    
    特性：
    - 无状态
    - 纯业务逻辑
    
    注意：
    - 当前实现为基于规则的简单推理
    - 阶段五将集成 LLM 进行更智能的推理
    """
    
    def analyze_by_rules(
        self,
        evidence_list: list[Evidence]
    ) -> list[RootCause]:
        """基于规则的根因分析
        
        根据证据中的关键词和模式，推断可能的根因
        
        Args:
            evidence_list: 证据列表
        
        Returns:
            根因列表（按置信度排序）
        """
        if not evidence_list:
            return []
        
        root_causes = []
        
        # 规则 1: 检查内存相关问题
        memory_evidence = self._find_evidence_by_keyword(
            evidence_list, ["memory", "内存", "heap", "oom", "OutOfMemoryError"]
        )
        if memory_evidence:
            confidence = self._calculate_confidence_by_evidence_count(
                len(memory_evidence), len(evidence_list)
            )
            root_causes.append(RootCause(
                cause="JVM 堆内存泄漏或内存不足",
                confidence=confidence,
                evidence_ids=[e.id for e in memory_evidence]
            ))
        
        # 规则 2: 检查 CPU 相关问题
        cpu_evidence = self._find_evidence_by_keyword(
            evidence_list, ["cpu", "CPU", "处理器", "load", "负载"]
        )
        if cpu_evidence:
            confidence = self._calculate_confidence_by_evidence_count(
                len(cpu_evidence), len(evidence_list)
            )
            root_causes.append(RootCause(
                cause="CPU 负载过高或死循环",
                confidence=confidence,
                evidence_ids=[e.id for e in cpu_evidence]
            ))
        
        # 规则 3: 检查连接池相关问题
        pool_evidence = self._find_evidence_by_keyword(
            evidence_list, ["pool", "连接池", "connection", "timeout", "超时"]
        )
        if pool_evidence:
            confidence = self._calculate_confidence_by_evidence_count(
                len(pool_evidence), len(evidence_list)
            )
            root_causes.append(RootCause(
                cause="数据库连接池耗尽",
                confidence=confidence,
                evidence_ids=[e.id for e in pool_evidence]
            ))
        
        # 规则 4: 检查慢查询相关问题
        slow_query_evidence = self._find_evidence_by_keyword(
            evidence_list, ["slow", "慢", "query", "查询", "SQL"]
        )
        if slow_query_evidence:
            confidence = self._calculate_confidence_by_evidence_count(
                len(slow_query_evidence), len(evidence_list)
            )
            root_causes.append(RootCause(
                cause="慢 SQL 查询导致性能下降",
                confidence=confidence,
                evidence_ids=[e.id for e in slow_query_evidence]
            ))
        
        # 规则 5: 检查 GC 相关问题
        gc_evidence = self._find_evidence_by_keyword(
            evidence_list, ["gc", "GC", "garbage", "垃圾回收", "Full GC"]
        )
        if gc_evidence:
            confidence = self._calculate_confidence_by_evidence_count(
                len(gc_evidence), len(evidence_list)
            )
            root_causes.append(RootCause(
                cause="频繁 Full GC 导致应用暂停",
                confidence=confidence,
                evidence_ids=[e.id for e in gc_evidence]
            ))
        
        # 排序根因（按置信度从高到低）
        root_causes.sort()
        
        # 更新 rank
        for idx, rc in enumerate(root_causes, start=1):
            rc.rank = idx
        
        return root_causes
    
    def _find_evidence_by_keyword(
        self,
        evidence_list: list[Evidence],
        keywords: list[str]
    ) -> list[Evidence]:
        """根据关键词筛选证据"""
        matched = []
        
        for evidence in evidence_list:
            text = f"{evidence.summary} {evidence.source}".lower()
            if any(keyword.lower() in text for keyword in keywords):
                matched.append(evidence)
        
        return matched
    
    def _calculate_confidence_by_evidence_count(
        self,
        matched_count: int,
        total_count: int
    ) -> Confidence:
        """根据证据数量计算置信度
        
        计算公式：
        - 1 条证据：0.4
        - 2 条证据：0.6
        - 3 条及以上：0.8
        - 如果匹配证据占比 > 50%，则 +0.1
        """
        base_confidence = 0.3
        
        if matched_count == 1:
            base_confidence = 0.4
        elif matched_count == 2:
            base_confidence = 0.6
        elif matched_count >= 3:
            base_confidence = 0.8
        
        # 如果匹配证据占比高，增加置信度
        if total_count > 0 and matched_count / total_count > 0.5:
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        return Confidence(base_confidence)
    
    def merge_similar_causes(
        self,
        root_causes: list[RootCause],
        similarity_threshold: float = 0.7
    ) -> list[RootCause]:
        """合并相似的根因
        
        Args:
            root_causes: 根因列表
            similarity_threshold: 相似度阈值（0.0 ~ 1.0）
        
        Returns:
            合并后的根因列表
        """
        if len(root_causes) <= 1:
            return root_causes
        
        # 简单实现：基于关键词重叠度判断相似性
        merged = []
        used_indices = set()
        
        for i, rc1 in enumerate(root_causes):
            if i in used_indices:
                continue
            
            similar_group = [rc1]
            
            for j, rc2 in enumerate(root_causes[i + 1:], start=i + 1):
                if j in used_indices:
                    continue
                
                similarity = self._calculate_text_similarity(rc1.cause, rc2.cause)
                if similarity >= similarity_threshold:
                    similar_group.append(rc2)
                    used_indices.add(j)
            
            # 合并相似根因
            if len(similar_group) > 1:
                merged_cause = self._merge_causes(similar_group)
                merged.append(merged_cause)
            else:
                merged.append(rc1)
        
        # 重新排序
        merged.sort()
        for idx, rc in enumerate(merged, start=1):
            rc.rank = idx
        
        return merged
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现：基于共同单词比例）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        common = words1 & words2
        total = words1 | words2
        
        return len(common) / len(total) if total else 0.0
    
    def _merge_causes(self, causes: list[RootCause]) -> RootCause:
        """合并多个根因为一个"""
        # 选择置信度最高的作为主根因
        primary = max(causes, key=lambda rc: rc.confidence.value)
        
        # 合并证据 ID
        all_evidence_ids = []
        for rc in causes:
            all_evidence_ids.extend(rc.evidence_ids)
        unique_evidence_ids = list(set(all_evidence_ids))
        
        # 计算平均置信度
        avg_confidence = sum(rc.confidence.value for rc in causes) / len(causes)
        
        return RootCause(
            cause=primary.cause,
            confidence=Confidence(min(avg_confidence + 0.1, 1.0)),  # 合并后提升置信度
            evidence_ids=unique_evidence_ids
        )
    
    def explain_confidence(
        self,
        root_cause: RootCause,
        evidence_list: list[Evidence]
    ) -> str:
        """解释置信度的计算依据
        
        Args:
            root_cause: 根因
            evidence_list: 所有证据
        
        Returns:
            置信度解释文本
        """
        evidence_count = len(root_cause.evidence_ids)
        total_evidence = len(evidence_list)
        
        explanation = f"置信度 {root_cause.confidence} 的计算依据:\n"
        explanation += f"- 支持证据数量: {evidence_count}/{total_evidence}\n"
        
        if evidence_count == 1:
            explanation += "- 仅有 1 条证据支持，置信度中等\n"
        elif evidence_count == 2:
            explanation += "- 有 2 条证据支持，置信度较高\n"
        elif evidence_count >= 3:
            explanation += "- 有 3 条及以上证据支持，置信度高\n"
        
        if total_evidence > 0:
            ratio = evidence_count / total_evidence
            if ratio > 0.5:
                explanation += f"- 支持证据占比 {ratio:.1%}，超过 50%\n"
        
        return explanation
