"""AnomalyDetector 领域服务测试"""
import pytest

from domain.services.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """AnomalyDetector 测试类"""
    
    def test_threshold_detect_above(self):
        """测试阈值检测（超过阈值）"""
        detector = AnomalyDetector()
        
        # 有值超过阈值
        assert detector.threshold_detect([70, 85, 95], threshold=80, direction="above") is True
        
        # 所有值都低于阈值
        assert detector.threshold_detect([70, 75, 79], threshold=80, direction="above") is False
        
        # 边界值
        assert detector.threshold_detect([80], threshold=80, direction="above") is False
    
    def test_threshold_detect_below(self):
        """测试阈值检测（低于阈值）"""
        detector = AnomalyDetector()
        
        # 有值低于阈值
        assert detector.threshold_detect([15, 25, 35], threshold=20, direction="below") is True
        
        # 所有值都高于阈值
        assert detector.threshold_detect([25, 30, 35], threshold=20, direction="below") is False
    
    def test_threshold_detect_empty_list(self):
        """测试空列表"""
        detector = AnomalyDetector()
        assert detector.threshold_detect([], threshold=80, direction="above") is False
    
    def test_sigma_detect_normal(self):
        """测试 3-sigma 检测（正常数据）"""
        detector = AnomalyDetector()
        
        # 正常分布数据
        is_anomaly, detail = detector.sigma_detect([10, 12, 11, 13, 12, 10])
        assert is_anomaly is False
        assert detail is None
    
    def test_sigma_detect_with_anomaly(self):
        """测试 3-sigma 检测（有异常）"""
        detector = AnomalyDetector()
        
        # 有一个明显异常值
        is_anomaly, detail = detector.sigma_detect([10, 12, 11, 13, 50])
        assert is_anomaly is True
        assert detail is not None
        assert 50 in detail["anomaly_values"]
    
    def test_sigma_detect_insufficient_data(self):
        """测试数据不足"""
        detector = AnomalyDetector()
        
        is_anomaly, detail = detector.sigma_detect([10, 12])
        assert is_anomaly is False
        assert detail is None
    
    def test_compare_detect_increase(self):
        """测试环比检测（增长）"""
        detector = AnomalyDetector()
        
        # 增长 50%
        is_anomaly, detail = detector.compare_detect(
            current=150,
            baseline=100,
            threshold=0.3
        )
        assert is_anomaly is True
        assert detail is not None
        assert detail["change_rate"] == 0.5
        assert detail["change_direction"] == "increase"
    
    def test_compare_detect_decrease(self):
        """测试环比检测（下降）"""
        detector = AnomalyDetector()
        
        # 下降 50%
        is_anomaly, detail = detector.compare_detect(
            current=50,
            baseline=100,
            threshold=0.3
        )
        assert is_anomaly is True
        assert detail["change_direction"] == "decrease"
    
    def test_compare_detect_normal(self):
        """测试环比检测（正常变化）"""
        detector = AnomalyDetector()
        
        # 仅增长 10%
        is_anomaly, detail = detector.compare_detect(
            current=110,
            baseline=100,
            threshold=0.3
        )
        assert is_anomaly is False
    
    def test_detect_spike(self):
        """测试尖峰检测"""
        detector = AnomalyDetector()
        
        # 有明显尖峰
        values = [10, 12, 11, 13, 50, 12, 11]
        is_spike, indices = detector.detect_spike(values, window_size=3, spike_threshold=2.0)
        assert is_spike is True
        assert 4 in indices  # 索引 4 是尖峰（值 50）
    
    def test_detect_trend_increasing(self):
        """测试趋势检测（上升）"""
        detector = AnomalyDetector()
        
        values = [10, 20, 30, 40, 50]
        has_trend, direction = detector.detect_trend(values, min_length=5)
        assert has_trend is True
        assert direction == "increasing"
    
    def test_detect_trend_decreasing(self):
        """测试趋势检测（下降）"""
        detector = AnomalyDetector()
        
        values = [50, 40, 30, 20, 10]
        has_trend, direction = detector.detect_trend(values, min_length=5)
        assert has_trend is True
        assert direction == "decreasing"
    
    def test_detect_trend_no_trend(self):
        """测试趋势检测（无趋势）"""
        detector = AnomalyDetector()
        
        values = [10, 20, 15, 30, 25]
        has_trend, direction = detector.detect_trend(values, min_length=5)
        assert has_trend is False
        assert direction is None
