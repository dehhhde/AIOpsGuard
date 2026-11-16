"""证据聚合领域服务"""
from collections import defaultdict
from typing import Optional

from ..models.evidence import Evidence


class EvidenceAggregator:
    """证据聚合服务
    
    职责：
    1. 证据去重
    2. 证据聚合
    3. 证据关联分析
    
    特性：
    - 无状态
    - 纯业务逻辑
    """
    
    def deduplicate(
        self,
        evidence_list: list[Evidence],
        key: str = "source"
    ) -> list[Evidence]:
        """证据去重
        
        根据指定键去重，保留第一个出现的证据
        
        Args:
            evidence_list: 证据列表
            key: 去重键（source: 来源, summary: 摘要）
        
        Returns:
            去重后的证据列表
        
        Examples:
            >>> aggregator = EvidenceAggregator()
            >>> evidence = [Evidence(...), Evidence(...)]
            >>> unique = aggregator.deduplicate(evidence, key="source")
        """
        seen = set()
        unique_evidence = []
        
        for evidence in evidence_list:
            if key == "source":
                value = evidence.source
            elif key == "summary":
                value = evidence.summary
            elif key == "id":
                value = evidence.id
            else:
                raise ValueError(f"Invalid key: {key}")
            
            if value not in seen:
                seen.add(value)
                unique_evidence.append(evidence)
        
        return unique_evidence
    
    def group_by_type(
        self,
        evidence_list: list[Evidence]
    ) -> dict[str, list[Evidence]]:
        """按类型分组证据
        
        将证据按 METRIC、LOG、TRACE 分组
        
        Args:
            evidence_list: 证据列表
        
        Returns:
            分组后的字典 {类型: [证据列表]}
        """
        grouped = defaultdict(list)
        
        for evidence in evidence_list:
            grouped[evidence.type.value].append(evidence)
        
        return dict(grouped)
    
    def group_by_source(
        self,
        evidence_list: list[Evidence]
    ) -> dict[str, list[Evidence]]:
        """按来源分组证据
        
        Args:
            evidence_list: 证据列表
        
        Returns:
            分组后的字典 {来源: [证据列表]}
        """
        grouped = defaultdict(list)
        
        for evidence in evidence_list:
            grouped[evidence.source].append(evidence)
        
        return dict(grouped)
    
    def filter_by_time_overlap(
        self,
        evidence_list: list[Evidence],
        min_overlap_count: int = 2
    ) -> list[Evidence]:
        """筛选时间重叠的证据
        
        找出时间范围相互重叠的证据（可能是关联的）
        
        Args:
            evidence_list: 证据列表
            min_overlap_count: 最小重叠数量（至少与多少其他证据重叠）
        
        Returns:
            时间重叠的证据列表
        """
        result = []
        
        for i, evidence in enumerate(evidence_list):
            overlap_count = 0
            
            for j, other in enumerate(evidence_list):
                if i != j and evidence.time_range.overlaps(other.time_range):
                    overlap_count += 1
            
            if overlap_count >= min_overlap_count - 1:  # -1 因为不包括自己
                result.append(evidence)
        
        return result
    
    def find_related_evidence(
        self,
        target_evidence: Evidence,
        evidence_list: list[Evidence],
        max_time_gap_seconds: float = 60.0
    ) -> list[Evidence]:
        """查找关联证据
        
        查找与目标证据时间接近的其他证据
        
        Args:
            target_evidence: 目标证据
            evidence_list: 所有证据列表
            max_time_gap_seconds: 最大时间间隔（秒）
        
        Returns:
            关联证据列表
        """
        related = []
        
        for evidence in evidence_list:
            if evidence.id == target_evidence.id:
                continue
            
            # 检查时间范围是否重叠
            if target_evidence.time_range.overlaps(evidence.time_range):
                related.append(evidence)
                continue
            
            # 检查时间间隔是否在阈值内
            gap = abs(
                (target_evidence.time_range.start - evidence.time_range.start).total_seconds()
            )
            if gap <= max_time_gap_seconds:
                related.append(evidence)
        
        return related
    
    def calculate_evidence_weight(
        self,
        evidence: Evidence,
        all_evidence: list[Evidence]
    ) -> float:
        """计算证据权重
        
        基于证据的关联性计算权重（0.0 ~ 1.0）
        
        Args:
            evidence: 目标证据
            all_evidence: 所有证据列表
        
        Returns:
            证据权重（关联证据越多，权重越高）
        """
        if not all_evidence or len(all_evidence) == 1:
            return 1.0
        
        related_count = len(self.find_related_evidence(evidence, all_evidence))
        max_related = len(all_evidence) - 1  # 最多关联数
        
        # 基础权重 0.3 + 关联权重 0.7
        base_weight = 0.3
        related_weight = 0.7 * (related_count / max_related) if max_related > 0 else 0.0
        
        return base_weight + related_weight
    
    def summarize(
        self,
        evidence_list: list[Evidence]
    ) -> dict:
        """证据摘要统计
        
        Args:
            evidence_list: 证据列表
        
        Returns:
            统计摘要字典
        """
        if not evidence_list:
            return {
                "total": 0,
                "by_type": {},
                "time_span_seconds": 0,
            }
        
        by_type = self.group_by_type(evidence_list)
        
        # 计算时间跨度
        all_starts = [e.time_range.start for e in evidence_list]
        all_ends = [e.time_range.end for e in evidence_list]
        time_span = (max(all_ends) - min(all_starts)).total_seconds()
        
        return {
            "total": len(evidence_list),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "time_span_seconds": time_span,
            "sources": list(set(e.source for e in evidence_list)),
        }
