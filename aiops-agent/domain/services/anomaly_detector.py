"""异常检测领域服务"""
import statistics
from typing import Optional


class AnomalyDetector:
    """异常检测服务
    
    提供多种异常检测算法：
    1. 阈值检测（Threshold Detection）
    2. 3-sigma 检测（Statistical Detection）
    3. 环比检测（Comparison Detection）
    
    特性：
    - 无状态（每次检测独立）
    - 纯业务逻辑（无基础设施依赖）
    """
    
    def threshold_detect(
        self,
        values: list[float],
        threshold: float,
        direction: str = "above"
    ) -> bool:
        """阈值检测
        
        检测值是否超过固定阈值
        
        Args:
            values: 数值列表
            threshold: 阈值
            direction: 检测方向（above: 超过阈值, below: 低于阈值）
        
        Returns:
            是否检测到异常
        
        Examples:
            >>> detector = AnomalyDetector()
            >>> detector.threshold_detect([70, 85, 95], threshold=80, direction="above")
            True
        """
        if not values:
            return False
        
        if direction == "above":
            return any(v > threshold for v in values)
        elif direction == "below":
            return any(v < threshold for v in values)
        else:
            raise ValueError(f"Invalid direction: {direction}")
    
    def sigma_detect(
        self,
        values: list[float],
        sigma: float = 3.0
    ) -> tuple[bool, Optional[dict]]:
        """3-sigma 检测（标准差检测）
        
        基于统计学原理，检测偏离均值超过 N 个标准差的值
        
        Args:
            values: 数值列表（至少需要 3 个值）
            sigma: 标准差倍数（默认 3.0）
        
        Returns:
            (是否检测到异常, 异常详情)
        
        Examples:
            >>> detector = AnomalyDetector()
            >>> is_anomaly, detail = detector.sigma_detect([10, 12, 11, 13, 50])
            >>> is_anomaly
            True
            >>> detail['anomaly_values']
            [50]
        """
        if len(values) < 3:
            return False, None
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        if stdev == 0:
            return False, None
        
        anomaly_values = []
        for v in values:
            z_score = abs(v - mean) / stdev
            if z_score > sigma:
                anomaly_values.append(v)
        
        if anomaly_values:
            return True, {
                "mean": mean,
                "stdev": stdev,
                "sigma": sigma,
                "anomaly_values": anomaly_values,
                "z_scores": [(v - mean) / stdev for v in anomaly_values]
            }
        
        return False, None
    
    def compare_detect(
        self,
        current: float,
        baseline: float,
        threshold: float = 0.5
    ) -> tuple[bool, Optional[dict]]:
        """环比检测（对比检测）
        
        对比当前值与基线值，检测增幅或降幅是否超过阈值
        
        Args:
            current: 当前值
            baseline: 基线值（如上周同时段）
            threshold: 变化阈值（默认 0.5 即 50%）
        
        Returns:
            (是否检测到异常, 异常详情)
        
        Examples:
            >>> detector = AnomalyDetector()
            >>> is_anomaly, detail = detector.compare_detect(150, 100, threshold=0.3)
            >>> is_anomaly
            True
            >>> detail['change_rate']
            0.5
        """
        if baseline == 0:
            # 基线为 0 时，如果当前值不为 0 则认为异常
            return current != 0, {"change_rate": float("inf") if current != 0 else 0}
        
        change_rate = abs(current - baseline) / baseline
        
        if change_rate > threshold:
            return True, {
                "current": current,
                "baseline": baseline,
                "change_rate": change_rate,
                "change_direction": "increase" if current > baseline else "decrease"
            }
        
        return False, None
    
    def detect_spike(
        self,
        values: list[float],
        window_size: int = 5,
        spike_threshold: float = 2.0
    ) -> tuple[bool, Optional[list[int]]]:
        """尖峰检测
        
        检测短时间内的突然上升（spike）
        
        Args:
            values: 时间序列数值
            window_size: 滑动窗口大小
            spike_threshold: 尖峰阈值（相对于窗口均值的倍数）
        
        Returns:
            (是否检测到尖峰, 尖峰位置索引列表)
        """
        if len(values) < window_size:
            return False, None
        
        spike_indices = []
        
        for i in range(window_size, len(values)):
            window = values[i - window_size:i]
            window_mean = statistics.mean(window)
            
            if window_mean == 0:
                continue
            
            if values[i] > window_mean * spike_threshold:
                spike_indices.append(i)
        
        return len(spike_indices) > 0, spike_indices if spike_indices else None
    
    def detect_trend(
        self,
        values: list[float],
        min_length: int = 5
    ) -> tuple[bool, Optional[str]]:
        """趋势检测
        
        检测持续上升或下降趋势
        
        Args:
            values: 时间序列数值
            min_length: 最小趋势长度
        
        Returns:
            (是否检测到趋势, 趋势方向: 'increasing' 或 'decreasing')
        """
        if len(values) < min_length:
            return False, None
        
        # 检查是否单调递增
        increasing = all(values[i] < values[i + 1] for i in range(len(values) - 1))
        if increasing:
            return True, "increasing"
        
        # 检查是否单调递减
        decreasing = all(values[i] > values[i + 1] for i in range(len(values) - 1))
        if decreasing:
            return True, "decreasing"
        
        return False, None
